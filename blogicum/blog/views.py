from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .constants import INDEX_POSTS_QUANTITY
from .forms import CommentForm, PostForm, ProfileEditForm
from .models import Category, Comment, Post


def select_related_func(queryset=None):
    if queryset is None:
        queryset = Post.objects.all()

    queryset = queryset.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).select_related(
        'location',
        'category',
        'author'
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')

    return queryset


def paginate(queryset, request, per_page):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    posts = select_related_func()
    page_obj = paginate(posts, request, INDEX_POSTS_QUANTITY)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        queryset = select_related_func()
        post = get_object_or_404(queryset, id=post_id)

    return render(request, 'blog/detail.html', {
        'post': post,
        'form': CommentForm(),
        'comments': post.comments.all()
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    posts = select_related_func(
        queryset=category.posts.all()
    )
    page_obj = paginate(posts, request, INDEX_POSTS_QUANTITY)

    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj,
    })


def profile_view(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        posts = author.posts.all().order_by('-pub_date')
    else:
        posts = select_related_func(queryset=author.posts.all())
    page_obj = paginate(posts, request, INDEX_POSTS_QUANTITY)

    return render(request, 'blog/profile.html', {
        'profile': author,
        'page_obj': page_obj,
    })


@login_required
def edit_profile(request):
    user = request.user
    form = ProfileEditForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', user.username)
    return render(request, 'blog/user.html', {'form': form})


@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {"form": form})


def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post.id)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == "POST":
        post.delete()
        return redirect('blog:index')
    return render(request, 'blog/create.html', {'post': post})


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        post = get_object_or_404(Post, id=post_id)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('blog:post_detail', post_id=post.id)
    return render(request, 'blog/comment.html', {
        'form': form,
        'post': post,
        'comments': post.comments.all()
    })


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, "blog/comment.html", {
        "form": form,
        "comment": comment,
        "post_id": post_id
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == "POST":
        comment.delete()
        return redirect("blog:post_detail", post_id=post_id)
    return render(request, "blog/comment.html", {
        "comment": comment,
        "post_id": post_id
    })
