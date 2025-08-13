from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    userId = models.ForeignKey(User, on_delete=models.CASCADE, primary_key=True)
    profileName = models.CharField(max_length=50)
    profilePhoneNumber = models.CharField(max_length=15)

class Store(models.Model):
    userId = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='stores')
    name = models.CharField(max_length=50)
    address = models.TextField()
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    kakaoStore = models.IntegerField(blank=True)
    type = models.TextField(blank=True)
    category = models.TextField(blank=True)
    isWillingCollaborate = models.BooleanField(default=False)
    storeContent = models.TextField(blank=True)
    menu = models.TextField(blank=True)
    price = models.TextField(blank=True)
    visitor = models.TextField(blank=True)
    
    
class NewsLetter(models.Model):
    newsId = models.AutoField(primary_key=True)
    userId = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='newsletters')
    storeId = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='newsletters')
    reviewAnalysisId = models.ForeignKey('review.ReviewAnalysis', on_delete=models.CASCADE, related_name='newsletters')
    keywordId = models.ForeignKey('trend.Keyword', on_delete=models.CASCADE, related_name='newsletters')
    newsContent = models.TextField()
