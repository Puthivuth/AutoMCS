"""Download -> validate -> load -> readiness-check for the local model. Runs inside the 'local' Celery worker."""
import hashlib, json, shutil, time
from pathlib import Path
from django.conf import settings
from django.db import transaction

NAME = "deepseek-r1-distill-qwen-1.5b"
_rt = {"tok": None, "model": None}          # per worker process
WANTED = (".json", ".safetensors", ".txt", ".model")


class ModelNotReady(Exception):
    pass


def cfg(): return settings.AUTOMCS
def model_dir() -> Path: return Path(cfg()["LOCAL_MODEL_DIR"])
def model_label(): return f"{cfg()['LOCAL_MODEL_REPO']}@{(cfg()['LOCAL_MODEL_REVISION'] or 'unpinned')[:12]}"


def installation():
    from ..models import ModelInstallation
    obj, _ = ModelInstallation.objects.get_or_create(name=NAME, defaults=dict(
        repo=cfg()["LOCAL_MODEL_REPO"], revision=cfg()["LOCAL_MODEL_REVISION"], path=str(model_dir())))
    return obj


def config_problems():
    c = cfg(); p = []
    if not installed() and not c["AUTO_DOWNLOAD"]: p.append("Model files are missing and automatic download is disabled.")
    if not installed() and c["AUTO_DOWNLOAD"] and not c["LOCAL_MODEL_REVISION"]:
        p.append("Set LOCAL_MODEL_REVISION to a pinned commit hash before downloading.")
    return p


def installed() -> bool:
    mf = model_dir() / "manifest.json"
    try:
        m = json.loads(mf.read_text())
        return (m.get("status") == "installed" and m.get("revision") == cfg()["LOCAL_MODEL_REVISION"]
                and all((model_dir() / f).is_file() and (model_dir() / f).stat().st_size == s for f, s in m["files"].items()))
    except Exception:
        return False


def status() -> dict:
    i = installation()
    if i.status in ("missing", "failed", "downloaded") and installed() and i.status != "failed":
        i.status = "downloaded"; i.save(update_fields=["status"])
    return dict(status=i.status, progress=i.progress, detail=i.detail, repo=i.repo, revision=cfg()["LOCAL_MODEL_REVISION"],
                path=str(model_dir()), installed=installed(), auto_download=cfg()["AUTO_DOWNLOAD"],
                loaded=_rt["model"] is not None, problems=config_problems())


def _set(i, **kw):
    for k, v in kw.items(): setattr(i, k, v)
    i.save()


def download():
    from ..models import ModelInstallation
    c = cfg(); i = installation()
    if installed(): return
    if not c["AUTO_DOWNLOAD"]: raise ModelNotReady("Model is missing and automatic download is disabled.")
    if not c["LOCAL_MODEL_REVISION"]: raise ModelNotReady("LOCAL_MODEL_REVISION must be a pinned commit hash.")
    with transaction.atomic():      # only one worker may download
        claimed = ModelInstallation.objects.filter(pk=i.pk).exclude(status__in=["downloading", "loading"]).update(
            status="downloading", progress=0, detail="Starting download")
    if not claimed:
        for _ in range(3600):       # someone else is downloading: wait for them
            i.refresh_from_db()
            if i.status not in ("downloading", "loading"): break
            time.sleep(2)
        if not installed(): raise ModelNotReady(f"Model download did not finish: {i.detail}")
        return
    try:
        from huggingface_hub import HfApi, hf_hub_download
        info = HfApi().model_info(c["LOCAL_MODEL_REPO"], revision=c["LOCAL_MODEL_REVISION"], files_metadata=True)
        files = [s for s in info.siblings if s.rfilename.endswith(WANTED) and "/" not in s.rfilename]
        total = sum(s.size or 0 for s in files)
        model_dir().mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(model_dir()).free < total * 1.15: raise ModelNotReady("Not enough free disk space for the model.")
        done = 0; manifest = {}
        for s in files:
            hf_hub_download(c["LOCAL_MODEL_REPO"], s.rfilename, revision=c["LOCAL_MODEL_REVISION"], local_dir=str(model_dir()))
            p = model_dir() / s.rfilename
            if s.size and p.stat().st_size != s.size: raise ModelNotReady(f"Size mismatch for {s.rfilename}.")
            sha = getattr(getattr(s, "lfs", None), "sha256", None)
            if sha:
                h = hashlib.sha256()
                with open(p, "rb") as fh:
                    for b in iter(lambda: fh.read(1 << 20), b""): h.update(b)
                if h.hexdigest() != sha: raise ModelNotReady(f"Checksum mismatch for {s.rfilename}.")
            manifest[s.rfilename] = p.stat().st_size; done += s.size or 0
            ModelInstallation.objects.filter(pk=i.pk).update(progress=100 * done / max(total, 1), detail=f"Downloaded {s.rfilename}")
        (model_dir() / "manifest.json").write_text(json.dumps(dict(
            repo=c["LOCAL_MODEL_REPO"], revision=c["LOCAL_MODEL_REVISION"], format="safetensors", status="installed", files=manifest), indent=1))
        ModelInstallation.objects.filter(pk=i.pk).update(status="downloaded", progress=100, detail="Downloaded and verified", revision=c["LOCAL_MODEL_REVISION"])
    except Exception as e:
        ModelInstallation.objects.filter(pk=i.pk).update(status="failed", detail=str(e)[:500])
        raise ModelNotReady(str(e))


def load():
    from ..models import ModelInstallation
    i = installation()
    if not installed(): raise ModelNotReady("Model files are not installed.")
    ModelInstallation.objects.filter(pk=i.pk).update(status="loading", detail="Loading model")
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(str(model_dir()), local_files_only=True)
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        mdl = AutoModelForCausalLM.from_pretrained(str(model_dir()), local_files_only=True,
                torch_dtype=torch.bfloat16 if dev == "cuda" else torch.float32).to(dev).eval()
        _rt.update(tok=tok, model=mdl)
        out = generate('Reply with exactly: {"ok": true}', max_new_tokens=16)      # readiness check
        if not out.strip(): raise ModelNotReady("Readiness check returned empty output.")
        ModelInstallation.objects.filter(pk=i.pk).update(status="ready", detail=f"Ready on {dev}")
    except Exception as e:
        _rt.update(tok=None, model=None)
        ModelInstallation.objects.filter(pk=i.pk).update(status="failed", detail=str(e)[:500])
        raise ModelNotReady(str(e))


def ensure_ready():
    if _rt["model"] is not None: return
    download(); load()


def generate(prompt: str, max_new_tokens: int = 3072) -> str:
    tok, mdl = _rt["tok"], _rt["model"]
    if mdl is None: raise ModelNotReady("Model is not loaded.")
    import torch
    ids = tok.apply_chat_template([{"role": "user", "content": prompt}], add_generation_prompt=True, return_tensors="pt").to(mdl.device)
    with torch.no_grad():
        out = mdl.generate(ids, max_new_tokens=max_new_tokens, do_sample=False)     # greedy = reproducible
    return tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
