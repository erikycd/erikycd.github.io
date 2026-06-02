#!/usr/bin/env python3
"""Fetch top-cited Google Scholar publications and export to Jekyll data YAML."""

from __future__ import annotations

import argparse
import html
import heapq
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen


SCHOLAR_BASE_URL = "https://scholar.google.com"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_text(value: str) -> str:
    text = re.sub(r"<[^>]*>", "", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_profile_publications(html_doc: str) -> list[dict[str, Any]]:
    rows = re.findall(
        r'<tr[^>]*class="[^"]*\bgsc_a_tr\b[^"]*"[^>]*>(.*?)</tr>',
        html_doc,
        flags=re.S,
    )
    publications: list[dict[str, Any]] = []

    for row in rows:
        title_anchor_match = re.search(
            r'<a[^>]*class="[^"]*\bgsc_a_at\b[^"]*"[^>]*>(.*?)</a>',
            row,
            flags=re.S,
        )
        if not title_anchor_match:
            continue

        title_anchor_html = title_anchor_match.group(0)
        href_match = re.search(r'href="([^"]+)"', title_anchor_html, flags=re.S)
        title_text_match = re.search(r'>(.*?)</a>', title_anchor_html, flags=re.S)
        if not href_match or not title_text_match:
            continue

        meta_blocks = re.findall(r'<div class="gs_gray">(.*?)</div>', row, flags=re.S)
        citations_match = re.search(
            r'<a[^>]*class="[^"]*\bgsc_a_ac\b[^"]*"[^>]*>(\d*)</a>',
            row,
            flags=re.S,
        )
        year_match = re.search(r'<span[^>]*>(\d{4})</span>', row, flags=re.S)

        href = html.unescape(href_match.group(1))
        details_url = urljoin(SCHOLAR_BASE_URL, href)

        publications.append(
            {
                "title": clean_text(title_text_match.group(1)),
                "authors": clean_text(meta_blocks[0]) if len(meta_blocks) > 0 else "",
                "venue": clean_text(meta_blocks[1]) if len(meta_blocks) > 1 else "",
                "citations": int(citations_match.group(1)) if citations_match and citations_match.group(1) else 0,
                "year": int(year_match.group(1)) if year_match else 0,
                "details_url": details_url,
            }
        )

    return publications


def parse_doi(details_html: str) -> str | None:
    pattern = re.compile(
        r'<div class="gsc_oci_field">\s*DOI\s*</div>\s*'
        r'<div class="gsc_oci_value">(.*?)</div>',
        flags=re.I | re.S,
    )
    match = pattern.search(details_html)
    if not match:
        return None

    doi_value = clean_text(match.group(1))
    doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", doi_value, flags=re.I)
    if not doi_match:
        return None
    return doi_match.group(0)


def yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def to_yaml(publications: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for pub in publications:
        lines.append(f'- title: "{yaml_escape(pub["title"])}"')
        lines.append(f'  authors: "{yaml_escape(pub["authors"])}"')
        lines.append(f"  year: {pub['year']}")
        lines.append(f'  venue: "{yaml_escape(pub["venue"])}"')
        lines.append(f"  citations: {pub['citations']}")
        if pub.get("doi"):
            lines.append(f'  doi: "{yaml_escape(pub["doi"])}"')
            lines.append(f'  url: "https://doi.org/{yaml_escape(pub["doi"])}"')
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def extract_scholar_user_id(profile_url: str) -> str:
    parsed = urlparse(profile_url)
    query = parse_qs(parsed.query)
    user_ids = query.get("user")
    if not user_ids:
        raise ValueError("The Google Scholar URL must include a 'user' query parameter.")
    return user_ids[0]


def build_profile_url(user_id: str) -> str:
    return (
        f"{SCHOLAR_BASE_URL}/citations?hl=en&user={user_id}&view_op=list_works"
        "&sortby=pubdate&cstart=0&pagesize=100"
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    default_output = repo_root / "_data" / "featured_publications.yml"

    parser = argparse.ArgumentParser(
        description="Fetch top-cited publications from a Google Scholar profile."
    )
    parser.add_argument(
        "--scholar-url",
        required=True,
        help="Full Google Scholar profile URL.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of top publications to export (default: 5).",
    )
    parser.add_argument(
        "--output",
        default=str(default_output),
        help="Output YAML file path.",
    )
    args = parser.parse_args()

    user_id = extract_scholar_user_id(args.scholar_url)
    profile_html = fetch_text(build_profile_url(user_id))
    publications = parse_profile_publications(profile_html)
    if not publications:
        raise RuntimeError("No publications found in the Google Scholar profile.")

    top_publications = heapq.nlargest(args.top, publications, key=lambda item: item["citations"])

    for pub in top_publications:
        try:
            details_html = fetch_text(pub["details_url"])
            pub["doi"] = parse_doi(details_html)
        except Exception as exc:
            print(
                f"Warning: DOI lookup failed for '{pub['title']}': {exc}",
                file=sys.stderr,
            )
            pub["doi"] = None

    top_publications.sort(key=lambda item: (item["year"], item["citations"]), reverse=True)

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(to_yaml(top_publications), encoding="utf-8")

    print(f"Generated file: {output_path}")
    print(f"Exported publications: {len(top_publications)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
