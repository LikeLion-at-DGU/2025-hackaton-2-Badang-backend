# trend/services.py
import json
from django.db import transaction
from trend.models import *
from openai import OpenAI
import boto3

import base64, hashlib
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _prompt_for(keyword: str) -> str:
    return (f"{keyword} 관련 상업용 일러스트. "
            f"배경 깔끔, 시니어 친화, 고대비, 텍스트/로고/브랜드 미포함.")

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def generate_local_image_for_keyword(keyword: str, size: str = "1792x1024") -> str:
    
    #이미 존재하면 재사용. 새로 만들면 저장 후 상대 경로('trends/xxx.png') 반환.
    
    prompt = _prompt_for(keyword)
    key = _hash(f"{prompt}|{size}")
    rel_path = f"trends/{key}.png"  # MEDIA_ROOT/trends/xxx.png

    if default_storage.exists(rel_path):
        return rel_path

    res = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=size,
        response_format="b64_json",
        n=1,
    )
    b64 = res.data[0].b64_json
    raw = base64.b64decode(b64)

    default_storage.save(rel_path, ContentFile(raw))
    return rel_path


#이미지 생성. S3 연결 예정

# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# def _prompt_for(keyword: str) -> str:
#     return (f"{keyword} 관련 상업용 홍보 일러스트. 깔끔한 배경, "
#             f"시니어 친화적, 명도 대비 높음, 텍스트 없음, 로고/브랜드 미포함.")

# def _hash_prompt(p: str) -> str:
#     return hashlib.sha256(p.encode("utf-8")).hexdigest()

# def _upload_to_s3(b64_data: str, key: str) -> str:
#     img_bytes = base64.b64decode(b64_data)
#     s3 = boto3.client("s3",
#         aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#         region_name=settings.AWS_REGION,
#     )
#     bucket = settings.AWS_BUCKET_NAME
#     s3.put_object(Bucket=bucket, Key=key, Body=img_bytes, ContentType="image/png", ACL="public-read")
#     return f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"

# def generate_image_for_keyword(keyword: str) -> TrendImage:
#     prompt = _prompt_for(keyword)
#     h = _hash_prompt(prompt)

#     # Idempotency: 이미 있으면 재사용
#     obj, created = TrendImage.objects.get_or_create(
#         prompt_hash=h,
#         defaults={"keyword": keyword, "prompt": prompt, "status": "pending"},
#     )
#     if not created and obj.status == "succeeded":
#         return obj

#     # 실제 생성 호출 (b64로 받아서 우리 스토리지에 저장)
#     try:
#         res = client.images.generate(
#             model="gpt-image-1",
#             prompt=prompt,
#             size="512x512",
#             response_format="b64_json",
#             n=1,
#         )
#         b64 = res.data[0].b64_json
#         s3_key = f"trends/{h}.png"
#         url = _upload_to_s3(b64, s3_key)

#         obj.image_url = url
#         obj.status = "succeeded"
#         obj.save()
#         return obj
#     except Exception as e:
#         obj.status = "failed"
#         obj.save()
#         # 로깅만; 상위에서 재시도 정책
#         raise
