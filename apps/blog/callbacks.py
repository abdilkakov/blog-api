import json
from typing import Any

from django.db.models import Count
from django.http import HttpRequest

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post
from settings.conf import BLOG_ENV_ID

TOP_AUTHOR_LIMIT = 5
PERCENTAGE = 100

def environment_label(request: HttpRequest) -> list[str]:
    if BLOG_ENV_ID == "prod":
        return ["Production", "danger"]
    return ["Local", "warning"]
def drafts_badge(request: HttpRequest) -> int:
    return Post.objects.filter(status=Post.Status.DRAFT).count()

def superuser_only(request: HttpRequest) -> bool:
    return request.user.is_superuser

def dashboard_callback(
        request: HttpRequest, context: dict[str, Any]
) -> dict[str, Any]:
    published_count = Post.objects.filter(status=Post.Status.PUBLISHED).count()
    drafts_count = Post.objects.filter(status=Post.Status.DRAFT).count()
    posts_total = published_count + drafts_count

    category_counts = list(Category.objects.annotate(posts_count=Count("posts")).values("name", "posts_count").order_by("name"))
    top_authors = list(User.objects.annotate(posts_count=Count("posts")).order_by("-posts_count", "email")[:TOP_AUTHOR_LIMIT].values("email", "posts_count"))
    published_percentage = (published_count/posts_total * PERCENTAGE if posts_total else 0)
    draft_percentage = (drafts_count/posts_total * PERCENTAGE if posts_total else 0)

    context.update(
        {
            "stats": [
                {"label": "Users", "value": User.objects.count()},
                {"label": "Published posts", "value": published_count},
                {"label": "Drafts", "value": drafts_count},
                {"label": "Comments", "value": Comment.objects.count()},
            ],
            "categories_chart": json.dumps(
                {
                    "labels": [item["name"] for item in category_counts],
                    "datasets": [

                    {
                        "label": "Posts",
                        "data": [
                            item["posts_count"] for item in category_counts
                        ],
                        "backgroundColor": "#2563eb"
                    }
                ],
                }
            ),
            "top_authors" : {
                "headers": ["Author", "Posts"],
                "rows": [
                    [author["email"], author["posts_count"]]
                    for author in top_authors
                ],
        },
        "published_percentage": round(published_percentage, 1),
        "draft_percentage": round(draft_percentage, 1),
    }
    )
    return context
