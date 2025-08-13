from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    userId = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    profileName = models.CharField(max_length=50)
    profilePhoneNumber = models.CharField(max_length=15)
    
class Menu(models.Model):
    menu_name = models.CharField(max_length=50)
    menu_price = models.IntegerField()
    
class Visitor(models.Model):
    gender = models.CharField(max_length=5)
    age = models.IntegerField(default=2)
    # 0 = 청소년
    # 1 = 청년
    # 2 = 중년
    # 3 = 노년
    is_foreign = models.BooleanField(default=False)

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
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='stores')
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='stores', null=True, blank=True)
    
class NewsLetter(models.Model):
    newsId = models.AutoField(primary_key=True)
    userId = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='newsletters')
    storeId = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='newsletters')
    reviewAnalysisId = models.ForeignKey('review.ReviewAnalysis', on_delete=models.CASCADE, related_name='newsletters')
    keywordId = models.ForeignKey('trend.Keyword', on_delete=models.CASCADE, related_name='newsletters')
    newsContent = models.TextField()
