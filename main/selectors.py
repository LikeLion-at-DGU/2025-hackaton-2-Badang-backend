from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, get_list_or_404
from common.serializers import *
from main.models import *
from .models import *
from django.core.exceptions import ObjectDoesNotExist

class DomainError(Exception):
    pass


def getUserByUsername(username: str) -> User | None:
    return User.objects.filter(username=username).first()

def getProfileByUser(user: User) -> Profile | None:
    try:
        return Profile.objects.select_related('userId').get(userId=user)
    except ObjectDoesNotExist:
        return None