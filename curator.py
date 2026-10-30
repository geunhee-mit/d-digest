import json
import os
import re
import sys
import requests
from config import GEMINI_API_KEY, GEMINI_MODEL, CURATOR_SYSTEM_PROMPT


def call_gemini_api(prompt, api_key=None):
    """Google Gemini 2.0 Flash / 1.5 Flash 무료 REST API 호출"""
    key = api_key or os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY
    if not key:
        return None

    # Google AI Studio v1beta API endpoint (Free tier)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }

    try:
        res = requests.post(url, json=payload, timeout=30)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {}).get("parts", [])[0].get("text", "")
                return json.loads(content)
        else:
            print(f"Gemini API returned status {res.status_code}: {res.text}", file=sys.stderr)
    except Exception as e:
        print(f"Gemini API invocation error: {e}", file=sys.stderr)
    return None


def heuristic_curate(items):
    """API 키가 없을 때 로컬에서 동작하는 스마트 룰 기반 폴백 큐레이터"""
    curated = []
    # 연구 키워드 가중치
    keywords_map = {
        "커먼즈": ["commons", "commoning", "p2p", "ostrom", "cooperation", "cooperative", "공유재", "협동", "자치", "공동체"],
        "시빅HCI·UXR": ["civic", "participatory", "public", "user", "interface", "governance", "시민", "공공", "안전", "참여"],
        "농생태·생태전환": ["farmer", "agriculture", "ecological", "care", "crisis", "peasant", "생태", "농업", "기후", "토양", "다종"],
        "재난안전·공공인프라": ["disaster", "vulnerable", "safety", "emergency", "재난", "취약", "대피", "인프라"]
    }

    for item in items:
        text = f"{item['title']} {item['abstract']}".lower()
        matched_cat = item["category"]
        score = 6.0

        for cat, kws in keywords_map.items():
            hit_count = sum(1 for kw in kws if kw in text)
            if hit_count > 0:
                score += min(hit_count * 1.0, 3.5)
                matched_cat = cat

        if score >= 6.5:
            # 3줄 가상 요약 생성
            curated.append({
                "id": item["id"],
                "title_kr": f"[큐레이션] {item['title']}",
                "original_title": item["title"],
                "source": item["source"],
                "authors": item["authors"] or "연구진",
                "published": item["published"],
                "url": item["url"],
                "category": matched_cat,
                "relevance_score": round(min(score, 9.8), 1),
                "summary_points": [
                    f"본 연구/기사는 {item['source']}에 수록된 글로, '{item['title']}'에 관한 주요 논점을 다룹니다.",
                    f"원문 요지: {item['abstract'][:180]}..." if item['abstract'] else "원문 링크를 통해 상세 연구 내용을 확인할 수 있습니다.",
                    f"트윈 연구 시사점: '{matched_cat}' 영역의 관점에서 자율적 개인과 공공 인프라 간의 상호작용 및 자치 모델에 중요한 참고가 됩니다."
                ],
                "keywords": [f"#{matched_cat}", "#연구노트", "#학술다이제스트"]
            })

    # 관련도 순으로 정렬 후 상위 6~8개 선택
    curated.sort(key=lambda x: x["relevance_score"], reverse=True)
    return curated[:8]


def curate_items(raw_items, api_key=None):
    """후보 목록을 Gemini 무료 AI로 큐레이션 및 한국어 요약"""
    if not raw_items:
        return []

    # API 키가 설정되어 있으면 Gemini 2.0 Flash로 고품질 큐레이션 진행
    key = api_key or os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY
    if key:
        items_payload = [
            {
                "idx": i,
                "title": it["title"],
                "abstract": it["abstract"][:500],
                "source": it["source"],
                "category": it["category"],
                "url": it["url"],
                "authors": it["authors"],
                "published": it["published"]
            }
            for i, it in enumerate(raw_items)
        ]

        prompt = f"""{CURATOR_SYSTEM_PROMPT}

아래 제공된 후보 학술 논문 및 기사 목록을 엄밀히 검토하십시오.
연구자의 관심사(커먼즈, 시빅HCI/UXR, 농생태학, 포용적 재난안전망, 자율적 개인의 공생)와 가장 부합하는 최상위 5~7개 항목을 선별하십시오.

입력 데이터:
{json.dumps(items_payload, ensure_ascii=False, indent=2)}

반드시 다음 JSON 배열 규격으로만 응답하십시오:
[
  {{
    "idx": 원본 idx,
    "title_kr": "직관적이고 학술적인 한국어 번역 제목",
    "category": "커먼즈" | "시빅HCI·UXR" | "농생태·생태전환" | "재난안전·공공인프라",
    "relevance_score": 8.5 (1.0~10.0),
    "summary_points": [
      "1. 핵심 주장 및 발견: 연구의 핵심 내용 1~2문장",
      "2. 방법론 및 접근: 사용된 데이터, 프레임워크 또는 실천 사례",
      "3. 연구자 시사점: 트윈의 연구(공공UXR, 커머닝, 대지윤리)에 주는 통찰"
    ],
    "keywords": ["#키워드1", "#키워드2", "#키워드3"]
  }}
]
"""
        res_json = call_gemini_api(prompt, key)
        if res_json and isinstance(res_json, list):
            enriched = []
            for item in res_json:
                idx = item.get("idx")
                if idx is not None and 0 <= idx < len(raw_items):
                    orig = raw_items[idx]
                    enriched.append({
                        "id": orig["id"],
                        "title_kr": item.get("title_kr", orig["title"]),
                        "original_title": orig["title"],
                        "source": orig["source"],
                        "authors": orig["authors"],
                        "published": orig["published"],
                        "url": orig["url"],
                        "category": item.get("category", orig["category"]),
                        "relevance_score": item.get("relevance_score", 8.0),
                        "summary_points": item.get("summary_points", []),
                        "keywords": item.get("keywords", [])
                    })
            enriched.sort(key=lambda x: x["relevance_score"], reverse=True)
            return enriched

    # 키가 없거나 호출 실패 시 폴백 큐레이션 실행
    print("Gemini API key not found or error. Using fallback heuristic curator.", file=sys.stderr)
    return heuristic_curate(raw_items)
