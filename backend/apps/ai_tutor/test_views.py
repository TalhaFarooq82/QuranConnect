from unittest.mock import patch

from django.test import SimpleTestCase

from .views import generate_chat_title


class GenerateChatTitleTests(SimpleTestCase):
    def test_empty_message_returns_new_chat(self):
        self.assertEqual(
            generate_chat_title(""),
            "New Chat",
        )

    @patch(
        "apps.ai_tutor.views.get_ai_answer",
        side_effect=RuntimeError("AI unavailable"),
    )
    def test_uses_local_fallback_when_ai_fails(self, mocked_answer):
        title = generate_chat_title(
            "Can you tell me how to perform wudu?"
        )

        self.assertEqual(title, "Perform Wudu")
        mocked_answer.assert_called_once()

    @patch(
        "apps.ai_tutor.views.get_ai_answer",
        return_value="benefits of daily prayer",
    )
    def test_formats_generated_title(self, mocked_answer):
        title = generate_chat_title(
            "What are the benefits of daily prayer?"
        )

        self.assertEqual(title, "Benefits Of Daily Prayer")
        mocked_answer.assert_called_once()
