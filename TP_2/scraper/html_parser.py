"""
html_parser.py
Funciones de parsing HTML para extraer título, links, estructura, etc.
"""

from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .metadata_extractor import extract_meta_tags


def extract_page_data(html: str, base_url: str) -> Dict:
    """
    A partir del HTML crudo y la URL base, devuelve un diccionario con:

      - title
      - links (lista de URLs absolutas)
      - meta_tags (description, keywords, og:*)
      - structure (conteo h1..h6)
      - images_count
      - images (lista de URLs absolutas de imágenes)
    """
    soup = BeautifulSoup(html, "lxml")

    title = _extract_title(soup)
    links = _extract_links(soup, base_url)
    structure = _count_headers(soup)
    images, images_count = _extract_images(soup, base_url)
    meta_tags = extract_meta_tags(soup)

    return {
        "title": title,
        "links": links,
        "meta_tags": meta_tags,
        "structure": structure,
        "images_count": images_count,
        "images": images,
    }


def _extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""


def _extract_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        absolute = urljoin(base_url, href)
        links.append(absolute)
    return links


def _count_headers(soup: BeautifulSoup) -> Dict[str, int]:
    structure: Dict[str, int] = {}
    for level in range(1, 7):
        tag = f"h{level}"
        structure[tag] = len(soup.find_all(tag))
    return structure


def _extract_images(soup: BeautifulSoup, base_url: str) -> tuple[List[str], int]:
    images: List[str] = []
    for img in soup.find_all("img", src=True):
        src = img["src"].strip()
        absolute = urljoin(base_url, src)
        images.append(absolute)
    return images, len(images)
