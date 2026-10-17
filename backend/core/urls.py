from django.urls import path
from . import views as v
urlpatterns = [
    path("auth/csrf/", v.csrf), path("auth/login/", v.login_view), path("auth/logout/", v.logout_view), path("auth/me/", v.me),
    path("public/config/", v.public_config), path("contact/", v.contact),
    path("projects/", v.projects), path("projects/<int:pk>/", v.project_detail), path("projects/<int:pk>/dashboard/", v.dashboard),
    path("projects/<int:pk>/documents/", v.project_documents), path("projects/<int:pk>/extract/", v.project_extract),
    path("projects/<int:pk>/jobs/", v.project_jobs), path("projects/<int:pk>/review-queue/", v.review_queue),
    path("projects/<int:pk>/evaluations/", v.project_evaluations), path("projects/<int:pk>/exports/", v.project_exports),
    path("projects/<int:pk>/training-runs/", v.training_runs),
    path("providers/", v.providers),
    path("documents/<int:pk>/", v.document_detail), path("documents/<int:pk>/file/", v.document_file),
    path("documents/<int:pk>/pages/<int:page>/image/", v.document_page_image), path("documents/<int:pk>/table/", v.document_table),
    path("documents/<int:pk>/predictions/", v.document_predictions), path("documents/<int:pk>/extract/", v.document_extract),
    path("documents/<int:pk>/approve/", v.document_approve),
    path("jobs/<int:pk>/", v.job_detail), path("jobs/<int:pk>/retry/", v.job_retry), path("jobs/<int:pk>/cancel/", v.job_cancel),
    path("cells/<int:pk>/label/", v.cell_label), path("cells/<int:pk>/review/", v.cell_review), path("cells/<int:pk>/history/", v.cell_history),
    path("evaluations/<int:pk>/", v.evaluation_detail), path("exports/<int:pk>/", v.export_detail), path("exports/<int:pk>/download/", v.export_download),
    path("models/local/status/", v.local_model_status), path("models/local/prepare/", v.local_model_prepare),
    path("settings/", v.site_settings),
]
