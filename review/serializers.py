from rest_framework import serializers
from .models import *


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"
class ReviewPercentageSerializer(serializers.Serializer):
    goodPercentage = serializers.FloatField()
    middlePercentage = serializers.FloatField()
    badPercentage = serializers.FloatField()

class ReviewAnalysisSerializer(serializers.Serializer):
    storeName = serializers.CharField()
    goodPoint = serializers.CharField()
    badPoint = serializers.CharField()
    percentage = ReviewPercentageSerializer()
    analysisKeyword = serializers.CharField()
    analysisProblem = serializers.CharField()
    analysisSolution = serializers.CharField()

class StoreReviewResponseSerializer(serializers.Serializer):
    statusCode = serializers.IntegerField()
    message = serializers.CharField()
    data = ReviewAnalysisSerializer()