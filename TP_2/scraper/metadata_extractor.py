"""
metadata_extractor.py
Funciones para extraer meta tags relevantes de un documento HTML.
"""

from typing import Dict

from bs4 import BeautifulSoup


def extract_meta_tags(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extrae meta tags "description", "keywords" y todas las Open Graph (og:*)
    y las devuelve en un diccionario {nombre: valor}.
    """
    meta: Dict[str, str] = {}

    # Meta clásicas por nombre
    for name in ("description", "keywords"):
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            meta[name] = tag["content"].strip()

    # Meta Open Graph (property="og:...")
    for tag in soup.find_all("meta", attrs={"property": True}):
        prop = tag.get("property", "")
        if prop.startswith("og:") and tag.get("content"):
            meta[prop] = tag["content"].strip()

    return meta
