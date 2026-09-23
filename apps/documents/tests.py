from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.documents.models import Document, Folder


class FolderNestingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", password="pass")
        self.client.force_login(self.user)
        self.root = Folder.objects.create(name="Manuals", icon="📘", is_standard=True)

    def test_create_subfolder(self):
        response = self.client.post(
            f"{reverse('documents:folder_add')}?parent={self.root.pk}",
            {"name": "2024", "icon": "📁"},
        )
        self.assertRedirects(response, reverse("documents:folder", args=[self.root.pk]))
        child = Folder.objects.get(name="2024")
        self.assertEqual(child.parent, self.root)

    def test_same_name_allowed_under_different_parents(self):
        other_root = Folder.objects.create(name="QTG", icon="📈")
        Folder.objects.create(name="Reports", parent=self.root)
        Folder.objects.create(name="Reports", parent=other_root)
        self.assertEqual(Folder.objects.filter(name="Reports").count(), 2)

    def test_unique_name_per_parent(self):
        Folder.objects.create(name="Reports", parent=self.root)
        response = self.client.post(
            f"{reverse('documents:folder_add')}?parent={self.root.pk}",
            {"name": "Reports", "icon": "📁"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists at this level")
        self.assertEqual(self.root.children.filter(name="Reports").count(), 1)

    def test_list_shows_only_root_folders(self):
        Folder.objects.create(name="2024", parent=self.root)
        response = self.client.get(reverse("documents:list"))
        self.assertContains(response, "Manuals")
        self.assertNotContains(response, ">2024<")

    def test_delete_promotes_children(self):
        custom = Folder.objects.create(name="Custom", icon="📁")
        child = Folder.objects.create(name="Nested", parent=custom)
        grandchild = Folder.objects.create(name="Deep", parent=child)
        response = self.client.post(reverse("documents:folder_delete", args=[child.pk]))
        self.assertRedirects(response, reverse("documents:folder", args=[custom.pk]))
        grandchild.refresh_from_db()
        self.assertEqual(grandchild.parent, custom)
        self.assertFalse(Folder.objects.filter(pk=child.pk).exists())

    def test_delete_blocked_when_child_name_collides(self):
        custom = Folder.objects.create(name="Custom", icon="📁")
        Folder.objects.create(name="Reports", parent=custom)
        child = Folder.objects.create(name="Nested", parent=custom)
        Folder.objects.create(name="Reports", parent=child)
        response = self.client.post(reverse("documents:folder_delete", args=[child.pk]))
        self.assertRedirects(response, reverse("documents:folder", args=[child.pk]))
        self.assertTrue(Folder.objects.filter(pk=child.pk).exists())
        child.refresh_from_db()
        self.assertEqual(child.children.get(name="Reports").parent, child)

    def test_delete_orphans_documents(self):
        custom = Folder.objects.create(name="Custom", icon="📁")
        doc = Document.objects.create(original_name="note.pdf", folder=custom)
        self.client.post(reverse("documents:folder_delete", args=[custom.pk]))
        doc.refresh_from_db()
        self.assertIsNone(doc.folder)


class DocumentMoveTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("tester", password="pass")
        self.client.force_login(self.user)
        self.source = Folder.objects.create(name="Manuals", icon="📘")
        self.target = Folder.objects.create(name="QTG", icon="📈")
        self.doc = Document.objects.create(original_name="guide.pdf", folder=self.source)

    def test_move_document_between_folders(self):
        response = self.client.post(
            reverse("documents:move", args=[self.doc.pk]),
            {"folder": self.target.pk},
        )
        self.assertRedirects(response, reverse("documents:folder", args=[self.target.pk]))
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.folder, self.target)

    def test_upload_form_shows_folder_paths(self):
        Folder.objects.create(name="2024", parent=self.source)
        response = self.client.get(reverse("documents:upload"))
        self.assertContains(response, "Manuals / 2024")

    def test_upload_creates_file_in_subfolder(self):
        child = Folder.objects.create(name="2024", parent=self.source)
        upload = SimpleUploadedFile("spec.pdf", b"pdf-bytes", content_type="application/pdf")
        response = self.client.post(
            reverse("documents:upload"),
            {"file": upload, "folder": child.pk, "notes": ""},
        )
        self.assertRedirects(response, reverse("documents:folder", args=[child.pk]))
        self.assertTrue(Document.objects.filter(original_name="spec.pdf", folder=child).exists())
