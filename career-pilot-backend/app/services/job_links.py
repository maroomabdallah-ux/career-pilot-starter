from datetime import UTC, datetime

import httpx

from app.schemas.job import JobResult

CLOSED_MARKERS = (
    "job is no longer available",
    "position has been filled",
    "posting has expired",
    "job has been removed",
)


async def validate_job_link(job: JobResult) -> JobResult:
    """Best-effort validation; access controls never become false dead-link reports."""
    checked = job.model_copy(deep=True)
    checked.link_checked_at = datetime.now(UTC)
    if checked.normalized_status in {"closed", "expired"} or checked.expired:
        checked.link_status = "expired"
        return checked
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=8) as client:
            response = await client.get(
                str(checked.apply_url), headers={"User-Agent": "CareerPilot-LinkCheck/1.0"}
            )
        if response.status_code in {404, 410}:
            checked.link_status = "invalid"
        elif response.status_code in {401, 403, 429}:
            checked.link_status = "restricted"
        elif response.status_code >= 500:
            checked.link_status = "unverified"
        elif any(marker in response.text[:100_000].casefold() for marker in CLOSED_MARKERS):
            checked.link_status = "expired"
            checked.normalized_status = "closed"
        elif 200 <= response.status_code < 400:
            checked.link_status = "valid"
        else:
            checked.link_status = "unverified"
    except (httpx.HTTPError, ValueError):
        checked.link_status = "unverified"
    return checked
