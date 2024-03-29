import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="NeStasBasov")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.new_group = Group.objects.create(
            title="Новая группа",
            slug="new",
            description="Проверка наличия поста в группе",
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись."""
        posts_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Тестовый текст ни о чем",
            "group": PostCreateFormTests.group.id,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:profile",
                kwargs={"username": PostCreateFormTests.user.username},
            ),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст ни о чем",
                group=PostCreateFormTests.group,
                author=PostCreateFormTests.user,
                image="posts/small.gif",
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись."""
        posts_count = Post.objects.count()
        self.authorized_client.post(
            reverse("posts:post_create"),
            data={
                "text": "Тестовый текст ни о чем",
                "group": PostCreateFormTests.group.id,
            },
            follow=True,
        )
        post = get_object_or_404(Post, id=1)
        form_data = {
            "text": "Это новый тестовый текст ни о чем",
            "group": PostCreateFormTests.new_group.id,
        }
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post_edited = get_object_or_404(Post, id=post.id)
        self.assertEqual(post_edited.text, form_data["text"])
        self.assertEqual(post_edited.group, PostCreateFormTests.new_group)
        self.assertEqual(post_edited.author, PostCreateFormTests.user)

    def test_add_comment(self):
        """Валидная форма создает комментарий."""
        self.authorized_client.post(
            reverse("posts:post_create"),
            data={
                "text": "Тестовый текст ни о чем",
            },
            follow=True,
        )
        post = get_object_or_404(Post, id=1)
        comments_count = Comment.objects.all().filter(post_id=1).count()
        form_data = {
            "text": "Это новый комментарий ни о чем",
        }
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse("posts:post_detail", kwargs={"post_id": post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        comment = Comment.objects.get(id=1)
        self.assertEqual(comment.text, form_data["text"])
        self.assertEqual(comment.author, PostCreateFormTests.user)
