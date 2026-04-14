"""Strategy document builder — produces a self-contained HTML strategy one-pager."""

import html
import re


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

    def _css(self) -> str:
        return """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg: #0a0c12;
  --surface: rgba(22, 25, 35, 0.95);
  --surface-hover: rgba(30, 34, 48, 0.95);
  --border: rgba(255, 255, 255, 0.06);
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent: #3B82F6;
  --green: #10B981;
  --amber: #F59E0B;
  --red: #EF4444;
  --purple: #A855F7;
  --radius: 8px;
  --font-sans: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--text-primary);
  font-family: var(--font-sans);
  line-height: 1.6;
}

main { max-width: 960px; margin: 0 auto; }

.act { padding: 80px 24px; }

.act-label {
  font-family: var(--font-mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--text-muted);
  margin-bottom: 24px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
}

.solution-row {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 32px;
  margin-bottom: 40px;
}

.phone-frame {
  width: 280px;
  border: 3px solid #2a2d3a;
  border-radius: 32px;
  padding: 12px 8px;
  background: #1a1d28;
  position: relative;
  margin: 0 auto;
}

.phone-frame::before {
  content: '';
  position: absolute;
  top: 6px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 20px;
  background: #2a2d3a;
  border-radius: 0 0 12px 12px;
  z-index: 1;
}

.phone-frame__screen {
  border-radius: 24px;
  overflow: hidden;
  background: #fff;
  height: 480px;
}

.phone-frame__screen iframe {
  width: 100%;
  height: 100%;
  border: 0;
}

.collapsible-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 16px;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 14px;
  font-family: var(--font-sans);
}

.collapsible-toggle::after {
  content: '\25B8';
  transition: transform 0.3s ease;
}

.collapsible-toggle.open::after {
  transform: rotate(90deg);
}

.collapsible-panel {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.dot-toc {
  position: fixed;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 100;
}

.dot-toc__dot { text-decoration: none; }

.dot-toc__dot span {
  display: block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--text-muted);
  transition: all 0.3s ease;
}

.dot-toc__dot.active span {
  background: var(--accent);
  border-color: var(--accent);
}

.carousel {
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  display: flex;
  gap: 24px;
  padding-bottom: 16px;
}

.carousel__slide {
  scroll-snap-align: start;
  flex: 0 0 auto;
  width: calc(100% - 48px);
}

.carousel__nav {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
}

.carousel__btn {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  cursor: pointer;
  color: var(--text-primary);
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.bar {
  height: 6px;
  border-radius: 3px;
  background: var(--border);
}

.bar__fill {
  height: 100%;
  border-radius: 3px;
}

.context-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.signal-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.signal-list li {
  padding: 8px 0;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.signal-list li::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.signal--success::before { background: var(--green); }
.signal--kill::before { background: var(--red); }

h1 { font-size: 32px; line-height: 1.2; margin: 0 0 16px; }
h2 { font-size: 22px; margin: 32px 0 16px; color: var(--text-primary); }
h3 { font-size: 16px; margin: 24px 0 12px; color: var(--text-secondary); }
p { margin: 0 0 12px; color: var(--text-secondary); }

.heat-map { display: grid; gap: 4px; }

.heat-map__cell {
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
  text-align: center;
}

.conditions-table { width: 100%; border-collapse: collapse; }

.conditions-table th,
.conditions-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.conditions-table th {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

@media (max-width: 768px) {
  .solution-row { grid-template-columns: 1fr; }
  .dot-toc { display: none; }
  .act { padding: 40px 16px; }
}
"""

    def _js(self) -> str:
        return """
document.addEventListener('DOMContentLoaded', () => {
  const dots = document.querySelectorAll('.dot-toc__dot');
  const acts = document.querySelectorAll('.act');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        dots.forEach(d => d.classList.toggle('active', d.getAttribute('href') === '#' + id));
      }
    });
  }, { rootMargin: '-40% 0px -40% 0px', threshold: 0 });
  acts.forEach(a => observer.observe(a));
  dots.forEach(d => d.addEventListener('click', e => {
    e.preventDefault();
    document.getElementById(d.getAttribute('href').slice(1)).scrollIntoView({ behavior: 'smooth' });
  }));

  document.querySelectorAll('.collapsible-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const panel = btn.nextElementSibling;
      btn.classList.toggle('open');
      if (btn.classList.contains('open')) {
        panel.style.maxHeight = panel.scrollHeight + 'px';
      } else {
        panel.style.maxHeight = '0';
      }
    });
  });

  document.querySelectorAll('.carousel__btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const track = btn.closest('.carousel-container').querySelector('.carousel');
      const direction = btn.dataset.dir === 'next' ? 1 : -1;
      const slideWidth = track.querySelector('.carousel__slide').offsetWidth + 24;
      track.scrollBy({ left: direction * slideWidth, behavior: 'smooth' });
    });
  });
});
"""

    @staticmethod
    def _sanitize_html(content: str) -> str:
        """Strip dangerous HTML: scripts, event handlers, javascript: URLs."""
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'\bon\w+\s*=\s*"[^"]*"', '', content, flags=re.IGNORECASE)
        content = re.sub(r"\bon\w+\s*=\s*'[^']*'", '', content, flags=re.IGNORECASE)
        content = re.sub(r'javascript\s*:', '', content, flags=re.IGNORECASE)
        return content

    def _render_act1_problem(self) -> str:
        parts: list[str] = []
        esc = html.escape

        # --- Hero ---
        title = esc(self.opp.get("title", ""))
        if title:
            parts.append(f"<h1>{title}</h1>")

        opp_type = self.opp.get("type", "")
        if opp_type:
            parts.append(
                f'<span class="badge" style="background:var(--accent);color:#fff">'
                f"{esc(opp_type)}</span>"
            )

        description = esc(self.opp.get("description", ""))
        if description:
            parts.append(f"<p>{description}</p>")

        # --- Context Grid ---
        extracted = self.opp.get("extracted_context") or []
        if extracted:
            parts.append("<h2>Context</h2>")
            # Group by category
            grouped: dict[str, list[dict]] = {}
            for item in extracted:
                cat = item.get("category", "other")
                grouped.setdefault(cat, []).append(item)

            parts.append('<div class="context-grid">')
            for category, facts in grouped.items():
                parts.append('<div class="card">')
                parts.append(f"<h3>{esc(category.replace('_', ' ').title())}</h3>")
                for fact_item in facts:
                    parts.append('<div style="margin-bottom:12px">')
                    parts.append(
                        f'<div style="color:var(--text-primary)">'
                        f'{esc(fact_item.get("fact", ""))}</div>'
                    )
                    value = fact_item.get("value")
                    if value:
                        parts.append(
                            f'<span class="badge" style="background:var(--accent);color:#fff">'
                            f"{esc(str(value))}</span>"
                        )
                    source = fact_item.get("source_layer", "")
                    if source:
                        parts.append(
                            f'<div style="color:var(--text-muted);font-size:12px">'
                            f"{esc(source)}</div>"
                        )
                    parts.append("</div>")
                parts.append("</div>")
            parts.append("</div>")

        # --- Assumptions ---
        assumptions = self.opp.get("assumptions") or []
        if assumptions:
            status_colors = {
                "supported": "var(--green)",
                "untested": "var(--amber)",
                "contradicted": "var(--red)",
            }
            importance_colors = {
                "critical": "#EF4444",
                "high": "#F59E0B",
                "medium": "#3B82F6",
                "low": "#64748B",
            }
            parts.append("<h2>Assumptions</h2>")
            for asm in assumptions:
                importance = asm.get("importance", "medium")
                status = asm.get("status", "untested")
                border_color = importance_colors.get(importance, "#64748B")
                badge_color = status_colors.get(status, "var(--amber)")
                parts.append(
                    f'<div class="card" style="border-left:3px solid {border_color}">'
                )
                parts.append(
                    '<div style="display:flex;justify-content:space-between;align-items:center">'
                )
                parts.append(
                    f'<span style="color:var(--text-primary)">'
                    f'{esc(asm.get("content", ""))}</span>'
                )
                parts.append(
                    f'<span class="badge" style="background:{badge_color};color:#fff">'
                    f"{esc(status)}</span>"
                )
                parts.append("</div></div>")

        # --- Signals ---
        success = self.opp.get("success_signals") or []
        kill = self.opp.get("kill_signals") or []
        if success or kill:
            parts.append("<h2>Signals</h2>")
            parts.append(
                '<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">'
            )
            # Success
            parts.append("<div><h3>Success Signals</h3>")
            if success:
                parts.append('<ul class="signal-list">')
                for sig in success:
                    parts.append(f'<li class="signal--success">{esc(sig)}</li>')
                parts.append("</ul>")
            parts.append("</div>")
            # Kill
            parts.append("<div><h3>Kill Signals</h3>")
            if kill:
                parts.append('<ul class="signal-list">')
                for sig in kill:
                    parts.append(f'<li class="signal--kill">{esc(sig)}</li>')
                parts.append("</ul>")
            parts.append("</div>")
            parts.append("</div>")

        return "\n".join(parts)

    def _render_act2_strategy(self) -> str:
        esc = html.escape
        parts: list[str] = []

        if not self.synthesis:
            parts.append('<p class="muted">No investigation data yet.</p>')
            return "\n".join(parts)

        # --- Color mappings ---
        rec_colors = {
            "proceed": "#10B981",
            "pivot": "#F59E0B",
            "kill": "#EF4444",
            "need_more_data": "#64748B",
        }
        severity_colors = {
            "critical": "#EF4444",
            "notable": "#F59E0B",
            "minor": "#64748B",
        }

        # --- Verdict Banner ---
        verdict_summary = self.synthesis.get("verdict_summary", "")
        recommendation = self.synthesis.get("recommendation", "")
        if verdict_summary or recommendation:
            rec_color = rec_colors.get(recommendation, "#64748B")
            parts.append(
                f'<div class="card" style="border-left:4px solid {rec_color};padding:24px">'
            )
            if verdict_summary:
                parts.append(
                    f'<div style="font-size:20px;font-weight:600;color:var(--text-primary);margin-bottom:8px">'
                    f"{esc(verdict_summary)}</div>"
                )
            if recommendation:
                parts.append(
                    f'<span class="badge" style="background:{rec_color};color:#fff">'
                    f"{esc(recommendation)}</span>"
                )
            parts.append("</div>")

        # --- Evidence Summary ---
        evidence = self.synthesis.get("evidence_summary") or {}
        if evidence:
            parts.append("<h2>Evidence</h2>")
            parts.append('<div class="card">')
            total = evidence.get("total_findings", 0)
            parts.append(
                f'<div style="font-size:28px;font-weight:700;color:var(--text-primary)">'
                f"{total} findings</div>"
            )
            by_function = evidence.get("by_function") or {}
            if by_function:
                sorted_fns = sorted(by_function.items(), key=lambda x: x[1], reverse=True)
                max_count = max(by_function.values()) if by_function else 1
                for fn, count in sorted_fns:
                    pct = (count / max_count) * 100 if max_count > 0 else 0
                    parts.append('<div style="margin:8px 0">')
                    parts.append(
                        '<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
                    )
                    parts.append(
                        f'<span style="color:var(--text-secondary);font-size:13px">{esc(fn)}</span>'
                    )
                    parts.append(
                        f'<span style="color:var(--text-muted);font-size:13px">{count}</span>'
                    )
                    parts.append("</div>")
                    parts.append(
                        f'<div class="bar"><div class="bar__fill" style="width:{pct:.0f}%;background:var(--accent)"></div></div>'
                    )
                    parts.append("</div>")

            strongest = evidence.get("strongest_signal", "")
            if strongest:
                parts.append(
                    '<div style="margin-top:16px;padding:12px;background:rgba(16,185,129,0.1);border-radius:var(--radius)">'
                )
                parts.append(
                    '<div style="color:var(--green);font-size:12px;font-weight:600;margin-bottom:4px">STRONGEST SIGNAL</div>'
                )
                parts.append(
                    f'<div style="color:var(--text-primary)">{esc(strongest)}</div>'
                )
                parts.append("</div>")

            strongest_counter = evidence.get("strongest_counter_signal", "")
            if strongest_counter:
                parts.append(
                    '<div style="margin-top:8px;padding:12px;background:rgba(239,68,68,0.1);border-radius:var(--radius)">'
                )
                parts.append(
                    '<div style="color:var(--red);font-size:12px;font-weight:600;margin-bottom:4px">STRONGEST COUNTER-SIGNAL</div>'
                )
                parts.append(
                    f'<div style="color:var(--text-primary)">{esc(strongest_counter)}</div>'
                )
                parts.append("</div>")

            parts.append("</div>")

        # --- Convergence ---
        convergence = self.synthesis.get("convergence") or []
        if convergence:
            parts.append("<h2>Where Agents Agree</h2>")
            for item in convergence:
                finding = esc(item.get("finding", ""))
                agent_count = item.get("agent_count", 0)
                sources = item.get("sources") or []
                parts.append('<div class="card">')
                parts.append(
                    '<div style="display:flex;justify-content:space-between;align-items:center">'
                )
                parts.append(
                    f'<span style="color:var(--text-primary)">{finding}</span>'
                )
                parts.append(
                    f'<span class="badge" style="background:var(--accent);color:#fff">'
                    f"{agent_count} agents</span>"
                )
                parts.append("</div>")
                if sources:
                    parts.append(
                        f'<div style="color:var(--text-muted);font-size:12px;margin-top:4px">'
                        f"{esc(', '.join(sources))}</div>"
                    )
                parts.append("</div>")

        # --- Counter-Signals ---
        counter_signals = self.synthesis.get("counter_signals") or []
        if counter_signals:
            parts.append("<h2>Counter-Signals</h2>")
            for cs in counter_signals:
                summary = esc(cs.get("summary", ""))
                severity = cs.get("severity", "minor")
                addressed = cs.get("addressed", False)
                sev_color = severity_colors.get(severity, "#64748B")
                parts.append(
                    f'<div class="card" style="border-left:3px solid {sev_color}">'
                )
                parts.append(
                    '<div style="display:flex;justify-content:space-between;align-items:center">'
                )
                parts.append(
                    f'<span style="color:var(--text-primary)">{summary}</span>'
                )
                parts.append(
                    f'<span class="badge" style="background:{sev_color};color:#fff">'
                    f"{esc(severity)}</span>"
                )
                parts.append("</div>")
                addr_text = "\u2713 Addressed" if addressed else "\u26a0 Unaddressed"
                parts.append(
                    f'<div style="color:var(--text-muted);font-size:12px;margin-top:4px">'
                    f"{addr_text}</div>"
                )
                parts.append("</div>")

        # --- Conflicts ---
        conflicts = self.synthesis.get("conflicts") or []
        if conflicts:
            parts.append("<h2>Conflicts</h2>")
            for conflict in conflicts:
                topic = esc(conflict.get("topic", ""))
                side_a = conflict.get("side_a") or {}
                side_b = conflict.get("side_b") or {}
                resolution = esc(conflict.get("resolution", ""))

                parts.append('<div class="card">')
                parts.append(f'<h3 style="margin-top:0">{topic}</h3>')
                parts.append(
                    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">'
                )

                # Side A
                a_agents = ", ".join(side_a.get("agents") or [])
                a_position = esc(side_a.get("position", ""))
                a_evidence = esc(side_a.get("evidence", ""))
                parts.append(
                    '<div style="padding:12px;background:rgba(59,130,246,0.1);border-radius:var(--radius)">'
                )
                parts.append(
                    f'<div style="color:var(--accent);font-size:12px;font-weight:600;margin-bottom:4px">'
                    f"SIDE A \u2014 {esc(a_agents)}</div>"
                )
                parts.append(
                    f'<div style="color:var(--text-primary)">{a_position}</div>'
                )
                if a_evidence:
                    parts.append(
                        f'<div style="color:var(--text-muted);font-size:12px;margin-top:4px">'
                        f"{a_evidence}</div>"
                    )
                parts.append("</div>")

                # Side B
                b_agents = ", ".join(side_b.get("agents") or [])
                b_position = esc(side_b.get("position", ""))
                b_evidence = esc(side_b.get("evidence", ""))
                parts.append(
                    '<div style="padding:12px;background:rgba(168,85,247,0.1);border-radius:var(--radius)">'
                )
                parts.append(
                    f'<div style="color:var(--purple);font-size:12px;font-weight:600;margin-bottom:4px">'
                    f"SIDE B \u2014 {esc(b_agents)}</div>"
                )
                parts.append(
                    f'<div style="color:var(--text-primary)">{b_position}</div>'
                )
                if b_evidence:
                    parts.append(
                        f'<div style="color:var(--text-muted);font-size:12px;margin-top:4px">'
                        f"{b_evidence}</div>"
                    )
                parts.append("</div>")

                parts.append("</div>")  # grid

                if resolution:
                    parts.append(
                        f'<div style="color:var(--text-secondary);margin-top:12px;font-style:italic">'
                        f"Resolution: {resolution}</div>"
                    )
                parts.append("</div>")  # card

        return "\n".join(parts)

    def _match_prototype(self, sol_id: str, sol_title: str) -> str | None:
        slug = re.sub(r'[^a-z0-9]+', '-', sol_title.lower()).strip('-')
        for fname, content in self.prototypes.items():
            if sol_id in fname or slug in fname:
                return self._sanitize_html(content)
        return None

    def _render_act3_product(self) -> str:
        solutions = self.synthesis.get("solutions", [])
        if not solutions:
            return '<p style="color:var(--text-muted)">No solutions yet.</p>'

        dot_vote = self.synthesis.get("dot_vote_summary", {})
        heat_map = dot_vote.get("heat_map", {})
        counter_signals = self.synthesis.get("counter_signals", [])

        parts = ['<h2>Solutions</h2>']
        for sol in solutions:
            parts.append(self._render_solution_row(sol, heat_map, counter_signals))

        # Compound plays carousel
        compound = [s for s in solutions if len(s.get("depends_on", [])) >= 2]
        if compound:
            parts.append(self._render_compound_carousel(compound, solutions))

        return "\n".join(parts)

    def _render_solution_row(self, sol: dict, heat_map: dict, counter_signals: list) -> str:
        esc = html.escape
        sol_id = sol.get("id", "")
        title = esc(sol.get("title", ""))
        description = esc(sol.get("description", ""))
        archetype = sol.get("archetype", "")
        recommendation = sol.get("recommendation", "")
        ice = sol.get("ice_score", {})
        impact = ice.get("impact", 0)
        confidence = ice.get("confidence", 0)
        ease = ice.get("ease", 0)
        total = ice.get("total", 0)
        proceed_conditions = sol.get("proceed_conditions") or []
        evidence_refs = sol.get("evidence_refs") or []
        solution_quality = sol.get("solution_quality") or {}

        # Color mappings
        arch_colors = {"incremental": "#10B981", "moderate": "#3B82F6", "ambitious": "#A855F7"}
        rec_colors = {"proceed": "#10B981", "proceed_if": "#F59E0B", "defer": "#64748B", "kill": "#EF4444"}
        sev_colors = {"critical": "#EF4444", "notable": "#F59E0B", "minor": "#64748B"}

        arch_color = arch_colors.get(archetype, "#64748B")
        rec_color = rec_colors.get(recommendation, "#64748B")

        # Match prototype
        prototype_html = self._match_prototype(sol_id, sol.get("title", ""))

        # Determine grid columns
        grid_cols = "1fr 320px" if prototype_html else "1fr"

        parts = [f'<div class="solution-row" style="grid-template-columns:{grid_cols}">']

        # --- Left column ---
        parts.append('<div>')
        parts.append(f'<span class="badge" style="background:{arch_color};color:#fff">{esc(archetype)}</span>')
        parts.append(f'<span class="badge" style="background:{rec_color};color:#fff;margin-left:8px">{esc(recommendation)}</span>')
        parts.append(f'<h3 style="margin-top:12px">{title}</h3>')
        parts.append(f'<p>{description}</p>')

        # ICE mini-bars
        parts.append('<div style="margin:16px 0">')
        for dim_name, dim_val in [("Impact", impact), ("Confidence", confidence), ("Ease", ease)]:
            pct = dim_val * 10
            parts.append('<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">')
            parts.append(f'<span style="width:80px;color:var(--text-muted);font-size:12px">{dim_name}</span>')
            parts.append(f'<div class="bar" style="flex:1"><div class="bar__fill" style="width:{pct}%;background:var(--accent)"></div></div>')
            parts.append(f'<span style="color:var(--text-secondary);font-size:13px;width:24px">{dim_val}</span>')
            parts.append('</div>')
        parts.append(f'<div style="color:var(--text-muted);font-size:12px;margin-top:4px">Total: {total}</div>')
        parts.append('</div>')

        # Heat Map
        sol_has_heat = any(sol_id in scores for scores in heat_map.values())
        if sol_has_heat:
            parts.append(f'<div class="heat-map" style="grid-template-columns:120px repeat(1, 1fr);margin:16px 0">')
            for agent_fn, scores in heat_map.items():
                score = scores.get(sol_id)
                if score is not None:
                    if score >= 7:
                        score_bg = "rgba(16,185,129,0.2)"
                    elif score >= 5:
                        score_bg = "rgba(59,130,246,0.2)"
                    else:
                        score_bg = "rgba(239,68,68,0.2)"
                    parts.append(f'<div class="heat-map__cell" style="color:var(--text-muted);text-align:left">{esc(agent_fn)}</div>')
                    parts.append(f'<div class="heat-map__cell" style="background:{score_bg}">{score}</div>')
            parts.append('</div>')

        # Collapsible panels

        # Panel 1: Proceed Conditions
        if proceed_conditions:
            parts.append('<button class="collapsible-toggle">Proceed Conditions</button>')
            parts.append('<div class="collapsible-panel">')
            parts.append('<div style="padding:12px 0">')
            parts.append('<table class="conditions-table">')
            parts.append('<thead><tr><th>Condition</th><th>Measurement</th><th>Threshold</th></tr></thead>')
            parts.append('<tbody>')
            for cond in proceed_conditions:
                parts.append(f'<tr><td>{esc(cond.get("condition", ""))}</td>'
                             f'<td>{esc(cond.get("measurement", ""))}</td>'
                             f'<td>{esc(cond.get("threshold", ""))}</td></tr>')
            parts.append('</tbody></table>')
            parts.append('</div></div>')

        # Panel 2: Evidence
        if evidence_refs:
            parts.append('<button class="collapsible-toggle">Evidence</button>')
            parts.append('<div class="collapsible-panel">')
            parts.append('<div style="padding:12px 0">')
            parts.append('<ul style="margin:0;padding-left:16px;color:var(--text-secondary)">')
            for ref in evidence_refs:
                parts.append(f'<li>{esc(ref)}</li>')
            parts.append('</ul>')
            parts.append('</div></div>')

        # Panel 3: Economics
        parts.append('<button class="collapsible-toggle">Economics</button>')
        parts.append('<div class="collapsible-panel">')
        parts.append('<div style="padding:12px 0;color:var(--text-secondary)">')
        parts.append(f'<div>Impact: {impact}/10 · Confidence: {confidence}/10 · Ease: {ease}/10</div>')
        parts.append(f'<div style="margin-top:8px">ICE Total: {total}</div>')
        if solution_quality:
            eg = solution_quality.get("evidence_grounding", 0)
            dist = solution_quality.get("distinctiveness", 0)
            parts.append(f'<div style="margin-top:8px">Evidence grounding: {eg:.0%} · Distinctiveness: {dist:.0%}</div>')
        parts.append('</div></div>')

        # Panel 4: Risks
        parts.append('<button class="collapsible-toggle">Risks</button>')
        parts.append('<div class="collapsible-panel">')
        parts.append('<div style="padding:12px 0">')
        for cs in counter_signals:
            summary = esc(cs.get("summary", ""))
            severity = cs.get("severity", "minor")
            sev_color = sev_colors.get(severity, "#64748B")
            parts.append(f'<div style="margin-bottom:8px">')
            parts.append(f'<span class="badge" style="background:{sev_color};color:#fff">{esc(severity)}</span>')
            parts.append(f'<span style="color:var(--text-secondary);margin-left:8px">{summary}</span>')
            parts.append('</div>')
        # Vote flags for this solution
        for vote_entry in self.votes:
            voter_fn = vote_entry.get("voter_function", "")
            for v in vote_entry.get("votes", []):
                if v.get("solution_id") == sol_id:
                    for flag in v.get("flags") or []:
                        parts.append(f'<div style="color:var(--amber);font-size:13px">\u26a0 {esc(flag)} (from {esc(voter_fn)})</div>')
        parts.append('</div></div>')

        parts.append('</div>')  # end left column

        # --- Right column: phone frame ---
        if prototype_html:
            escaped_proto = html.escape(prototype_html)
            parts.append('<div>')
            parts.append('<div class="phone-frame">')
            parts.append('<div class="phone-frame__screen">')
            parts.append(f'<iframe srcdoc="{escaped_proto}" sandbox="allow-same-origin"></iframe>')
            parts.append('</div></div></div>')

        parts.append('</div>')  # end solution-row

        return "\n".join(parts)

    def _render_compound_carousel(self, compound: list, all_solutions: list) -> str:
        esc = html.escape
        sol_map = {s.get("id", ""): s.get("title", "") for s in all_solutions}

        parts = ['<h2>Compound Plays</h2>']
        parts.append('<div class="carousel-container">')
        parts.append('<div class="carousel__nav">')
        parts.append('<button class="carousel__btn" data-dir="prev">\u2190</button>')
        parts.append('<button class="carousel__btn" data-dir="next">\u2192</button>')
        parts.append('</div>')
        parts.append('<div class="carousel">')
        for sol in compound:
            title = esc(sol.get("title", ""))
            description = esc(sol.get("description", ""))
            deps = sol.get("depends_on", [])
            dep_titles = [esc(sol_map.get(d, d)) for d in deps]
            dep_str = " + ".join(dep_titles)
            parts.append('<div class="carousel__slide">')
            parts.append('<div class="card">')
            parts.append(f'<h3>{title}</h3>')
            parts.append(f'<p>{description}</p>')
            parts.append(f'<div style="color:var(--text-muted);font-size:13px">Depends on: {dep_str}</div>')
            parts.append('</div></div>')
        parts.append('</div></div>')

        return "\n".join(parts)

    def _render_act4_plan(self) -> str:
        if not self.synthesis:
            return '<p style="color:var(--text-muted)">No plan data yet.</p>'

        parts: list[str] = []
        rec = self.synthesis.get("recommendation", "")
        rec_colors = {"proceed": "#10B981", "pivot": "#F59E0B", "kill": "#EF4444", "need_more_data": "#64748B"}
        rec_color = rec_colors.get(rec, "#64748B")

        # 1. Recommendation Card
        verdict = html.escape(self.synthesis.get("verdict_summary", ""))
        rationale = html.escape(self.synthesis.get("rationale", ""))
        if verdict:
            parts.append(f'''<div class="card" style="border-left:4px solid {rec_color};padding:24px 24px 16px">
<div style="font-size:24px;font-weight:700;color:var(--text-primary);margin-bottom:8px">{verdict}</div>
<span class="badge" style="background:{rec_color};color:#fff">{html.escape(rec)}</span>
{f'<p style="margin-top:16px;color:var(--text-secondary);line-height:1.6">{rationale}</p>' if rationale else ''}
</div>''')

        # 2. Impact & Effort (side by side)
        impact = html.escape(self.synthesis.get("expected_impact", ""))
        effort = html.escape(self.synthesis.get("estimated_effort", ""))
        if impact or effort:
            parts.append('<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:16px 0">')
            if impact:
                parts.append(f'''<div class="card">
<div style="color:var(--green);font-size:12px;font-weight:600;margin-bottom:8px">EXPECTED IMPACT</div>
<div style="color:var(--text-primary)">{impact}</div>
</div>''')
            if effort:
                parts.append(f'''<div class="card">
<div style="color:var(--accent);font-size:12px;font-weight:600;margin-bottom:8px">ESTIMATED EFFORT</div>
<div style="color:var(--text-primary)">{effort}</div>
</div>''')
            parts.append('</div>')

        # 3. Consensus Ranking
        solutions = self.synthesis.get("solutions", [])
        sol_map = {s["id"]: s for s in solutions}
        ranking = self.synthesis.get("dot_vote_summary", {}).get("consensus_ranking", [])
        arch_colors = {"incremental": "#10B981", "moderate": "#3B82F6", "ambitious": "#A855F7"}

        if ranking:
            parts.append('<h2>Consensus Ranking</h2>')
            for i, sol_id in enumerate(ranking):
                sol = sol_map.get(sol_id, {})
                title = html.escape(sol.get("title", sol_id))
                arch = sol.get("archetype", "")
                total = sol.get("ice_score", {}).get("total", "")
                ac = arch_colors.get(arch, "#64748B")
                parts.append(f'''<div class="card" style="display:flex;align-items:center;gap:16px">
<div style="font-size:24px;font-weight:700;color:var(--text-muted);width:32px">{i+1}</div>
<div style="flex:1">
  <span style="color:var(--text-primary);font-weight:600">{title}</span>
  <span class="badge" style="background:{ac};color:#fff;margin-left:8px">{html.escape(arch)}</span>
</div>
<div style="color:var(--text-muted);font-size:13px">ICE {total}</div>
</div>''')

        # 4. Recommended Sequence (visual chain)
        seq = self.synthesis.get("recommended_sequence", [])
        if seq:
            parts.append('<h2>Recommended Sequence</h2>')
            parts.append('<div style="display:flex;align-items:center;flex-wrap:wrap;gap:0">')
            for j, sid in enumerate(seq):
                sol = sol_map.get(sid, {})
                title = html.escape(sol.get("title", sid))
                arch = sol.get("archetype", "")
                ac = arch_colors.get(arch, "#64748B")
                deps = sol.get("depends_on", [])
                dep_text = ""
                if deps:
                    dep_names = [html.escape(sol_map.get(d, {}).get("title", d)) for d in deps]
                    dep_text = f'<div style="color:var(--text-muted);font-size:11px;margin-top:4px">After: {", ".join(dep_names)}</div>'
                parts.append(f'''<div class="card" style="flex:0 0 auto;text-align:center;min-width:140px">
<div style="color:{ac};font-size:12px;font-weight:600;text-transform:uppercase">{html.escape(arch)}</div>
<div style="color:var(--text-primary);font-weight:600;margin-top:4px">{title}</div>
{dep_text}
</div>''')
                if j < len(seq) - 1:
                    parts.append('<div style="color:var(--text-muted);font-size:20px;padding:0 8px">\u2192</div>')
            parts.append('</div>')

        # 5. Proceed Conditions (aggregate from all solutions)
        all_conditions: list[dict] = []
        for sol in solutions:
            for cond in sol.get("proceed_conditions", []):
                all_conditions.append(cond)
        if all_conditions:
            parts.append('<h2>Proceed Conditions</h2>')
            parts.append('''<table class="conditions-table"><thead><tr>
<th>Condition</th><th>Measurement</th><th>Threshold</th>
</tr></thead><tbody>''')
            for c in all_conditions:
                parts.append(f'''<tr>
<td style="color:var(--text-primary)">{html.escape(c.get("condition", ""))}</td>
<td style="color:var(--text-secondary)">{html.escape(c.get("measurement", ""))}</td>
<td style="color:var(--text-secondary)">{html.escape(c.get("threshold", ""))}</td>
</tr>''')
            parts.append('</tbody></table>')

        # 6. Quality Scores (5 horizontal bars)
        qs = self.synthesis.get("quality_score", {})
        if qs:
            parts.append('<h2>Investigation Quality</h2>')
            parts.append('<div class="card">')
            labels = {
                "assumption_coverage": "Assumption Coverage",
                "evidence_balance": "Evidence Balance",
                "conflict_surfacing": "Conflict Surfacing",
                "artifact_relevance": "Artifact Relevance",
                "overall": "Overall",
            }
            for key, label in labels.items():
                val = qs.get(key, 0)
                pct = round(val * 100)
                parts.append(f'''<div style="margin-bottom:12px">
<div style="display:flex;justify-content:space-between;margin-bottom:4px">
  <span style="color:var(--text-secondary);font-size:13px">{label}</span>
  <span style="color:var(--text-muted);font-size:13px">{pct}%</span>
</div>
<div class="bar"><div class="bar__fill" style="width:{pct}%;background:var(--accent)"></div></div>
</div>''')
            parts.append('</div>')

        return "\n".join(parts)
