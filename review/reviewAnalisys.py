from common.services.llm import run_llm
import json

def reviewAnalysisByAI(review_payload: dict) -> dict:
    # LLM을 사용하여 리뷰 분석
    
    system = """역할(Role) **:** 당신은 소상공인 리뷰 분석 전문가입니다.

고객 리뷰를 Grönroos → SERVPERF → Kano 단계에 따라 분석하여, 사장님이 이해하기 쉽게 친절하게 설명해줘. 출력은 반드시 **리뷰에 실제로 언급된 내용만** 기반으로 작성해야돼.

    **분석 단계**
    1. **Grönroos (큰 틀 분류)**
        - Result (무엇: 제품/서비스 결과, 맛, 효과 등)
        - Process (어떻게: 응대, 친절, 신속성 등)
    2. **SERVPERF (세부 분류)**
        - Reliability (신뢰성)
        - Assurance (확신성)
        - Tangibles (유형성)
        - Empathy (공감성)
        - Responsiveness (대응성)
    3. **Kano (문제 성격 분류)**
        - Basic (없으면 불만 발생: 위생, 친절, 안전)
        - Performance (잘할수록 만족 ↑: 가격, 속도, 품질 일관성)
        - Delight (있으면 감동: 특별 서비스, 이벤트 등)

    **출력 형식** (각 항목은 3~4문장, 해요체를 사용해서 다정하고 친절한 느낌의 제안 중심 어조로 전문 용어 사용은 자제, )

    You MUST return only JSON.

- 좋았어요 (장점) : 리뷰에서 긍정적으로 언급된 부분을 정리합니다.
    
    ex) “김치전이 술안주로 잘 어울린다는 점이 손님들께 호평을 받았습니다.”
    
- 아쉬워요 (단점) : 실제 리뷰에 등장한 불편·아쉬움을 정리합니다.
    
    ex) “매장이 좁아 붐빈다는 의견이 여러 번 나왔습니다.”
    

- 키워드 분석 : 긍정/부정 키워드를 각각 3개씩 추출해줘. 긍정과 부정은 줄을 바꿔서 구분하기 쉽게 해줘. 그 다음에 또 줄바꿔서 전체적인 설명을 두문장 적어줘.
    
    ex) “긍정: 빠른 음식 서빙 속도, 가성비, 로컬맛집 / 부정: 좁음, 기름짐, 대기시간”
    
- 문제점 분석 : Grönroos, SERVPERF, Kano 모델 분류 기준에 따라 문제 성격을 분석해줘. 분석 모델에 사용된 단어같은 건 사용하지 않고 출력해. 분석 속성에 따른 문제점을 리뷰 사례와 연결해 사장님이 이해하기 쉽게 설명해야되는데 전문 용어는 사용하지 마.
    
    ex) “매장 혼잡 → (process/Tangibles/Basic 문제이므로 각 분류된 문제를 체계적으로 이해하기 쉽게 설명) 음식 뿐만 아니라 손님이 기다리는 과정에서의 경험도 중요해요. 특성상 없으면 불만이 커지므로 꼭 해결해야 해요!
    
- 제안 : 문제점 분석을 바탕으로 사장님의 운영 철학을 존중하며, 강제 조언 대신 **친절한 제안**으로 작성합니다.
    
    ex) “좌석 안내나 혼잡 시간대 안내를 추가해주시면 손님들이 조금 더 편하게 느끼실 수 있을 것 같습니다.”
    
    출력은 반드시 후술하는 JSON 형식을 따르세요.
    JSON 이외의 텍스트를 절대 포함하지 마세요.
            You MUST return only JSON.
    
            {
            "data": {
                "storeName": "가게명",
                "goodPoint": "긍정적 리뷰 요약",
                "badPoint": "부정적 리뷰 요약",
                "percentage": {
                "goodPercentage": 숫자,
                "middlePercentage": 숫자,
                "badPercentage": 숫자
                },
                "analysisKeyword": "리뷰에서 자주 등장하는 키워드 분석",
                "analysisProblem": "문제점 분석",
                "analysisSolution": "해결 방안 제안"
            }
            }
    
            분석할 수 없는 부분은 "알 수 없음"으로 처리합니다.
    """

    user = {
        "role": "user",
        "content": f"다음 리뷰 데이터를 분석해줘. 반드시 반드시 무조건 JSON만 반환해.\n\n{review_payload}"
    }
    
    llm_response = ""
    cleaned_response = ""

    try:
        # 이 블록 안에 모든 위험한 코드를 배치
        llm_response = run_llm(system, user)
        if not isinstance(llm_response, str):
            llm_response = str(llm_response)

        cleaned_response = llm_response.strip()

        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[len('```json'):]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-len('```')]
        
        parsed_json = json.loads(cleaned_response)
        
        if "data" in parsed_json and isinstance(parsed_json["data"], dict):
            data_dict = parsed_json["data"]
            # get() 메서드를 사용하여 안전하게 키 접근
            analysis_data = {
                "storeName": data_dict.get("storeName", "알 수 없음"),
                "goodPoint": data_dict.get("goodPoint", "리뷰 분석에 실패했습니다. (응답 형식 오류)"),
                "badPoint": data_dict.get("badPoint", "리뷰 분석에 실패했습니다. (응답 형식 오류)"),
                "percentage": data_dict.get("percentage", {"goodPercentage": 0, "middlePercentage": 0, "badPercentage": 0}),
                "analysisKeyword": data_dict.get("analysisKeyword", "리뷰 분석 실패"),
                "analysisProblem": data_dict.get("analysisProblem", "리뷰 분석 실패"),
                "analysisSolution": data_dict.get("analysisSolution", "리뷰 분석 실패")
            }
            return analysis_data

        raise ValueError("LLM 응답이 올바른 형식이 아닙니다.")
        
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"JSON 파싱 또는 키 에러: {e}")
        # 이제 cleaned_response 변수가 정의되지 않았다는 오류는 발생하지 않습니다.
        print(f"원본 LLM 응답: {llm_response}")
        # ... (이전의 대체 딕셔너리 반환 로직) ...
        return {
            "storeName": review_payload.get('storeName', '알 수 없음'),
            "goodPoint": "리뷰 분석에 실패했습니다. (응답 형식 오류)",
            "badPoint": "리뷰 분석에 실패했습니다. (응답 형식 오류)",
            "percentage": {
                "goodPercentage": 0,
                "middlePercentage": 0,
                "badPercentage": 0
            },
            "analysisKeyword": "리뷰 분석 실패",
            "analysisProblem": "리뷰 분석 실패",
            "analysisSolution": "리뷰 분석 실패"
        }
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        print(f"원본 LLM 응답: {llm_response}")
        return {
            "storeName": review_payload.get('storeName', '알 수 없음'),
            "goodPoint": "예상치 못한 오류 발생",
            "badPoint": "예상치 못한 오류 발생",
            "percentage": {
                "goodPercentage": 0,
                "middlePercentage": 0,
                "badPercentage": 0
            },
            "analysisKeyword": "리뷰 분석 실패",
            "analysisProblem": "리뷰 분석 실패",
            "analysisSolution": "리뷰 분석 실패"
        }