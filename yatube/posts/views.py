from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from . import utils
from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(1, key_prefix='index_page')
def index(request):
    posts = Post.objects.all()
    page_obj = utils.get_page_context(request, posts)
    template = 'posts/index.html'
    if request.user.is_authenticated:
        follower = request.user.follower.exists()
        context = dict(page_obj=page_obj, follower=follower)
        return render(request, template, context)
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
    user = request.user
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = utils.get_page_context(request, posts)
    template = 'posts/profile.html'
    context = dict(author=author,
                   page_obj=page_obj,
                   following=False)
    if user.is_authenticated and author.following.filter(user=user):
        context.update(following=True)
        return render(request, template, context)
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post.comments.all()
    template = 'posts/post_detail.html'
    context = dict(post=post, form=form, comments=comments)
    return render(request, template, context)


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
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = dict(form=form, is_edit=True, post_id=post_id)
    return render(request, 'posts/post_create.html', context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    post.delete()
    return redirect('posts:profile', request.user)


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
    page_obj = utils.get_page_context(request, posts)
    follower = request.user.follower.exists()
    template = 'posts/follow.html'
    context = dict(page_obj=page_obj, follower=follower)
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author and not user.follower.filter(author=author):
        Follow.objects.create(user=user, author=author)
    template = 'posts:profile'
    return redirect(template, username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(Follow, user=request.user,
                      author__username=username).delete()
    template = 'posts:profile'
    return redirect(template, username=username)
