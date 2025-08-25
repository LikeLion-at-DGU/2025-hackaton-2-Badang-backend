from django.contrib import admin
from .models import Review, ReviewAnalysis, Reviewer
# Register your models here.

admin.site.register(Review)
admin.site.register(ReviewAnalysis)
admin.site.register(Reviewer)