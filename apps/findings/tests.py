from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.findings.models import Finding


class FindingListFilterPersistenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", password="pass")
        self.client.force_login(self.user)
        self.finding = Finding.objects.create(
            source=Finding.Source.AUTHORITY,
            title="Test finding",
            category="Hardware",
            status=Finding.Status.OPEN,
        )

    def test_save_returns_to_filtered_list(self):
        self.client.get(reverse("findings:authority"), {"status": "Open"})
        response = self.client.post(
            reverse("findings:authority_edit", args=[self.finding.pk]),
            {
                "title": "Test finding",
                "category": "Hardware",
                "status": Finding.Status.OPEN,
            },
        )
        self.assertRedirects(
            response,
            f"{reverse('findings:authority')}?status=Open",
            fetch_redirect_response=False,
        )

    def test_edit_cancel_keeps_filters(self):
        self.client.get(reverse("findings:authority"), {"status": "Open"})
        response = self.client.get(reverse("findings:authority_edit", args=[self.finding.pk]))
        self.assertContains(response, 'href="/findings/?status=Open"')

    def test_bare_list_clears_remembered_filters(self):
        self.client.get(reverse("findings:authority"), {"status": "Open"})
        self.client.get(reverse("findings:authority"))
        response = self.client.get(reverse("findings:authority_edit", args=[self.finding.pk]))
        self.assertContains(response, 'href="/findings/"')
        self.assertNotContains(response, 'href="/findings/?status=Open"')
