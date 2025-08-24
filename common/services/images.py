# common/services/images.py
import base64, hashlib, logging
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)
client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    project=getattr(settings, "OPENAI_PROJECT_ID", None), 
)

def _promptFor(keyword: str) -> str:
    return (f"{keyword} 관련 상업용 일러스트. 배경 깔끔, 시니어 친화, 고대비, 텍스트/로고/브랜드 미포함.")

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def generateImageForKeyword(keyword: str, size: str = "1024x1024") -> dict:
    
    allowedSizes = {"256x256", "512x512", "1024x1024"}
    if size not in allowedSizes:
        logger.warning(f"Unsupported size {size}, fallback to 1024x1024")
        size = "1024x1024"

    prompt = _promptFor(keyword)
    key = _hash(f"{prompt}|{size}|gpt-image-1")
    relPath = f"trends/{key}.png"

    # 캐시 히트
    if default_storage.exists(relPath):
        return {"path": relPath, "url": default_storage.url(relPath)}

    try:
        res = client.images.generate(
            model="gpt-image-1", 
            prompt=prompt,
            size=size,
            n=1,
        )
        b64 = res.data[0].b64_json
        raw = base64.b64decode(b64)
        savedPath = default_storage.save(relPath, ContentFile(raw))
        return {"path": savedPath, "url": default_storage.url(savedPath)}

    except Exception as e:
        logger.exception(f"Image generation failed for '{keyword}': {e}")
        # 여기서 raise 그대로 두면 호출부에서 failed 처리됨
        raise
