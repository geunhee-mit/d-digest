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
        "category": "커먼즈·공유재",
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
        "category": "농생태·식량주권",
        "issn": "0306-6150",
        "type": "openalex_journal"
    },
    {
        "name": "Archives of Design Research (디자인학연구)",
        "category": "시빅HCI·UXR",
        "issn": "1226-8046",
        "type": "openalex_journal"
    },
    {
        "name": "Social Studies of Science (SSS)",
        "category": "과학기술학·STS",
        "issn": "0306-3127",
        "type": "openalex_journal"
    },
    {
        "name": "Antipode: A Radical Journal of Geography",
        "category": "공간사회·도시커먼즈",
        "issn": "0066-4812",
        "type": "openalex_journal"
    },
    {
        "name": "Big Data & Society",
        "category": "과학기술학·STS",
        "issn": "2053-9517",
        "type": "openalex_journal"
    },
    {
        "name": "Environmental Humanities",
        "category": "농생태·식량주권",
        "issn": "2201-1919",
        "type": "openalex_journal"
    }
]

# 학술 검색 쿼리 (OpenAlex & arXiv - STS, 시빅HCI, 공간/도시, 농생태)
SCHOLARLY_QUERIES = [
    {
        "name": "Ecological Art & Multispecies Aesthetics (생태예술 & 다종공생 미학)",
        "category": "농생태·식량주권",
        "type": "openalex_search",
        "query": "ecological art OR environmental aesthetics OR land art OR multispecies art OR dialogical art"
    },
    {
        "name": "Science & Technology Studies (과학기술학 & 기술정치)",
        "category": "과학기술학·STS",
        "type": "openalex_search",
        "query": "science and technology studies OR socio-technical systems OR technology politics"
    },
    {
        "name": "Civic HCI & Participatory Design (시빅 컴퓨팅 & 참여디자인)",
        "category": "시빅HCI·UXR",
        "type": "openalex_search",
        "query": "civic computing OR participatory design OR civic tech OR public service design"
    },
    {
        "name": "Space and Society & Urban Commons (공간과 사회 & 도시 커먼즈)",
        "category": "공간사회·도시커먼즈",
        "type": "openalex_search",
        "query": "urban commons OR spatial justice OR right to the city"
    },
    {
        "name": "Disaster Vulnerability & Public Safety (재난 취약계층 & 공공안전)",
        "category": "재난안전·공공인프라",
        "type": "openalex_search",
        "query": "disaster vulnerable OR public safety infrastructure OR crisis informatics"
    },
    {
        "name": "arXiv Civic & Public Computing",
        "category": "시빅HCI·UXR",
        "type": "arxiv",
        "query": "cat:cs.HC AND (all:civic OR all:participatory OR all:disaster OR all:commons)"
    }
]

# 뉴스, 비판 담론 및 P2P 미디어 RSS 피드
RSS_FEEDS = [
    {
        "name": "P2P Foundation Blog (P2P 커먼즈 & 피어생산)",
        "category": "커먼즈·공유재",
        "url": "https://blog.p2pfoundation.net/feed",
        "type": "rss"
    },
    {
        "name": "한겨레 기후·사회 뉴스",
        "category": "농생태·식량주권",
        "url": "https://www.hani.co.kr/rss/",
        "type": "rss"
    },
    {
        "name": "한겨레 오피니언·칼럼",
        "category": "커먼즈·공유재",
        "url": "https://www.hani.co.kr/rss/opinion/",
        "type": "rss"
    }
]

# 트윈의 지적 관심사 필터링 및 고품질 학술 큐레이션 프롬프트
CURATOR_SYSTEM_PROMPT = """당신은 '비판적 생태·기술 커먼즈, 과학기술학(STS), 시빅 HCI/UXR 및 농생태학' 분야의 수석 연구 큐레이터입니다.

[연구자의 5대 핵심 관심 지형]
1. 커먼즈(Commons) & 자율성: 엘리너 오스트롬의 자치 관리론, 데이비드 볼리어의 커머닝(Commoning), 디지털·데이터 커먼즈, P2P 피어생산, 플랫폼 협동조합, 자본주의적 사유화(Enclosure) 비판.
2. 과학기술학(STS) & 미디어/기술정치: 사회기술시스템(Socio-technical systems), 기술의 정치성, 시민 과학, 알고리즘과 플랫폼 권력, 디지털 불평등.
3. 시빅 HCI & 공공 UXR: 취약계층 재난 안전망, 참여 디자인, 공공데이터, 관료주의를 넘는 포용적이고 무해한 유니버설 인터페이스.
4. 농생태학 & 다종 공생: 흙/토양의 생태정치, 대지 윤리, 식량주권, 에코페미니즘, 인간 중심주의를 탈피한 다종 얽힘(Multispecies).
5. 자율적 개인을 위한 공공 인프라: 침해적인 집단주의 규율 없이도, 고독과 사생활의 경계를 지키며 안전하게 자립하도록 돕는 공공 인프라.

[절대 엄수 작업 지침]
1. 잔여 영어 0% 원칙: 모든 분석 내용('daily_summary', 'summary_points')은 반드시 100% 자연스럽고 품격 있는 한국어 학술 문장으로 작성하십시오. 영어 원문 문장을 번역 없이 그대로 복사하거나 인용하지 마십시오 (영문 저자명 또는 통용 학술 고유명사 제외).
2. 피상적 상투어 절대 금지: "기존 한계를 극복하고 발전에 기여한다" 같은 상투적이고 공허한 문구를 배제하고, 해당 논문이 제기하는 구체적인 갈등 구조, 데이터 메커니즘, 트윈 연구(자립적 1인 가구, 비시장적 공유 인프라, 커머닝 프로토콜 등)와의 접점을 날카롭게 분석하십시오.
3. 제목 정제: 제목 말머리에 '[큐레이션]', '[요약]', '[논문]' 같은 태그를 일절 붙이지 말고, 세련된 한국어 학술 번역 제목만 작성하십시오.
4. 오늘의 사유 지형(Daily Summary) 도출: 개별 논문 나열을 넘어, 오늘 수집된 연구들을 관통하는 지적 화두와 핵심 명제 3가지를 도출하십시오.
"""
