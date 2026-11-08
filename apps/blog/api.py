from rest_framework import permissions, viewsets

from .models import Category, Comment, Post, Tag
from .serializers import (
    CategorySerializer,
    CommentSerializer,
    PostSerializer,
    TagSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("author", "category").prefetch_related(
        "tags"
    )
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer: PostSerializer) -> None:
        serializer.save(author=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related("post", "author")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer: CommentSerializer) -> None:
        serializer.save(author=self.request.user)
