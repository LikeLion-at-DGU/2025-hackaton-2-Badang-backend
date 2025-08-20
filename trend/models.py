from django.db import models
from main.models import *
# Create your models here.

class Trend(models.Model):
    trendData = models.TextField()
    createdAt = models.DateTimeField(auto_now_add=True)

class Keyword(models.Model):
    keywordName = models.CharField(max_length=50)
    keywordImageUrl = models.URLField(blank=True, null=True)
    trend = models.ForeignKey(Trend, on_delete=models.CASCADE, related_name='keywords', null=True)
    isImage = models.BooleanField(default=False)
    keywordCreatedAt = models.DateField(auto_now_add=True)
    isCreatedByUser = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='keywords', null=True,blank=True)
    status = models.CharField(max_length=20, default="pending")