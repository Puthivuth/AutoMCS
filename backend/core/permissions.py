from django.db.models import Q
from django.shortcuts import get_object_or_404


def scoped(qs, user, path="project"):
    """Restrict any queryset to projects the user owns or is a member of. Used for EVERY lookup."""
    p = f"{path}__" if path else ""
    return qs.filter(Q(**{f"{p}owner": user}) | Q(**{f"{p}members": user})).distinct()


def obj_for(model, user, pk, path="project", select=()):
    qs = model.objects.select_related(*select) if select else model.objects.all()
    return get_object_or_404(scoped(qs, user, path), pk=pk)


def audit(user, action, project=None, target="", **meta):
    from .models import AuditLog
    AuditLog.objects.create(user=user, project=project, action=action, target=str(target)[:120], meta=meta)
