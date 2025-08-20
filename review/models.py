from django.db import models
from main.models import *


# Create your models here.
class Reviewer(models.Model):
    reviewerId = models.AutoField(primary_key=True)
    follower = models.IntegerField(blank=True, null=True)
    reviewCount = models.IntegerField(blank=True, null=True)
    reviewAvg = models.FloatField(blank=True, null=True)
    reviewerName = models.CharField(max_length=50, blank=True, null=True)  # 오타 수정

    def __str__(self):
        return f"Reviewer {self.reviewerId}"


class Review(models.Model):
    reviewId = models.AutoField(primary_key=True)

    storeId = models.ForeignKey("main.Store", on_delete=models.CASCADE, related_name="reviews")

    reviewer = models.ForeignKey(Reviewer, on_delete=models.CASCADE, related_name="reviews")
    reviewContent = models.TextField()
    reviewDate = models.DateTimeField()
    reviewRate = models.IntegerField()

    def __str__(self):
        return f"Review {self.reviewId} for {self.storeId.name}"


class ReviewAnalysis(models.Model):
    reviewAnalysisId = models.AutoField(primary_key=True)
    storeId = models.ForeignKey(  # 한 가게당 하나의 분석 결과만 가지도록
        Store,
        on_delete=models.CASCADE,
        related_name="review_analysis"
    )

    storeName = models.CharField(max_length=255, blank=True, default="")  # 가게명
    goodPoint = models.TextField(blank=True, default="")                # 긍정적 리뷰 요약
    badPoint = models.TextField(blank=True, default="")                 # 부정적 리뷰 요약

    goodPercentage = models.FloatField(default=50.0)
    middlePercentage = models.FloatField(default=0.0)
    badPercentage = models.FloatField(default=50.0)

    analysisKeyword = models.TextField(blank=True, default="")          # 키워드 분석
    analysisProblem = models.TextField(blank=True, default="")          # 문제점 분석
    analysisSolution = models.TextField(blank=True, default="")         # 해결 방안 제안

    createdAt = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updatedAt = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"ReviewAnalysis for {self.storeName}"