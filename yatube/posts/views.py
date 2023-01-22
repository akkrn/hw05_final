import functools

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post


def paginate_posts(queryset, page_number):
    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    post_list = Post.objects.all().order_by("-created")
    page_number = request.GET.get("page")
    page_obj = paginate_posts(post_list, page_number)
    context = {"page_obj": page_obj}
    template = "posts/index.html"
    return render(request, template, context)


def groups_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.order_by("-created")
    page_number = request.GET.get("page")
    page_obj = paginate_posts(post_list, page_number)
    context = {"group": group, "page_obj": page_obj}
    template = "posts/group_list.html"
    return render(request, template, context)


User = get_user_model()


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_count = Post.objects.filter(author=author).count()
    post_list = author.posts.order_by("-created")
    page_number = request.GET.get("page")
    page_obj = paginate_posts(post_list, page_number)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    context = {
        "author": author,
        "posts_count": posts_count,
        "page_obj": page_obj,
        "following": following,
    }
    template = "posts/profile.html"
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    count_posts = Post.objects.all().filter(author=post.author).count()
    comments = Comment.objects.all().filter(post_id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        "is_valid": request.user == post.author,
        "post": post,
        "count_posts": count_posts,
        "comments": comments,
        "form": form,
    }
    template = "posts/post_detail.html"
    return render(request, template, context)


@login_required
def post_create(request):
    template = "posts/post_create.html"
    if request.method == "POST":
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect("posts:profile", post.author)
        context = {"form": form}
        return render(request, template, context)
    form = PostForm()
    context = {"form": form}
    return render(request, template, context)


def user_master_required(func):
    """Декоратор, который проверяет имеет ли право юзер редактировать пост"""

    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        post = Post.objects.get(id=kwargs["post_id"])
        if request.user != post.author:
            return redirect("posts:post_detail", post.pk)
        return func(request, *args, **kwargs)

    return wrapper


@user_master_required
def post_edit(request, post_id):
    template = "posts/post_create.html"
    post = get_object_or_404(Post, id=post_id)
    is_edit = True
    if request.method == "POST":
        form = PostForm(
            request.POST or None, files=request.FILES or None, instance=post
        )
        if form.is_valid():
            post = form.save()
            return redirect("posts:post_detail", post.pk)
        context = {
            "form": form,
            "is_edit": is_edit,
            "post": post,
        }
        return render(request, template, context)
    form = PostForm(instance=post)
    context = {
        "form": form,
        "is_edit": is_edit,
        "post": post,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    authors = Follow.objects.filter(user=request.user).values_list(
        "author", flat=True
    )
    post_list = Post.objects.filter(author__in=authors)
    page_number = request.GET.get("page")
    page_obj = paginate_posts(post_list, page_number)
    context = {"page_obj": page_obj}
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    if request.user != author and following is False:
        Follow.objects.create(user=request.user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("posts:profile", username=username)
