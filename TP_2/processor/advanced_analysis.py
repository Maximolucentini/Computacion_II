"""

Incluye:
- Detección simple de tecnologías usadas (frameworks JS, CMS, etc.)
- Análisis SEO básico (score 0-100)
- Detección de datos estructurados (JSON-LD / Schema.org)
- Análisis de accesibilidad (uso de alt en imágenes)

Todo se hace con:
- HTML crudo (string)
- scraping_data (meta_tags, structure, images_count, etc.)
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


def analyze_advanced(
    url: str,
    scraping_data: Dict[str, Any],
    html: str,
) -> Dict[str, Any]:
    """
    Devuelve un dict con claves:
        - technologies
        - seo
        - structured_data
        - accessibility

    Si no hay HTML o hay errores de parseo, devuelve lo que pueda.
    """
    logger = logging.getLogger(__name__)

    soup: Optional[BeautifulSoup] = None
    if html:
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo parsear HTML para análisis avanzado: %s", exc)
            soup = None

    technologies = _detect_technologies(scraping_data, soup, html)
    seo = _analyze_seo(scraping_data)
    structured_data = _analyze_structured_data(soup)
    accessibility = _analyze_accessibility(soup, scraping_data)

    return {
        "url": url,
        "technologies": technologies,
        "seo": seo,
        "structured_data": structured_data,
        "accessibility": accessibility,
    }


# ----------------------------------------------------------------------
#  Tecnologías: frameworks JS, CMS, etc.
# ----------------------------------------------------------------------


def _detect_technologies(
    scraping_data: Dict[str, Any],
    soup: Optional[BeautifulSoup],
    html: str,
) -> Dict[str, Any]:
    frameworks_js: List[str] = []
    cms: Optional[str] = None
    others: List[str] = []

    html_lower = html.lower() if html else ""

    # Heurísticas simples para CMS
    if "wp-content" in html_lower or "wordpress" in html_lower:
        cms = "WordPress"
    elif "drupal" in html_lower:
        cms = "Drupal"
    elif "joomla" in html_lower:
        cms = "Joomla"

    
    if soup is not None:
        meta_gen = soup.find("meta", attrs={"name": "generator"})
        if meta_gen and meta_gen.get("content"):
            gen_value = meta_gen["content"].lower()
            if "wordpress" in gen_value:
                cms = "WordPress"
            elif "drupal" in gen_value:
                cms = "Drupal"
            elif "joomla" in gen_value:
                cms = "Joomla"

   
    framework_patterns = {
        "react": "React",
        "angular": "Angular",
        "vue": "Vue.js",
        "jquery": "jQuery",
        "next.js": "Next.js",
        "nuxt.js": "Nuxt.js",
    }

    if soup is not None:
        for script in soup.find_all("script"):
            text = ""
            if script.get("src"):
                text = script["src"]
            elif script.string:
                text = script.string
            text_lower = text.lower()
            for key, name in framework_patterns.items():
                if key in text_lower and name not in frameworks_js:
                    frameworks_js.append(name)

    
    if "bootstrap" in html_lower:
        others.append("Bootstrap")
    if "tailwind" in html_lower:
        others.append("Tailwind CSS")

    return {
        "frameworks_js": frameworks_js,
        "cms": cms,
        "other": others,
    }


# ----------------------------------------------------------------------
#  SEO: score simple usando meta_tags y structure
# ----------------------------------------------------------------------


def _analyze_seo(scraping_data: Dict[str, Any]) -> Dict[str, Any]:
    meta = scraping_data.get("meta_tags", {}) or {}
    structure = scraping_data.get("structure", {}) or {}
    title = scraping_data.get("title", "") or ""

    has_description = bool(meta.get("description"))
    has_keywords = bool(meta.get("keywords"))
    og_title_present = bool(meta.get("og:title"))
    h1_count = int(structure.get("h1", 0) or 0)

    score = 0

    if has_description:
        score += 30
    if h1_count >= 1:
        score += 20
    if 10 <= len(title) <= 70:
        score += 20
    if og_title_present:
        score += 15
    if has_keywords:
        score += 10

    # Pequeño ajuste por longitud de título muy mala
    if len(title) < 3:
        score -= 10

    score = max(0, min(100, score))

    return {
        "score": score,
        "has_meta_description": has_description,
        "has_keywords": has_keywords,
        "has_h1": h1_count >= 1,
        "title_length": len(title),
        "h1_count": h1_count,
    }


# ----------------------------------------------------------------------
#  Datos estructurados: JSON-LD / Schema.org
# ----------------------------------------------------------------------


def _analyze_structured_data(soup: Optional[BeautifulSoup]) -> Dict[str, Any]:
    if soup is None:
        return {
            "json_ld_count": 0,
            "schema_org_detected": False,
            "examples": [],
        }

    json_ld_tags = soup.find_all("script", type="application/ld+json")
    json_ld_count = len(json_ld_tags)

    schema_org_detected = False
    examples: List[Dict[str, Any]] = []

    for tag in json_ld_tags[:3]:  # no procesar infinitos
        text = tag.string or ""
        if "schema.org" in text.lower():
            schema_org_detected = True
        try:
            data = json.loads(text)
            examples.append(_simplify_json_ld(data))
        except Exception:
            # Si no se puede parsear, ignoramos
            continue

    return {
        "json_ld_count": json_ld_count,
        "schema_org_detected": schema_org_detected,
        "examples": examples,
    }


def _simplify_json_ld(data: Any) -> Any:
    """
    Intenta devolver una versión "resumida" del JSON-LD:
    - si es dict con "@type" y "name", devolvemos solo eso.
    """
    if isinstance(data, dict):
        result = {}
        for key in ("@type", "name", "headline"):
            if key in data:
                result[key] = data[key]
        if result:
            return result
    return data


# ----------------------------------------------------------------------
#  Accesibilidad: alt en imágenes
# ----------------------------------------------------------------------


def _analyze_accessibility(
    soup: Optional[BeautifulSoup],
    scraping_data: Dict[str, Any],
) -> Dict[str, Any]:
    if soup is None:
        total_images = scraping_data.get("images_count")
        return {
            "total_images": total_images,
            "images_with_alt": None,
            "alt_coverage": None,
        }

    imgs = soup.find_all("img")
    total = len(imgs)
    with_alt = 0

    for img in imgs:
        alt = img.get("alt")
        if alt is not None and alt.strip():
            with_alt += 1

    coverage = (with_alt / total) if total > 0 else None

    return {
        "total_images": total,
        "images_with_alt": with_alt,
        "alt_coverage": coverage,
    }
