from rest_framework import serializers
from .models import *


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"


class ReviewAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewAnalysis
        fields = "__all__"
