from datetime import date, datetime
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from account.models import Customer, Product, order


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost"],
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class RevenueViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="secret123")
        self.customer = Customer.objects.create(
            name="Revenue Customer",
            email="revenue@example.com",
            phone="1234567890",
            address="Kolkata",
        )

        self.delivered_product_one = Product.objects.create(
            name="Delivered One",
            price=1000,
            category="Indoor",
            description="Delivered revenue source",
        )
        self.delivered_product_two = Product.objects.create(
            name="Delivered Two",
            price=500,
            category="Outdoor",
            description="Delivered revenue source",
        )
        self.pending_product = Product.objects.create(
            name="Pending Product",
            price=300,
            category="Indoor",
            description="Pipeline revenue source",
        )

        self.delivered_order_one = order.objects.create(
            customer=self.customer,
            product=self.delivered_product_one,
            status="Delivered",
        )
        self.delivered_order_two = order.objects.create(
            customer=self.customer,
            product=self.delivered_product_two,
            status="Delivered",
        )
        self.pending_order = order.objects.create(
            customer=self.customer,
            product=self.pending_product,
            status="Pending",
        )

        delivered_timestamp = timezone.make_aware(datetime(2026, 2, 13, 10, 15, 0))
        pending_timestamp = timezone.make_aware(datetime(2026, 2, 14, 11, 30, 0))

        order.objects.filter(pk__in=[self.delivered_order_one.pk, self.delivered_order_two.pk]).update(
            date_created=delivered_timestamp
        )
        order.objects.filter(pk=self.pending_order.pk).update(date_created=pending_timestamp)

    def test_revenue_page_uses_database_calculations(self):
        self.client.force_login(self.user)

        with mock.patch("account.views.timezone.localdate", return_value=date(2026, 3, 25)):
            response = self.client.get("/revenue/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["delivered_orders_count"], 2)
        self.assertEqual(response.context["ytd_realized_revenue"], 1500.0)
        self.assertEqual(response.context["pipeline_revenue"], 300.0)
        self.assertAlmostEqual(response.context["average_daily_revenue"], 1500.0 / 84, places=6)
        self.assertAlmostEqual(
            response.context["projected_annual_revenue"],
            (1500.0 / 84) * 365,
            places=6,
        )

        self.assertEqual(len(response.context["daily_revenue_rows"]), 1)
        self.assertEqual(response.context["daily_revenue_rows"][0]["orders"], 2)
        self.assertEqual(response.context["daily_revenue_rows"][0]["revenue"], 1500.0)
        self.assertContains(response, "Rs. 1500.00")
        self.assertContains(response, "Revenue Intelligence")
        self.assertContains(response, "Pending Pipeline")


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost"],
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class AskToAIViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ai-user", password="secret123")

    def test_ask_to_ai_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get("/ask-to-ai/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ASK to AI")
        self.assertContains(response, "Groq")

    @mock.patch("account.views.generate_ai_chat_response")
    def test_ask_to_ai_message_endpoint_returns_json(self, mocked_generate):
        mocked_generate.return_value = {
            "reply": "Revenue is calculated from delivered orders.",
            "sources": [{"title": "Revenue", "url": "/revenue/"}],
            "used_groq": False,
        }

        self.client.force_login(self.user)
        response = self.client.post(
            "/ask-to-ai/message/",
            data='{"message":"How does revenue work?"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["reply"], "Revenue is calculated from delivered orders.")
        self.assertEqual(payload["sources"][0]["url"], "/revenue/")

        session_history = self.client.session.get("ask_to_ai_history", [])
        self.assertEqual(len(session_history), 2)
        self.assertEqual(session_history[0]["role"], "user")
        self.assertEqual(session_history[1]["role"], "assistant")

    def test_ask_to_ai_reset_endpoint_clears_history(self):
        session = self.client.session
        session["ask_to_ai_history"] = [{"role": "user", "content": "Hi"}]
        session.save()

        self.client.force_login(self.user)
        response = self.client.post("/ask-to-ai/reset/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ok"], True)
        self.assertEqual(self.client.session.get("ask_to_ai_history"), None)
