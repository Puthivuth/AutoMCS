from django.contrib import admin
from . import models as m
for model in (m.Project, m.Document, m.ExtractionJob, m.EvaluationRun, m.ExportJob, m.ModelInstallation,
              m.SiteSettings, m.ContactMessage, m.AuditLog):
    admin.site.register(model)
