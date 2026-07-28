import uuid

from django.test import SimpleTestCase
from django.urls import reverse


class AITutorUrlTests(SimpleTestCase):
    def test_home_url(self):
        self.assertEqual(
            reverse("ai_tutor_home"),
            "/ai_tutor/",
        )

    def test_new_chat_url(self):
        self.assertEqual(
            reverse("ai_tutor_new"),
            "/ai_tutor/new/",
        )

    def test_chat_detail_url(self):
        self.assertEqual(
            reverse("ai_tutor_chat", args=[12]),
            "/ai_tutor/chat/12/",
        )

    def test_message_action_urls(self):
        self.assertEqual(
            reverse("ai_tutor_regenerate", args=[8]),
            "/ai_tutor/msg/8/regenerate/",
        )
        self.assertEqual(
            reverse("ai_tutor_shorter", args=[8]),
            "/ai_tutor/msg/8/shorter/",
        )
        self.assertEqual(
            reverse("ai_tutor_easier", args=[8]),
            "/ai_tutor/msg/8/easier/",
        )

    def test_shared_chat_url(self):
        token = uuid.UUID(
            "12345678-1234-5678-1234-567812345678"
        )

        self.assertEqual(
            reverse("ai_tutor_shared_view", args=[token]),
            f"/ai_tutor/share/{token}/",
        )
