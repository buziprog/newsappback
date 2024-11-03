from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Articles(models.Model):
    external_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    slug = models.SlugField()
    published_at = models.DateTimeField()
    image_url = models.URLField()
    status = models.CharField(max_length=20, null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    excerpt = models.TextField(null=True, blank=True)
    author = models.CharField(max_length=100, null=True, blank=True)
    categories = models.ManyToManyField(
        Category, related_name='articles', blank=True)

    class Meta:
        app_label = 'articles'


class Comment(models.Model):
    article = models.ForeignKey(
        Articles, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created']
        indexes = [
            models.Index(fields=['created']),
        ]

    def __str__(self):
        return f'Comment by {self.name} on {self.article}'
        pass

    pass


class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='bookmarks')
    article = models.ForeignKey(
        Articles, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}'s bookmark of {self.article}"
