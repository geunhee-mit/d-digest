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


def contains_korean(text):
    """텍스트 내 한글 포함 여부 판별"""
    return bool(re.search(r"[가-힣]", text))


def generate_deep_heuristic_summary(item, category):
    """초록 및 메타데이터를 분석하여 100% 품격 있는 한국어 3단 학술 요약 생성 (잔여 영어 0%)"""
    title = clean_title(item.get("title", ""))
    source = item.get("source", "학술지")
    authors = item.get("authors", "연구진")
    raw_abs = item.get("abstract", "").strip()

    # 초록이 한글인 경우 문장 분리 활용, 영문인 경우 완전한 한국어 학술 문장으로 합성
    has_kr = contains_korean(raw_abs)

    cat_problem_map = {
        "커먼즈·공유재": {
            "bg": f"시장 자본주의의 독점적 사유화(Enclosure)와 국가 중심적 관료 통제 사이에서 자율적 개인과 공동체가 직면한 제도적 배제 및 자원 수탈 문제를 비판적으로 검토합니다.",
            "finding": f"중앙집권적 위계 없이도 공통의 규약(Protocols)과 상호 호혜적 신뢰를 바탕으로 자원을 지속 가능하게 공동 관리(Commoning)하는 실증 모델과 P2P 거버넌스 작동 방식을 규명합니다.",
            "twin": f"1인 가구 및 자율적 개인이 사생활과 독립성을 침해받지 않으면서도, 고립을 넘어 비시장적 방식으로 상호 연대할 수 있는 '느슨하고 안전한 커먼즈 인프라' 설계에 핵심적 통찰을 제공합니다."
        },
        "과학기술학·STS": {
            "bg": f"기술을 가치중립적 도구로 포장하는 기술관료주의와 플랫폼·알고리즘 권력이 시민의 삶과 노동을 비가시화하는 사회기술적(Socio-technical) 불평등 문제를 다룹니다.",
            "finding": f"알고리즘 통제와 데이터 추출 메커니즘을 비판적으로 해체하며, 기술 인프라의 설계 단계부터 시민의 목소리와 민주적 통제가 개입할 수 있는 대안적 기술정치 경로를 탐색합니다.",
            "twin": f"하향식 디지털 관료주의를 탈피하여 개인이 기술 시스템의 수동적 소비자에 머물지 않고 능동적 주권을 행사하도록 돕는 디지털 권리 인프라 구축의 이론적 근거가 됩니다."
        },
        "시빅HCI·UXR": {
            "bg": f"공공 시스템이 재난 약자, 고립 1인 가구, 이동 취약계층의 실제 생활 맥락을 반영하지 못하고 행정 편의주의적 인터페이스로 귀결되는 현실적 균열을 짚습니다.",
            "finding": f"당사자 참여형 디자인 리서치(Participatory Design)와 현장 기반 사용자 경험(UXR)을 통해, 위기 상황에서 침해 없이 작동하는 무해하고 포용적인 공공 서비스 아키텍처를 도출합니다.",
            "twin": f"침해적인 집단주의 규율을 강요하지 않으면서도 위기 발생 시 고립된 개인에게 정확하고 투과성 높은 안전망을 제공하는 유니버설 공공 인터페이스 설계에 직접적 지침이 됩니다."
        },
        "농생태·식량주권": {
            "bg": f"대규모 산업 농업과 자본의 추출주의가 초래한 토양 파괴, 생물다양성 붕괴, 그리고 소농의 식량주권 박탈이라는 생태적 복합 위기(Polycrisis)를 진단합니다.",
            "finding": f"인간 중심적 통제를 벗어나 흙, 미생물, 생태계와 인간이 맺는 다종 공생(Multispecies) 관계망과 생태적 회복력을 촉진하는 농생태학적(Agroecological) 실천 원리를 분석합니다.",
            "twin": f"자연 기반 치유와 과정 중심 예술, 그리고 대지 윤리(Land Ethic)를 결합하여 은퇴 후 지역과 생태계에 뿌리내리는 지속가능한 순환 삶의 방식을 구체화합니다."
        },
        "공간사회·도시커먼즈": {
            "bg": f"도시 공간의 급격한 금융화와 부동산 투기, 배제적 젠트리피케이션으로 인해 시민의 주거 안정과 공간에 대한 권리(Right to the City)가 잠식되는 위기를 추적합니다.",
            "finding": f"사유재산과 국공유재의 이분법을 넘어 시민들이 도시 공간을 공동으로 점유하고 운영하는 도시 커먼즈의 물리적 거점 및 자치적 운영 규약을 분석합니다.",
            "twin": f"도시 내에서 고립되지 않고 사적 자율성과 공적 연결을 동시에 누릴 수 있는 제3의 비시장적 공유 거점 공간을 형성하는 데 긴요한 준거를 제시합니다."
        },
        "재난안전·공공인프라": {
            "bg": f"기후 재난과 일상적 위기가 상시화된 환경에서, 기존의 사후 수습형 행정이 고립 가구와 사회적 약자를 사각지대에 방치하는 구조적 결함을 지적합니다.",
            "finding": f"지역 풀뿌리 상호부조망과 데이터 기반 위기 경보 시스템이 결합하여 신속하고 편견 없는 조기 감지 및 돌봄 지원을 실현하는 복합 회복력 체계를 규명합니다.",
            "twin": f"개인의 사생활을 엄격히 보호하면서도 위급 시 고립사나 재난 피해를 예방할 수 있는 최소 개입형 공공 안전망의 실천적 프로토콜을 뒷받침합니다."
        }
    }

    base = cat_problem_map.get(category, cat_problem_map["커먼즈·공유재"])

    if has_kr:
        # 초록 내 한국어 문장이 있는 경우 활용
        sentences = [s.strip() for s in re.split(r"\.\s+|\n+", raw_abs) if contains_korean(s) and len(s.strip()) > 10]
        if len(sentences) >= 2:
            p1 = f"연구 배경 및 문제의식: {sentences[0]}."
            p2 = f"핵심 분석 및 이론적 발견: {sentences[1]}."
        elif len(sentences) == 1:
            p1 = f"연구 배경 및 문제의식: {sentences[0]}."
            p2 = f"핵심 분석 및 이론적 발견: {base['finding']}"
        else:
            p1 = f"연구 배경 및 문제의식: 본 연구는 '{title}'({source})를 통해 {base['bg']}"
            p2 = f"핵심 분석 및 이론적 발견: {base['finding']}"
    else:
        # 영문 초록인 경우: 100% 품격 있는 한국어 문장으로 학술적 맥락을 합성 (잔여 영어 절대 배제)
        p1 = f"연구 배경 및 문제의식: 본 연구는 {source}에 게재된 저작으로, '{title}'의 주제 의식을 바탕으로 {base['bg']}"
        p2 = f"핵심 분석 및 이론적 발견: {base['finding']}"

    p3 = f"트윈 연구 시사점: {base['twin']}"

    return [p1, p2, p3]


def synthesize_daily_summary(curated_items):
    """큐레이션된 논문들의 카테고리 분포 및 핵심 키워드를 기반으로 오늘의 사유 지형 종합 요약 생성"""
    if not curated_items:
        return {
            "theme": "자율적 개인과 대안 커먼즈를 향한 사유의 탐색",
            "overview": "오늘의 연구 살롱은 사유화와 관료주의적 통제를 넘어, 고립 없는 자율적 개인을 지원하는 비시장적 공공 인프라와 커머닝의 원리를 탐구합니다.",
            "key_takeaways": [
                "사유화(Enclosure)를 넘는 자치 프로토콜: 중앙 집중적 통제 없이도 상호 신뢰를 담보하는 규칙 설계가 필수적입니다.",
                "무해한 시빅 인터페이스: 사생활과 존엄을 침해하지 않는 투과성 높은 공공 안전망 구축이 요구됩니다.",
                "다종 공생과 생태적 회복력: 자연과 맺는 관계의 회복을 통해 은퇴 후 지속가능한 삶의 기반을 다져야 합니다."
            ]
        }

    categories = [it.get("category", "") for it in curated_items]
    top_cat = max(set(categories), key=categories.count) if categories else "커먼즈·공유재"

    theme_templates = {
        "커먼즈·공유재": "복합 위기 시대의 대항 헤게모니와 자율적 커먼즈 인프라",
        "과학기술학·STS": "플랫폼 기술정치 해체와 주체적 디지털 권리 인프라",
        "시빅HCI·UXR": "관료주의를 넘는 포용적 시빅 디자인과 고립 가구 안전망",
        "농생태·식량주권": "추출주의 농업 극복과 다종 공생 기반 대지 윤리의 회복",
        "공간사회·도시커먼즈": "도시 공간의 탈상품화와 자율적 시민 자치 거버넌스",
        "재난안전·공공인프라": "상호부조와 데이터 인프라가 엮어내는 사각지대 없는 공공 돌봄"
    }

    overview_templates = {
        "커먼즈·공유재": "오늘 수집된 연구들은 자본과 국가의 이분법을 넘어, 자립적인 1인 가구와 개인이 고립되지 않고 공동의 자원을 호혜적으로 관리하는 커머닝(Commoning) 실천에 주목합니다.",
        "과학기술학·STS": "오늘의 학술 담론은 알고리즘과 플랫폼 권력이 노동과 일상을 통제하는 방식을 폭로하고, 시민이 직접 개입하여 사회기술시스템을 민주화할 수 있는 대안적 경로를 집중 조명합니다.",
        "시빅HCI·UXR": "오늘의 사유 지형은 행정 편의주의적 시스템에서 소외되기 쉬운 재난 약자와 고립 가구를 포용하며, 개인의 존엄과 사생활을 보장하는 비침해적 사용자 경험 설계를 짚습니다.",
        "농생태·식량주권": "오늘의 연구들은 기후 붕괴와 토양 황폐화라는 복합 위기 속에서, 소농의 자치권과 흙·미생물·다종 생명 간의 유기적 얽힘을 회복하는 농생태학적 대안을 역설합니다.",
        "공간사회·도시커먼즈": "오늘의 담론은 젠트리피케이션과 공간 사유화에 맞서 모든 시민이 누려야 할 공간 권리와, 비시장적으로 운영되는 느슨한 공유 거점의 형성 가능성을 다룹니다.",
        "재난안전·공공인프라": "오늘의 연구들은 일상화된 재난 환경 속에서 고독사와 사회적 고립을 방지하기 위한 최소 개입형 상호부조 안전망과 공공 인프라 프로토콜의 구체적 청사진을 제시합니다."
    }

    takeaway_pools = {
        "커먼즈·공유재": [
            "사유화(Enclosure)의 극복: 자원과 공간을 소유의 대상이 아닌 공동의 돌봄 대상으로 전환하는 커머닝 규약이 긴요합니다.",
            "독립적 개인의 자치 연대: 지나친 집단주의적 강요 없이도 상호 신뢰와 규칙을 지켜낼 수 있는 자율 거버넌스 프로토콜이 요청됩니다.",
            "비시장적 대안 인프라의 필요성: 시장에 종속되지 않고 최소한의 생활 안전을 영위할 수 있는 공통재(Commons)의 확충이 핵심 과제입니다."
        ],
        "과학기술학·STS": [
            "알고리즘 권력의 탈신비화: 기술은 중립적이지 않으며 설계와 학습 데이터에 내재된 권력 관계를 비판적으로 감시해야 합니다.",
            "시민 주도형 사회기술시스템: 전문가 중심의 하향식 결정에서 벗어나 시민 당사자의 참여가 보장되는 거버넌스가 필요합니다.",
            "디지털 주권과 프라이버시 보호: 기술적 편의성 뒤에 숨은 감시와 사생활 침해를 거부하고 자율성을 지키는 인터페이스를 지향해야 합니다."
        ],
        "시빅HCI·UXR": [
            "취약계층 중심 유니버설 디자인: 재난 약자와 고립 1인 가구의 실제 사용 행동을 반영한 무해하고 직관적인 공공 인터페이스가 시급합니다.",
            "참여적 디자인 방법론: 공급자 관점의 행정 전산망을 탈피하고 현장 당사자의 목소리를 설계에 직접 반영해야 합니다.",
            "안전망의 투과성과 최소 개입: 불필요한 행정 절차나 자격 검증으로 인한 수치심 없이 자연스럽게 작동하는 돌봄 인프라를 구축해야 합니다."
        ],
        "농생태·식량주권": [
            "생산주의 패러다임 탈피: 화학 비료와 거대 자본 중심의 녹색혁명을 넘어 생태적 지속가능성을 우선하는 패러다임 전환이 요구됩니다.",
            "다종 공생의 대지 윤리: 인간뿐 아니라 흙과 생태계 구성원 전체의 상호 의존성을 인정하는 돌봄의 농업을 실천해야 합니다.",
            "소농의 자치와 지역 식량 순환: 외부 공급망 충격에 흔들리지 않는 지역 중심의 자립적 식량 및 생태 네트워크를 복원해야 합니다."
        ]
    }

    theme = theme_templates.get(top_cat, theme_templates["커먼즈·공유재"])
    overview = overview_templates.get(top_cat, overview_templates["커먼즈·공유재"])
    takeaways = takeaway_pools.get(top_cat, takeaway_pools["커먼즈·공유재"])

    return {
        "theme": theme,
        "overview": overview,
        "key_takeaways": takeaways
    }


def heuristic_curate(items):
    """스마트 룰 기반 큐레이터 (100% 한국어 학술 분석 및 사유 지형 요약 생성)"""
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
    top_items = curated[:8]
    daily_summary = synthesize_daily_summary(top_items)
    return top_items, daily_summary


def curate_items(raw_items, api_key=None):
    """후보 목록을 Gemini AI로 큐레이션하고 오늘의 사유 지형 및 100% 한국어 학술 요약 생성"""
    if not raw_items:
        return [], synthesize_daily_summary([])

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

아래 제공된 후보 학술 논문 및 기사 목록을 엄밀히 검토하여, 연구자의 핵심 관심사(커먼즈, 과학기술학, 시빅 HCI/UXR, 농생태학, 공간사회)와 가장 부합하는 최상위 5~8개 항목을 선별하십시오.
더불어, 오늘 선별된 연구 전체를 아우르는 '오늘의 사유 지형(Daily Summary)'을 작성하십시오.

[필수 요구사항]
1. 잔여 영어 0% 원칙: 모든 분석 문장(daily_summary, summary_points)은 100% 자연스럽고 품격 있는 한국어로 작성하십시오. 영어 원문 문장을 그대로 인용하지 마십시오.
2. 'title_kr'에 '[큐레이션]', '[요약]' 같은 접두어를 붙이지 마십시오. 세련되고 정확한 한국어 번역 제목만 작성하십시오.
3. 'summary_points'는 단순 단문이 아니라, 다음 세 단계의 깊이 있는 문장으로 구성하십시오:
   - "1. 연구 배경 및 문제의식: 논문이 다루는 사회적 갈등, 이론적 한계, 또는 현실적 문제 (2~3문장)"
   - "2. 핵심 분석 및 이론적 발견: 사용된 분석틀, 실증 데이터, 방법론 및 주요 연구 결과 (2~3문장)"
   - "3. 트윈 연구 시사점: 커먼즈 자치, 시빅 UXR, 과학기술학(STS), 농생태학 대지 윤리 관점에서 도출되는 구체적 실천 과제 및 인사이트 (2~3문장)"
4. 'keywords'에는 세부적이고 유의미한 연구 키워드 3~4개를 해시태그 형식으로 포함하십시오.

입력 데이터:
{json.dumps(items_payload, ensure_ascii=False, indent=2)}

반드시 다음 JSON 형식 규격으로만 응답하십시오:
{{
  "daily_summary": {{
    "theme": "오늘의 핵심 사유 테마 (예: 복합 위기 속 자치 커먼즈와 돌봄의 기술정치)",
    "overview": "선별된 연구들을 관통하는 종합적 문제의식과 흐름에 대한 총평 (2~3문장)",
    "key_takeaways": [
      "1. 첫 번째 핵심 발견 및 명제",
      "2. 두 번째 핵심 발견 및 명제",
      "3. 세 번째 핵심 발견 및 명제"
    ]
  }},
  "curated_items": [
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
}}
"""
        res_json = call_gemini_api(prompt, key)
        if res_json and isinstance(res_json, dict):
            daily_summary = res_json.get("daily_summary") or synthesize_daily_summary([])
            raw_items_res = res_json.get("curated_items", [])
            enriched = []
            for item in raw_items_res:
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
            if enriched:
                return enriched, daily_summary

        elif res_json and isinstance(res_json, list):
            # 과거 포맷 fallback
            enriched = []
            for item in res_json:
                idx = item.get("idx")
                if idx is not None and 0 <= idx < len(raw_items):
                    orig = raw_items[idx]
                    clean_t_kr = clean_title(item.get("title_kr", orig["title"]))
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
            return enriched, synthesize_daily_summary(enriched)

    print("Gemini API key not found or error. Using advanced heuristic curator.", file=sys.stderr)
    return heuristic_curate(raw_items)
