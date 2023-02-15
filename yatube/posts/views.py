from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from .forms import CommentForm, PostForm
from .models import Post, Group, User, Follow

POSTS_PER_PAGE = 10


def paginator(request, post_list):
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    return render(
        request, 'posts/index.html',
        {'page_obj': paginator(
            request, Post.objects.select_related('author', 'group').all())
         }
    )


def group_posts(request, slug):
    return render(
        request, 'posts/group_list.html',
        {'group': get_object_or_404(Group, slug=slug),
         'page_obj': paginator(
            request, get_object_or_404(
                Group, slug=slug).posts.select_related('author').all())
         }
    )


def profile(request, username):
    return render(
        request, 'posts/profile.html',
        {'page_obj': paginator(
            request, Post.objects.select_related('group').all()),
         'author': get_object_or_404(User, username=username),
         'following': request.user.is_authenticated and (
            request.user.follower.filter(
                author=get_object_or_404(User, username=username)).exists()
        )
        }
    )


def post_detail(request, post_id):
    return render(
        request, 'posts/post_detail.html',
        {'post': get_object_or_404(Post, pk=post_id),
         'form': CommentForm(),
         'comments': get_object_or_404(Post, pk=post_id).comments.all()
         }
    )


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'post': post,
            'form': form,
            'is_edit': True
        })
    form.save()
    return redirect('posts:post_detail', post_id=post_id)


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
    return render(
        request, 'posts/follow.html',
        {'page_obj': paginator(
            request, Post.objects.filter(author__following__user=request.user))
         }
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.username != username:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
