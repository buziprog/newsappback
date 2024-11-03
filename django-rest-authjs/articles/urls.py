from django.urls import path
from .views import ArticleViewSet, BookmarkViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')
urlpatterns = router.urls
