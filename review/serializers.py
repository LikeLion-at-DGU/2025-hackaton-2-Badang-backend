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

class ReviewAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewAnalysis
        fields = [
            "reviewAnalysisId",
            "storeId",
            "storeName",
            "goodPoint",
            "badPoint",
            "goodPercentage",
            "middlePercentage",
            "badPercentage",
            "analysisKeyword",
            "analysisProblem",
            "analysisSolution",
            "createdAt",
            "updatedAt",
        ]

class StoreReviewResponseSerializer(serializers.Serializer):
    statusCode = serializers.IntegerField()
    message = serializers.CharField()
    data = ReviewAnalysisSerializer()