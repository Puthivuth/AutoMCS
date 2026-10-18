import json
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.core.cache import cache
from core.models import SiteSettings, Project, Document
from core.services.providers.gemini import (
    GeminiProvider,
    get_all_key_slots,
    get_key_slot,
    mark_key_exhausted,
    clear_key_cooldown,
    get_provider,
    is_quota_or_token_error,
)
from core.services.providers.base import ProviderError


class DummyAPIError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class GeminiMultiKeyTest(TestCase):
    def setUp(self):
        cache.clear()
        self.settings = SiteSettings.get()
        self.settings.gemini_api_key_1 = "test-key-1"
        self.settings.gemini_api_key_2 = "test-key-2"
        self.settings.gemini_api_key_3 = ""
        self.settings.gemini_api_key_4 = ""
        self.settings.save()

    def tearDown(self):
        cache.clear()

    def test_key_slots_configuration(self):
        slots = get_all_key_slots()
        self.assertEqual(len(slots), 4)
        self.assertTrue(slots[0]["configured"])
        self.assertEqual(slots[0]["key"], "test-key-1")
        self.assertTrue(slots[1]["configured"])
        self.assertEqual(slots[1]["key"], "test-key-2")
        self.assertFalse(slots[2]["configured"])
        self.assertFalse(slots[3]["configured"])

    def test_quota_error_detection(self):
        err_429 = DummyAPIError(429, "Resource has been exhausted (e.g. check quota).")
        err_token = DummyAPIError(403, "Quota exceeded for tokens per minute")
        err_500 = DummyAPIError(500, "Internal server error")
        self.assertTrue(is_quota_or_token_error(err_429))
        self.assertTrue(is_quota_or_token_error(err_token))
        self.assertFalse(is_quota_or_token_error(err_500))

    def test_cooldown_marking(self):
        mark_key_exhausted(1, "Quota exceeded", cooldown=30)
        slot1 = get_key_slot(1)
        self.assertTrue(slot1["cooling"])
        self.assertGreater(slot1["cooldown_remaining"], 0)

        clear_key_cooldown(1)
        slot1_cleared = get_key_slot(1)
        self.assertFalse(slot1_cleared["cooling"])

    @patch.object(GeminiProvider, "_call_gemini_single")
    def test_auto_switch_on_quota_exhausted(self, mock_call):
        # Key 1 raises 429 quota error, Key 2 succeeds
        mock_response = json.dumps({"columns": ["Col1", "Col2"], "rows": [{"Col1": "1.00", "Col2": "2.00"}]})

        def side_effect(key, png):
            if key == "test-key-1":
                raise DummyAPIError(429, "Resource has been exhausted (e.g. check quota).")
            elif key == "test-key-2":
                return mock_response
            raise ValueError(f"Unexpected key: {key}")

        mock_call.side_effect = side_effect

        provider = GeminiProvider()
        result = provider.extract_page(b"fake-png-bytes", page_number=1)

        self.assertIn("Col1", result.columns)
        self.assertIn("Col2", result.columns)
        self.assertEqual(len(result.rows), 1)
        self.assertIn("Key 2", result.model_id)

        # Slot 1 should now be marked as cooling
        slot1 = get_key_slot(1)
        self.assertTrue(slot1["cooling"])

    @patch.object(GeminiProvider, "_call_gemini_single")
    def test_all_keys_exhausted_raises_provider_error(self, mock_call):
        mock_call.side_effect = DummyAPIError(429, "Quota exhausted")

        provider = GeminiProvider()
        with self.assertRaises(ProviderError):
            provider.extract_page(b"fake-png-bytes", page_number=1)

    def test_provider_registry(self):
        p_auto = get_provider("gemini")
        self.assertEqual(p_auto.name, "gemini")

        p_key2 = get_provider("gemini_2")
        self.assertEqual(p_key2.name, "gemini_2")
        self.assertEqual(p_key2.preferred_slot, 2)

        # Retired deepseek fallback
        p_ds = get_provider("deepseek")
        self.assertIsInstance(p_ds, GeminiProvider)

