from django.test import SimpleTestCase

from .services import (
    clean_text,
)


class CleanTextTests(SimpleTestCase):
    def test_removes_html_tags(self):
        result = clean_text("<p>Prayer is important.</p>")

        self.assertEqual(result, "Prayer is important.")

    def test_uses_allah_in_translation_text(self):
        result = clean_text("God is Most Merciful")

        self.assertEqual(result, "Allah is Most Merciful")
