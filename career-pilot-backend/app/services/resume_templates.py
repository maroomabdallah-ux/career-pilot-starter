# ruff: noqa: E501
from __future__ import annotations

import re
from html import escape
from typing import Any

TEMPLATES = {
    "careerpilot_classic": {"id":"careerpilot_classic","name":"CareerPilot Classic","categories":["ats","professional"],"tier":"free","supports_resume":True,"supports_cv":True},
    "clear_ats": {"id":"clear_ats","name":"Clear ATS","categories":["ats","simple"],"tier":"free","supports_resume":True,"supports_cv":True},
    "horizon": {"id":"horizon","name":"Horizon","categories":["modern","professional"],"tier":"free","supports_resume":True,"supports_cv":True},
    "nova_tech": {"id":"nova_tech","name":"Nova Tech","categories":["tech","modern"],"tier":"free","supports_resume":True,"supports_cv":False},
    "executive_line": {"id":"executive_line","name":"Executive Line","categories":["executive","professional"],"tier":"free","supports_resume":True,"supports_cv":True},
    "minimal_edge": {"id":"minimal_edge","name":"Minimal Edge","categories":["simple","professional"],"tier":"free","supports_resume":True,"supports_cv":True},
    "dual_focus": {"id":"dual_focus","name":"Dual Focus","categories":["two_column","modern"],"tier":"free","supports_resume":True,"supports_cv":True},
    "graduate_launch": {"id":"graduate_launch","name":"Graduate Launch","categories":["entry_level","modern"],"tier":"free","supports_resume":True,"supports_cv":False},
    "slate_column": {"id":"slate_column","name":"Slate Column","categories":["two_column","professional"],"tier":"free","supports_resume":True,"supports_cv":True},
    "atlas": {"id":"atlas","name":"Atlas","categories":["professional","executive"],"tier":"free","supports_resume":True,"supports_cv":True},
    "cedar": {"id":"cedar","name":"Cedar","categories":["simple","professional"],"tier":"free","supports_resume":True,"supports_cv":True},
    "pulse": {"id":"pulse","name":"Pulse","categories":["modern","tech"],"tier":"free","supports_resume":True,"supports_cv":False},
    "academic_crest": {"id":"academic_crest","name":"Academic Crest","categories":["professional","simple"],"tier":"free","supports_resume":True,"supports_cv":True},
    "metro": {"id":"metro","name":"Metro","categories":["two_column","creative","modern"],"tier":"free","supports_resume":True,"supports_cv":False},
    "keystone": {"id":"keystone","name":"Keystone","categories":["executive","ats"],"tier":"free","supports_resume":True,"supports_cv":True},
}
LEGACY_TEMPLATE_IDS = {"ats_classic":"careerpilot_classic","ats_modern":"horizon","premium_minimal":"minimal_edge"}


def get_template(template_id: str | None) -> dict[str, Any]:
    template_id = LEGACY_TEMPLATE_IDS.get(template_id or "", template_id)
    return TEMPLATES.get(template_id or "", TEMPLATES["careerpilot_classic"])


class TemplateAccessService:
    def can_preview(self, template_id: str) -> bool:
        return bool(get_template(template_id))

    def can_export(self, template_id: str, user) -> bool:
        template = get_template(template_id)
        if template["tier"] == "free":
            return True
        return bool(getattr(user, "has_premium", False))


def _text(value):
    return escape(str(value or ""))


def _link(url, label):
    return f'<a href="{_text(url)}">{_text(label)}</a>' if url else ""


def _rich(value):
    """Render the editor's small Markdown subset after escaping all source text."""
    text = _text(value)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__([^_]+)__", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "<br>".join(lines)


def render_resume_html(content: dict, template_id: str) -> str:
    template = get_template(template_id)
    header = content.get("header", {})
    contact = " · ".join(
        filter(None, [header.get("email"), header.get("phone"), header.get("location")])
    )
    links = " · ".join(
        filter(
            None,
            [
                _link(header.get("linkedin"), "LinkedIn"),
                _link(header.get("github"), "GitHub"),
                _link(header.get("portfolio"), "Portfolio"),
            ],
        )
    )
    sections = []
    summary = content.get("summary")
    if summary:
        sections.append(("summary", "Professional Summary", f"<p>{_rich(summary)}</p>"))
    exp = "".join(
        f'<article><div class="row"><h3>{_text(x.get("job_title"))} · {_text(x.get("company"))}</h3><time>{_text(x.get("start_date"))} – {_text(x.get("end_date") or ("Present" if x.get("is_current") else ""))}</time></div><p class="meta">{_text(x.get("location"))}</p><ul>{"".join(f"<li>{_rich(b)}</li>" for b in x.get("bullets", []))}</ul></article>'
        for x in content.get("experience", [])
        if x.get("visible", True)
    )
    if exp:
        sections.append(("experience", "Experience", exp))
    edu = "".join(
        f'<article><div class="row"><h3>{_text(x.get("degree"))}{" in " + _text(x.get("field_of_study")) if x.get("field_of_study") else ""}</h3><time>{_text(x.get("start_date"))} – {_text(x.get("end_date"))}</time></div><p>{_text(x.get("institution"))}</p><p class="meta">{_text(x.get("grade"))}</p><p>{_rich(x.get("description"))}</p></article>'
        for x in content.get("education", [])
        if x.get("visible", True)
    )
    if edu:
        sections.append(("education", "Education", edu))
    projects = "".join(
        f'<article><h3>{_text(x.get("name"))}{" · " + _text(x.get("role")) if x.get("role") else ""}</h3><p>{_rich(x.get("description"))}</p><ul>{"".join(f"<li>{_rich(b)}</li>" for b in x.get("bullets", []))}</ul><p class="meta">{_text(" · ".join(x.get("technologies", [])))}</p><p>{_link(x.get("project_url"), "Project")} {_link(x.get("repository_url"), "Repository")}</p></article>'
        for x in content.get("projects", [])
        if x.get("visible", True)
    )
    if projects:
        sections.append(("projects", "Projects", projects))
    skills = "".join(
        f"<p><strong>{_text(x.get('category'))}:</strong> {_text(', '.join(x.get('items', [])))}</p>"
        for x in content.get("skill_groups", [])
        if x.get("visible", True)
    )
    if skills:
        sections.append(("skills", "Skills", skills))
    order = content.get("section_order") or [x[0] for x in sections]
    by_id = {key: (title, body) for key, title, body in sections}
    body = "".join(
        f"<section><h2>{title}</h2>{html}</section>"
        for key in order
        if key not in set(content.get("hidden_sections", [])) and key in by_id
        for title, html in [by_id[key]]
    )
    styles = {
        "careerpilot_classic":"--accent:#17233c;--font:Arial,sans-serif;--head:uppercase;--rule:2px",
        "clear_ats":"--accent:#111827;--font:Arial,sans-serif;--head:uppercase;--rule:1px",
        "horizon":"--accent:#1769d2;--font:Arial,sans-serif;--head:uppercase;--rule:1px",
        "nova_tech":"--accent:#075985;--font:Arial,sans-serif;--head:uppercase;--rule:3px",
        "executive_line":"--accent:#3f342d;--font:Georgia,serif;--head:none;--rule:1px",
        "minimal_edge":"--accent:#14395b;--font:Georgia,serif;--head:none;--rule:1px",
        "dual_focus":"--accent:#24556f;--font:Arial,sans-serif;--head:uppercase;--rule:2px",
        "graduate_launch":"--accent:#2563eb;--font:Arial,sans-serif;--head:uppercase;--rule:4px",
        "slate_column":"--accent:#334155;--font:Arial,sans-serif;--head:uppercase;--rule:3px",
        "atlas":"--accent:#263c5a;--font:Arial,sans-serif;--head:uppercase;--rule:5px",
        "cedar":"--accent:#6b5c45;--font:Georgia,serif;--head:none;--rule:1px",
        "pulse":"--accent:#0f766e;--font:Arial,sans-serif;--head:uppercase;--rule:3px",
        "academic_crest":"--accent:#653c50;--font:Georgia,serif;--head:none;--rule:1px",
        "metro":"--accent:#4338ca;--font:Arial,sans-serif;--head:uppercase;--rule:4px",
        "keystone":"--accent:#1e3a5f;--font:Arial,sans-serif;--head:uppercase;--rule:2px",
    }[template["id"]]
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
    @page{{size:A4;margin:14mm 16mm}}*{{box-sizing:border-box}}body{{{styles};font-family:var(--font);color:#17233c;font-size:10pt;line-height:1.45;margin:0}}header{{border-bottom:var(--rule) solid var(--accent);padding-bottom:12px;margin-bottom:18px}}h1{{font-size:25pt;margin:0;color:var(--accent)}}header strong{{font-size:11pt}}header p{{margin:5px 0 0}}a{{color:var(--accent);text-decoration:none}}section{{break-inside:auto;margin:0 0 16px}}h2{{break-after:avoid;font-size:10pt;text-transform:var(--head);letter-spacing:.1em;color:var(--accent);border-bottom:1px solid #ccd9e5;padding-bottom:4px;margin:0 0 9px}}article{{break-inside:avoid;margin:0 0 10px}}h3{{font-size:10pt;margin:0}}p{{margin:3px 0}}ul{{margin:4px 0;padding-left:18px}}li{{margin:2px 0}}.row{{display:flex;justify-content:space-between;gap:15px}}time,.meta{{color:#607086;font-size:8.5pt}}.premium_minimal header{{padding:18px;background:#f0f7fc;border:0}}.premium_minimal h2{{font-size:12pt;text-transform:none;letter-spacing:.03em}} 
    .minimal_edge header{{padding:18px;background:#f0f7fc;border:0}}.minimal_edge h2,.executive_line h2{{font-size:12pt;text-transform:none;letter-spacing:.03em}}
    .horizon header,.graduate_launch header{{background:var(--accent);color:white;padding:18px}}.horizon header h1,.graduate_launch header h1{{color:white}}.nova_tech header{{border-left:8px solid var(--accent);padding-left:16px}}.executive_line header{{text-align:center;border-top:1px solid var(--accent)}}
    </style></head><body class="{template["id"]}"><header><h1>{_text(header.get("full_name"))}</h1><strong>{_text(header.get("professional_title"))}</strong><p>{_text(contact)}</p><p>{links}</p></header>{body}</body></html>'''
