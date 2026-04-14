"""Read product_lines/ markdown context files and serve them as structured JSON."""

import re
import logging
from pathlib import Path

from server.services.context_index import (
    CANONICAL_SECTIONS,
    _score_completeness,
    _extract_last_updated,
)

logger = logging.getLogger(__name__)

SKIP_DIRS = {"_company", "_shared"}

# Section heading patterns that map to UI content fields
STRATEGY_HEADINGS = {"bl strategy", "strategy"}
PERSONA_HEADINGS = {"customer segments", "personas"}
COMPETITOR_HEADINGS = {"competitors"}
GOALS_HEADINGS = {"jobs to be done", "jtbd"}
VOC_HEADINGS = {"key pain points", "voice of customer"}
METRICS_HEADINGS = {"unit economics", "bl performance", "platform capabilities"}


class MarkdownContextReader:
    """Reads _context.md files from product_lines/ and returns structured JSON."""

    def __init__(self, product_lines_dir: Path):
        self.root = product_lines_dir

    # --- Public API ---

    def list_layers(self, layer_type: str | None = None) -> list[dict]:
        """Walk the product_lines tree and return summary metadata for each layer."""
        layers = []
        self._collect_layers(layers)
        if layer_type:
            layers = [l for l in layers if l["layer_type"] == layer_type]
        return layers

    def get_layer(self, layer_type: str, name: str) -> dict | None:
        """Return full parsed context for a specific layer."""
        path = self._resolve_path(layer_type, name)
        if path is None or not path.exists():
            return None
        return self._parse_context_md(path, layer_type, name)

    # --- Layer discovery ---

    def _collect_layers(self, layers: list[dict]):
        """Enumerate all context layers in the tree."""
        # Company
        company_ctx = self.root / "_company" / "_context.md"
        if company_ctx.exists():
            layers.append(self._summary("company", "global", "company-global", "Company", company_ctx))

        # Company countries
        company_countries = self.root / "_company" / "countries"
        if company_countries.is_dir():
            for c in sorted(company_countries.iterdir()):
                if c.is_dir() and not c.name.startswith(".") and (c / "_context.md").exists():
                    layers.append(self._summary("country", "country", f"country-{c.name}", c.name.upper(), c / "_context.md"))

        # Business lines
        for bl_dir in sorted(self.root.iterdir()):
            if not bl_dir.is_dir() or bl_dir.name in SKIP_DIRS or bl_dir.name.startswith("."):
                continue
            bl_ctx = bl_dir / "_context.md"
            if bl_ctx.exists():
                layers.append(self._summary("bl", "business_line", f"bl-{bl_dir.name}", bl_dir.name, bl_ctx))
            # BL countries
            bl_countries = bl_dir / "countries"
            if bl_countries.is_dir():
                for c in sorted(bl_countries.iterdir()):
                    if c.is_dir() and not c.name.startswith(".") and (c / "_context.md").exists():
                        layers.append(self._summary(
                            "bl-country", "business_line_country",
                            f"bl-country-{bl_dir.name}-{c.name}",
                            f"{bl_dir.name} ({c.name.upper()})",
                            c / "_context.md",
                        ))

    def _summary(self, layer_type: str, type_: str, id_: str, name: str, path: Path) -> dict:
        """Build a summary dict (for list_layers)."""
        text = path.read_text()
        filled, total = _score_completeness(text)
        status = "sufficient" if filled >= total * 0.7 else "gaps_identified"
        return {
            "id": id_,
            "type": type_,
            "name": name,
            "layer_type": layer_type,
            "file_name": path.stem,
            "sufficiency": {"status": status, "gaps": []},
        }

    def _resolve_path(self, layer_type: str, name: str) -> Path | None:
        """Map layer_type + name to a filesystem path."""
        if layer_type in ("company", "_company"):
            return self.root / "_company" / "_context.md"
        if layer_type == "country":
            return self.root / "_company" / "countries" / name / "_context.md"
        if layer_type == "bl":
            return self.root / name / "_context.md"
        if layer_type == "bl-country":
            # name format: "bl_name-country_name" e.g. "groceries-uae"
            parts = name.split("-", 1)
            if len(parts) == 2:
                return self.root / parts[0] / "countries" / parts[1] / "_context.md"
        # Fallback: raw directory name from agent tool-call detection
        # e.g. layer_type="groceries", name="_context"
        candidate = self.root / layer_type / (name + ".md")
        if candidate.exists():
            return candidate
        country_candidate = self.root / "_company" / "countries" / layer_type / (name + ".md")
        if country_candidate.exists():
            return country_candidate
        return None

    # --- Full parsing ---

    def _parse_context_md(self, path: Path, layer_type: str, name: str) -> dict:
        """Parse a _context.md into the JSON structure the UI expects."""
        text = path.read_text()
        sections = self._extract_sections(text)
        content = self._map_to_content(sections)
        sufficiency = self._compute_sufficiency(text)
        sources = self._extract_sources(text)

        return {
            "id": f"{layer_type}-{name}",
            "type": self._type_for(layer_type),
            "name": name,
            "content": content,
            "sufficiency": sufficiency,
            "sources": sources,
            "markdown_body": text,
            "created_at": None,
            "updated_at": _extract_last_updated(text),
        }

    def _type_for(self, layer_type: str) -> str:
        return {
            "company": "global",
            "_company": "global",
            "country": "country",
            "bl": "business_line",
            "bl-country": "business_line_country",
        }.get(layer_type, layer_type)

    # --- Section extraction ---

    def _extract_sections(self, text: str) -> dict[str, str]:
        """Split markdown by ## headings into {heading_lower: body} dict."""
        sections = {}
        current_heading = None
        current_lines = []

        for line in text.split("\n"):
            m = re.match(r"^##\s+(.+)", line)
            if m:
                if current_heading is not None:
                    sections[current_heading] = "\n".join(current_lines).strip()
                current_heading = m.group(1).strip().lower()
                # Normalize: remove parenthetical like "(BL-wide)"
                current_heading = re.sub(r"\s*\(.*?\)\s*$", "", current_heading)
                current_lines = []
            elif current_heading is not None:
                current_lines.append(line)

        if current_heading is not None:
            sections[current_heading] = "\n".join(current_lines).strip()

        return sections

    def _map_to_content(self, sections: dict[str, str]) -> dict:
        """Map parsed sections to the JSON fields the UI expects."""
        content = {}

        # product_overview / strategy — partial match on section keys
        for key in sections:
            if any(h in key for h in STRATEGY_HEADINGS):
                content["product_overview"] = sections[key]
                if "strategy" == key:
                    content["strategy"] = sections[key]
                break

        # personas from Customer Segments table
        for heading in PERSONA_HEADINGS:
            if heading in sections:
                rows = self._parse_markdown_table(sections[heading])
                content["personas"] = [
                    {"name": r.get("Segment", r.get("Name", "")), "description": r.get("Description", "")}
                    for r in rows
                ]
                break

        # competitors
        for heading in COMPETITOR_HEADINGS:
            matched = [k for k in sections if heading in k]
            for key in matched:
                rows = self._parse_markdown_table(sections[key])
                content["competitors"] = [
                    {
                        "name": r.get("Competitor", r.get("Name", "")),
                        "positioning": r.get("Model", r.get("Positioning", "")),
                        "strengths": [r["Strength"]] if r.get("Strength") else [],
                        "weaknesses": [r["Weakness"]] if r.get("Weakness") else [],
                    }
                    for r in rows
                ]
                break

        # goals from JTBD
        for heading in GOALS_HEADINGS:
            if heading in sections:
                content["goals"] = self._parse_numbered_list(sections[heading])
                break

        # voice_of_customer
        for heading in VOC_HEADINGS:
            matched = [k for k in sections if heading in k.lower() or any(h in k for h in VOC_HEADINGS)]
            for key in matched:
                content["voice_of_customer"] = self._parse_voc(sections[key])
                break

        # org_metrics from Unit Economics / BL Performance
        for heading in METRICS_HEADINGS:
            matched = [k for k in sections if heading in k]
            for key in matched:
                rows = self._parse_markdown_table(sections[key])
                if rows:
                    # First data column as value
                    content["org_metrics"] = [
                        {"name": r.get("Metric", r.get("Capability", list(r.values())[0] if r else "")),
                         "value": list(r.values())[1] if len(r) > 1 else ""}
                        for r in rows
                    ]
                break

        return content

    # --- Parsers ---

    def _parse_markdown_table(self, text: str) -> list[dict]:
        """Parse a markdown table into a list of dicts."""
        lines = [l.strip() for l in text.split("\n") if l.strip().startswith("|")]
        if len(lines) < 3:  # header + separator + at least one row
            return []

        # Parse header
        headers = [h.strip() for h in lines[0].split("|")[1:-1]]

        # Skip separator (lines[1])
        rows = []
        for line in lines[2:]:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))

        return rows

    def _parse_numbered_list(self, text: str) -> list[str]:
        """Parse numbered list items, preserving bold markers."""
        items = []
        for line in text.split("\n"):
            m = re.match(r"^\d+\.\s+(.+)", line.strip())
            if m:
                # Strip markdown bold wrappers but keep the text
                item = m.group(1).strip()
                items.append(item)
        return items

    def _parse_voc(self, text: str) -> dict:
        """Parse VoC section with love/frustration/wishes/churn_signals subsections."""
        voc = {"love": [], "frustration": [], "wishes": [], "churn_signals": []}

        current_key = None
        for line in text.split("\n"):
            lower = line.lower().strip()
            if "love" in lower and (lower.startswith("**") or lower.startswith("#")):
                current_key = "love"
            elif "frustrat" in lower and (lower.startswith("**") or lower.startswith("#")):
                current_key = "frustration"
            elif "wish" in lower and (lower.startswith("**") or lower.startswith("#")):
                current_key = "wishes"
            elif "churn" in lower and (lower.startswith("**") or lower.startswith("#")):
                current_key = "churn_signals"
            elif ("breaks trust" in lower or "break" in lower) and (lower.startswith("**") or lower.startswith("#")):
                current_key = "frustration"
            elif current_key and (line.strip().startswith("-") or line.strip().startswith("1.")):
                # Strip list marker
                item = re.sub(r"^[-\d.]+\s*", "", line.strip())
                if item:
                    voc[current_key].append(item)

        return voc

    # --- Sufficiency & sources ---

    def _compute_sufficiency(self, text: str) -> dict:
        """Compute sufficiency from section completeness."""
        filled, total = _score_completeness(text)
        if filled >= total * 0.8:
            status = "sufficient"
        elif filled >= total * 0.4:
            status = "gaps_identified"
        else:
            status = "insufficient"

        gaps = []
        text_lower = text.lower()
        for section in CANONICAL_SECTIONS:
            pattern = rf"^#{{2,3}}\s+.*{re.escape(section.lower())}"
            if not re.search(pattern, text_lower, re.MULTILINE):
                gaps.append({
                    "field": section.lower().replace(" ", "_"),
                    "severity": "important",
                    "description": f"Missing '{section}' section",
                })

        return {"status": status, "gaps": gaps}

    def _extract_sources(self, text: str) -> list[dict]:
        """Parse ### Sources section into list of source dicts."""
        # Find the ### Sources section
        m = re.search(r"^###\s+Sources\s*\n(.*?)(?=^###|\Z)", text, re.MULTILINE | re.DOTALL)
        if not m:
            return []

        sources = []
        for line in m.group(1).split("\n"):
            line = line.strip()
            if line.startswith("-"):
                item = line.lstrip("- ").strip()
                # Try to extract "Type — Name, Date" pattern
                parts = re.split(r"\s*[—–-]\s*", item, maxsplit=1)
                source_type = "document"
                name = item
                if len(parts) == 2:
                    source_type = self._guess_source_type(parts[0])
                    name = parts[1]
                sources.append({
                    "type": source_type,
                    "name": name,
                    "description": "",
                })

        return sources

    def _guess_source_type(self, prefix: str) -> str:
        """Guess source type from prefix text."""
        p = prefix.lower().strip()
        if "drive" in p or "google" in p:
            return "document"
        if "bigquery" in p or "bq" in p:
            return "bigquery"
        if "slack" in p:
            return "slack"
        if "gmail" in p:
            return "document"
        if "looker" in p:
            return "dashboard"
        if "eppo" in p:
            return "analytics"
        if "interview" in p:
            return "interview"
        return "document"
