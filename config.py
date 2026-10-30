import os

# ==============================================================================
# 트윈 맞춤형 연구 분야 큐레이션 설정 (Research Digest Config)
# ==============================================================================

# Gemini 무료 API 키 (환경변수 GEMINI_API_KEY 또는 기본값)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Gemini 모델명 (무료 티어 지원 최신 모델)
GEMINI_MODEL = "gemini-2.0-flash"

# 수집 대상 학술 저널 (OpenAlex ISSN 기준 - 전 세계 최신 논문 실시간 추적)
TARGET_JOURNALS = [
    {
        "name": "International Journal of the Commons (IJC)",
        "category": "커먼즈",
        "issn": "1875-0281",
        "type": "openalex_journal"
    },
    {
        "name": "Agriculture and Human Values",
        "category": "농생태·식량주권",
        "issn": "0889-048X",
        "type": "openalex_journal"
    },
    {
        "name": "The Journal of Peasant Studies",
        "category": "생태정치·대지인클로저",
        "issn": "0306-6150",
        "type": "openalex_journal"
    }
]

# 학술 검색 쿼리 (OpenAlex & arXiv)
SCHOLARLY_QUERIES = [
    {
        "name": "Civic HCI & Participatory Design",
        "category": "시빅HCI·UXR",
        "type": "openalex_search",
        "query": "civic computing OR participatory design OR civic tech"
    },
    {
        "name": "Disaster Vulnerability & Public Safety",
        "category": "재난안전·공공인프라",
        "type": "openalex_search",
        "query": "disaster vulnerable OR public safety mobile OR civic data"
    },
    {
        "name": "arXiv Civic & Public Computing",
        "category": "시빅HCI·공공데이터",
        "type": "arxiv",
        "query": "cat:cs.HC AND (all:civic OR all:participatory OR all:disaster)"
    }
]

# 뉴스 및 미디어 RSS 피드
RSS_FEEDS = [
    {
        "name": "한겨레 뉴스 (사회·기후·칼럼)",
        "category": "사회·생태동향",
        "url": "https://www.hani.co.kr/rss/",
        "type": "rss"
    },
    {
        "name": "한겨레 오피니언 (사설·칼럼)",
        "category": "비판담론",
        "url": "https://www.hani.co.kr/rss/opinion/",
        "type": "rss"
    },
    {
        "name": "P2P Foundation Blog (P2P 커먼즈)",
        "category": "커먼즈",
        "url": "https://blog.p2pfoundation.net/feed",
        "type": "rss"
    }
]

# 트윈의 지적 관심사 필터링 및 큐레이션 프롬프트
CURATOR_SYSTEM_PROMPT = """당신은 '비판적 생태·기술 커먼즈 및 공공 UXR 연구자'의 전담 학술 큐레이터입니다.

[연구자의 핵심 관심 지형]
1. 커먼즈(Commons): 자치 관리, 커머닝(Commoning), 디지털·데이터 커먼즈, P2P 피어생산, 플랫폼 협동조합, 신자유주의 사유화(Enclosure) 비판.
2. 시빅 HCI & 공공 UXR: 취약계층 재난 안전망, 참여 디자인, 공공데이터(안심이 등), 관료주의를 넘는 포용적 유니버설 인터페이스.
3. 농생태학 & 다종 공생: 흙/토양의 생태정치, 대지 윤리, 식량주권, 에코페미니즘, 비인간 생명과의 공존.
4. 자율적 개인의 공생: 집단주의적 강요 없이, 고독과 사생활의 경계를 지키며 안전하게 자립하도록 돕는 공공 인프라.

[작업 지침]
제공된 논문/기사 목록 중에서 연구자의 지적 관심사와 부합하는 가장 가치 있는 항목을 선별하고, 각 항목에 대해 JSON 형식으로 응답하십시오.
- 단순 상업 광고, 표피적인 주식/투자 뉴스, 정치 공방성 기사는 과감히 제외(False) 처리하십시오.
- 선정된 항목에 대해서는 연구자가 바쁜 아침/저녁에 한눈에 파악할 수 있도록 깊이 있는 '한국어 3줄 요약'과 '연구적 시사점'을 제공하십시오.
"""
