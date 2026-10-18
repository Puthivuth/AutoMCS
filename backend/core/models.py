import os, uuid
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import Q

User = settings.AUTH_USER_MODEL


def originals_storage():
    return FileSystemStorage(location=settings.ORIGINALS_DIR)   # no base_url: never served publicly


def original_path(inst, filename):
    return f"{inst.project_id}/{uuid.uuid4().hex}{os.path.splitext(filename)[1].lower()}"


class Project(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="owned_projects")
    members = models.ManyToManyField(User, blank=True, related_name="shared_projects")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def for_user(cls, user):
        return cls.objects.filter(Q(owner=user) | Q(members=user)).distinct()


class Document(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="documents")
    file = models.FileField(upload_to=original_path, storage=originals_storage)
    original_name = models.CharField(max_length=255)
    relative_path = models.CharField(max_length=500, blank=True)
    kind = models.CharField(max_length=8, choices=[("image", "image"), ("pdf", "pdf")])
    mime = models.CharField(max_length=60)
    size = models.BigIntegerField()
    sha256 = models.CharField(max_length=64, db_index=True)
    page_count = models.PositiveIntegerField(default=1)
    uploaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["project", "sha256"], name="uniq_doc_per_project")]
        ordering = ["relative_path", "original_name"]


class ExtractionJob(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="jobs")
    provider = models.CharField(max_length=20)
    model_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=24, default="queued")  # queued running completed completed_with_errors failed cancelled
    params = models.JSONField(default=dict)
    cancel_requested = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class JobItem(models.Model):
    job = models.ForeignKey(ExtractionJob, on_delete=models.CASCADE, related_name="items")
    document = models.ForeignKey(Document, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, default="pending")  # pending running done needs_review failed cancelled
    error = models.TextField(blank=True)
    cells_extracted = models.PositiveIntegerField(default=0)
    uncertain = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)


class Prediction(models.Model):
    """Immutable record of one raw model attempt for one page."""
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name="predictions")
    job_item = models.ForeignKey(JobItem, null=True, on_delete=models.SET_NULL)
    page_number = models.PositiveIntegerField(default=1)
    provider = models.CharField(max_length=20)
    model_id = models.CharField(max_length=200)
    columns = models.JSONField(default=list)
    raw_output = models.TextField(blank=True)
    warnings = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PredictionCell(models.Model):
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name="cells")
    row_index = models.PositiveIntegerField()
    col_index = models.PositiveIntegerField()
    raw_text = models.TextField(null=True)
    value = models.CharField(max_length=40, null=True)     # normalized, or None
    flags = models.CharField(max_length=120, blank=True)   # comma separated
    confidence = models.FloatField(null=True)


class Cell(models.Model):
    """Working record: latest prediction + human verification. Ground truth = verified_value when approved."""
    STATUS = [(s, s) for s in ("unreviewed", "corrected", "approved", "rejected")]
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="cells")
    page_number = models.PositiveIntegerField(default=1)
    row_index = models.PositiveIntegerField()
    col_index = models.PositiveIntegerField()
    column_name = models.CharField(max_length=60)
    bbox = models.JSONField(null=True, blank=True)          # [x0,y0,x1,y1] in page pixels, if known
    raw_text = models.TextField(null=True, blank=True)
    predicted_value = models.CharField(max_length=40, null=True, blank=True)
    flags = models.CharField(max_length=120, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    latest_prediction = models.ForeignKey(Prediction, null=True, on_delete=models.SET_NULL, related_name="+")
    verified_value = models.CharField(max_length=40, null=True, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default="unreviewed")
    note = models.TextField(blank=True)
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["document", "page_number", "row_index", "col_index"], name="uniq_cell")]
        ordering = ["document_id", "page_number", "row_index", "col_index"]

    @property
    def flag_list(self):
        return [f for f in self.flags.split(",") if f]

    @property
    def effective_value(self):
        return self.verified_value if self.status in ("corrected", "approved") else self.predicted_value


class CellEvent(models.Model):
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE, related_name="events")
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=16)    # predicted label approve reject reopen
    source = models.CharField(max_length=20)    # ai manual human_correction verification
    old_value = models.CharField(max_length=40, null=True, blank=True)
    new_value = models.CharField(max_length=40, null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    project = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=60)
    target = models.CharField(max_length=120, blank=True)
    meta = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class EvaluationRun(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="evaluations")
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    provider = models.CharField(max_length=20, blank=True)
    model_id = models.CharField(max_length=200, blank=True)
    rules = models.JSONField(default=dict)
    metrics = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ExportJob(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="exports")
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=10, default="queued")  # queued running done failed
    options = models.JSONField(default=dict)
    file_path = models.CharField(max_length=500, blank=True)
    summary = models.JSONField(default=dict)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class ModelInstallation(models.Model):
    name = models.CharField(max_length=60, unique=True)
    repo = models.CharField(max_length=200)
    revision = models.CharField(max_length=80, blank=True)
    path = models.CharField(max_length=500)
    status = models.CharField(max_length=12, default="missing")  # missing downloading downloaded loading ready failed
    progress = models.FloatField(default=0)
    detail = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class SiteSettings(models.Model):
    default_provider = models.CharField(max_length=20, default="gemini")
    gemini_model = models.CharField(max_length=120, blank=True)
    gemini_api_key_1 = models.CharField(max_length=200, blank=True)
    gemini_api_key_2 = models.CharField(max_length=200, blank=True)
    gemini_api_key_3 = models.CharField(max_length=200, blank=True)
    gemini_api_key_4 = models.CharField(max_length=200, blank=True)
    supervisor = models.CharField(max_length=160, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)

    @classmethod
    def get(cls):
        return cls.objects.get_or_create(pk=1)[0]



class DatasetVersion(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    snapshot = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class TrainingRun(models.Model):   # placeholder: training is not implemented yet
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    dataset_version = models.ForeignKey(DatasetVersion, null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=16, default="unavailable")
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
