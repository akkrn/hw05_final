import shutil
import tempfile
import time

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username="NeStasBasov")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            text="Тестовый текст № 1",
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.new_group = Group.objects.create(
            title="Новая группа",
            slug="new",
            description="Проверка наличия поста в группе",
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_show_correct_context(self):
        """Cтраницы с постами сформированы с правильным контекстом."""
        pages_names = [
            reverse("posts:index"),
            reverse(
                "posts:group_list", kwargs={"slug": PostPagesTests.group.slug}
            ),
            reverse(
                "posts:profile",
                kwargs={"username": PostPagesTests.user.username},
            ),
        ]
        for name in pages_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                context_object = response.context["page_obj"][0]
                post_author = context_object.author
                post_text = context_object.text
                post_group = context_object.group.title
                post_image = context_object.image
                self.assertEqual(post_author, PostPagesTests.user)
                self.assertEqual(post_text, PostPagesTests.post.text)
                self.assertEqual(post_group, PostPagesTests.group.title)
                self.assertEqual(post_image, PostPagesTests.post.image)

    def test_initial_value_in_create_post(self):
        """Cтраница создания и редактирования поста сформированы с правильным
        контекстом."""
        pages_names = [
            reverse("posts:post_create"),
            reverse(
                "posts:post_edit", kwargs={"post_id": PostPagesTests.post.id}
            ),
        ]
        for name in pages_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                form_fields = {
                    "text": forms.fields.CharField,
                    "group": forms.fields.ChoiceField,
                    "image": forms.fields.ImageField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context["form"].fields[value]
                        self.assertIsInstance(form_field, expected)
        self.assertTrue(
            response.context["post"].group != PostPagesTests.new_group
        )

    def test_value_in_post_detail(self):
        """Cтраница поста сформирована с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                "posts:post_detail", kwargs={"post_id": PostPagesTests.post.id}
            )
        )
        self.assertEqual(response.context["post"], PostPagesTests.post)
        self.assertEqual(
            response.context["post"].text, PostPagesTests.post.text
        )
        self.assertEqual(
            response.context["post"].group, PostPagesTests.post.group
        )
        self.assertEqual(
            response.context["post"].image, PostPagesTests.post.image
        )

    def test_first_page_contains_ten_records(self):
        """Страница паджинатора содержит 10 постов."""
        post_list = []
        for i in range(2, 14):
            post = Post.objects.create(
                text=f"Тестовый текст № {i}",
                author=PostPagesTests.user,
                group=PostPagesTests.group,
            )
            post_list.append(post)
            time.sleep(0.1)
        templates_pages_names = [
            reverse("posts:index"),
            reverse(
                "posts:group_list", kwargs={"slug": PostPagesTests.group.slug}
            ),
            reverse(
                "posts:profile",
                kwargs={"username": PostPagesTests.user.username},
            ),
        ]
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context["page_obj"]), 10)
                response = self.authorized_client.get(reverse_name + "?page=2")
                self.assertEqual(len(response.context["page_obj"]), 3)

    def test_cache(self):
        """Страница сохраняет данные в кэш."""
        first_response = self.authorized_client.get(reverse("posts:index"))
        self.assertEqual(len(first_response.context["page_obj"]), 1)
        Post.objects.filter(id=1).delete()
        second_response = self.authorized_client.get(reverse("posts:index"))
        self.assertTrue(first_response.content == second_response.content)
        self.assertEqual(len(second_response.context["page_obj"]), 0)
        cache.clear()
        third_response = self.authorized_client.get(reverse("posts:index"))
        self.assertTrue(first_response.content != third_response.content)
        self.assertEqual(len(third_response.context["page_obj"]), 0)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="StasBasov")
        cls.author = User.objects.create_user(username="ThomasAnderson")
        cls.unfollowing_user = User.objects.create_user(
            username="NikitaBelkin"
        )
        cls.unauthorised_client = Client()
        cls.unfollowing_client = Client()
        cls.unfollowing_client.force_login(cls.unfollowing_user)
        cls.post = Post.objects.create(
            text="Тестовый текст Избранного",
            author=cls.author,
        )
        cls.following = Follow.objects.create(user=cls.user, author=cls.author)

    def test_authenticated_user_can_follow_authors(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        following = Follow.objects.filter(
            user=self.unfollowing_user, author=self.author
        ).exists()
        self.assertFalse(following)
        response = self.unfollowing_client.post(
            reverse(
                "posts:profile_follow",
                kwargs={"username": FollowTests.author.username},
            ),
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:profile",
                kwargs={"username": FollowTests.author.username},
            ),
        )
        following = Follow.objects.filter(
            user=self.unfollowing_user, author=self.author
        ).exists()
        self.assertTrue(following)
        response = self.unfollowing_client.post(
            reverse(
                "posts:profile_unfollow",
                kwargs={"username": FollowTests.author.username},
            )
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:profile",
                kwargs={"username": FollowTests.author.username},
            ),
        )
        following = Follow.objects.filter(
            user=self.unfollowing_user, author=self.author
        ).exists()
        self.assertFalse(following)

    def test_only_followers_get_post(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        response = self.unfollowing_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context["page_obj"]), 0)
        self.unauthorised_client.force_login(self.user)
        response = self.unauthorised_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context["page_obj"]), 1)
