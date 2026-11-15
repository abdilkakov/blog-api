from datetime import timedelta
from typing import Any

from django.core.management import BaseCommand, CommandError, CommandParser
from django.db import connection
from django.db.models import Count, Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.auths.models import User
from apps.blog.models import Comment, Post
from apps.blog.queries import QUERIES

DISPLAY_ROWS = 5
MUTATING_NUMBERS = {40, 41, 42, 43, 44}

def example_arguments() -> dict[int, dict[str, Any]]:
    post = Post.objects.order_by("-created_at").first()
    published = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .select_related("author")
        .order_by("-created_at")
        .first()
    )
    user = User.objects.order_by("pk").first()
    pair_post = (
        Post.objects.annotate(tag_total=Count("tags"))
        .filter(tag_total__gte=2)
        .order_by("pk")
        .first()
    )
    pair = (
        list(pair_post.tags.order_by("pk").values_list("slug", flat=True)[:2])
        if pair_post else []
    )
    comment_category = (
        Comment.objects.filter(post__category__isnull=False)
        .values_list("post__category__slug", flat=True)
        .first()
    )
    example_date = post.created_at.date() if post else timezone.localdate()
    example_word = post.title.split()[0] if post and post.title else "python"
    example_domain = (
        user.email.partition("@")[2] if user and "@" in user.email
        else "example.com"
    )
    first_tag = pair[0] if pair else "python"
    second_tag = pair[1] if len(pair) > 1 else "django"

    return {
        4: {"slug": post.slug if post else "missing-slug"},
        7: {"page": 1},
        8: {"word": example_word},
        9: {"domain": example_domain},
        11: {"slugs": ["python", "django"]},
        12: {"year": example_date.year, "month": example_date.month},
        13: {"days": 365},
        14: {
            "start": example_date - timedelta(days=30),
            "end": example_date,
        },
        15: {"email": published.author.email if published else ""},
        16: {"tag_slug": first_tag},
        17: {"category_slug": comment_category or "python"},
        21: {"first_slug": first_tag, "second_slug": second_tag},
        22: {"text": example_word},
        34: {"min_posts": 1},
        37: {"text": user.first_name[:2] if user else "jo"},
        40: {"name": "Django ORM"},
        41: {"days": 30},
        42: {"category_slug": "python", "tag_slug": "orm"},
        43: {"source_slug": "testing", "target_slug": "django"},
    }

def format_row(row: Any, annotations: tuple[str, ...]) -> str:
    if not isinstance(row, Model):
        return repr(row)

    parts = [f"{row._meta.object_name}(pk={row.pk})"]
    for field in ("title", "name", "email", "body"):
        if field in row.__dict__:
            value = str(row.__dict__[field]).replace("\n", " ")
            parts.append(f"{field}={value[:60]!r}")
    for field in annotations:
        parts.append(f"{field}={getattr(row, field)!r}")
    return " ".join(parts)

class Command(BaseCommand):

    help = "Run Homework 3 ORM queries and show query counts."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--number", type=int, help="Run just one query number"
        )
        parser.add_argument(
            "--sql", action="store_true", help="Also show executed SQL"
        )

    def handle(self, *args, **options) -> None:
        requested = options["number"]
        if requested is not None and requested not in QUERIES:
            raise CommandError(f"Unknown query number: {requested}")

        numbers = (
            [requested]
            if requested is not None
            else [number for number in QUERIES if number not in MUTATING_NUMBERS]
        )
        arguments = example_arguments()

        for number in numbers:
            function = QUERIES[number]
            with CaptureQueriesContext(connection) as context:
                result = function(**arguments.get(number, {}))
                if isinstance(result, QuerySet):
                    rows = list(result)
                    annotations = tuple(result.query.annotations)
                elif isinstance(result, list):
                    rows = result
                    annotations = ()
                else:
                    rows = None
                    annotations = ()

            sql_count = len(context.captured_queries)
            sql_label = "SQL query" if sql_count == 1 else "SQL queries"
            self.stdout.write(
                f"#{number} {function.__name__} - {sql_count} {sql_label}"
            )

            if rows is None:
                self.stdout.write(f" {result!r}")
            else:
                for row in rows[:DISPLAY_ROWS]:
                    self.stdout.write(f" {format_row(row, annotations)}")
                self.stdout.write(f" ({len(rows)} rows)")
            if options["sql"]:
                for query in context.captured_queries:
                    self.stdout.write(f" SQL: {query['sql']}")

            self.stdout.write("")