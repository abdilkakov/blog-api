from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django.contrib import admin
from django.urls import include, path

from apps.blog.api import CategoryViewSet, CommentViewSet, PostViewSet, TagViewSet


router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("tags", TagViewSet)
router.register("posts", PostViewSet)
router.register("comments", CommentViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
