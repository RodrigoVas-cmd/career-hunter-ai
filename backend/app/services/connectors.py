import hashlib
import html
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
JSONLD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def strip_html(raw: Optional[str]) -> str:
    if not raw:
        return ""
    unescaped = html.unescape(raw)
    text = TAG_RE.sub(" ", unescaped)
    return WS_RE.sub(" ", text).strip()


def infer_modality(text: str) -> Optional[str]:
    low = text.lower()
    if any(k in low for k in ["100% remoto", "trabalho remoto", "remote", "home office", "remoto"]):
        return "remoto"
    if any(k in low for k in ["híbrido", "hibrido", "hybrid"]):
        return "hibrido"
    if any(k in low for k in ["presencial", "on-site", "onsite"]):
        return "presencial"
    return None


def infer_seniority(title: str, description: str = "") -> Optional[str]:
    combined = f"{title} {description[:300]}".lower()
    for level, keywords in [
        ("Diretoria", ["diretor", "director", "vp ", "head of", "c-level", "cto", "cpo", "cfo"]),
        ("Gerência", ["gerente", "manager", "engineering manager", "product manager"]),
        ("Coordenação", ["coordenador", "coordinator", "tech lead", "líder técnico"]),
        ("Especialista", ["especialista", "specialist", "staff", "principal"]),
        ("Sênior", ["sênior", "senior", "sr.", "sr "]),
        ("Pleno", ["pleno", "mid-level", "mid level"]),
        ("Analista", ["analista", "analyst", "júnior", "junior", "jr"]),
    ]:
        if any(k in combined for k in keywords):
            return level
    return None


def extract_requirements(description: str) -> List[Dict[str, str]]:
    """Extracts candidate requirements from job description text (treated as untrusted data)."""
    reqs: List[Dict[str, str]] = []
    seen = set()
    for raw_line in re.split(r"[\n•;]+", description):
        line = raw_line.strip(" -*\t")
        if len(line) < 12 or len(line) > 260:
            continue
        low = line.lower()
        req_type = None
        if any(k in low for k in ["obrigatório", "indispensável", "requisito", "experiência em", "experiência com", "conhecimento em", "domínio de", "required", "must have"]):
            req_type = "mandatory"
        elif any(k in low for k in ["desejável", "diferencial", "plus", "nice to have", "será um diferencial"]):
            req_type = "desirable"

        if req_type and line.lower() not in seen:
            seen.add(line.lower())
            reqs.append({"requirement_type": req_type, "text": line})
        if len(reqs) >= 12:
            break
    return reqs


def compute_dedup_hash(company_name: str, title: str, original_url: str, external_id: Optional[str]) -> str:
    key = f"{company_name.strip().lower()}|{title.strip().lower()}|{external_id or original_url.strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def detect_connector_from_url(url: str) -> Tuple[str, str]:
    """Detects supported public ATS boards from a careers URL."""
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    parts = [p for p in parsed.path.split("/") if p]

    if "greenhouse.io" in host and parts:
        return "greenhouse", parts[0]
    if "lever.co" in host and parts:
        return "lever", parts[0]
    return "jsonld", url.strip()


def fetch_greenhouse_jobs(board_token: str, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    with httpx.Client(timeout=15.0, headers={"User-Agent": "CareerHunterAI/1.0"}) as client:
        resp = client.get(url)
        resp.raise_for_status()
        payload = resp.json()

    jobs: List[Dict[str, Any]] = []
    for item in payload.get("jobs", []):
        title = (item.get("title") or "").strip()
        if not title:
            continue
        desc = strip_html(item.get("content"))
        loc = (item.get("location") or {}).get("name")
        abs_url = item.get("absolute_url") or f"https://boards.greenhouse.io/{board_token}/jobs/{item.get('id')}"
        comp = company_name or board_token.replace("-", " ").title()
        pub = None
        if item.get("updated_at"):
            try:
                pub = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
            except ValueError:
                pub = None

        jobs.append({
            "external_id": str(item.get("id")),
            "company_name": comp,
            "title": title,
            "description": desc or title,
            "original_url": abs_url,
            "location": loc,
            "modality": infer_modality(f"{title} {loc or ''} {desc[:400]}"),
            "seniority": infer_seniority(title, desc),
            "salary_range_text": None,
            "benefits": [],
            "published_at": pub,
            "requirements": extract_requirements(desc),
        })
    return jobs


def fetch_lever_jobs(company_slug: str, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
    url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
    with httpx.Client(timeout=15.0, headers={"User-Agent": "CareerHunterAI/1.0"}) as client:
        resp = client.get(url)
        resp.raise_for_status()
        payload = resp.json()

    jobs: List[Dict[str, Any]] = []
    for item in payload if isinstance(payload, list) else []:
        title = (item.get("text") or "").strip()
        if not title:
            continue
        desc = strip_html(item.get("descriptionPlain") or item.get("description"))
        cats = item.get("categories") or {}
        loc = cats.get("location")
        comp = company_name or company_slug.replace("-", " ").title()
        pub = None
        if item.get("createdAt"):
            try:
                pub = datetime.fromtimestamp(item["createdAt"] / 1000.0, tz=timezone.utc)
            except Exception:
                pub = None

        jobs.append({
            "external_id": str(item.get("id")),
            "company_name": comp,
            "title": title,
            "description": desc or title,
            "original_url": item.get("hostedUrl") or f"https://jobs.lever.co/{company_slug}/{item.get('id')}",
            "location": loc,
            "modality": infer_modality(f"{title} {loc or ''} {cats.get('commitment', '')} {desc[:400]}"),
            "seniority": infer_seniority(title, desc),
            "salary_range_text": None,
            "benefits": [],
            "published_at": pub,
            "requirements": extract_requirements(desc),
        })
    return jobs


def extract_jsonld_jobs_from_html(html_content: str, page_url: str, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
    jobs: List[Dict[str, Any]] = []
    for block in JSONLD_RE.findall(html_content):
        try:
            data = json.loads(block.strip())
        except Exception:
            continue

        candidates = data if isinstance(data, list) else [data]
        expanded: List[Dict[str, Any]] = []
        for c in candidates:
            if isinstance(c, dict) and "@graph" in c and isinstance(c["@graph"], list):
                expanded.extend(g for g in c["@graph"] if isinstance(g, dict))
            elif isinstance(c, dict):
                expanded.append(c)

        for obj in expanded:
            if obj.get("@type") != "JobPosting":
                continue
            title = (obj.get("title") or "").strip()
            if not title:
                continue
            org = obj.get("hiringOrganization") or {}
            comp = (org.get("name") if isinstance(org, dict) else None) or company_name or urlparse(page_url).netloc
            desc = strip_html(obj.get("description"))
            loc_obj = obj.get("jobLocation") or {}
            if isinstance(loc_obj, list) and loc_obj:
                loc_obj = loc_obj[0]
            addr = loc_obj.get("address") if isinstance(loc_obj, dict) else {}
            loc = addr.get("addressLocality") if isinstance(addr, dict) else None
            if obj.get("jobLocationType") == "TELECOMMUTE":
                modality = "remoto"
            else:
                modality = infer_modality(f"{title} {loc or ''} {desc[:400]}")

            jobs.append({
                "external_id": obj.get("identifier", {}).get("value") if isinstance(obj.get("identifier"), dict) else None,
                "company_name": comp,
                "title": title,
                "description": desc or title,
                "original_url": obj.get("url") or page_url,
                "location": loc,
                "modality": modality,
                "seniority": infer_seniority(title, desc),
                "salary_range_text": None,
                "benefits": [],
                "published_at": None,
                "requirements": extract_requirements(desc),
            })
    return jobs


def fetch_jsonld_jobs(page_url: str, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
    with httpx.Client(timeout=15.0, follow_redirects=True, headers={"User-Agent": "CareerHunterAI/1.0"}) as client:
        resp = client.get(page_url)
        resp.raise_for_status()
        return extract_jsonld_jobs_from_html(resp.text, str(resp.url), company_name=company_name)


def fetch_remotive_jobs(search_query: str, limit: int = 15) -> List[Dict[str, Any]]:
    url = "https://remotive.com/api/remote-jobs"
    with httpx.Client(timeout=15.0, headers={"User-Agent": "CareerHunterAI/1.0"}) as client:
        resp = client.get(url, params={"search": search_query, "limit": limit})
        resp.raise_for_status()
        payload = resp.json()

    jobs: List[Dict[str, Any]] = []
    for item in payload.get("jobs", [])[:limit]:
        title = (item.get("title") or "").strip()
        if not title:
            continue
        desc = strip_html(item.get("description"))
        jobs.append({
            "external_id": str(item.get("id")),
            "company_name": (item.get("company_name") or "Empresa").strip(),
            "title": title,
            "description": desc or title,
            "original_url": item.get("url") or "https://remotive.com",
            "location": item.get("candidate_required_location") or "Remoto",
            "modality": "remoto",
            "seniority": infer_seniority(title, desc),
            "salary_range_text": item.get("salary") or None,
            "benefits": [],
            "published_at": None,
            "requirements": extract_requirements(desc),
        })
    return jobs
