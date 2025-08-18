from django.db import models
from main.models import *
# Create your models here.

class Collaborate(models.Model):
    requestStore = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='requestCollaborate')
    responseStore = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='responseCollaborate')
    isAccepted = models.IntegerField(default=0)
    requestCreatedAt = models.DateTimeField(auto_now_add=True)
    createdAt = models.DateTimeField(blank=True)
    content = models.TextField(blank=True,null=True)