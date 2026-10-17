from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from core import models as m
from core.services.tables import save_prediction

U = get_user_model()


class IsolationAndIntegrity(APITestCase):
    def setUp(self):
        self.a, self.b = U.objects.create_user("a", password="x" * 12), U.objects.create_user("b", password="x" * 12)
        self.pa = m.Project.objects.create(owner=self.a, name="A")
        self.doc = m.Document.objects.create(project=self.pa, original_name="t.png", kind="image", mime="image/png", size=1, sha256="0" * 64, file="x/t.png")
        save_prediction(self.doc, 1, None, "gemini", "test", ["I", "II"], [{"No": 1, "I": "5.126", "II": None}], "{}", [])
        self.cell = self.doc.cells.get(column_name="I")
        self.ca = APIClient(); self.ca.force_login(self.a)
        self.cb = APIClient(); self.cb.force_login(self.b)

    def test_other_user_cannot_see_anything(self):
        for url in (f"/api/projects/{self.pa.id}/", f"/api/documents/{self.doc.id}/", f"/api/documents/{self.doc.id}/table/",
                    f"/api/projects/{self.pa.id}/dashboard/", f"/api/cells/{self.cell.id}/history/"):
            self.assertEqual(self.cb.get(url).status_code, 404, url)
        self.assertEqual(self.cb.patch(f"/api/cells/{self.cell.id}/label/", {"value": "1"}, format="json").status_code, 404)
        self.assertEqual(self.cb.get("/api/projects/").json(), [])

    def test_anonymous_is_rejected(self):
        self.assertIn(APIClient().get("/api/projects/").status_code, (401, 403))

    def test_normalization_and_approval(self):
        self.assertEqual(self.cell.predicted_value, "5.13"); self.assertIn("rounded", self.cell.flag_list)
        r = self.ca.post(f"/api/cells/{self.cell.id}/review/", {"action": "approve"}, format="json"); self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["verified_value"], "5.13")

    def test_rerun_never_overwrites_approved(self):
        self.ca.post(f"/api/cells/{self.cell.id}/review/", {"action": "approve"}, format="json")
        save_prediction(self.doc, 1, None, "gemini", "test", ["I", "II"], [{"No": 1, "I": "9.99", "II": None}], "{}", [])
        self.cell.refresh_from_db()
        self.assertEqual((self.cell.status, self.cell.verified_value), ("approved", "5.13"))

    def test_invalid_label_rejected(self):
        self.assertEqual(self.ca.patch(f"/api/cells/{self.cell.id}/label/", {"value": "abc"}, format="json").status_code, 400)
