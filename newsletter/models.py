from django.db import models
from main.models import Store, Profile
from review.models import ReviewAnalysis
from trend.models import Keyword

# Create your models here.
class Newsletter(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="newsletters")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="newsletters")
    review_analysis = models.ForeignKey(ReviewAnalysis, on_delete=models.CASCADE, related_name="newsletters")
    keywords = models.ManyToManyField(Keyword)
    
    title = models.CharField(max_length=100)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    isUserMade = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    isLiked = models.BooleanField(default=False)
    
    firstContent = models.TextField()
    secondContent = models.TextField() 
    feedback = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{', '.join(str(keyword) for keyword in self.keywords.all())}에 대한 뉴스레터 {self.title}"
