from rest_framework import serializers

from .models import Category, Comment, Post, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class PostSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id", "author", "title", "slug", "body", "category",
            "tags", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "post", "author", "body", "created_at"]
        read_only_fields = ["created_at"]
