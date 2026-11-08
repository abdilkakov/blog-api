from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import  (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponse
from  django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.text import Truncator


from .models import Category, Comment, Post, Tag



COMMENT_PREVIEW_LENGTH = 80
INLINE_COMMENTS_PER_PAGE = 10

class CategoryPostsSection(TableSection):
    verbose_name = "Posts in this category"
    related_name = "posts"
    fields = ["title", "status", "created_at"]

class PostCommentsSection(TableSection):
    verbose_name = "Comments"
    related_name = "comments"
    fields = ["author", "body", "created_at"]

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_sections = [CategoryPostsSection]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        return (
            super().get_queryset(request).annotate(_post_count=Count("posts")).prefetch_related("posts")
        )
    @display(description="Posts", ordering="_post_count")
    def post_count(self, obj:Category) -> int:
        return obj._post_count
@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        return  super().get_queryset(request).annotate(
            _post_count=Count("posts")
        )

    @display(description="Posts", ordering="_post_count")
    def post_count(self, obj:Tag) -> int:
        return  obj._post_count

@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("post", "author", "short_body", "created_at")
    search_fields = ("body", "author__email", "post__title")
    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter)
    )
    list_filter_submit = True
    autocomplete_fields = ("post", "author")
    list_select_related = ("post", "author")

    @display(description="Comment")
    def short_body(self, obj:Comment) -> str:
        return Truncator(obj.body).chars(COMMENT_PREVIEW_LENGTH)

class CommentInline(TabularInline):
    model = Comment
    tab = True
    per_page = INLINE_COMMENTS_PER_PAGE
    extra = 0
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)

@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = (
        "post_header", "status_label", "category", "tags_dropdown",
        "comments_count", "created_at",
    )
    search_fields = ("title", "body", "author__email")
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True
    list_sections = [PostCommentsSection]
    autocomplete_fields = ("author", "category", "tags")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    warn_unsaved_form = True
    formfield_overrides = {
        models.TextField: {"widget": WysiwygWidget},
    }
    fieldsets = (
        (
            "Content",
            {
                "classes": ("tab",),
                "fields": ("title", "slug", "body"),
            },
        ),
        (
            "Classification",
            {
                "classes": ("tab",),
                "fields": ("category", "tags", "status"),
            },
        ),
        (
            "Meta",
            {
                "classes": ("tab",),
                "fields": ("author", "created_at", "updated_at"),
            },
        ),
    )
    inlines = [CommentInline]
    actions = ("publish_selected", "move_to_drafts")
    actions_row = ["toggle_publish"]
    actions_list = ["publish_all_drafts"]
    actions_detail = ["open_comments"]
    actions_submit_line = ["save_and_publish"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        return (
            super().get_queryset(request).select_related("author", "category")
            .prefetch_related("tags","comments__author")
            .annotate(_comments_count=Count("comments", distinct=True))

        )

    @display(description="Post", ordering="title", header=True)
    def post_header(self, obj: Post) -> list[str]:
        return [obj.title, obj.author.email]

    @display(
        description="Status", ordering = "status",
        label={"published": "success", "draft":"warning"},
    )
    def status_label(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj: Post) -> dict[str, object]:
        tags = list(obj.tags.all())
        return {
            "title": f"{len(tags)} tags",
            "items": [{"title": tag.name} for tag in tags],
        }
    @display(description="Comments", ordering="_comments_count")
    def comments_count(self, obj: Post) -> int:
        return obj._comments_count

    @action(description="Publish selected")
    def publish_selected(self,
                         request: HttpRequest, queryset: QuerySet[Post]) -> None:
        queryset.update(status=Post.Status.PUBLISHED)

    @action(description="Move to drafts")
    def move_to_drafts(self,
                       request: HttpRequest, queryset: QuerySet[Post]) -> None:
        queryset.update(status=Post.Status.DRAFT)

    @action(description="Publish / unpublish", url_path="toggle-publish")
    def toggle_publish(self,
                       request: HttpRequest, object_id: str) -> HttpResponse:
        post = get_object_or_404(Post, pk=object_id)
        new_status = (
            Post.Status.DRAFT
            if post.status == Post.Status.PUBLISHED
            else Post.Status.PUBLISHED
        )
        Post.objects.filter(pk=post.pk).update(status=new_status)
        return redirect("admin:blog_post_changelist")

    @action(description="Publish all drafts", url_path="publish-all-drafts")
    def publish_all_drafts(self,
                           request: HttpRequest) -> HttpResponse:
        published = Post.objects.filter(
            status=Post.Status.DRAFT
        ).update(status=Post.Status.PUBLISHED)
        messages.success(request, f"Published {published} drafts.")
        return redirect("admin:blog_post_changelist")

    @action(description="Open this post's comments", url_path="comments")
    def open_comments(self,
                      request: HttpRequest, object_id: str) -> HttpResponse:
        post = get_object_or_404(Post, pk=object_id)
        url = reverse("admin:blog_comment_changelist")
        return redirect(f"{url}?post__id__exact={post.pk}")

    @action(description="Save & publish")
    def save_and_publish(self,
                         request: HttpRequest, obj: Post) -> None:
        Post.objects.filter(pk=obj.pk).update(status=Post.Status.PUBLISHED)

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass