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
        return ""

    def _render_act2_strategy(self) -> str:
        return ""

    def _render_act3_product(self) -> str:
        return ""

    def _render_act4_plan(self) -> str:
        return ""
