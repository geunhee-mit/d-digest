import sys
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
from config import TARGET_JOURNALS, SCHOLARLY_QUERIES, RSS_FEEDS

HEADERS = {"User-Agent": "ResearchDigestCurator/1.0 (mailto:twin@commons.org)"}


def reconstruct_abstract(inverted_index):
    """OpenAlex의 abstract_inverted_index를 일반 문장으로 복원"""
    if not inverted_index:
        return ""
    word_pos = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_pos.append((pos, word))
    word_pos.sort(key=lambda x: x[0])
    return " ".join(w[1] for w in word_pos)


def fetch_openalex_journal(journal_config, limit=3):
    """OpenAlex API를 통해 특정 핵심 저널의 최신 논문 수집"""
    results = []
    issn = journal_config["issn"]
    url = f"https://api.openalex.org/works?filter=primary_location.source.issn:{issn}&sort=publication_date:desc&per-page={limit}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json().get("results", [])
            for item in data:
                title = item.get("title") or ""
                if not title:
                    continue
                abstract = reconstruct_abstract(item.get("abstract_inverted_index"))
                authors = [
                    a.get("author", {}).get("display_name", "")
                    for a in item.get("authorships", [])[:3]
                ]
                doi = item.get("doi") or item.get("id")
                results.append({
                    "id": doi,
                    "title": title,
                    "abstract": abstract[:1000] if abstract else "Abstract not available in metadata.",
                    "url": doi,
                    "source": journal_config["name"],
                    "category": journal_config["category"],
                    "authors": ", ".join(filter(None, authors)),
                    "published": item.get("publication_date", ""),
                    "type": "scholarly_paper"
                })
    except Exception as e:
        print(f"Error fetching OpenAlex journal {journal_config['name']}: {e}", file=sys.stderr)
    return results


def fetch_openalex_search(query_config, limit=3):
    """OpenAlex 검색 쿼리를 통한 최신 주제 논문 수집"""
    results = []
    query = query_config["query"]
    url = f"https://api.openalex.org/works?search={requests.utils.quote(query)}&sort=publication_date:desc&per-page={limit}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            data = res.json().get("results", [])
            for item in data:
                title = item.get("title") or ""
                if not title:
                    continue
                abstract = reconstruct_abstract(item.get("abstract_inverted_index"))
                authors = [
                    a.get("author", {}).get("display_name", "")
                    for a in item.get("authorships", [])[:3]
                ]
                doi = item.get("doi") or item.get("id")
                source_name = (
                    item.get("primary_location", {})
                    .get("source", {})
                    .get("display_name")
                    or "Scholarly Pre-print / Journal"
                )
                results.append({
                    "id": doi,
                    "title": title,
                    "abstract": abstract[:1000] if abstract else "",
                    "url": doi,
                    "source": source_name,
                    "category": query_config["category"],
                    "authors": ", ".join(filter(None, authors)),
                    "published": item.get("publication_date", ""),
                    "type": "scholarly_paper"
                })
    except Exception as e:
        print(f"Error fetching OpenAlex search {query_config['name']}: {e}", file=sys.stderr)
    return results


def fetch_arxiv(arxiv_config, limit=3):
    """arXiv API를 통한 프리프린트 수집"""
    results = []
    query = arxiv_config["query"]
    url = f"http://export.arxiv.org/api/query?search_query={requests.utils.quote(query)}&sortBy=submittedDate&sortOrder=descending&max_results={limit}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns)
                summary = entry.find("atom:summary", ns)
                entry_id = entry.find("atom:id", ns)
                published = entry.find("atom:published", ns)
                authors = [
                    a.find("atom:name", ns).text
                    for a in entry.findall("atom:author", ns)
                    if a.find("atom:name", ns) is not None
                ][:3]

                t_text = title.text.strip().replace("\n", " ") if title is not None else ""
                s_text = summary.text.strip().replace("\n", " ") if summary is not None else ""
                link = entry_id.text.strip() if entry_id is not None else ""
                pub_date = published.text.split("T")[0] if published is not None else ""

                if t_text:
                    results.append({
                        "id": link,
                        "title": t_text,
                        "abstract": s_text[:1000],
                        "url": link,
                        "source": "arXiv cs.HC / cs.CY",
                        "category": arxiv_config["category"],
                        "authors": ", ".join(authors),
                        "published": pub_date,
                        "type": "preprint"
                    })
    except Exception as e:
        print(f"Error fetching arXiv {arxiv_config['name']}: {e}", file=sys.stderr)
    return results


def fetch_rss(feed_config, limit=4):
    """RSS 피드를 통한 기사 및 칼럼 수집"""
    results = []
    url = feed_config["url"]
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            # RSS 2.0 또는 Atom 지원
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
            
            for item in items[:limit]:
                # Title
                t = item.find("title")
                if t is None:
                    t = item.find("{http://www.w3.org/2005/Atom}title")
                title_text = t.text.strip() if t is not None and t.text else ""
                
                # Link
                l = item.find("link")
                if l is None:
                    l = item.find("{http://www.w3.org/2005/Atom}link")
                link_text = l.text.strip() if l is not None and l.text else (l.attrib.get("href", "") if l is not None else "")
                
                # Description
                d = item.find("description")
                if d is None:
                    d = item.find("{http://www.w3.org/2005/Atom}summary")
                desc_text = d.text.strip() if d is not None and d.text else ""

                # Clean CDATA/HTML tags if simple
                if "<" in desc_text and ">" in desc_text:
                    import re
                    desc_text = re.sub(r"<[^>]+>", "", desc_text).strip()

                # PubDate
                p = item.find("pubDate")
                pub_text = p.text.strip() if p is not None and p.text else datetime.now().strftime("%Y-%m-%d")

                if title_text and link_text:
                    results.append({
                        "id": link_text,
                        "title": title_text,
                        "abstract": desc_text[:600],
                        "url": link_text,
                        "source": feed_config["name"],
                        "category": feed_config["category"],
                        "authors": feed_config["name"],
                        "published": pub_text[:25],
                        "type": "news_article"
                    })
    except Exception as e:
        print(f"Error fetching RSS {feed_config['name']}: {e}", file=sys.stderr)
    return results


def fetch_all():
    """모든 소스에서 후보 수집 및 중복 제거"""
    raw_candidates = []
    
    # 1. 핵심 학술 저널 (OpenAlex)
    for j in TARGET_JOURNALS:
        raw_candidates.extend(fetch_openalex_journal(j, limit=2))
        
    # 2. 학술 쿼리 (OpenAlex & arXiv)
    for q in SCHOLARLY_QUERIES:
        if q["type"] == "openalex_search":
            raw_candidates.extend(fetch_openalex_search(q, limit=2))
        elif q["type"] == "arxiv":
            raw_candidates.extend(fetch_arxiv(q, limit=2))
            
    # 3. 뉴스 및 비판 담론 RSS
    for r in RSS_FEEDS:
        raw_candidates.extend(fetch_rss(r, limit=3))
        
    # 중복 제거 (URL 기준)
    seen_urls = set()
    deduped = []
    for item in raw_candidates:
        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(item)
            
    return deduped


if __name__ == "__main__":
    items = fetch_all()
    print(f"Total candidate items fetched: {len(items)}")
    for i, it in enumerate(items[:5], 1):
        print(f"[{i}] ({it['category']}) {it['title']} - {it['source']}")
