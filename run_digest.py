import argparse
import sys
from datetime import datetime
from fetcher import fetch_all
from curator import curate_items
from exporter import export_digest

# Windows 콘솔 인코딩 대응
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Run Academic & Civic Research Digest")
    parser.add_argument(
        "--edition",
        choices=["morning", "afternoon", "auto"],
        default="auto",
        help="Digest edition to generate (morning or afternoon)"
    )
    args = parser.parse_args()

    # 에디션 자동 판별 (13시 이전이면 morning, 이후면 afternoon)
    edition = args.edition
    if edition == "auto":
        current_hour = datetime.now().hour
        edition = "morning" if current_hour < 13 else "afternoon"

    print(f"==================================================")
    print(f"🚀 Research Digest Pipeline Started [{edition.upper()} EDITION]")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"==================================================")

    # 1. 정보 수집 (학술 저널, arXiv, RSS)
    print("[1/3] Fetching candidates from scholarly APIs & RSS feeds...")
    raw_candidates = fetch_all()
    print(f"      -> {len(raw_candidates)} items retrieved.")

    # 2. 무료 AI 큐레이션 및 3줄 요약
    print("[2/3] Curating & summarizing with AI (Gemini 2.0 Flash / Heuristic fallback)...")
    curated_items = curate_items(raw_candidates)
    print(f"      -> {len(curated_items)} high-relevance items curated.")

    # 3. 결과 내보내기 (웹앱 JSON + 옵시디언 볼트 마크다운)
    print("[3/3] Exporting to web app data & Obsidian vault...")
    export_digest(curated_items, edition=edition)

    print("==================================================")
    print(f"✨ {edition.capitalize()} Digest Generation Completed!")
    print("==================================================")


if __name__ == "__main__":
    main()
