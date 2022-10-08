from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from . import utils
from .forms import CommentForm, PostForm
from .models import Group, Post, User, Follow


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.all()
    template = 'posts/index.html'
    page_obj = utils.get_page_context(request, posts)
    if request.user.is_authenticated:
        follower = request.user.follower.exists()
        context = dict(page_obj=page_obj, follower=follower)
        return render(request, template, context)
    else:
        context = dict(page_obj=page_obj)
        return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = utils.get_page_context(request, posts)
    context = dict(group=group, page_obj=page_obj)
    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author__username=author)
    post_count = posts.count()
    page_obj = utils.get_page_context(request, posts)
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user)
        context = dict(post_count=post_count,
                       author=author,
                       page_obj=page_obj,
                       following=following)
        return render(request, 'posts/profile.html', context)
    else:
        context = dict(post_count=post_count,
                       author=author,
                       page_obj=page_obj)
        return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = dict(post=post, form=form, comments=comments)
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST,
        files=request.FILES or None)
    if form.is_valid():
        post = form.save(False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    context = dict(form=form, is_edit=True, post_id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    template = 'posts/follow.html'
    page_obj = utils.get_page_context(request, posts)
    follower = request.user.follower.exists()
    context = dict(page_obj=page_obj, follower=follower)
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    follower = Follow.objects.filter(user=user, author=author)
    if user != author and not follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', username=username)
