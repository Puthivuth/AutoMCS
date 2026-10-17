from rest_framework import serializers as s
from . import models as m


class ProjectS(s.ModelSerializer):
    class Meta: model = m.Project; fields = ["id", "name", "description", "archived", "created_at"]; read_only_fields = ["id", "created_at"]

class DocumentS(s.ModelSerializer):
    status = s.SerializerMethodField()
    class Meta: model = m.Document; fields = ["id", "original_name", "relative_path", "kind", "mime", "size", "page_count", "created_at", "status"]
    def get_status(self, d):
        c = list(d.cells.values_list("status", flat=True)) if hasattr(d, "cells") else []
        return "not_extracted" if not c else "approved" if all(x == "approved" for x in c) else "needs_review"

class CellS(s.ModelSerializer):
    flags = s.SerializerMethodField()
    class Meta: model = m.Cell; fields = ["id", "page_number", "row_index", "col_index", "column_name", "bbox", "raw_text", "predicted_value", "flags", "confidence", "verified_value", "status", "note"]
    def get_flags(self, c): return c.flag_list

class ItemS(s.ModelSerializer):
    document_name = s.CharField(source="document.original_name", read_only=True)
    class Meta: model = m.JobItem; fields = ["id", "document", "document_name", "status", "error", "cells_extracted", "uncertain"]

class JobS(s.ModelSerializer):
    items = ItemS(many=True, read_only=True)
    class Meta: model = m.ExtractionJob; fields = ["id", "provider", "model_id", "status", "error", "created_at", "finished_at", "items"]

class EventS(s.ModelSerializer):
    user = s.CharField(source="user.username", default=None, read_only=True)
    class Meta: model = m.CellEvent; fields = ["id", "action", "source", "old_value", "new_value", "note", "user", "created_at"]

class EvalS(s.ModelSerializer):
    class Meta: model = m.EvaluationRun; fields = ["id", "provider", "model_id", "rules", "metrics", "created_at"]

class ExportS(s.ModelSerializer):
    class Meta: model = m.ExportJob; fields = ["id", "status", "options", "summary", "error", "created_at", "finished_at"]
