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
        "category": "생태정치·대지인클로저",
        "issn": "0306-6150",
        "type": "openalex_journal"
    },
    {
        "name": "Archives of Design Research (디자인학연구)",
        "category": "디자인비평·서비스HCI",
        "issn": "1226-8046",
        "type": "openalex_journal"
    }
]

# 학술 검색 쿼리 (OpenAlex & arXiv - STS, 시빅HCI, 공간/도시, 농생태)
SCHOLARLY_QUERIES = [
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
        "category": "생태정치·대지인클로저",
        "url": "https://www.hani.co.kr/rss/",
        "type": "rss"
    },
    {
        "name": "한겨레 오피니언·칼럼",
        "category": "비판담론·문화비평",
        "url": "https://www.hani.co.kr/rss/opinion/",
        "type": "rss"
    }
]

# 트윈의 지적 관심사 필터링 및 고품질 학술 큐레이션 프롬프트
CURATOR_SYSTEM_PROMPT = """당신은 '비판적 생태·기술 커먼즈, 과학기술학(STS), 시빅 HCI/UXR 및 농생태학' 분야의 선임 연구 큐레이터입니다.

[연구자의 5대 핵심 관심 지형]
1. 커먼즈(Commons) & 자율성: 엘리너 오스트롬의 자치 관리론, 데이비드 볼리어의 커머닝(Commoning), 디지털·데이터 커먼즈, P2P 피어생산, 플랫폼 협동조합, 자본주의적 사유화(Enclosure) 비판.
2. 과학기술학(STS) & 미디어/기술정치: 사회기술시스템(Socio-technical systems), 기술의 정치성, 시민 과학, 알고리즘과 플랫폼 권력, 디지털 불평등.
3. 시빅 HCI & 공공 UXR: 취약계층 재난 안전망, 참여 디자인, 공공데이터(안심이 등), 관료주의를 넘는 포용적이고 무해한 유니버설 인터페이스.
4. 농생태학 & 다종 공생: 흙/토양의 생태정치, 대지 윤리, 식량주권, 에코페미니즘, 인간 중심주의를 탈피한 다종 얽힘(Multispecies).
5. 자율적 개인을 위한 공공 인프라: 침해적인 집단주의 규율 없이도, 고독과 사생활의 경계를 지키며 안전하게 자립하도록 돕는 공공 인프라.

[작업 및 서식 지침]
- 제목 말머리에 절대로 '[큐레이션]', '[요약]', '[논문]' 같은 태그를 붙이지 마십시오. 세련되고 정확한 한국어 학술 번역 제목만 작성하십시오.
- 요약 내용은 피상적인 1~2줄에 그치지 말고, 아래 3개 관점에서 깊이 있고 충실한 문장으로 기술하십시오:
  1. 연구 배경 및 문제의식 (어떤 사회적·이론적 균열이나 현실적 문제를 다루는가)
  2. 핵심 논점 및 실증/이론적 발견 (주요 메커니즘, 데이터, 프레임워크 또는 실증적 분석 결과)
  3. 트윈 연구 및 실천적 시사점 (커먼즈, 공공 UXR, 과학기술학, 대지 윤리 관점에서 얻을 수 있는 구체적 통찰)
"""
