import random
from time import perf_counter
from typing import Any

from faker import Faker
from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag


DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500
SEED_PASSWORD = "SeedPassword123!"
PUBLISHED_RATIO = 0.70
UNCATEGORIZED_RATIO = 0.10
INACTIVE_RATIO = 0.15
STAFF_RATIO = 0.10
MIN_SPECIAL_USERS = 1
MAX_POST_TAGS = 5
POST_PARAGRAPHS = 3
POST_TITLE_WORDS = 6
SUMMARY_WIDTH = 5
MIN_COMMENT_SENTENCES = 1
MAX_COMMENT_SENTENCES = 3
EMAIL_DOMAIN = "example.com"
SLUG_SUFFIX_START = 2

CATEGORY_NAMES = (
    "Python", "Django", "DevOps", "Databases",
    "Web Development", "APIs", "Security", "Testing",
)
TAG_NAMES = (
    "backend", "frontend", "rest", "jwt", "postgresql",
    "sqlite", "docker", "deployment", "tutorial", "beginners",
    "advanced", "authentication", "orm", "migration", "testing",
    "performance", "python", "django", "security", "database",
)


def unique_slug(text: str, used: set[str], max_length: int) -> str:
    base = slugify(text)[:max_length].strip("-") or "post"
    candidate = base
    suffix_number = SLUG_SUFFIX_START

    while candidate in used:
        suffix = f"-{suffix_number}"
        candidate = f"{base[:max_length - len(suffix)].rstrip('-')}{suffix}"
        suffix_number += 1

    used.add(candidate)
    return candidate


class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--users", type=int, default=DEFAULT_USERS,
            help="Number of users to create",
        )
        parser.add_argument(
            "--posts", type=int, default=DEFAULT_POSTS,
            help="Number of posts to create",
        )
        parser.add_argument(
            "--comments", type=int, default=DEFAULT_COMMENTS,
            help="Number of comments to create",
        )
        parser.add_argument(
            "--clear", action="store_true",
            help="Delete non-superuser data before seeding",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        started_at = perf_counter()
        counts = {
            "Users": options["users"],
            "Posts": options["posts"],
            "Comments": options["comments"],
        }
        for label, count in counts.items():
            if count < 0:
                raise CommandError(f"{label} cannot be negative.")

        if options["clear"]:
            Comment.objects.all().delete()
            Post.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        fake = Faker()
        password = make_password(SEED_PASSWORD)
        emails = set(User.objects.values_list("email", flat=True))
        total = counts["Users"]

        inactive_n = min(
            total, max(MIN_SPECIAL_USERS, round(total * INACTIVE_RATIO))
        )
        staff_n = min(
            total, max(MIN_SPECIAL_USERS, round(total * STAFF_RATIO))
        )

        inactive = set(random.sample(range(total), inactive_n))
        staff = set(random.sample(range(total), staff_n))

        users = []
        for index in range(total):
            first, last = fake.first_name(), fake.last_name()
            base = f"{slugify(first)}.{slugify(last)}"
            email = f"{base}@{EMAIL_DOMAIN}"
            number = SLUG_SUFFIX_START

            while email in emails:
                email = f"{base}{number}@{EMAIL_DOMAIN}"
                number += 1

            emails.add(email)
            users.append(User(
                email=email,
                first_name=first,
                last_name=last,
                password=password,
                is_active=index not in inactive,
                is_staff=index in staff,
            ))

        User.objects.bulk_create(users)
        authors = list(User.objects.all())

        if (counts["Posts"] or counts["Comments"]) and not authors:
            raise CommandError("Cannot create posts/comments without users.")

        old_categories = set(
            Category.objects.values_list("name", flat=True)
        )
        old_tags = set(Tag.objects.values_list("name", flat=True))

        new_categories = [
            Category(name=name, slug=slugify(name))
            for name in CATEGORY_NAMES if name not in old_categories
        ]
        new_tags = [
            Tag(name=name, slug=slugify(name))
            for name in TAG_NAMES if name not in old_tags
        ]

        Category.objects.bulk_create(new_categories)
        Tag.objects.bulk_create(new_tags)

        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())

        slugs = set(Post.objects.values_list("slug", flat=True))
        slug_length = Post._meta.get_field("slug").max_length

        posts = []
        for _ in range(counts["Posts"]):
            title = fake.sentence(nb_words=POST_TITLE_WORDS).rstrip(".")

            posts.append(Post(
                author=random.choice(authors),
                title=title,
                slug=unique_slug(title, slugs, slug_length),
                body="\n\n".join(fake.paragraphs(nb=POST_PARAGRAPHS)),
                category=(
                    random.choice(categories)
                    if categories and random.random() >= UNCATEGORIZED_RATIO
                    else None
                ),
                status=(
                    Post.Status.PUBLISHED
                    if random.random() < PUBLISHED_RATIO
                    else Post.Status.DRAFT
                ),
            ))

        Post.objects.bulk_create(posts)

        for post in posts:
            post.tags.set(random.sample(
                tags,
                random.randint(0, min(MAX_POST_TAGS, len(tags))),
            ))

        published = list(
            Post.objects.filter(status=Post.Status.PUBLISHED)
        )

        if counts["Comments"] and not published:
            raise CommandError(
                "Cannot create comments without published posts."
            )

        comments = [
            Comment(
                post=random.choice(published),
                author=random.choice(authors),
                body=" ".join(
                    fake.sentence()
                    for _ in range(random.randint(
                        MIN_COMMENT_SENTENCES,
                        MAX_COMMENT_SENTENCES,
                    ))
                ),
            )
            for _ in range(counts["Comments"])
        ]

        Comment.objects.bulk_create(comments)

        created = {
            "Users": len(users),
            "Categories": len(new_categories),
            "Tags": len(new_tags),
            "Posts": len(posts),
            "Comments": len(comments),
        }

        for label, count in created.items():
            self.stdout.write(
                f"{label + ':':<12}{count:>{SUMMARY_WIDTH}} created"
            )

        elapsed = perf_counter() - started_at
        self.stdout.write(
            self.style.SUCCESS(f"Done in {elapsed:.2f} seconds")
        )