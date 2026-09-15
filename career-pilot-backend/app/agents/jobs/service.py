import re

REMOTE = ("remote", "عن بعد", "ريموت")
HYBRID = ("hybrid", "هجين")
ONSITE = ("on-site", "onsite", "مكتبي", "من المكتب")
LEVELS = {
    "junior": ("junior", "entry", "مبتدئ", "جونيور"),
    "internship": ("intern", "internship", "تدريب", "متدرب"),
    "senior": ("senior", "سينيور", "خبير"),
}
KNOWN_LOCATIONS = {
    "amman": "Amman",
    "عمان": "Amman",
    "عمّان": "Amman",
    "jordan": "Jordan",
    "الأردن": "Jordan",
    "الاردن": "Jordan",
    "montreal": "Montreal",
    "canada": "Canada",
    "berlin": "Berlin",
    "germany": "Germany",
    "europe": "Europe",
}


def is_job_search_request(message: str) -> bool:
    return bool(
        re.search(
            r"(?:\b(?:find|search|show|look for)\b.*\b(?:job|jobs|role|roles)\b|"
            r"\bjobs?\b|وظائف|وظيفة|شغل|دورلي)",
            message,
            re.I,
        )
    )


def understand_job_search(message: str) -> dict:
    """Extract conservative bilingual criteria without inventing missing preferences."""
    text = " ".join(message.split())
    folded = text.casefold()
    workplace = None
    if any(value in folded for value in REMOTE):
        workplace = "remote"
    elif any(value in folded for value in HYBRID):
        workplace = "hybrid"
    elif any(value in folded for value in ONSITE):
        workplace = "on-site"
    level = next(
        (key for key, words in LEVELS.items() if any(word in folded for word in words)), None
    )
    date_posted = (
        "24h"
        if any(x in folded for x in ("today", "24h", "اليوم"))
        else "7d"
        if any(x in folded for x in ("this week", "7d", "هالأسبوع", "هذا الأسبوع"))
        else "30d"
        if any(x in folded for x in ("this month", "30d", "هذا الشهر"))
        else None
    )
    location = next(
        (canonical for alias, canonical in KNOWN_LOCATIONS.items() if alias in folded), None
    )
    employment = next(
        (value for value in ("full-time", "part-time", "contract") if value in folded), None
    )
    query = _query(text)
    if re.search(r"\b(محاسبة|محاسب|محاسبين)\b", query):
        query = "Accountant"
    generic = not query or query.casefold() in {"jobs", "job", "work", "وظائف", "شغل"}
    return {
        "query": None if generic else query,
        "location": location,
        "workplace_type": workplace,
        "employment_type": employment,
        "experience_level": level,
        "date_posted": date_posted,
    }


def _query(text: str) -> str:
    cleaned = re.sub(
        r"\b(find|show|search|me|for|jobs?|roles?|in|near|posted|this|week|remote|hybrid|on-?site|please)\b",
        " ",
        text,
        flags=re.I,
    )
    cleaned = re.sub(r"(دورلي|ابحث|عن|وظائف|شغل|مناسب|لمهاراتي|إلي|الي|بدي)", " ", cleaned)
    cleaned = re.sub(
        r"\b(Amman|Jordan|Montreal|Canada|Berlin|Germany|Europe)\b|"
        r"(?:ب|في\s*)?(?:عمان|عمّان|الأردن|الاردن)",
        " ",
        cleaned,
        flags=re.I,
    )
    return " ".join(cleaned.split())[:200]
