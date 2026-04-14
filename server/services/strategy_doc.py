"""Strategy document builder — produces a self-contained HTML strategy one-pager."""

import html


class StrategyDocBuilder:
    def __init__(self, workspace: dict, votes: list[dict], prototypes: dict[str, str]):
        self.opp = workspace.get("opportunity", {})
        self.synthesis = workspace.get("synthesis") or {}
        self.contributions = workspace.get("contributions", [])
        self.votes = votes
        self.prototypes = prototypes  # {filename: html_content}

    def build(self) -> str:
        return self._wrap_document(
            self._render_act1_problem(),
            self._render_act2_strategy(),
            self._render_act3_product(),
            self._render_act4_plan(),
        )

    def _wrap_document(self, act1: str, act2: str, act3: str, act4: str) -> str:
        title = html.escape(self.opp.get("title", "Strategy Document"))
        acts = [
            ("act-1", "The Problem", act1),
            ("act-2", "The Strategy", act2),
            ("act-3", "The Product", act3),
            ("act-4", "The Plan", act4),
        ]
        sections = "\n".join(
            f'<section id="{aid}" class="act"><div class="act-label">{label}</div>{content}</section>'
            for aid, label, content in acts
        )
        return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>{self._css()}</style>
</head><body>
<nav class="dot-toc">{self._dot_toc_html()}</nav>
<main>{sections}</main>
<script>{self._js()}</script>
</body></html>"""

    def _dot_toc_html(self) -> str:
        labels = ["Problem", "Strategy", "Product", "Plan"]
        return "".join(
            f'<a class="dot-toc__dot" href="#act-{i+1}" title="{l}"><span></span></a>'
            for i, l in enumerate(labels)
        )

    # Stub methods for Phase 1 — will be implemented in later tasks
    def _css(self) -> str:
        return ""

    def _js(self) -> str:
        return ""

    def _render_act1_problem(self) -> str:
        return ""

    def _render_act2_strategy(self) -> str:
        return ""

    def _render_act3_product(self) -> str:
        return ""

    def _render_act4_plan(self) -> str:
        return ""
