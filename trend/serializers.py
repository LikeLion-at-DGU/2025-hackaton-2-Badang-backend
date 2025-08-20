from rest_framework import serializers
from django.db import transaction
from .models import *
from main.models import *
from review.models import *

#---------키워드 serializers-----------#
#사용자가 직접 입력하는 키워드를 keyword db 에 등록할 떄 사용
class KeywordsInputReq(serializers.Serializer):
    keyword = serializers.CharField()
    storeId = serializers.IntegerField()
    
# trend 를 ai에게 넘긴 후 ai가 분석해 반환해주는 키워드들을 keyword db에 저장하는 용도의 데이터 형식
class TrendAnalysisByAiReq(serializers.Serializer):
    keyword = serializers.CharField()


#----image 생성 serialzier --------#  
#이미지를 만들라고 할 때 ai 에게 넘겨줄 데이터 형식
class GenerateImageReq(serializers.Serializer):
    keyword = serializers.CharField(max_length=100)


#ai 가 제작한 키워드에 맞는 이미지를 db 에 저장할 용도의 데이터 형식
class TrendImageRes(serializers.Serializer):
    keyword = serializers.CharField()
    image_url = serializers.CharField(allow_null=True)
    status = serializers.CharField()