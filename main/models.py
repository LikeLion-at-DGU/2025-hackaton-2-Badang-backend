from django.db import models

# Create your models here.

class Store(models.Model):
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
    
    
    