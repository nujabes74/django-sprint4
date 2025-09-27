from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .constants import POSTS_QUANTITY
from .forms import CommentForm, PostForm, ProfileEditForm
from .models import Category, Comment, Post


def get_posts(
    posts=Post.objects.all(),
    do_filter=True,
    do_select_related=True,
    do_annotate=True
):
    if do_filter:
        posts = posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )

    if do_select_related:
        posts = posts.select_related('location', 'category', 'author')

    if do_annotate:
        posts = posts.annotate(
            comment_count=Count('comments')
        ).order_by(
            *Post._meta.ordering
        )
    return posts


def paginate(posts, request, per_page=POSTS_QUANTITY):
    return Paginator(
        posts, per_page
    ).get_page(request.GET.get('page'))


def index(request):
    return render(request, 'blog/index.html', {
        'page_obj': paginate(get_posts(), request),
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        post = get_object_or_404(
            get_posts(do_select_related=False, do_annotate=False), id=post_id)
    return render(request, 'blog/detail.html', {
        'post': post,
        'form': CommentForm(),
        'comments': post.comments.all()
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True
    )
    return render(
        request,
        'blog/category.html',
        {
            'category': category,
            'page_obj': paginate(
                get_posts(posts=category.posts.all()),
                request,
            ),
        }
    )


def profile_view(request, username):
    author = get_object_or_404(User, username=username)
    posts = get_posts(
        posts=author.posts.all(),
        do_filter=(author != request.user),
    )
    page_obj = paginate(posts, request, POSTS_QUANTITY)
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
    if not form.is_valid():
        return render(request, 'blog/create.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('blog:profile', request.user.username)


def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post.id)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post.id)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post.id)
    if request.method == "POST":
        post.delete()
        return redirect('blog:index')
    return render(request, 'blog/create.html', {'post': post})


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.save()
    return redirect('blog:post_detail', post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    post = comment.post
    if comment.author != request.user:
        return redirect('blog:post_detail', post.pk)
    form = CommentForm(request.POST or None, instance=comment)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('blog:post_detail', post.pk)
    return render(request, "blog/comment.html", {
        "form": form,
        "comment": comment,
        "post": post
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    post = comment.post
    if comment.author != request.user:
        return redirect('blog:post_detail', post.pk)
    if request.method == "POST":
        comment.delete()
        return redirect("blog:post_detail", post.pk)
    return render(request, "blog/comment.html", {
        "comment": comment,
        "post": post
    })
