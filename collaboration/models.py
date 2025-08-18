from django.db import models
from django.db.models import F,Q
from django.db.models.functions import Greatest, Least
from main.models import *
# Create your models here.

class Collaborate(models.Model):
    requestStore = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='requestCollaborate')
    responseStore = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='responseCollaborate')
    
    
    createdAt = models.DateTimeField(auto_now_add=True)
    #처음 요청 시 입력하는 메세지 
    initialMessage = models.TextField(blank=True, null=True)
    
    #두개에는 디폴트로 처음 요청하는 메세지가 입력되고, 이후 수정 가능하게
    requestMemo = models.TextField(blank=True, null=True)
    responseMemo = models.TextField(blank=True, null=True)
    
    
    class Status(models.IntegerChoices):
        PENDING = 0, '대기'
        ACCEPTED = 1, '수락'
        REJECTED = 2, '거절'
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)
    is_active = models.BooleanField(default=True)
    
    requestCreatedAt = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            # 자기 자신 금지
            models.CheckConstraint(
                check=~models.Q(requestStore=models.F('responseStore')),
                name='collab_diff_stores'
            ),
            # isAccepted는 0/1/2만 허용
            models.CheckConstraint(
                check=models.Q(isAccepted__in=[0,1,2]),
                name='collab_status_012_only'
            ),
            # 순서 무시 유니크: 두 FK의 "작은쪽/큰쪽" 조합으로 유니크 강제 (1,2) 나 (2,1) 동일하게 (1,2)로 취급함
            models.UniqueConstraint(
                expressions=[
                    Least(F('requestStore_id'), F('responseStore_id')),
                    Greatest(F('requestStore_id'), F('responseStore_id')),
                ],
                condition=Q(is_active=True),
                name='unique_collab_unordered_pair',
            ),
        ]