from common.serializers import *
from main.models import *
from .models import *
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate

class DomainError(Exception):
    pass


def profileLogin(username: str, password: str):
    
    user = authenticate(username=username, password=password)
    if user is None:
        raise DomainError("아이디 또는 비밀번호가 잘못되었습니다.")
    
    if not user.is_active:
        raise DomainError("비활성화된 계정입니다.")
    
    return user