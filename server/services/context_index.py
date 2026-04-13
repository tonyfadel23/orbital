"""Generate a health dashboard INDEX.md for the product_lines context tree."""

import re
from datetime import datetime
from pathlib import Path

CANONICAL_SECTIONS = [
    "BL Strategy",
    "Jobs to Be Done",
    "Customer Segments",
    "Competitors",
    "Unit Economics",
    "Trade-offs",
    "Experiment History",
    "Sources",
    "Propagation History",
]

SKIP_DIRS = {"_company", "_shared"}


def _score_completeness(text: str) -> tuple[int, int]:
    """Count how many canonical sections are present in a _context.md file."""
    total = len(CANONICAL_SECTIONS)
    text_lower = text.lower()
    filled = 0
    for section in CANONICAL_SECTIONS:
        # Match heading containing the section name anywhere (case insensitive)
        pattern = rf"^#{{2,3}}\s+.*{re.escape(section.lower())}"
        if re.search(pattern, text_lower, re.MULTILINE):
            filled += 1
    return filled, total


def _extract_last_updated(text: str) -> str | None:
    """Parse the '> Last updated: ...' line from a _context.md file."""
    match = re.search(r">\s*Last updated:\s*(.+)", text)
    return match.group(1).strip() if match else None


def _detect_staleness(date_str: str | None, threshold_days: int = 30) -> bool:
    """Return True if the date is older than threshold_days or missing."""
    if not date_str:
        return True
    # Parse common formats: "April 2026", "March 2026", "January 2025"
    for fmt in ("%B %Y", "%b %Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return (datetime.now() - dt).days > threshold_days
        except ValueError:
            continue
    return True  # unparseable = stale


def generate_index(product_lines_dir: Path) -> str:
    """Generate a markdown health dashboard for all business lines."""
    lines = [
        "# Product Lines — Context Health Index",
        f"> Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Business Lines",
        "",
        "| BL | Sections | Last Updated | WIKI | _sources/ | Links |",
        "|----|----------|-------------|------|-----------|-------|",
    ]

    stale_alerts = []
    bls = []

    for bl_dir in sorted(product_lines_dir.iterdir()):
        if not bl_dir.is_dir() or bl_dir.name in SKIP_DIRS or bl_dir.name.startswith("."):
            continue

        context_path = bl_dir / "_context.md"
        if not context_path.exists():
            continue

        text = context_path.read_text()
        filled, total = _score_completeness(text)
        last_updated = _extract_last_updated(text)
        is_stale = _detect_staleness(last_updated)
        has_wiki = (bl_dir / "WIKI.md").exists()
        has_sources = (bl_dir / "_sources").is_dir()

        wiki_col = f"[WIKI]({bl_dir.name}/WIKI.md)" if has_wiki else "-"
        sources_col = "Y" if has_sources else "-"
        link = f"[context]({bl_dir.name}/_context.md)"

        lines.append(
            f"| {bl_dir.name} | {filled}/{total} | {last_updated or 'unknown'} | {wiki_col} | {sources_col} | {link} |"
        )

        if is_stale:
            stale_alerts.append(f"- `{bl_dir.name}/_context.md` — last updated: {last_updated or 'unknown'}")

        bls.append(bl_dir.name)

    lines.append("")

    if stale_alerts:
        lines.append("## Staleness Alerts")
        lines.append("")
        lines.extend(stale_alerts)
        lines.append("")

    # Coverage matrix — countries, okrs, trees
    lines.append("## Coverage Matrix")
    lines.append("")
    lines.append("| BL | _context.md | countries/ | okrs/ | trees/ | WIKI.md | _sources/ |")
    lines.append("|----|-------------|-----------|-------|--------|---------|-----------|")

    for bl_name in bls:
        bl_dir = product_lines_dir / bl_name
        has_context = (bl_dir / "_context.md").exists()
        countries = list((bl_dir / "countries").iterdir()) if (bl_dir / "countries").is_dir() else []
        country_count = len([c for c in countries if c.is_dir() and not c.name.startswith(".")])
        has_okrs = (bl_dir / "okrs").is_dir()
        has_trees = (bl_dir / "trees").is_dir()
        has_wiki = (bl_dir / "WIKI.md").exists()
        has_sources = (bl_dir / "_sources").is_dir()

        lines.append(
            f"| {bl_name} | {'Y' if has_context else '-'} "
            f"| {country_count if country_count else '-'} "
            f"| {'Y' if has_okrs else '-'} "
            f"| {'Y' if has_trees else '-'} "
            f"| {'Y' if has_wiki else '-'} "
            f"| {'Y' if has_sources else '-'} |"
        )

    lines.append("")
    return "\n".join(lines)
