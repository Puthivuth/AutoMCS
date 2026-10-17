import os
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.validators import validate_email
from django.db.models import Count, Q
from django.http import FileResponse, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework import status as st
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from . import models as m, serializers as sz, tasks
from .permissions import audit, obj_for, scoped
from .services import evaluation, files, model_manager
from .services.decimals import normalize
from .services.providers.base import ProviderError
from .services.providers.deepseek import get_provider

User = get_user_model()
class LoginThrottle(AnonRateThrottle): scope = "login"
class ContactThrottle(AnonRateThrottle): scope = "contact"
def bad(msg, code=400): return Response({"detail": msg}, status=code)
def me_data(u): return {"id": u.id, "username": u.username, "email": u.email, "is_admin": u.is_staff}


# ---------- auth & public ----------
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request): return Response({"csrfToken": get_token(request)})

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login_view(request):
    ident = str(request.data.get("username", "")).strip(); pw = str(request.data.get("password", ""))
    u = User.objects.filter(email__iexact=ident).first() if "@" in ident else None
    user = authenticate(request, username=u.username if u else ident, password=pw)
    if not user: return bad("Invalid username or password.", 401)
    login(request, user); audit(user, "login"); return Response(me_data(user))

@api_view(["POST"])
def logout_view(request): logout(request); return Response({"ok": True})

@api_view(["GET"])
def me(request): return Response(me_data(request.user))

@api_view(["GET"])
@permission_classes([AllowAny])
def public_config(request):
    s = m.SiteSettings.get()
    return Response({"supervisor": s.supervisor, "institution": s.institution, "contact_email": s.contact_email})

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ContactThrottle])
def contact(request):
    d = request.data
    if d.get("website"): return Response({"ok": True})          # honeypot
    name, email, msg = str(d.get("name", "")).strip(), str(d.get("email", "")).strip(), str(d.get("message", "")).strip()
    try: validate_email(email)
    except Exception: return bad("Enter a valid email address.")
    if not name or len(msg) < 10 or len(msg) > 4000: return bad("Name and a message of 10–4000 characters are required.")
    m.ContactMessage.objects.create(name=name[:120], email=email, message=msg); return Response({"ok": True})


# ---------- projects ----------
@api_view(["GET", "POST"])
def projects(request):
    if request.method == "POST":
        s = sz.ProjectS(data=request.data); s.is_valid(raise_exception=True)
        p = s.save(owner=request.user); audit(request.user, "project.create", p, p.id)
        return Response(sz.ProjectS(p).data, status=201)
    qs = m.Project.for_user(request.user).filter(archived=request.query_params.get("archived") == "1").order_by("name")
    return Response(sz.ProjectS(qs, many=True).data)

@api_view(["GET", "PATCH", "DELETE"])
def project_detail(request, pk):
    p = get_object_or_404(m.Project.for_user(request.user), pk=pk)
    if request.method == "GET": return Response(sz.ProjectS(p).data)
    if p.owner_id != request.user.id: return bad("Only the owner can change a project.", 403)
    if request.method == "DELETE":              # archive, never destroy research data
        p.archived = True; p.save(); audit(request.user, "project.archive", p, p.id); return Response(status=204)
    s = sz.ProjectS(p, data=request.data, partial=True); s.is_valid(raise_exception=True); s.save()
    return Response(s.data)

@api_view(["GET"])
def dashboard(request, pk):
    p = get_object_or_404(m.Project.for_user(request.user), pk=pk)
    docs = m.Document.objects.filter(project=p); cells = m.Cell.objects.filter(document__project=p)
    with_cells = cells.values("document").distinct().count()
    cs = dict(cells.values_list("status").annotate(n=Count("id")))
    jobs = dict(m.ExtractionJob.objects.filter(project=p).values_list("status").annotate(n=Count("id")))
    awaiting = m.Document.objects.filter(project=p).filter(cells__status__in=["unreviewed", "corrected", "rejected"]).distinct().count()
    return Response({"documents": docs.count(), "images": docs.filter(kind="image").count(), "pdfs": docs.filter(kind="pdf").count(),
        "awaiting_extraction": docs.count() - with_cells, "processing": jobs.get("running", 0) + jobs.get("queued", 0),
        "awaiting_review": awaiting, "completed_jobs": jobs.get("completed", 0) + jobs.get("completed_with_errors", 0),
        "failed_jobs": jobs.get("failed", 0), "predicted_cells": cells.exclude(predicted_value=None).count(),
        "corrected_cells": cs.get("corrected", 0), "approved_cells": cs.get("approved", 0),
        "activity": list(m.AuditLog.objects.filter(project=p).values("action", "target", "created_at", "user__username")[:8])})


# ---------- documents ----------
@api_view(["GET", "POST"])
def project_documents(request, pk):
    p = get_object_or_404(m.Project.for_user(request.user), pk=pk)
    if request.method == "GET":
        return Response(sz.DocumentS(m.Document.objects.filter(project=p).prefetch_related("cells"), many=True).data)
    fl = request.FILES.getlist("files"); paths = request.POST.getlist("paths")
    if len(fl) > settings.AUTOMCS["MAX_BATCH_FILES"]: return bad(f"At most {settings.AUTOMCS['MAX_BATCH_FILES']} files per request.")
    res = []
    for i, f in enumerate(fl):
        try:
            kind, mime, pages, sha = files.inspect_upload(f)
            if m.Document.objects.filter(project=p, sha256=sha).exists():
                res.append({"name": f.name, "status": "duplicate"}); continue
            d = m.Document(project=p, original_name=files.safe_name(f.name), relative_path=files.clean_relpath(paths[i]) if i < len(paths) else "",
                           kind=kind, mime=mime, size=f.size, sha256=sha, page_count=pages, uploaded_by=request.user)
            d.file.save(f.name, f, save=False); d.save()
            res.append({"name": f.name, "status": "created", "id": d.id})
        except files.UploadRejected as e:
            res.append({"name": f.name, "status": "rejected", "reason": str(e)})
    audit(request.user, "documents.upload", p, created=sum(r["status"] == "created" for r in res))
    return Response({"results": res})

def _doc(request, pk): return obj_for(m.Document, request.user, pk, select=("project",))

@api_view(["GET"])
def document_detail(request, pk): return Response(sz.DocumentS(_doc(request, pk)).data)

@api_view(["GET"])
def document_file(request, pk):
    d = _doc(request, pk)
    return FileResponse(d.file.open("rb"), content_type=d.mime, as_attachment=request.query_params.get("download") == "1", filename=d.original_name)

@api_view(["GET"])
def document_page_image(request, pk, page):
    d = _doc(request, pk)
    if not 1 <= page <= d.page_count: return bad("No such page.", 404)
    r = HttpResponse(files.render_page_png(d, page), content_type="image/png"); r["Cache-Control"] = "private, max-age=300"; return r

@api_view(["GET"])
def document_table(request, pk):
    d = _doc(request, pk)
    return Response({"document": sz.DocumentS(d).data, "cells": sz.CellS(d.cells.all(), many=True).data})

@api_view(["GET"])
def document_predictions(request, pk):
    d = _doc(request, pk)
    return Response([{"id": p.id, "page": p.page_number, "provider": p.provider, "model_id": p.model_id, "warnings": p.warnings,
                      "created_at": p.created_at, "raw_output": p.raw_output[:5000]} for p in d.predictions.all()[:50]])


# ---------- extraction ----------
def _start(user, project, docs, provider, pages):
    try: prov = get_provider(provider)
    except ProviderError as e: return bad(str(e))
    problems = prov.preflight()
    if problems: return Response({"detail": "Provider is not configured.", "problems": problems}, status=400)
    if not docs: return bad("No documents selected.")
    job = m.ExtractionJob.objects.create(project=project, provider=provider, model_id=prov.model_id, params={"pages": pages}, created_by=user)
    m.JobItem.objects.bulk_create([m.JobItem(job=job, document=d) for d in docs])
    tasks.run_extraction_job.apply_async(args=[job.id], queue="local" if provider == "deepseek" else "default")
    audit(user, "extract.start", project, job.id, provider=provider, documents=len(docs))
    return Response(sz.JobS(job).data, status=202)

@api_view(["POST"])
def project_extract(request, pk):
    p = get_object_or_404(m.Project.for_user(request.user), pk=pk)
    docs = list(m.Document.objects.filter(project=p, id__in=request.data.get("document_ids", [])))
    return _start(request.user, p, docs, request.data.get("provider", ""), request.data.get("pages"))

@api_view(["POST"])
def document_extract(request, pk):
    d = _doc(request, pk)
    return _start(request.user, d.project, [d], request.data.get("provider", ""), request.data.get("pages"))

@api_view(["GET"])
def providers(request):
    s = m.SiteSettings.get(); out = []
    for name in ("gemini", "deepseek"):
        pr = get_provider(name); pb = pr.preflight()
        out.append({"name": name, "label": pr.label, "model_id": pr.model_id, "problems": pb, "ready": not pb, "default": s.default_provider == name})
    return Response(out)

@api_view(["GET"])
def project_jobs(request, pk):
    p = get_object_or_404(m.Project.for_user(request.user), pk=pk)
    return Response(sz.JobS(m.ExtractionJob.objects.filter(project=p).prefetch_related("items__document")[:30], many=True).data)

@api_view(["GET"])
def job_detail(request, pk): return Response(sz.JobS(obj_for(m.ExtractionJob, request.user, pk)).data)

@api_view(["POST"])
def job_retry(request, pk):
    j = obj_for(m.ExtractionJob, request.user, pk)
    if j.status in ("queued", "running"): return bad("Job is still active.")
    n = j.items.filter(status__in=["failed", "cancelled"]).update(status="pending", error="")
    if not n: return bad("Nothing to retry.")
    j.status, j.cancel_requested, j.error = "queued", False, ""; j.save()
    tasks.run_extraction_job.apply_async(args=[j.id], queue="local" if j.provider == "deepseek" else "default")
    return Response(sz.JobS(j).data, status=202)

@api_view(["POST"])
def job_cancel(request, pk):
    j = obj_for(m.ExtractionJob, request.user, pk)
    if j.status not in ("queued", "running"): return bad("Job is not active.")
    j.cancel_requested = True
    if j.status == "queued": j.status = "cancelled"; j.items.update(status="cancelled")
    j.save(); return Response(sz.JobS(j).data)


# ---------- labeling & review ----------
def _cell(request, pk): return obj_for(m.Cell, request.user, pk, path="document__project", select=("document__project",))
def _event(c, user, action, source, old, new, note=""):
    m.CellEvent.objects.create(cell=c, user=user, action=action, source=source, old_value=old, new_value=new, note=note)

@api_view(["PATCH"])
def cell_label(request, pk):
    c = _cell(request, pk); n = normalize(request.data.get("value"))
    if n.state == "invalid": return bad("Not a valid decimal number.")
    old = c.effective_value; reopened = c.status == "approved"
    c.verified_value, c.status, c.updated_by = n.value, "corrected", request.user
    c.note = request.data.get("note", c.note); c.save()
    _event(c, request.user, "reopen" if reopened else "label", "human_correction" if c.predicted_value is not None else "manual", old, n.value, c.note)
    return Response(sz.CellS(c).data)

def _approve(c, user):
    if c.status == "approved": return True
    if c.status == "unreviewed":
        if "invalid_decimal" in c.flag_list: return False
        c.verified_value = c.predicted_value
    elif c.status == "rejected": return False
    c.status, c.updated_by = "approved", user; c.save()
    _event(c, user, "approve", "verification", c.predicted_value, c.verified_value); return True

@api_view(["POST"])
def cell_review(request, pk):
    c = _cell(request, pk); a = request.data.get("action")
    if a == "approve":
        if not _approve(c, request.user): return bad("This value is invalid or rejected; correct it first.")
    elif a == "reject":
        old = c.effective_value; c.status, c.updated_by = "rejected", request.user; c.save(); _event(c, request.user, "reject", "verification", old, None, request.data.get("note", ""))
    elif a == "reopen":
        c.status, c.updated_by = "unreviewed" if c.verified_value is None else "corrected", request.user; c.save(); _event(c, request.user, "reopen", "verification", c.verified_value, c.verified_value)
    else: return bad("action must be approve, reject or reopen.")
    return Response(sz.CellS(c).data)

@api_view(["GET"])
def cell_history(request, pk): return Response(sz.EventS(_cell(request, pk).events.select_related("user"), many=True).data)

@api_view(["POST"])
def document_approve(request, pk):
    d = _doc(request, pk); ok = skipped = 0
    for c in d.cells.exclude(status="approved"):
        if _approve(c, request.user): ok += 1
        else: skipped += 1
    audit(request.user, "document.approve", d.project, d.id, approved=ok, skipped=skipped)
    return Response({"approved": ok, "skipped": skipped})

@api_view(["GET"])
def review_queue(request, pk):
    p = get_object_or_404(m.Project.for_user(request.user), pk=pk); q = request.query_params
    cells = m.Cell.objects.filter(document__project=p).exclude(status="approved").select_related("document")
    reason = q.get("reason", "flagged")
    cells = cells.filter(flags__contains=reason) if reason in ("invalid_decimal", "rounded", "low_confidence") else \
            cells.filter(status__in=["corrected", "rejected"]) if reason == "pending_approval" else cells.exclude(flags="")
    if q.get("document"): cells = cells.filter(document_id=q["document"])
    if q.get("provider"): cells = cells.filter(latest_prediction__provider=q["provider"])
    bad_json = m.JobItem.objects.filter(job__project=p, status="needs_review").values("document", "document__original_name", "job__provider")[:50]
    return Response({"cells": [dict(sz.CellS(c).data, document=c.document_id, document_name=c.document.original_name) for c in cells[:200]],
                     "invalid_json": list(bad_json)})


# ---------- evaluation / export / models / training ----------
@api_view(["GET", "POST"])
def project_evaluations(request, pk):
    p = get_object_or_404(m.Project.for_user(request.user), pk=pk)
    if request.method == "GET": return Response(sz.EvalS(p.evaluations.all()[:20], many=True).data)
    d = request.data; docs = m.Document.objects.filter(project=p)
    if d.get("document_ids"): docs = docs.filter(id__in=d["document_ids"])
    prov, mid = d.get("provider", ""), d.get("model_id", "")
    try: met = evaluation.evaluate(p, docs, prov, mid, str(d.get("tolerance", "0")))
    except Exception: return bad("Invalid evaluation settings.")
    run = m.EvaluationRun.objects.create(project=p, created_by=request.user, provider=prov, model_id=mid,
        rules={**evaluation.RULES, "tolerance": str(d.get("tolerance", "0")), "rounding": settings.AUTOMCS["ROUNDING"], "document_ids": d.get("document_ids")}, metrics=met)
    return Response(sz.EvalS(run).data, status=201)

@api_view(["GET"])
def evaluation_detail(request, pk): return Response(sz.EvalS(obj_for(m.EvaluationRun, request.user, pk)).data)

@api_view(["GET", "POST"])
def project_exports(request, pk):
    p = get_object_or_404(m.Project.for_user(request.user), pk=pk)
    if request.method == "GET": return Response(sz.ExportS(p.exports.all()[:20], many=True).data)
    d = request.data
    opts = {"document_ids": d.get("document_ids") or None, "allow_partial": bool(d.get("allow_partial")),
            "include_history": bool(d.get("include_history")), "jsonl": bool(d.get("jsonl"))}
    job = m.ExportJob.objects.create(project=p, created_by=request.user, options=opts)
    tasks.run_export.apply_async(args=[job.id]); audit(request.user, "export.create", p, job.id)
    return Response(sz.ExportS(job).data, status=202)

@api_view(["GET"])
def export_detail(request, pk): return Response(sz.ExportS(obj_for(m.ExportJob, request.user, pk)).data)

@api_view(["GET"])
def export_download(request, pk):
    e = obj_for(m.ExportJob, request.user, pk)
    if e.status != "done" or not os.path.isfile(e.file_path): return bad("Export is not ready.", 404)
    audit(request.user, "export.download", e.project, e.id)
    return FileResponse(open(e.file_path, "rb"), as_attachment=True, filename=f"automcs_dataset_{e.id}.zip")

@api_view(["GET"])
def local_model_status(request): return Response(model_manager.status())

@api_view(["POST"])
@permission_classes([IsAdminUser])
def local_model_prepare(request):
    tasks.prepare_local_model.apply_async(queue="local"); audit(request.user, "model.prepare"); return Response({"queued": True}, status=202)

@api_view(["GET", "PATCH"])
@permission_classes([IsAdminUser])
def site_settings(request):
    s = m.SiteSettings.get()
    if request.method == "PATCH":
        for k in ("default_provider", "gemini_model", "supervisor", "institution", "contact_email"):
            if k in request.data: setattr(s, k, request.data[k])
        s.save(); audit(request.user, "settings.update")
    return Response({k: getattr(s, k) for k in ("default_provider", "gemini_model", "supervisor", "institution", "contact_email")})

@api_view(["GET", "POST"])
def training_runs(request, pk):
    get_object_or_404(m.Project.for_user(request.user), pk=pk)
    if request.method == "POST": return Response({"detail": "Training is not available yet. No training job was started."}, status=501)
    return Response({"status": "unavailable", "runs": []})
