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

    def _render_act3_product(self) -> str:
        return ""

    def _render_act4_plan(self) -> str:
        return ""
