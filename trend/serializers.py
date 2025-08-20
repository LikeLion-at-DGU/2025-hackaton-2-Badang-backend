from rest_framework import serializers
from django.db import transaction
from .models import *
from main.models import *
from review.models import *

#---------키워드 serializers-----------#

class KeywordsInputReq(serializers.Serializer):
    keywords = serializers.CharField()
    storeId = serializers.IntegerField()
    
    
class TrendAnalysisByAiReq(serializers.Serializer):
    keyword = serializers.CharField()


#----image 생성 serialzier --------#  
class GenerateImageReq(serializers.Serializer):
    keyword = serializers.CharField(max_length=100)

class TrendImageRes(serializers.Serializer):
    keyword = serializers.CharField()
    image_url = serializers.URLField(allow_null=True)
    status = serializers.CharField()