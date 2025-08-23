# common/services/images.py  (또는 네가 둔 유틸 파일)
import base64, hashlib, logging
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def _promptFor(keyword: str) -> str:
    return (f"{keyword} 관련 상업용 일러스트. "
            f"배경 깔끔, 시니어 친화, 고대비, 텍스트/로고/브랜드 미포함.")

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def generateImageForKeyword(keyword: str, size: str = "1792x1024") -> dict:
    
    # 사이즈 검증
    validSizes = {
        "dall-e-3": ["1024x1024", "1792x1024", "1024x1792"],
        "dall-e-2": ["256x256", "512x512", "1024x1024"]
    }
    
    # DALL-E 3를 기본으로 사용하되, 지원하지 않는 사이즈면 DALL-E 2 사용
    model = "dall-e-3"
    if size not in validSizes["dall-e-3"]:
        if size in validSizes["dall-e-2"]:
            model = "dall-e-2"
        else:
            # 지원하지 않는 사이즈면 기본값으로 변경
            logger.warning(f"Unsupported size {size}, using 1024x1024")
            size = "1024x1024"
    
    prompt = _promptFor(keyword)
    key = _hash(f"{prompt}|{size}|{model}")
    relPath = f"trends/{key}.png"

    # 이미 존재하는 파일이면 바로 반환
    if default_storage.exists(relPath):
        logger.info(f"Using cached image for keyword: {keyword}")
        return {"path": relPath, "url": default_storage.url(relPath)} 

    try:
        logger.info(f"Generating image for keyword: {keyword} with {model}")
        
        # DALL-E API 호출
        res = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            response_format="b64_json",
            n=1,
        )
        
        # base64 디코딩 및 저장
        b64 = res.data[0].b64_json
        rawData = base64.b64decode(b64)
        
        # 파일 저장
        savedPath = default_storage.save(relPath, ContentFile(rawData))
        logger.info(f"Image saved successfully: {savedPath}")
        
        fileUrl = default_storage.url(savedPath)
        return {"path": savedPath, "url": fileUrl}
        
    except Exception as e:
        logger.error(f"Failed to generate image for keyword '{keyword}': {str(e)}")
        raise Exception(f"Image generation failed: {str(e)}")