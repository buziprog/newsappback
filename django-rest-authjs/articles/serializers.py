from rest_framework import serializers
from .models import Articles, Category, Comment, Bookmark


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name',)


class CommentSerializer(serializers.ModelSerializer):
    # This will allow the request data to provide `external_id` for the article
    article = serializers.SlugRelatedField(
        slug_field='external_id',
        queryset=Articles.objects.all()
    )

    class Meta:
        model = Comment
        fields = '__all__'


class ArticleSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)  # Add this line

    class Meta:
        model = Articles
        fields = ('external_id', 'title', 'content', 'slug', 'published_at',
                  'image_url', 'link', 'status', 'excerpt', 'author', 'categories', 'comments')  # Add 'comments' field

# serializers.py


class BookmarkSerializer(serializers.ModelSerializer):
    # Since you are only reading the article details, 'read_only=True' is fine here
    article = ArticleSerializer(read_only=True)
    # For creating a bookmark, you need to accept an article ID, so add a write_only field for that
    article_id = serializers.PrimaryKeyRelatedField(
        queryset=Articles.objects.all(), write_only=True, source='article'
    )

    class Meta:
        model = Bookmark
        fields = ['id', 'article', 'created_at', 'article_id']
        # The 'article_id' is write_only, so it won't be included in the serialized representation
        # but it will be used for creating bookmarks
