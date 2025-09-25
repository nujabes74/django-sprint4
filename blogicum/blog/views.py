from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .constants import INDEX_POSTS_QTY
from .forms import CommentForm, PostForm, ProfileEditForm
from .models import Category, Comment, Post


def select_related_func():
    return (
        Post.objects.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )
        .select_related(
            'location',
            'category',
            'author',
        )
    )


def index(request):
    post_list = Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).order_by('-pub_date')

    paginator = Paginator(post_list, INDEX_POSTS_QTY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/index.html', {"page_obj": page_obj})


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related(
        'location', 'category', 'author'), id=post_id)

    if post.author != request.user:
        if not post.is_published or post.pub_date > timezone.now() or not post.category.is_published:
            raise Http404("Публикация недоступна")

    comment_form = CommentForm()

    return render(request, 'blog/detail.html', {
        'post': post,
        'form': comment_form,
        'comments': post.comments.all().order_by('-created_at')
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    post_list = Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')

    paginator = Paginator(post_list, INDEX_POSTS_QTY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj,
    })


@login_required
def simple_view(request):
    return HttpResponse('Страница для залогиненных пользователей!')


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)


def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def error_500(request):
    return render(request, "pages/500.html", status=500)


def profile_view(request, username):
    profile = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=profile).order_by('-pub_date')
    paginator = Paginator(post_list, INDEX_POSTS_QTY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/profile.html', {
        'profile': profile,
        'page_obj': page_obj,
    })


@login_required
def edit_profile(request):
    user = request.user
    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=user.username)
    else:
        form = ProfileEditForm(instance=user)
    return render(request, 'blog/user.html', {'form': form})


@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(reverse('blog:profile', args=[request.user.username]))
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {"form": form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == "POST":
        post.delete()
        return redirect('blog:index')
    return render(request, 'blog/create.html', {'post': post})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentForm()
    return render(request, 'blog/comment.html', {
        'form': form,
        'post': post,
        'comments': post.comments.all().order_by('-created_at')
    })


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(
        Comment, id=comment_id, author=request.user, post_id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)
    return render(request,
                  'blog/comment.html',
                  {'form': form, 'comment': comment, 'post_id': post_id})


@login_required
def delete_comment(request, post_id, comment_id):
    try:
        comment = Comment.objects.get(
            pk=comment_id,
            post_id=post_id,
            author=request.user
        )
    except Comment.DoesNotExist:
        raise Http404

    if request.method == "POST":
        comment.delete()
        return redirect("blog:post_detail", post_id=post_id)
    return render(request, "blog/comment.html", {
        "comment": comment,
        "form": None,
    })
