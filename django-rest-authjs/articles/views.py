from django.db import models
import pytz
from datetime import datetime
import requests
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Articles, Category, Comment, Bookmark
from .serializers import ArticleSerializer, CommentSerializer, BookmarkSerializer
from django.shortcuts import get_object_or_404
import time
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated


def fetch_and_store_articles():

    response = requests.get(
        'https://www.balkanweb.com//wp-json/wp/v2/posts')
    print("Response Status:", response.status_code)

    if response.status_code == 200:
        articles = response.json()

        for article in articles:
            external_id = article['id']

            if Articles.objects.filter(external_id=external_id).exists():
                continue  # Skip if article already exists

            wp_featuredmedia = article.get(
                '_links', {}).get('wp:featuredmedia', [])
            medium_image_url = ''

            for media_item in wp_featuredmedia:
                if 'href' in media_item:
                    media_response = requests.get(media_item['href'])
                    if media_response.status_code == 200:
                        media_data = media_response.json()
                        medium_image_url = media_data.get('source_url', '')
                    break

            category_objects = []
            wp_term = article.get('_links', {}).get('wp:term', [])
            categories_href = None

            for term in wp_term:
                if term.get('taxonomy') == 'category':
                    categories_href = term.get('href')
                    break

            if categories_href:
                category_response = requests.get(categories_href)
                if category_response.status_code == 200:
                    categories = category_response.json()

                    for item in categories:
                        name = item.get('slug')
                        category, created = Category.objects.get_or_create(
                            name=name)
                        category_objects.append(category)

            naive_datetime = datetime.fromisoformat(article['date_gmt'])
            aware_datetime = pytz.utc.localize(naive_datetime)

            new_article = Articles.objects.create(
                external_id=article['id'],
                title=article['title']['rendered'],
                content=article['content']['rendered'],
                slug=article['slug'],
                published_at=aware_datetime,
                image_url=medium_image_url,
                link=article['link'],
                status=article.get('status', ''),
                excerpt=article.get('excerpt', {}).get('rendered', ''),
                author=article.get('author', '')
            )

            new_article.categories.set(category_objects)
            new_article.save()


fetch_and_store_articles()


# ArticleViewSet manages CRUD for Articles and includes comment functionality
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Articles.objects.all().prefetch_related('categories', 'comments')
    serializer_class = ArticleSerializer
    lookup_field = 'external_id'  # This ensures the viewset uses `external_id` for lookup
    # Add this line to include SearchFilter in your viewset
    filter_backends = [SearchFilter]
    # Define fields you want to be searchable
    search_fields = ['title', 'content', 'categories__name']

    def get_object(self):
        # Override the default method to use `external_id` for fetching the article
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, *args, **kwargs):
        # Fetch the article by `external_id`
        article = self.get_object()
        if request.method == 'GET':
            comments = article.comments.filter(active=True)
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            # Debugging line to print incoming POST data
            print(f"Incoming POST data: {request.data}")
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(article=article)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                # Debugging line to print serializer errors
                print(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# CommentViewSet manages CRUD for Comments independently if needed


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        serializer.save()


class BookmarkViewSet(viewsets.ModelViewSet):
    queryset = Bookmark.objects.all()
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # Get bookmarks only for the logged-in user
        user = self.request.user
        return user.bookmarks.all()

    @action(detail=False, methods=['post'])
    def create_bookmark(self, request):
        article_id = request.data.get('article_id')
        article = get_object_or_404(Articles, external_id=article_id)
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user, article=article)

        if created:
            return Response(self.get_serializer(bookmark).data, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Bookmark already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_bookmark(self, request, pk=None):
        bookmark = get_object_or_404(Bookmark, id=pk, user=request.user)
        bookmark.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    queryset = Bookmark.objects.all()
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # No changes needed here, it's already correct
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def create_bookmark(self, request):
        article_id = request.data.get('article_id')
        article = get_object_or_404(Articles, id=article_id)
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user, article=article)

        if created:
            return Response(self.get_serializer(bookmark).data, status=status.HTTP_201_CREATED)
        return Response({'detail': 'Bookmark already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_bookmark(self, request, pk=None):
        bookmark = get_object_or_404(Bookmark, id=pk, user=request.user)
        bookmark.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        queryset = super().get_queryset()
        ids = self.request.query_params.get('')
        if ids:
            id_list = ids.split(',')
            queryset = queryset.filter(external_id=id_list)
        return queryset
