#!/usr/bin/env python3
"""Fetch top-cited Google Scholar publications and export to Jekyll data YAML."""

from __future__ import annotations

import argparse
import html
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
    rows = re.findall(r'<tr class="gsc_a_tr".*?>(.*?)</tr>', html_doc, flags=re.S)
    publications: list[dict[str, Any]] = []

    for row in rows:
        title_match = re.search(
            r'<a class="gsc_a_at" href="([^"]+)">(.*?)</a>',
            row,
            flags=re.S,
        )
        if not title_match:
            continue

        meta_blocks = re.findall(r'<div class="gs_gray">(.*?)</div>', row, flags=re.S)
        citations_match = re.search(
            r'<a[^>]*class="gsc_a_ac[^"]*"[^>]*>(\d+)</a>',
            row,
            flags=re.S,
        )
        year_match = re.search(r'<span[^>]*>(\d{4})</span>', row, flags=re.S)

        href = title_match.group(1)
        details_url = urljoin(SCHOLAR_BASE_URL, href)

        publications.append(
            {
                "title": clean_text(title_match.group(2)),
                "authors": clean_text(meta_blocks[0]) if len(meta_blocks) > 0 else "",
                "venue": clean_text(meta_blocks[1]) if len(meta_blocks) > 1 else "",
                "citations": int(citations_match.group(1)) if citations_match else 0,
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
        raise ValueError("No se encontró el parámetro 'user' en la URL de Google Scholar.")
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
        description="Obtiene las 5 publicaciones más citadas desde Google Scholar."
    )
    parser.add_argument(
        "--scholar-url",
        required=True,
        help="URL completa del perfil de Google Scholar.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Cantidad de publicaciones top a exportar (por defecto: 5).",
    )
    parser.add_argument(
        "--output",
        default=str(default_output),
        help="Ruta de salida del archivo YAML.",
    )
    args = parser.parse_args()

    user_id = extract_scholar_user_id(args.scholar_url)
    profile_html = fetch_text(build_profile_url(user_id))
    publications = parse_profile_publications(profile_html)
    if not publications:
        raise RuntimeError("No se encontraron publicaciones en el perfil de Google Scholar.")

    top_publications = sorted(publications, key=lambda item: item["citations"], reverse=True)[: args.top]

    for pub in top_publications:
        try:
            details_html = fetch_text(pub["details_url"])
            pub["doi"] = parse_doi(details_html)
        except Exception:
            pub["doi"] = None

    top_publications.sort(key=lambda item: (item["year"], item["citations"]), reverse=True)

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(to_yaml(top_publications), encoding="utf-8")

    print(f"Archivo generado: {output_path}")
    print(f"Publicaciones exportadas: {len(top_publications)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
