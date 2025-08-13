from django.db import models

# Create your models here.

class Trend(models.Model):
    trendData = models.TextField()

class KeyWordImage(models.Model):
    keyWordImageUrl = models.TextField()

class Keyword(models.Model):
    keyWordName = models.CharField(max_length=50)
    image = models.ForeignKey(KeyWordImage, on_delete=models.CASCADE, related_name='keywords')
    trend = models.ForeignKey(Trend, on_delete=models.CASCADE, related_name='keywords')
    isImage = models.BooleanField(default=False)
    keyWordCreatedAt = models.DateField(auto_now_add=True)