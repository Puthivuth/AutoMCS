import logging
from celery import shared_task
from django.utils import timezone
from .models import ExportJob, ExtractionJob
from .services import exporter
from .services.files import render_page_png
from .services.providers.base import ProviderError
from .services.providers import get_provider
from .services.tables import save_prediction

log = logging.getLogger(__name__)


def _process(job, item, prov):
    doc = item.document
    item.status, item.started_at = "running", timezone.now(); item.save()
    pages = job.params.get("pages") or list(range(1, doc.page_count + 1))
    cells = unc = 0; review = False
    try:
        for pn in pages:
            if not 1 <= pn <= doc.page_count: continue
            r = prov.extract_page(render_page_png(doc, pn), pn)
            _, n, u = save_prediction(doc, pn, item, prov.name, r.model_id, r.columns, r.rows, r.raw_output, r.warnings, r.bboxes, r.confidences)
            cells += n; unc += u; review |= bool(r.warnings)
        item.status = "needs_review" if review else "done"
    except ProviderError as e:
        item.status, item.error = "failed", f"{e}{' (retryable)' if e.retryable else ''}"
    except Exception:
        log.exception("extraction failed for document %s", doc.id)
        item.status, item.error = "failed", "Unexpected processing error; see server logs."
    item.cells_extracted, item.uncertain, item.finished_at = cells, unc, timezone.now(); item.save()


@shared_task
def run_extraction_job(job_id):
    job = ExtractionJob.objects.get(pk=job_id)
    if job.status == "cancelled": return
    job.status = "running"; job.save(update_fields=["status"])
    prov = get_provider(job.provider)
    try:
        prov.prepare()
    except Exception as e:
        job.status, job.error, job.finished_at = "failed", str(e)[:1000], timezone.now(); job.save(); return
    for item in job.items.filter(status="pending").select_related("document"):
        job.refresh_from_db(fields=["cancel_requested"])
        if job.cancel_requested:
            job.items.filter(status="pending").update(status="cancelled"); break
        _process(job, item, prov)          # one failing document never stops the others
    st = list(job.items.values_list("status", flat=True))
    job.status = ("cancelled" if job.cancel_requested else "failed" if st and all(s == "failed" for s in st)
                  else "completed_with_errors" if "failed" in st else "completed")
    job.finished_at = timezone.now(); job.save()


@shared_task
def run_export(export_id):
    job = ExportJob.objects.get(pk=export_id); job.status = "running"; job.save()
    try:
        job.file_path, job.summary = exporter.build_zip(job); job.status = "done"
    except Exception as e:
        log.exception("export failed"); job.status, job.error = "failed", str(e)[:500]
    job.finished_at = timezone.now(); job.save()


@shared_task
def prepare_local_model():
    pass

