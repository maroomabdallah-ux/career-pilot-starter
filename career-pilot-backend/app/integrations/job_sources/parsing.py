import re
from html import unescape

HTML = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")
KNOWN_SKILLS = (
    "Python", "Java", "JavaScript", "TypeScript", "React", "Angular", "Vue", "Node.js",
    "FastAPI", "Django", "Flask", "Spring Boot", "SQL", "PostgreSQL", "MySQL",
    "MongoDB", "Redis", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
    "Git", "REST", "GraphQL", "Machine Learning", "LangChain",
)


def plain_text(value: str | None) -> str:
    return SPACE.sub(" ", unescape(HTML.sub(" ", value or ""))).strip()


def extract_skills(value: str | None) -> list[str]:
    text = (value or "").casefold()
    return [skill for skill in KNOWN_SKILLS if _contains(text, skill)]


def _contains(text: str, skill: str) -> bool:
    token = re.escape(skill.casefold())
    return bool(re.search(rf"(?<![\w+#]){token}(?![\w+#])", text))


def infer_experience_level(title: str, description: str | None = None) -> str | None:
    text = f"{title} {description or ''}".casefold()
    for level, words in (
        ("internship", ("intern", "internship", "graduate")),
        ("junior", ("junior", "entry level", "entry-level", "associate")),
        ("senior", ("senior", "staff", "principal", "lead ", "manager", "director")),
    ):
        if any(word in text for word in words):
            return level
    return None


def infer_workplace(value: str | None) -> str:
    text = (value or "").casefold()
    if "hybrid" in text:
        return "hybrid"
    if "remote" in text:
        return "remote"
    if "on-site" in text or "onsite" in text:
        return "on-site"
    return "unknown"
