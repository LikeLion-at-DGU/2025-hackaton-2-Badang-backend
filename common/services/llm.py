import json
from typing import List, Dict, Union
from .openai_client import client, MODEL

# "한 번 질문" 기본형 (system+user 프롬프트)
def run_llm(system_prompt: str, user_prompt: Union[str, Dict]) -> str:
    # Responses API는 input으로 문자열 또는 배열을 받는다.
    # 배열로 넘기면 '대화 히스토리'처럼 쓸 수 있음.
    # (아래는 system+user 두 턴)
    input_msgs = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt if isinstance(user_prompt, str)
                             else json.dumps(user_prompt, ensure_ascii=False)}
    ]
    resp = client.responses.create(
        model=MODEL,
        input=input_msgs,
        temperature=0
    )
    return resp.output_text  # SDK가 제공하는 편의 속성
