from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display
from unfold.forms import AdminPasswordChangeForm

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, QuerySet
from  django.http import HttpRequest

from .forms import BlogUserCreationForm, BlogUserChangeForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = BlogUserChangeForm
    add_form =  BlogUserCreationForm
    change_password_form = AdminPasswordChangeForm
    ordering = ("email",)
    list_display = (
        "user_header", "active_label", "staff_label", "post_count"
    )
    search_fields = ("email", "first_name", "last_name")
    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )
    list_filter_submit = True
    readonly_fields = ("last_login",)
    fieldsets = (
            (
                "Personal info",
                {
                    "classes": ("tab",),
                    "fields": ("email", "first_name", "last_name", "password"),

                },

            ),
            (
                "Permissions",
                {
                    "classes":("tab",),
                     "fields": (
                        "is_active", "is_staff", "is_superuser","groups", "user_permissions"
                     ),
                },
                ),
            (
                "Important dates",
                {"classes": ("tab",), "fields": ("last_login",)},
            )
    )
    add_fieldsets = (
                ("New user",
                {
                    "fields": (
                        "email", "first_name", "last_name", "password1", "password2",
                    ),
                },
                ),
            ),

    actions = ("activate_users", "deactivate_users")

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return super().get_queryset(request).annotate(
            _post_count=Count("posts")
        )
    @display(description="User", ordering="email", header=True)
    def  user_header(self, obj: User) -> list[str]:
        initials = f"{obj.first_name[:1]}{obj.last_name[:1]}".upper()
        return [obj.get_full_name(), obj.email, initials]

    @display(
        description="Active", ordering="is_active",
        label={True: "success", False: "danger"},
    )
    def active_label(self, obj: User) -> tuple[bool, str]:
        return  obj.is_active, "Active" if obj.is_active else "Inactive"

    @display(description = "Staff", ordering="is_staff",
             label = {True: "info", False: "warning"},)
    def staff_label(self, obj: User) -> tuple[bool, str]:
        return obj.is_staff, "Staff" if obj.is_staff else "User"

    @display(description="Posts", ordering="_post_count")
    def post_count(self, obj: User) -> int:
        return obj._post_count

    @action(description="Acttive selected")
    def activate_users(self,
                     request: HttpRequest, queryset: QuerySet[User]) -> None:
        queryset.update(is_active=True)

    @action(description="Deactivate selected")
    def deactivate_users(self,
                         request: HttpRequest, queryset: QuerySet[User]) -> None:
        queryset.update(is_active=False)

