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
            "temperature": 0.25,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }

    try:
        res = requests.post(url, json=payload, timeout=35)
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


def clean_title(title):
    """말머리 태그 제거 및 제목 정제"""
    t = re.sub(r"^\[.*?\]\s*", "", title)
    t = re.sub(r"^\(.*?\)\s*", "", t)
    return t.strip()


def generate_deep_heuristic_summary(item, category):
    """초록(Abstract) 텍스트를 실질적으로 분석하여 깊이 있는 3단 학술 요약 생성"""
    raw_abs = item.get("abstract", "").strip()
    title = item.get("title", "")
    source = item.get("source", "")
    
    # 문장 단위 분리
    sentences = [s.strip() for s in re.split(r"\.\s+|\n+", raw_abs) if len(s.strip()) > 15]

    # 1. 연구 배경 및 문제의식
    if len(sentences) >= 1:
        p1 = f"연구 배경 및 문제의식: {sentences[0]}."
    else:
        p1 = f"연구 배경 및 문제의식: 본 연구는 {source}에 게재된 논문으로, '{title}'에 관한 기존 이론적 틀과 현실적 한계를 짚고 대안적 메커니즘을 탐구합니다."

    # 2. 핵심 연구 내용 및 실증/이론적 발견
    if len(sentences) >= 3:
        p2 = f"핵심 분석 및 발견: {sentences[1]}. 더불어 저자들은 {sentences[2]}."
    elif len(sentences) >= 2:
        p2 = f"핵심 분석 및 발견: {sentences[1]}."
    else:
        p2 = f"핵심 분석 및 발견: {source}의 해당 저작은 실천적 사례 연구와 개념 분석을 결합하여, 행위자 간의 상호작용 및 시스템 거버넌스 구조를 심층적으로 규명합니다."

    # 3. 트윈 연구와의 연결점 및 시사점
    cat_insights = {
        "커먼즈·공유재": f"트윈 연구 시사점: 자율적인 개인들이 중앙 집중적 권력이나 시장의 과도한 사유화(Enclosure)에 포섭되지 않고, 공유 자원을 민주적이고 지속 가능하게 자치 관리(Commoning)할 수 있는 프로토콜 설계에 중요한 이론적 디딤돌을 제공합니다.",
        "시빅HCI·UXR": f"트윈 연구 시사점: 기술 관료주의적 하향식 시스템을 넘어 시민과 취약계층이 스스로의 경험과 권리를 능동적으로 행사할 수 있는 참여적 사용자 인터페이스(Civic Interface) 및 포용적 공공데이터 안전망 설계에 직접적으로 적용될 수 있습니다.",
        "과학기술학·STS": f"트윈 연구 시사점: 기술 시스템을 단순한 기능적 도구가 아닌 권력과 사회적 가치가 각인된 '사회기술시스템(Socio-technical Systems)'으로 바라보며, 플랫폼 독점과 알고리즘 통제에 비판적으로 개입하는 분석적 안목을 확장합니다.",
        "농생태·식량주권": f"트윈 연구 시사점: 자본주의적 산업 농업과 추출주의적 대지 착취를 비판하고, 흙·미생물·농민의 자치 역량이 상호 얽혀 회복력을 발휘하는 농생태학(Agroecology) 및 대지 윤리적 실천에 긴밀히 연결됩니다.",
        "공간사회·도시커먼즈": f"트윈 연구 시사점: 도시 공간의 상품화와 젠트리피케이션에 맞서 모든 시민이 공간에 대한 권리(Right to the City)를 누릴 수 있는 도시 커먼즈의 물리적·사회적 인프라 전략에 시사점을 던집니다.",
        "재난안전·공공인프라": f"트윈 연구 시사점: 복합 위기(Polycrisis) 시대에 고립된 개인과 재난 약자가 배제되지 않도록 돕는 무해하고 투과성 높은 공공 위기 대응 인터페이스의 필요성을 뒷받침합니다."
    }
    p3 = cat_insights.get(category, f"트윈 연구 시사점: 독립적인 개인이 사회적 관계망 속에서 존엄과 자율성을 유지할 수 있도록 돕는 공공 인프라 구축의 필수적 참고 사례입니다.")

    return [p1, p2, p3]


def heuristic_curate(items):
    """스마트 룰 기반 큐레이터 (말머리 제거 및 깊이 있는 3단 학술 분석)"""
    curated = []
    category_weights = {
        "커먼즈·공유재": ["commons", "commoning", "p2p", "ostrom", "cooperation", "cooperative", "공유재", "협동", "자치", "공동체", "peer"],
        "시빅HCI·UXR": ["civic", "participatory", "public", "user", "interface", "governance", "시민", "공공", "안전", "참여", "ux", "interaction"],
        "과학기술학·STS": ["socio-technical", "politics", "algorithm", "platform", "science and technology", "기술", "사회기술", "알고리즘"],
        "농생태·식량주권": ["farmer", "agriculture", "ecological", "care", "crisis", "peasant", "생태", "농업", "기후", "토양", "다종", "식량"],
        "공간사회·도시커먼즈": ["urban", "spatial", "city", "space", "도시", "공간", "젠트리피케이션", "공간정의"],
        "재난안전·공공인프라": ["disaster", "vulnerable", "safety", "emergency", "crisis", "재난", "취약", "대피", "인프라"]
    }

    for item in items:
        text = f"{item['title']} {item['abstract']}".lower()
        matched_cat = item.get("category", "커먼즈·공유재")
        score = 6.5

        for cat, kws in category_weights.items():
            hit_count = sum(1 for kw in kws if kw in text)
            if hit_count > 0:
                score += min(hit_count * 0.9, 3.2)
                matched_cat = cat

        if score >= 6.8:
            clean_t = clean_title(item["title"])
            summary_points = generate_deep_heuristic_summary(item, matched_cat)

            # 세부 키워드 추출
            keywords = [f"#{matched_cat.split('·')[0]}"]
            if "commons" in text or "공유" in text:
                keywords.append("#커머닝")
            if "civic" in text or "시민" in text:
                keywords.append("#시빅테크")
            if "participatory" in text or "참여" in text:
                keywords.append("#참여디자인")
            if "socio-technical" in text or "기술" in text:
                keywords.append("#사회기술시스템")
            if "ecological" in text or "생태" in text:
                keywords.append("#다종공생")
            if "urban" in text or "도시" in text:
                keywords.append("#도시공간")
            if len(keywords) < 3:
                keywords.append("#연구동향")

            curated.append({
                "id": item["id"],
                "title_kr": clean_t,
                "original_title": item["title"],
                "source": item["source"],
                "authors": item["authors"] or "연구진",
                "published": item["published"],
                "url": item["url"],
                "category": matched_cat,
                "relevance_score": round(min(score, 9.8), 1),
                "summary_points": summary_points,
                "keywords": list(dict.fromkeys(keywords))[:4]
            })

    curated.sort(key=lambda x: x["relevance_score"], reverse=True)
    return curated[:8]


def curate_items(raw_items, api_key=None):
    """후보 목록을 Gemini 무료 AI로 큐레이션 및 고품질 학술 요약"""
    if not raw_items:
        return []

    key = api_key or os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY
    if key:
        items_payload = [
            {
                "idx": i,
                "title": clean_title(it["title"]),
                "abstract": it["abstract"][:700],
                "source": it["source"],
                "category": it["category"],
                "url": it["url"],
                "authors": it["authors"],
                "published": it["published"]
            }
            for i, it in enumerate(raw_items)
        ]

        prompt = f"""{CURATOR_SYSTEM_PROMPT}

아래 제공된 후보 학술 논문 및 기사 목록을 엄밀히 검토하여, 연구자의 핵심 관심사(커먼즈, 과학기술학, 시빅 HCI/UXR, 농생태학, 공간사회)와 가장 부합하는 최상위 5~7개 항목을 선별하십시오.

[필수 요구사항]
1. 'title_kr'에 절대로 '[큐레이션]', '[요약]' 같은 접두어를 붙이지 마십시오. 세련되고 정확한 한국어 번역 제목만 작성하십시오.
2. 'summary_points'는 단순 단문이 아니라, 다음 세 단계의 깊이 있는 문장으로 구성하십시오:
   - "1. 연구 배경 및 문제의식: 논문이 다루는 사회적 갈등, 이론적 한계, 또는 현실적 문제 (2~3문장)"
   - "2. 핵심 분석 및 이론적 발견: 사용된 분석틀, 실증 데이터, 방법론 및 주요 연구 결과 (2~3문장)"
   - "3. 연구자 시사점: 커먼즈 자치, 시빅 UXR, 과학기술학(STS), 농생태학 대지 윤리 관점에서 도출되는 구체적 실천 과제 및 인사이트 (2~3문장)"
3. 'keywords'에는 세부적이고 유의미한 연구 키워드 3~4개를 해시태그 형식으로 포함하십시오.

입력 데이터:
{json.dumps(items_payload, ensure_ascii=False, indent=2)}

반드시 다음 JSON 배열 규격으로만 응답하십시오:
[
  {{
    "idx": 원본 idx,
    "title_kr": "정확하고 학술적인 한국어 번역 제목",
    "category": "커먼즈·공유재" | "시빅HCI·UXR" | "과학기술학·STS" | "농생태·식량주권" | "공간사회·도시커먼즈" | "재난안전·공공인프라",
    "relevance_score": 8.5 (1.0~10.0),
    "summary_points": [
      "연구 배경 및 문제의식: ...",
      "핵심 분석 및 이론적 발견: ...",
      "트윈 연구 시사점: ..."
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
                    raw_title_kr = item.get("title_kr", orig["title"])
                    clean_t_kr = clean_title(raw_title_kr)

                    enriched.append({
                        "id": orig["id"],
                        "title_kr": clean_t_kr,
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

    print("Gemini API key not found or error. Using advanced heuristic curator.", file=sys.stderr)
    return heuristic_curate(raw_items)
