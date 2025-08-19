from django.db import models
from main.models import *
# Create your models here.

class Trend(models.Model):
    trendData = models.TextField()
    createdAt = models.DateTimeField(auto_now_add=True)

class KeywordImage(models.Model):
    keywordImageUrl = models.TextField()

class Keyword(models.Model):
    keywordName = models.CharField(max_length=50)
    image = models.ForeignKey(KeywordImage, on_delete=models.CASCADE, related_name='+')
    trend = models.ForeignKey(Trend, on_delete=models.CASCADE, related_name='keywords')
    isImage = models.BooleanField(default=False)
    keywordCreatedAt = models.DateField(auto_now_add=True)
    
class KeywordByUser(models.Model):
    keywordName = models.CharField(max_length=50)
    image = models.ForeignKey(KeywordImage, on_delete=models.CASCADE, related_name='+')
    isImage = models.BooleanField(default=False)
    keywordCreatedAt = models.DateField(auto_now_add=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='keywords')