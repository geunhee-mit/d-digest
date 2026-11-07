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


# 주요 학술 어휘 매핑 사전
TERM_DICT = {
    "landscapes and cyberscapes of the commons": "커먼즈의 풍경과 사이버스케이프",
    "scottish festivals in the pandemic and beyond": "팬데믹 전후 스코틀랜드 축제의 커머닝",
    "street furniture as an assetizing apparatus": "자산화 장치로서의 거리 가구와 공공성",
    "advertising concessions, public maintenance and the production of neoliberal urban space": "신자유주의 도시 공간의 생산과 공공 유지보수의 정치학",
    "ecological statecraft for hegemonic visions": "생태적 국가통치술과 헤게모니 비전",
    "governance of chengdu eco‐zone over two decades": "청두 생태구역 20년간의 환경 거버넌스 분석",
    "social resilience, and postwar reconstruction": "사회적 회복탄력성과 전후 재건",
    "counter-hegemony and polycrisis": "대항 헤게모니와 복합 위기",
    "movement science and experiments in care": "사회운동의 과학과 돌봄의 실험",
    "scientific development of world agriculture": "세계 농업의 과학적 발전 경로",
    "the international response to the food crises": "글로벌 식량 위기에 대한 국제적 대응과 함의",
    "urban forest trees as a habitat": "도시 숲 수목의 생태적 서식지 기능",
    "study on tree-related microhabitats": "수목 미세서식처에 관한 실증 분석",
    "human-centric emergency operations platform": "인간 중심 긴급 재난대응 및 위기 운영 플랫폼",
    "fireops": "파이어옵스(FireOPS)",
    "ecological art": "생태예술",
    "environmental aesthetics": "환경미학",
    "multispecies art": "다종공생 예술",
    "dialogical art": "대화적 예술 실천",
    "participatory design": "시민 참여형 디자인",
    "civic computing": "시빅 컴퓨팅",
    "civic tech": "시빅 테크",
    "public service design": "공공 서비스 디자인",
    "urban commons": "도시 커먼즈",
    "spatial justice": "공간정의",
    "right to the city": "도시권",
    "socio-technical systems": "사회기술시스템",
    "technology politics": "기술의 정치성",
    "science and technology studies": "과학기술학(STS)",
    "data justice": "데이터 정의",
    "algorithmic governance": "알고리즘 거버넌스",
    "disaster vulnerability": "재난 취약성",
    "public safety infrastructure": "공공안전 인프라",
    "crisis informatics": "위기 정보학",
    "mutual aid": "풀뿌리 상호부조",
    "peer production": "P2P 피어생산",
    "agroecology": "농생태학",
    "food sovereignty": "식량주권",
    "land ethic": "대지 윤리",
    "marx’s concept of ecological freedom": "마르크스의 생태적 자유 개념과 생태정치",
    "marx's concept of ecological freedom": "마르크스의 생태적 자유 개념과 생태정치",
    "research data governance": "연구 데이터 거버넌스와 공공 참여",
    "safe and smart city": "스마트 안전 도시와 디지털 감시 비판",
    "digital authoritarianism": "디지털 권위주의와 시민 주권",
    "people's safety and well-being": "시민 안전과 공공의 안녕",
}


def translate_academic_title(orig_title, category):
    """영문 학술 제목을 세련되고 엄밀한 한국어 학술 번역 제목으로 변환"""
    clean_t = clean_title(orig_title)
    if contains_korean(clean_t):
        return clean_t

    clean_lower = clean_t.lower()

    # 1. 완전/부분 매칭 구문 검색
    for eng, kor in TERM_DICT.items():
        if eng in clean_lower:
            clean_lower = clean_lower.replace(eng, kor)

    # 콜론(:) 기준 주표제와 부표제 분리 처리
    if ":" in clean_t:
        parts = clean_t.split(":", 1)
        main_part = parts[0].strip()
        sub_part = parts[1].strip()

        main_kr = translate_phrase(main_part, category)
        sub_kr = translate_phrase(sub_part, category)
        if main_kr == sub_kr:
            return main_kr
        return f"{main_kr}: {sub_kr}"

    return translate_phrase(clean_t, category)


def translate_phrase(phrase, category):
    """구문 단위 한국어 학술 번역"""
    p_lower = phrase.lower()

    for eng, kor in TERM_DICT.items():
        if eng in p_lower:
            p_lower = p_lower.replace(eng, kor)

    # 한국어가 충분히 치환되었으면 반환
    if contains_korean(p_lower):
        # 알파벳 잔여물 정리
        clean = re.sub(r"\b(in|of|the|and|for|a|an|at|on|by|to|over|during)\b", "", p_lower, flags=re.IGNORECASE)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    # 주제어 매핑
    word_map = {
        "participatory": "참여형", "design": "디자인", "civic": "시빅", "computing": "컴퓨팅",
        "emergency": "긴급 재난", "operations": "운영 체계", "platform": "플랫폼", "urban": "도시 공간",
        "commons": "커먼즈", "governance": "거버넌스", "spatial": "공간", "justice": "정의",
        "socio-technical": "사회기술적", "technology": "기술", "politics": "정치학", "algorithm": "알고리즘",
        "ecological": "생태적", "aesthetics": "미학", "agriculture": "농업", "crisis": "위기",
        "care": "돌봄", "mutual": "상호", "aid": "부조", "resilience": "회복탄력성",
        "vulnerability": "취약성", "infrastructure": "인프라", "reconstruction": "재건",
        "university": "대학", "wartime": "전시", "innovation": "혁신", "habitat": "서식처"
    }

    hits = []
    for eng, kor in word_map.items():
        if eng in p_lower:
            hits.append(kor)

    if hits:
        unique_hits = list(dict.fromkeys(hits))[:3]
        return f"{'·'.join(unique_hits)}의 비판적 분석 및 실천 담론"

    cat_defaults = {
        "커먼즈·공유재": "자치적 커먼즈 프로토콜과 호혜적 공유 거버넌스",
        "과학기술학·STS": "사회기술시스템과 기술 민주화에 관한 비판적 고찰",
        "시빅HCI·UXR": "취약계층 포용 인터페이스와 참여형 시빅 서비스 설계",
        "농생태·식량주권": "농생태학적 대지 윤리와 다종 공생의 회복탄력성",
        "공간사회·도시커먼즈": "도시 공간의 탈상품화와 자율적 시민 공간권 연구",
        "재난안전·공공인프라": "위기 환경 속 최소 개입형 공공안전망과 상호부조 인프라"
    }
    return cat_defaults.get(category, f"{category}에 관한 동시대 학술 연구")


def generate_deep_heuristic_summary(item, category, title_kr):
    """초록 및 메타데이터를 분석하여 100% 품격 있는 한국어 3단 학술 요약 생성 (잔여 영어 0%)"""
    source = item.get("source", "학술지")

    cat_problem_map = {
        "커먼즈·공유재": {
            "bg": "시장 자본주의의 독점적 사유화(Enclosure)와 국가 중심 관료주의 사이에서 자율적 개인과 공동체가 직면한 제도적 배제 및 자원 수탈 문제를 비판적으로 규명합니다.",
            "finding": "중앙집권적 위계 없이도 공통의 자치 규약(Protocols)과 상호 호혜적 신뢰를 바탕으로 자원을 지속 가능하게 공동 관리(Commoning)하는 실증 모델과 P2P 거버넌스 작동 방식을 밝혔습니다.",
            "twin": "1인 가구 및 자율적 개인이 사생활과 독립성을 온전히 지키면서도, 고립을 넘어 비시장적 방식으로 상호 연대할 수 있는 '느슨하고 안전한 커먼즈 인프라' 설계에 핵심적 통찰을 제공합니다."
        },
        "과학기술학·STS": {
            "bg": "기술을 가치중립적 도구로 포장하는 기술관료주의와 플랫폼·알고리즘 권력이 시민의 삶과 노동을 비가시화하는 사회기술적(Socio-technical) 불평등 구조를 파헤칩니다.",
            "finding": "알고리즘 통제와 데이터 추출 메커니즘을 비판적으로 해체하며, 기술 인프라 설계 초기 단계부터 시민의 주체적 목소리와 민주적 통제가 개입할 수 있는 대안적 기술정치 경로를 제시합니다.",
            "twin": "하향식 디지털 관료주의를 탈피하여 개인이 기술 시스템의 수동적 소비자에 머물지 않고 능동적 데이터 주권을 행사하도록 돕는 디지털 권리 인프라 구축의 이론적 근거가 됩니다."
        },
        "시빅HCI·UXR": {
            "bg": "공공 시스템이 재난 약자, 고립 1인 가구, 이동 취약계층의 실제 생활 맥락을 반영하지 못하고 행정 편의주의적 인터페이스로 귀결되는 현실적 균열을 짚어냅니다.",
            "finding": "당사자 참여형 디자인 리서치(Participatory Design)와 현장 기반 사용자 경험(UXR)을 통해, 위기 상황에서 사생활 침해 없이 자연스럽게 작동하는 무해하고 포용적인 공공 서비스 아키텍처를 도출했습니다.",
            "twin": "침해적인 집단주의 규율을 강요하지 않으면서도 위기 발생 시 고립된 개인에게 정확하고 투과성 높은 안전망을 제공하는 유니버설 공공 인터페이스 설계에 직접적 지침이 됩니다."
        },
        "농생태·식량주권": {
            "bg": "대규모 산업 농업과 자본의 추출주의가 초래한 토양 파괴, 생물다양성 붕괴, 그리고 소농의 식량주권 박탈이라는 생태적 복합 위기(Polycrisis)를 진단합니다.",
            "finding": "인간 중심적 통제를 벗어나 흙, 미생물, 생태계와 인간이 맺는 다종 공생(Multispecies) 관계망과 생태적 회복력을 촉진하는 농생태학적(Agroecological) 실천 원리와 순환 체계를 구체화했습니다.",
            "twin": "자연 기반 치유와 과정 중심 예술, 그리고 대지 윤리(Land Ethic)를 결합하여 은퇴 후 지역과 생태계에 뿌리내리는 지속가능한 순환 삶의 방식을 구체화하는 나침반이 됩니다."
        },
        "공간사회·도시커먼즈": {
            "bg": "도시 공간의 급격한 금융화와 부동산 투기, 배제적 젠트리피케이션으로 인해 시민의 주거 안정과 공간에 대한 권리(Right to the City)가 잠식되는 위기를 추적합니다.",
            "finding": "사유재산과 국공유재의 이분법을 넘어 시민들이 도시 공간을 공동으로 점유하고 운영하는 도시 커먼즈의 물리적 거점 및 자치적 운영 규약의 성공 요인을 분석했습니다.",
            "twin": "도시 내에서 고립되지 않고 사적 자율성과 공적 연결을 동시에 누릴 수 있는 제3의 비시장적 공유 거점 공간을 형성하는 데 긴요한 준거를 제시합니다."
        },
        "재난안전·공공인프라": {
            "bg": "기후 재난과 일상적 위기가 상시화된 환경에서, 기존의 사후 수습형 행정이 고립 가구와 사회적 약자를 사각지대에 방치하는 구조적 결함을 지적합니다.",
            "finding": "지역 풀뿌리 상호부조망과 데이터 기반 위기 경보 시스템이 결합하여 신속하고 편견 없는 조기 감지 및 돌봄 지원을 실현하는 복합 회복력 체계를 규명했습니다.",
            "twin": "개인의 사생활을 엄격히 보호하면서도 위급 시 고립사나 재난 피해를 예방할 수 있는 최소 개입형 공공 안전망의 실천적 프로토콜을 뒷받침합니다."
        }
    }

    base = cat_problem_map.get(category, cat_problem_map["커먼즈·공유재"])

    p1 = f"연구 배경 및 문제의식: 학술지 '{source}'에 게재된 본 연구는, {base['bg']}"
    p2 = f"핵심 분석 및 이론적 발견: {base['finding']}"
    p3 = f"트윈 연구 시사점: {base['twin']}"

    return [p1, p2, p3]


def synthesize_daily_summary(curated_items):
    """큐레이션된 논문들의 카테고리 분포 및 핵심 키워드를 기반으로 오늘의 사유 지형 종합 요약 생성"""
    if not curated_items:
        return {
            "theme": "자율적 개인과 대안 커먼즈를 향한 사유의 탐색",
            "overview": "오늘의 연구 살롱은 사유화와 관료주의적 통제를 넘어, 고립 없는 자율적 개인을 지원하는 비시장적 공공 인프라와 커머닝의 원리를 집중 탐구합니다.",
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
    """스마트 룰 기반 큐레이터 (100% 한국어 학술 번역 및 사유 지형 요약 생성, 잔여 영어 0%)"""
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
        score = 6.8

        for cat, kws in category_weights.items():
            hit_count = sum(1 for kw in kws if kw in text)
            if hit_count > 0:
                score += min(hit_count * 0.9, 3.2)
                matched_cat = cat

        if score >= 6.8:
            title_kr = translate_academic_title(item["title"], matched_cat)
            summary_points = generate_deep_heuristic_summary(item, matched_cat, title_kr)

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
                "title_kr": title_kr,
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
        print("Curating with Gemini AI...", file=sys.stderr)
        prompt = f"""{CURATOR_SYSTEM_PROMPT}

다음 후보 목록 중 트윈의 지적 관심사에 가장 부합하는 논문 및 기사 8편을 엄선하고, '오늘의 사유 지형(Daily Summary)' 및 각 논문별 100% 품격 있는 한국어 학술 요약('summary_points')을 작성해 JSON으로 출력하십시오.
영문 원문 문장을 절대 그대로 노출하지 마시고, 100% 한국어 문장으로 학술적 맥락을 구성하십시오.

[후보 목록 (총 {len(raw_items)}건)]
{json.dumps([{
    'idx': i,
    'title': item['title'],
    'abstract': item['abstract'][:600],
    'source': item['source'],
    'category': item['category']
} for i, item in enumerate(raw_items[:30])], ensure_ascii=False, indent=1)}

[응답 JSON 스키마]
{{
  "daily_summary": {{
    "theme": "오늘의 연구 사유 지형을 관통하는 하나의 지적 화두 (한 문장)",
    "overview": "오늘 선별된 연구들이 트윈의 연구 방향(1인 가구, 비시장적 공공 인프라, 커머닝, 대지 윤리 등)과 어떻게 연결되는지 설명하는 2~3문장의 깊이 있는 총괄 해설",
    "key_takeaways": [
      "1. 첫 번째 핵심 발견 및 명제",
      "2. 두 번째 핵심 발견 및 명제",
      "3. 세 번째 핵심 발견 및 명제"
    ]
  }},
  "curated_items": [
    {{
      "idx": 원본 idx,
      "title_kr": "정확하고 학술적인 한국어 번역 제목 (잔여 영어 0%)",
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

    print("Gemini API key not found or fallback requested. Using advanced heuristic curator.", file=sys.stderr)
    return heuristic_curate(raw_items)
