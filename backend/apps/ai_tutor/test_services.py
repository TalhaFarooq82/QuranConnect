from django.test import SimpleTestCase

from .services import (
    clean_text,
    fetch_chapter,
    fetch_hadiths,
    extract_query_results,
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


class FetchHadithValidationTests(SimpleTestCase):
    def test_rejects_empty_book_name(self):
        with self.assertRaises(ValueError):
            fetch_hadiths("", page=1)

    def test_rejects_page_below_one(self):
        with self.assertRaises(ValueError):
            fetch_hadiths("sahih-bukhari", page=0)

    def test_rejects_non_numeric_page(self):
        with self.assertRaises(ValueError):
            fetch_hadiths("sahih-bukhari", page="first")


class ExtractQueryResultsTests(SimpleTestCase):
    def test_extracts_first_result_batch(self):
        results = {
            "documents": [["First document", "Second document"]],
            "metadatas": [[{"source": "Quran"}, {"source": "Hadith"}]],
        }

        documents, metadatas = extract_query_results(results)

        self.assertEqual(
            documents,
            ["First document", "Second document"],
        )
        self.assertEqual(len(metadatas), 2)

    def test_returns_empty_lists_for_invalid_result(self):
        documents, metadatas = extract_query_results(None)

        self.assertEqual(documents, [])
        self.assertEqual(metadatas, [])
