import json
import os
import re
from collections import Counter
from datetime import datetime

WEB_DATA_DIR = os.path.join(os.path.dirname(__file__), "web", "data")
ARCHIVE_FILE = os.path.join(WEB_DATA_DIR, "archive.json")
LATEST_FILE = os.path.join(WEB_DATA_DIR, "latest_digest.json")
TRENDS_FILE = os.path.join(WEB_DATA_DIR, "trends.json")
GURUS_FILE = os.path.join(WEB_DATA_DIR, "gurus.json")
PERIODICALS_FILE = os.path.join(WEB_DATA_DIR, "periodicals.json")
OBSIDIAN_DIGEST_DIR = r"H:\내 드라이브\lgh\10. Journals\Research Digest"


def compute_trends(archive):
    """누적된 아카이브 데이터를 바탕으로 주제별/기간별 키워드 및 연구 동향 통계 산출"""
    category_counts = Counter()
    keyword_counts = Counter()
    timeline_series = []

    for digest in archive:
        d_date = digest.get("date", "")
        d_edition = digest.get("edition", "")
        items = digest.get("items", [])
        
        timeline_series.append({
            "id": digest.get("id"),
            "date": d_date,
            "edition": d_edition,
            "label": f"{d_date} {'오전' if d_edition == 'morning' else '오후'}",
            "count": len(items)
        })

        for it in items:
            cat = it.get("category", "기타")
            category_counts[cat] += 1
            for kw in it.get("keywords", []):
                clean_kw = kw.strip()
                if clean_kw and clean_kw not in ["#연구동향", "연구동향"]:
                    keyword_counts[clean_kw] += 1

    top_keywords = [
        {"keyword": kw, "count": cnt}
        for kw, cnt in keyword_counts.most_common(20)
    ]

    total_gurus = 17
    if os.path.exists(GURUS_FILE):
        try:
            with open(GURUS_FILE, "r", encoding="utf-8") as f:
                gdata = json.load(f)
                total_gurus = len(gdata)
        except Exception:
            pass

    total_periodicals = 50
    if os.path.exists(PERIODICALS_FILE):
        try:
            with open(PERIODICALS_FILE, "r", encoding="utf-8") as f:
                pdata = json.load(f)
                total_periodicals = len(pdata)
        except Exception:
            pass

    trends_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_digests": len(archive),
        "total_papers_analyzed": sum(len(d.get("items", [])) for d in archive),
        "total_gurus": total_gurus,
        "total_periodicals": total_periodicals,
        "total_tracked_keywords": len(top_keywords),
        "category_distribution": [
            {"category": cat, "count": cnt}
            for cat, cnt in category_counts.most_common()
        ],
        "top_keywords": top_keywords,
        "timeline_series": list(reversed(timeline_series[-10:]))  # 최근 10회차
    }

    return trends_data


def export_digest(curated_items, daily_summary=None, edition="morning"):
    """큐레이션 결과를 웹앱 데이터(JSON) 및 옵시디언 볼트에 저장"""
    os.makedirs(WEB_DATA_DIR, exist_ok=True)
    os.makedirs(OBSIDIAN_DIGEST_DIR, exist_ok=True)

    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M")
    date_str = now.strftime("%Y-%m-%d")
    edition_label = "오전" if edition == "morning" else "오후"
    digest_id = f"digest-{now.strftime('%Y%m%d')}-{edition}"

    # 1. 아카이브 로드 및 갱신
    archive = []
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                archive = json.load(f)
        except Exception as e:
            print(f"Error loading archive: {e}")

    # 동일 ID(날짜-판)가 이미 존재하면 교체, 없으면 맨 앞에 추가
    existing_idx = next((i for i, d in enumerate(archive) if d.get("id") == digest_id), -1)
    new_entry = {
        "id": digest_id,
        "date": date_str,
        "edition": edition,
        "edition_label": edition_label,
        "timestamp": timestamp_str,
        "daily_summary": daily_summary,
        "items": curated_items
    }

    if existing_idx >= 0:
        archive[existing_idx] = new_entry
    else:
        archive.insert(0, new_entry)

    # 2. trends.json 산출
    trends = compute_trends(archive)

    # 3. JSON 파일 저장
    with open(LATEST_FILE, "w", encoding="utf-8") as f:
        json.dump(new_entry, f, ensure_ascii=False, indent=2)

    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)

    with open(TRENDS_FILE, "w", encoding="utf-8") as f:
        json.dump(trends, f, ensure_ascii=False, indent=2)

    print(f"Exported web digest to {LATEST_FILE} & {ARCHIVE_FILE}")

    # 4. 옵시디언 볼트에 마크다운 리포트 저장
    obsidian_filename = f"{date_str}-{edition_label}-리서치_다이제스트.md"
    obsidian_filepath = os.path.join(OBSIDIAN_DIGEST_DIR, obsidian_filename)

    md_content = generate_obsidian_markdown(new_entry)
    with open(obsidian_filepath, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Exported Obsidian digest to {obsidian_filepath}")
    return obsidian_filepath


def generate_obsidian_markdown(entry):
    """옵시디언 맞춤형 품격 있는 학술 다이제스트 마크다운 생성"""
    date = entry["date"]
    edition_label = entry["edition_label"]
    daily_sum = entry.get("daily_summary") or {}
    items = entry.get("items", [])

    lines = []
    lines.append("---")
    lines.append(f"title: \"{date} {edition_label} 학술 연구 다이제스트\"")
    lines.append(f"date: {date}")
    lines.append(f"edition: {entry['edition']}")
    lines.append("category:")
    lines.append("  - Research Digest")
    lines.append("  - Daily Salon")
    lines.append("tags:")
    lines.append("  - 리서치다이제스트")
    lines.append("  - 연구살롱")
    lines.append("  - 커먼즈")
    lines.append("  - STS")
    lines.append("  - 시빅디자인")
    lines.append("  - 에코페미니즘")
    lines.append("---")
    lines.append("")
    lines.append(f"# ☕ {date} {edition_label} 고요한 연구 살롱 다이제스트")
    lines.append("")

    if daily_sum:
        theme = daily_sum.get("theme", "오늘의 사유 지형")
        overview = daily_sum.get("overview", "")
        takeaways = daily_sum.get("key_takeaways", [])

        lines.append("## 🧭 오늘의 사유 지형 (Daily Horizon)")
        lines.append(f"> **화두: {theme}**")
        lines.append("")
        if overview:
            lines.append(overview)
            lines.append("")

        if takeaways:
            lines.append("### 💡 핵심 명제 3선")
            for t in takeaways:
                lines.append(f"- {t}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 📚 엄선된 최신 학술 논문 및 담론")
    lines.append("")

    for i, it in enumerate(items, 1):
        lines.append(f"### {i}. {it.get('title_kr', it['original_title'])}")
        lines.append(f"- **원제**: *{it['original_title']}*")
        lines.append(f"- **저자 및 출처**: {it.get('authors', '연구진')} | `{it.get('source', '')}` ({it.get('published', '')})")
        lines.append(f"- **분류 / 적합도**: `{it.get('category', '')}` (적합도 {it.get('relevance_score', 0)}/10.0)")
        if it.get("url"):
            lines.append(f"- **원문 링크**: [{it['url']}]({it['url']})")
        lines.append("")
        lines.append("**[심층 분석]**")
        for p in it.get("summary_points", []):
            lines.append(f"- {p}")
        lines.append("")
        kws = " ".join(it.get("keywords", []))
        if kws:
            lines.append(f"`{kws}`")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("\n*본 다이제스트는 트윈의 자율적 연구와 대안적 공공 인프라 탐색을 위해 자동 큐레이션되었습니다.*")
    return "\n".join(lines)
