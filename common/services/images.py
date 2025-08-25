# common/services/images.py
import base64
import hashlib
import logging
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

def _promptFor(keyword: str) -> str:
    return f"{keyword} 관련 상업용 일러스트. 배경 깔끔, 시니어 친화, 고대비, 텍스트/로고/브랜드 미포함."

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def normalizeSize(size: str) -> str:
    allowed = {"1024x1024", "1024x1536", "1536x1024", "auto"}
    s = (size or "1024x1024").lower()
    if s not in allowed:
        logger.warning(f"Unsupported size {size!r}, fallback to 1024x1024")
        return "1024x1024"
    return s

def _newOpenaiClient() -> OpenAI:
    """
    project/organization은 값이 있을 때만 세팅 (잘못된 값으로 401 방지)
    """
    kwargs = {"api_key": settings.OPENAI_API_KEY}
    project = getattr(settings, "OPENAI_PROJECT_ID", None)
    organization = getattr(settings, "OPENAI_ORGANIZATION", None)
    if project:
        kwargs["project"] = project
    if organization:
        kwargs["organization"] = organization
    return OpenAI(**kwargs)

def generateImageForKeyword(keyword: str, size: str = "1024x1024") -> dict:
    size = normalizeSize(size)
    prompt = _promptFor(keyword)

    # 캐시 키 (size가 'auto'여도 그대로 키에 포함해 구분)
    key = _hash(f"{prompt}|{size}|gpt-image-1")
    relPath = f"trends/{key}.png"

    # 캐시 히트 시 즉시 반환
    if default_storage.exists(relPath):
        return {"path": relPath, "url": default_storage.url(relPath)}

    client = _newOpenaiClient()

    try:
        res = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,     # 허용: 1024x1024 / 1024x1536 / 1536x1024 / auto
            n=1,
        )
        b64 = res.data[0].b64_json  # SDK 표준 필드
        raw = base64.b64decode(b64)

        savedPath = default_storage.save(relPath, ContentFile(raw))
        return {"path": savedPath, "url": default_storage.url(savedPath)}

    except Exception as e:
        logger.exception(f"Image generation failed for '{keyword}': {e}")
        # 호출부에서 상태코드 매핑하도록 예외는 그대로 던짐
        raise
