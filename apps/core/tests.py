from django.test import RequestFactory, TestCase

from apps.core.utils import clear_list_filters, remember_list_filters, remembered_list_url


class ListFilterSessionTests(TestCase):
    def _request(self, query=""):
        factory = RequestFactory()
        path = f"/findings/?{query}" if query else "/findings/"
        request = factory.get(path)
        request.session = {}
        return request

    def test_remember_and_build_url(self):
        request = self._request("status=Open&device=all")
        remember_list_filters(request, "findings:authority")
        url = remembered_list_url(request, "findings:authority")
        self.assertTrue(url.startswith("/findings/"))
        self.assertIn("status=Open", url)
        self.assertIn("device=all", url)

    def test_clear_returns_bare_url(self):
        request = self._request("status=Open")
        remember_list_filters(request, "findings:authority")
        clear_list_filters(request, "findings:authority")
        self.assertEqual(remembered_list_url(request, "findings:authority"), "/findings/")

    def test_lists_are_isolated(self):
        request = self._request("status=Open")
        remember_list_filters(request, "findings:authority")
        self.assertEqual(remembered_list_url(request, "findings:internal"), "/findings/internal/")
