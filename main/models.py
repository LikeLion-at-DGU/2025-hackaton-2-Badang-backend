from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    profileName = models.CharField(max_length=50)
    profilePhoneNumber = models.CharField(max_length=15)

class Search(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='searches')
    term = models.CharField(max_length=100, blank=True)
    searched_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)



class Visitor(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', '남'
        FEMALE = 'F', '여'
        OTHER = 'O', '기타'

    class AgeGroup(models.IntegerChoices):
        TEEN = 0, '청소년'
        YOUTH = 1, '청년'
        MIDDLE = 2, '중년'
        SENIOR = 3, '노년'

    gender = models.CharField(max_length=1, choices=Gender.choices)
    age_group = models.IntegerField(choices=AgeGroup.choices, default=AgeGroup.MIDDLE)
    is_foreign = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.get_gender_display()} / {self.get_age_group_display()} / 외국인:{self.is_foreign}'


class Type(models.Model):
    name = models.CharField(max_length=50)


class Category(models.Model):
    type = models.ForeignKey(Type, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.type.name} / {self.name}'

    
class Store(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='stores')
    name = models.CharField(max_length=50)
    address = models.TextField()
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    storeNumber = models.TextField(null=True, blank=True)

    kakaoPlaceId = models.BigIntegerField(blank=True, null=True, unique=True)

    type = models.ForeignKey(Type, on_delete=models.PROTECT, related_name='stores', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='stores', blank=True, null=True)

    isWillingCollaborate = models.BooleanField(default=False)
    content = models.TextField(blank=True)
    visitor = models.ForeignKey(Visitor, on_delete=models.SET_NULL, related_name='stores', null=True, blank=True)

    def __str__(self):
        return self.name


class Menu(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='menus', null=True, blank=True)
    name = models.CharField(max_length=50)
    price = models.IntegerField()

    def __str__(self):
        return f'{self.store.name} - {self.name}'

class NewsLetter(models.Model):
    newsId = models.AutoField(primary_key=True)
    userId = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='newsletters')
    storeId = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='newsletters')
    reviewAnalysisId = models.ForeignKey('review.ReviewAnalysis', on_delete=models.CASCADE, related_name='newsletters')
    keywordId = models.ForeignKey('trend.Keyword', on_delete=models.CASCADE, related_name='newsletters')
    newsContent = models.TextField()
