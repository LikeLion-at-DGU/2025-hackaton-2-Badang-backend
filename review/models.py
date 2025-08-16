from django.db import models
from main.models import *


# Create your models here.
class Reviewer(models.Model):
    reviewerId = models.AutoField(primary_key=True)
    follower = models.IntegerField()
    reviewCount = models.IntegerField()
    reviewAvg = models.FloatField()

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
    storeId = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="review_analysis")
    reviewId = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="review_analysis")
    analysisContent = models.TextField()

    def __str__(self):
        return f"Analysis {self.reviewAnalysisId} for Review {self.reviewId.reviewId}"
