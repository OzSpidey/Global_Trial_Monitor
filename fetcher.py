"""Fetches clinical trial data from ClinicalTrials.gov API v2."""
import requests
import time
from config import DISEASE_AREAS, MAX_PER_DISEASE

BASE_URL   = "https://clinicaltrials.gov/api/v2/studies"
PAGE_SIZE  = 100
RETRY_WAIT = 2   # seconds between retries on transient errors


def _parse_date(raw: str | None) -> str | None:
    """Normalise YYYY-MM or YYYY-MM-DD to YYYY-MM-DD, return None on failure."""
    if not raw:
        return None
    raw = raw.strip()
    try:
        parts = raw.split("-")
        if len(parts) == 2:
            return f"{parts[0]}-{parts[1]}-01"
        if len(parts) == 3:
            return raw
    except Exception:
        pass
    return None


def _extract_row(study: dict, disease_area: str) -> dict:
    """Flatten a raw ClinicalTrials.gov study JSON object into a flat dict."""
    ps   = study.get("protocolSection") or {}
    idm  = ps.get("identificationModule") or {}
    stm  = ps.get("statusModule") or {}
    dsm  = ps.get("designModule") or {}
    cond = ps.get("conditionsModule") or {}
    spm  = ps.get("sponsorCollaboratorsModule") or {}
    clm  = ps.get("contactsLocationsModule") or {}
    desc = ps.get("descriptionModule") or {}

    phases_raw = dsm.get("phases") or []
    phase = phases_raw[0] if phases_raw else "NA"

    locations = clm.get("locations") or []
    countries  = sorted(set(
        loc["country"] for loc in locations if loc.get("country")
    ))

    start_raw      = (stm.get("startDateStruct") or {}).get("date")
    completion_raw = (stm.get("primaryCompletionDateStruct") or {}).get("date")

    return {
        "nct_id":          idm.get("nctId"),
        "title":           idm.get("briefTitle"),
        "status":          stm.get("overallStatus"),
        "phase":           phase,
        "disease_area":    disease_area,
        "conditions":      cond.get("conditions") or [],
        "sponsor":         (spm.get("leadSponsor") or {}).get("name"),
        "countries":       countries,
        "start_date":      _parse_date(start_raw),
        "completion_date": _parse_date(completion_raw),
        "study_type":      dsm.get("studyType"),
        "brief_summary":   desc.get("briefSummary"),
    }


def fetch_studies(query: str, max_results: int = MAX_PER_DISEASE) -> list[dict]:
    """Fetch up to max_results raw study dicts from ClinicalTrials.gov for a query."""
    results   = []
    page_token = None
    fetched    = 0

    while fetched < max_results:
        batch = min(PAGE_SIZE, max_results - fetched)
        params = {
            "query.cond": query,
            "pageSize":   batch,
            "format":     "json",
        }
        if page_token:
            params["pageToken"] = page_token

        try:
            resp = requests.get(BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"[fetcher] API error for query '{query}': {exc}")
            time.sleep(RETRY_WAIT)
            break

        studies = data.get("studies") or []
        results.extend(studies)
        fetched += len(studies)

        page_token = data.get("nextPageToken")
        if not page_token or not studies:
            break

    return results


def fetch_all_disease_areas(
    progress_cb=None,
    max_per: int = MAX_PER_DISEASE,
) -> list[dict]:
    """Fetch and flatten studies for every disease area in DISEASE_AREAS."""
    all_rows = []
    areas    = list(DISEASE_AREAS.items())
    total    = len(areas)

    for idx, (area_name, query) in enumerate(areas, start=1):
        print(f"[fetcher] Fetching {area_name} ({idx}/{total}) ...")
        try:
            raw_studies = fetch_studies(query, max_results=max_per)
            for study in raw_studies:
                try:
                    row = _extract_row(study, area_name)
                    if row["nct_id"]:   # skip studies without an ID
                        all_rows.append(row)
                except Exception as exc:
                    print(f"[fetcher] Row parse error: {exc}")
        except Exception as exc:
            print(f"[fetcher] Failed area {area_name}: {exc}")

        if progress_cb:
            try:
                progress_cb(area_name, idx, total)
            except Exception:
                pass

    # Deduplicate by nct_id (keep latest disease_area assignment)
    seen: dict[str, dict] = {}
    for row in all_rows:
        seen[row["nct_id"]] = row
    deduped = list(seen.values())

    print(f"[fetcher] Done. {len(deduped)} unique studies across {total} areas.")
    return deduped
