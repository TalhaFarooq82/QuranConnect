from django.test import SimpleTestCase

from .services import (
    clean_text,
    fetch_chapter,
)


class CleanTextTests(SimpleTestCase):
    def test_removes_html_tags(self):
        result = clean_text("<p>Prayer is important.</p>")

        self.assertEqual(result, "Prayer is important.")

    def test_uses_allah_in_translation_text(self):
        result = clean_text("God is Most Merciful")

        self.assertEqual(result, "Allah is Most Merciful")


class FetchChapterValidationTests(SimpleTestCase):
    def test_rejects_chapter_below_valid_range(self):
        with self.assertRaises(ValueError):
            fetch_chapter(0)

    def test_rejects_chapter_above_valid_range(self):
        with self.assertRaises(ValueError):
            fetch_chapter(115)

    def test_rejects_non_numeric_chapter(self):
        with self.assertRaises(ValueError):
            fetch_chapter("first")
