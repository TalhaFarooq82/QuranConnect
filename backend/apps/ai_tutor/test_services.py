from django.test import SimpleTestCase

from .services import (
    clean_text,
    fetch_chapter,
    fetch_hadiths,
    extract_query_results,
    build_context,
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


class BuildContextTests(SimpleTestCase):
    def test_formats_quran_source(self):
        context = build_context(
            ["Arabic and translated verse"],
            [{
                "source": "Quran",
                "surah_number": 1,
                "ayah_number": 1,
                "arabic_text": "Arabic verse",
            }],
        )

        self.assertIn("Source 1: Quran", context)
        self.assertIn("Surah 1", context)
        self.assertIn("Ayah 1", context)

    def test_formats_hadith_source(self):
        context = build_context(
            ["Hadith text"],
            [{
                "source": "Hadith",
                "collection": "Sahih Bukhari",
                "hadith_number": "1",
                "chapter": "Revelation",
                "narrator": "Narrator",
                "status": "Sahih",
            }],
        )

        self.assertIn("Sahih Bukhari", context)
        self.assertIn("Hadith #1", context)
        self.assertIn("Status: Sahih", context)

    def test_tolerates_missing_metadata(self):
        context = build_context(
            ["Knowledge text"],
            [{}],
        )

        self.assertIn("Knowledge text", context)
        self.assertIn("Unknown", context)
