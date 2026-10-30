import json
import os
from datetime import datetime

WEB_DATA_DIR = os.path.join(os.path.dirname(__file__), "web", "data")
ARCHIVE_FILE = os.path.join(WEB_DATA_DIR, "archive.json")
LATEST_FILE = os.path.join(WEB_DATA_DIR, "latest_digest.json")
OBSIDIAN_DIGEST_DIR = r"H:\내 드라이브\lgh\10. Journals\Research Digest"


def export_digest(curated_items, edition="morning"):
    """큐레이션 결과를 웹앱 데이터(JSON) 및 옵시디언 볼트에 저장"""
    os.makedirs(WEB_DATA_DIR, exist_ok=True)
    os.makedirs(OBSIDIAN_DIGEST_DIR, exist_ok=True)

    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M")
    date_str = now.strftime("%Y-%m-%d")
    edition_label = "오전 다이제스트 (Morning Digest)" if edition == "morning" else "오후 다이제스트 (Afternoon Digest)"

    digest_payload = {
        "id": f"{date_str}_{edition}",
        "edition": edition,
        "edition_label": edition_label,
        "date": date_str,
        "timestamp": timestamp_str,
        "item_count": len(curated_items),
        "items": curated_items
    }

    # 1. web/data/latest_digest.json 업데이트
    with open(LATEST_FILE, "w", encoding="utf-8") as f:
        json.dump(digest_payload, f, ensure_ascii=False, indent=2)

    # 2. web/data/archive.json 누적 업데이트 (영구 보관 및 검색용)
    archive = []
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                archive = json.load(f)
        except Exception:
            archive = []

    # 기존 동일 id 항목 대체 또는 맨 앞에 추가
    archive = [d for d in archive if d.get("id") != digest_payload["id"]]
    archive.insert(0, digest_payload)

    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)

    # 3. 옵시디언 볼트용 마크다운 파일 생성 (Research Digest)
    obsidian_md_file = os.path.join(OBSIDIAN_DIGEST_DIR, f"{date_str}_{edition}.md")
    md_content = generate_markdown(digest_payload)
    with open(obsidian_md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"✅ Digest exported successfully:")
    print(f"   - Web Latest: {LATEST_FILE}")
    print(f"   - Web Archive: {ARCHIVE_FILE} (Total {len(archive)} editions)")
    print(f"   - Obsidian Vault: {obsidian_md_file}")


def generate_markdown(digest):
    """옵시디언 마크다운 형식 생성"""
    lines = [
        "---",
        f"date: {digest['date']}",
        f"edition: {digest['edition']}",
        f"item_count: {digest['item_count']}",
        "tags:",
        "  - topic/research-digest",
        "  - type/journal",
        "---",
        f"# ☕ {digest['date']} {digest['edition_label']}",
        "",
        f"> 발행 시각: `{digest['timestamp']}` | 총 `{digest['item_count']}`편의 엄선된 학술·담론 소식",
        "",
        "---",
        ""
    ]

    for i, it in enumerate(digest["items"], 1):
        lines.append(f"### {i}. [{it['category']}] {it['title_kr']}")
        lines.append(f"- **원제**: {it['original_title']}")
        lines.append(f"- **출처 / 저자**: `{it['source']}` · {it['authors']} ({it.get('published', '')})")
        lines.append(f"- **원문 링크**: [원문 읽기]({it['url']})")
        lines.append(f"- **관련도 점수**: ⭐ {it['relevance_score']}/10.0")
        lines.append("- **핵심 시사점 (3-Line Summary)**:")
        for sp in it.get("summary_points", []):
            lines.append(f"  - {sp}")
        if it.get("keywords"):
            lines.append(f"- **태그**: {' '.join(it['keywords'])}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
