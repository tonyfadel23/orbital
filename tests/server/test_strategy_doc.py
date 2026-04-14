"""Tests for StrategyDocBuilder — Task 1: skeleton + document shell."""

import re

import pytest

from server.services.strategy_doc import StrategyDocBuilder


@pytest.fixture
def minimal_workspace():
    return {
        "opportunity": {
            "id": "opp-20260410-090000",
            "title": "Improve checkout conversion",
            "description": "Users drop off at the payment step.",
        },
        "synthesis": None,
        "contributions": [],
    }


@pytest.fixture
def builder(minimal_workspace):
    return StrategyDocBuilder(
        workspace=minimal_workspace,
        votes=[],
        prototypes={},
    )


class TestBuildReturnsHtmlString:
    def test_build_returns_html_string(self, builder):
        result = builder.build()
        assert isinstance(result, str)
        assert len(result) > 0


class TestHtmlHasDoctype:
    def test_html_has_doctype(self, builder):
        result = builder.build()
        assert result.startswith("<!DOCTYPE html>")


class TestHtmlContainsTitle:
    def test_html_contains_title_in_title_tag(self, builder):
        result = builder.build()
        assert "<title>Improve checkout conversion</title>" in result

    def test_html_contains_title_with_special_chars(self):
        workspace = {
            "opportunity": {"title": 'Risk & "Reward" <Analysis>'},
            "contributions": [],
        }
        b = StrategyDocBuilder(workspace=workspace, votes=[], prototypes={})
        result = b.build()
        # HTML-escaped version must appear in <title>
        assert "Risk &amp; &quot;Reward&quot; &lt;Analysis&gt;" in result


class TestHtmlHasFourActSections:
    def test_html_has_four_act_sections(self, builder):
        result = builder.build()
        for i in range(1, 5):
            assert f'id="act-{i}"' in result, f"Missing section act-{i}"

    def test_acts_have_class(self, builder):
        result = builder.build()
        for i in range(1, 5):
            assert f'id="act-{i}" class="act"' in result


class TestHtmlIsSelfContained:
    def test_no_external_script_src(self, builder):
        result = builder.build()
        # No <script src="..."> allowed
        assert not re.search(r'<script\s+src=', result)

    def test_no_external_stylesheet_link(self, builder):
        result = builder.build()
        # No <link rel="stylesheet" href="..."> allowed
        # Google Fonts @import inside <style> is OK
        assert not re.search(r'<link\s[^>]*rel=["\']stylesheet["\'][^>]*href=', result)


class TestHtmlHasDotToc:
    def test_dot_toc_class_present(self, builder):
        result = builder.build()
        assert 'class="dot-toc"' in result

    def test_dot_toc_has_four_dots(self, builder):
        result = builder.build()
        dots = re.findall(r'class="dot-toc__dot"', result)
        assert len(dots) == 4

    def test_dot_toc_links_to_acts(self, builder):
        result = builder.build()
        for i in range(1, 5):
            assert f'href="#act-{i}"' in result


class TestCssCustomProperties:
    def test_css_contains_custom_properties(self, builder):
        result = builder.build()
        for prop in ["--bg", "--surface", "--text-primary"]:
            assert prop in result, f"Missing CSS custom property {prop}"


class TestCssResponsive:
    def test_css_contains_responsive_breakpoint(self, builder):
        result = builder.build()
        assert "768px" in result


class TestCssPhoneFrame:
    def test_css_phone_frame_class(self, builder):
        result = builder.build()
        assert ".phone-frame" in result


class TestCssCollapsible:
    def test_css_collapsible_classes(self, builder):
        result = builder.build()
        assert ".collapsible-toggle" in result
        assert ".collapsible-panel" in result


class TestJsIntersectionObserver:
    def test_js_has_intersection_observer(self, builder):
        result = builder.build()
        assert "IntersectionObserver" in result


class TestJsCollapsibleHandler:
    def test_js_has_collapsible_handler(self, builder):
        result = builder.build()
        assert "collapsible-toggle" in result


class TestJsCarouselScroll:
    def test_js_has_carousel_scroll(self, builder):
        result = builder.build()
        assert "scrollBy" in result


class TestSanitizeHtml:
    def test_sanitize_removes_script_tags(self):
        result = StrategyDocBuilder._sanitize_html('<div>safe</div><script>alert(1)</script>')
        assert '<script' not in result
        assert 'alert(1)' not in result
        assert '<div>safe</div>' in result

    def test_sanitize_removes_event_handlers(self):
        result = StrategyDocBuilder._sanitize_html('<button onclick="alert(1)">Click</button>')
        assert 'onclick' not in result
        assert '<button' in result
        assert 'Click</button>' in result

    def test_sanitize_removes_javascript_urls(self):
        result = StrategyDocBuilder._sanitize_html('<a href="javascript:alert(1)">Link</a>')
        assert 'javascript' not in result.lower()
        assert '<a' in result

    def test_sanitize_preserves_safe_html(self):
        safe = '<div class="container"><p>Hello</p><img src="photo.jpg" alt="test"></div>'
        result = StrategyDocBuilder._sanitize_html(safe)
        assert result == safe

    def test_sanitize_handles_multiline_script(self):
        content = '<div>before</div><script>\nvar x = 1;\nalert(x);\n</script><div>after</div>'
        result = StrategyDocBuilder._sanitize_html(content)
        assert '<script' not in result
        assert '<div>before</div>' in result
        assert '<div>after</div>' in result


# --- Act 1 fixtures and tests ---


@pytest.fixture
def rich_workspace():
    return {
        "opportunity": {
            "id": "opp-20260410-090000",
            "title": "HMW make fresh groceries a habitual purchase on tMart?",
            "description": "Users buy groceries once but don't return. We need to understand why.",
            "type": "hypothesis",
            "extracted_context": [
                {"category": "metric", "fact": "tMart fresh grew 23% YoY", "value": "23%", "source_layer": "L2a-groceries", "relevance": "Growth exists"},
                {"category": "metric", "fact": "Repeat rate is 18%", "value": "18%", "source_layer": "L2a-groceries", "relevance": "Low retention"},
                {"category": "persona", "fact": "Young professionals prefer convenience", "value": None, "source_layer": "L1-global", "relevance": "Target segment"},
            ],
            "assumptions": [
                {"id": "asm-001", "content": "Users want weekly delivery slots", "status": "untested", "importance": "high"},
                {"id": "asm-002", "content": "Price is the main barrier", "status": "contradicted", "importance": "critical"},
                {"id": "asm-003", "content": "Freshness perception drives repeat", "status": "supported", "importance": "medium"},
            ],
            "success_signals": ["Repeat rate > 30%", "Weekly active buyers +15%"],
            "kill_signals": ["Unit economics negative after 3 months", "NPS < 20"],
        },
        "synthesis": {
            "verdict_summary": "Proceed with grocery habit loop",
            "recommendation": "proceed",
            "solutions": [
                {"id": "sol-001", "title": "Weekly Box", "description": "Subscription box", "archetype": "incremental",
                 "ice_score": {"impact": 7, "confidence": 6, "ease": 8, "total": 336},
                 "recommendation": "proceed", "status": "proposed"},
            ],
            "convergence": [],
            "counter_signals": [],
            "conflicts": [],
            "evidence_summary": {"total_findings": 12, "by_function": {"market-analyst": 5, "ux-researcher": 4, "data-scientist": 3}},
            "quality_score": {"assumption_coverage": 0.8, "evidence_balance": 0.7, "conflict_surfacing": 0.6, "artifact_relevance": 0.9, "overall": 0.75},
        },
        "contributions": [],
    }


@pytest.fixture
def rich_builder(rich_workspace):
    return StrategyDocBuilder(workspace=rich_workspace, votes=[], prototypes={})


class TestAct1HmwTitle:
    def test_act1_renders_hmw_title(self, rich_builder):
        result = rich_builder.build()
        assert "HMW make fresh groceries" in result


class TestAct1TypeBadge:
    def test_act1_renders_type_badge(self, rich_builder):
        result = rich_builder.build()
        assert "hypothesis" in result.lower()


class TestAct1Description:
    def test_act1_renders_description(self, rich_builder):
        result = rich_builder.build()
        assert "Users buy groceries once" in result


class TestAct1ContextByCategory:
    def test_act1_groups_context_by_category(self, rich_builder):
        result = rich_builder.build()
        assert "metric" in result.lower()
        assert "persona" in result.lower()
        assert "tMart fresh grew 23% YoY" in result


class TestAct1ContextValues:
    def test_act1_context_shows_values(self, rich_builder):
        result = rich_builder.build()
        assert "23%" in result
        assert "18%" in result


class TestAct1Assumptions:
    def test_act1_renders_assumptions_with_status(self, rich_builder):
        result = rich_builder.build()
        assert "Users want weekly delivery slots" in result
        assert "untested" in result.lower()
        assert "contradicted" in result.lower()
        assert "supported" in result.lower()


class TestAct1Signals:
    def test_act1_renders_signals(self, rich_builder):
        result = rich_builder.build()
        assert "Repeat rate &gt; 30%" in result or "Repeat rate > 30%" in result
        assert "Unit economics negative" in result


class TestAct1EmptyContext:
    def test_act1_handles_empty_context(self, builder):
        """Minimal workspace with no extracted_context should not crash."""
        result = builder.build()
        assert 'id="act-1"' in result
