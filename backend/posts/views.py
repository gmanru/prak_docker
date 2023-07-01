from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User, Follow
from posts.forms import PostForm, Post, CommentForm

TEN_ENTRIES = 10


def get_page_context(queryset, request):
    paginator = Paginator(queryset, TEN_ENTRIES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


def index(request):
    """Здесь код запроса к модели главной
    страницы и создание словаря контекста"""
    template = 'posts/index.html'
    context = get_page_context(Post.objects.all(), request)
    return render(request, template, context)


def group_posts(request, slug):
    """Здесь код запроса к модели страницы
    постов группы и создание словаря контекста"""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all().order_by('-pub_date')
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(get_page_context(group.posts.all(), request))
    return render(request, template, context)


def profile(request, username):
    """Здесь код запроса к модели страницы
    профайла и создание словаря контекста"""
    user = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=user
        ).exists()
    else:
        following = False
    profile = user
    context = {
        'username': user,
        'following': following,
        'profile': profile,
    }
    context.update(get_page_context(user.posts.all(), request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Здесь код запроса к модели страницы
    деталей поста и создание словаря контекста"""
    posts = get_object_or_404(Post, pk=post_id)
    comments = posts.comments.all()
    form = CommentForm()
    context = {
        'posts': posts,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Здесь код запроса к модели страницы
    редактирования поста и создание словаря контекста"""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)

    form = PostForm()
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Здесь код запроса к модели страницы
    создания поста и создание словаря контекста"""
    post = get_object_or_404(Post, id=post_id)
    is_edit = True
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': is_edit,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """View-функция страницы, куда будут выведены посты авторов,
    на которых подписан текущий пользователь"""
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        'posts/follow.html',
        {
            'page': page,
            'page_obj': page_obj,
            'paginator': paginator,
        }
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(
        user=request.user,
        author=author,
    )
    if not follower.exists() and request.user != author:
        Follow.objects.create(
            user=request.user,
            author=author,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
