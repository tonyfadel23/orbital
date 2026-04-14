"""Tests for StrategyDocBuilder — Task 1: skeleton + document shell."""

import html
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


# --- Act 2 fixtures and tests ---


@pytest.fixture
def strategy_workspace():
    return {
        "opportunity": {"title": "Test Opportunity", "type": "hypothesis"},
        "synthesis": {
            "verdict_summary": "Strong signal to proceed with grocery habit loop",
            "recommendation": "proceed",
            "convergence": [
                {"finding": "Users want weekly delivery", "sources": ["market-analyst", "ux-researcher"], "agent_count": 3},
                {"finding": "Price sensitivity is secondary", "sources": ["data-scientist"], "agent_count": 2},
            ],
            "counter_signals": [
                {"finding_ref": "cs-001", "summary": "Logistics costs may erode margins", "severity": "critical", "addressed": False},
                {"finding_ref": "cs-002", "summary": "Competitor already testing subscriptions", "severity": "notable", "addressed": True},
            ],
            "conflicts": [
                {
                    "topic": "Pricing strategy",
                    "side_a": {"position": "Premium pricing justified by freshness", "agents": ["market-analyst"], "evidence": "Willingness to pay survey"},
                    "side_b": {"position": "Must match competitor pricing", "agents": ["data-scientist"], "evidence": "Price elasticity model"},
                    "resolution": "Test both in A/B experiment",
                },
            ],
            "evidence_summary": {
                "total_findings": 24,
                "by_function": {"market-analyst": 8, "ux-researcher": 7, "data-scientist": 5, "strategist": 4},
                "strongest_signal": "Weekly delivery demand confirmed across 3 user segments",
                "strongest_counter_signal": "Logistics cost structure unvalidated",
            },
        },
        "contributions": [],
    }


@pytest.fixture
def strategy_builder(strategy_workspace):
    return StrategyDocBuilder(workspace=strategy_workspace, votes=[], prototypes={})


class TestAct2VerdictBanner:
    def test_act2_renders_verdict_banner(self, strategy_builder):
        result = strategy_builder.build()
        assert "Strong signal to proceed" in result
        # proceed recommendation should use green
        assert "#10B981" in result or "var(--green)" in result


class TestAct2Convergence:
    def test_act2_renders_convergence(self, strategy_builder):
        result = strategy_builder.build()
        assert "Users want weekly delivery" in result
        assert "3" in result  # agent_count


class TestAct2CounterSignals:
    def test_act2_renders_counter_signals(self, strategy_builder):
        result = strategy_builder.build()
        assert "Logistics costs may erode margins" in result
        assert "critical" in result.lower()


class TestAct2Conflicts:
    def test_act2_renders_conflicts(self, strategy_builder):
        result = strategy_builder.build()
        assert "Pricing strategy" in result
        assert "Premium pricing justified" in result
        assert "Must match competitor" in result


class TestAct2EvidenceSummary:
    def test_act2_renders_evidence_summary(self, strategy_builder):
        result = strategy_builder.build()
        assert "24" in result  # total findings
        assert "market-analyst" in result


class TestAct2MissingSynthesis:
    def test_act2_handles_missing_synthesis(self, builder):
        """Minimal workspace with no synthesis should not crash."""
        result = builder.build()
        assert 'id="act-2"' in result


# --- Act 3 fixtures and tests ---


@pytest.fixture
def product_workspace():
    return {
        "opportunity": {"title": "Test Product", "type": "hypothesis"},
        "synthesis": {
            "solutions": [
                {
                    "id": "sol-001",
                    "title": "Weekly Box",
                    "description": "Curated weekly grocery box",
                    "archetype": "incremental",
                    "recommendation": "proceed",
                    "ice_score": {
                        "impact": 7,
                        "confidence": 6,
                        "ease": 8,
                        "total": 336,
                    },
                    "proceed_conditions": [
                        {
                            "condition": "Positive unit economics",
                            "measurement": "Margin per box",
                            "threshold": "> $2",
                        }
                    ],
                    "evidence_refs": ["Finding about weekly demand"],
                    "depends_on": [],
                    "solution_quality": {
                        "evidence_grounding": 0.8,
                        "distinctiveness": 0.7,
                    },
                },
                {
                    "id": "sol-002",
                    "title": "Smart Reorder",
                    "description": "AI-powered reorder suggestions",
                    "archetype": "moderate",
                    "recommendation": "proceed_if",
                    "ice_score": {
                        "impact": 8,
                        "confidence": 5,
                        "ease": 4,
                        "total": 160,
                    },
                    "proceed_conditions": [],
                    "evidence_refs": [],
                    "depends_on": ["sol-001"],
                },
                {
                    "id": "sol-003",
                    "title": "Grocery Platform",
                    "description": "Full marketplace for local farms",
                    "archetype": "ambitious",
                    "recommendation": "defer",
                    "ice_score": {
                        "impact": 9,
                        "confidence": 3,
                        "ease": 2,
                        "total": 54,
                    },
                    "depends_on": ["sol-001", "sol-002"],
                },
            ],
            "dot_vote_summary": {
                "heat_map": {
                    "market-analyst": {
                        "sol-001": 8.0,
                        "sol-002": 6.5,
                        "sol-003": 4.0,
                    },
                    "ux-researcher": {
                        "sol-001": 7.0,
                        "sol-002": 7.0,
                        "sol-003": 5.0,
                    },
                },
                "consensus_ranking": ["sol-001", "sol-002", "sol-003"],
            },
            "counter_signals": [
                {
                    "finding_ref": "cs-001",
                    "summary": "Logistics risk",
                    "severity": "critical",
                    "addressed": False,
                },
            ],
        },
        "contributions": [],
    }


@pytest.fixture
def product_builder(product_workspace):
    return StrategyDocBuilder(
        workspace=product_workspace,
        votes=[
            {
                "voter_function": "market-analyst",
                "votes": [
                    {
                        "solution_id": "sol-001",
                        "scores": {"impact": 8, "confidence": 7, "ease": 9},
                        "rationale": "Strong market signal",
                        "flags": [],
                    },
                    {
                        "solution_id": "sol-002",
                        "scores": {"impact": 7, "confidence": 5, "ease": 4},
                        "rationale": "Needs validation",
                        "flags": ["risk"],
                    },
                ],
            },
        ],
        prototypes={
            "sol-001-weekly-box.html": "<div>Prototype content</div><script>alert(1)</script>"
        },
    )


class TestAct3SolutionCards:
    def test_act3_renders_solution_cards(self, product_builder):
        result = product_builder.build()
        assert "Weekly Box" in result
        assert "Smart Reorder" in result
        assert "Grocery Platform" in result


class TestAct3ArchetypeBadge:
    def test_act3_archetype_badge(self, product_builder):
        result = product_builder.build()
        assert "incremental" in result.lower()
        assert "ambitious" in result.lower()


class TestAct3IceScores:
    def test_act3_ice_scores(self, product_builder):
        result = product_builder.build()
        # sol-001 ICE values
        assert "336" in result  # total


class TestAct3RecommendationBadge:
    def test_act3_recommendation_badge(self, product_builder):
        result = product_builder.build()
        assert "proceed" in result.lower()
        assert "defer" in result.lower()


class TestAct3PrototypeIframe:
    def test_act3_embeds_prototype_in_iframe(self, product_builder):
        result = product_builder.build()
        assert "srcdoc=" in result


class TestAct3PhoneFrame:
    def test_act3_phone_frame_wraps_prototype(self, product_builder):
        result = product_builder.build()
        assert 'class="phone-frame"' in result


class TestAct3NoPhoneWithoutPrototype:
    def test_act3_no_phone_without_prototype(self):
        ws = {
            "opportunity": {"title": "Test"},
            "synthesis": {
                "solutions": [
                    {
                        "id": "sol-099",
                        "title": "No Proto",
                        "description": "X",
                        "archetype": "incremental",
                        "ice_score": {
                            "impact": 5,
                            "confidence": 5,
                            "ease": 5,
                            "total": 125,
                        },
                        "recommendation": "proceed",
                    }
                ],
            },
            "contributions": [],
        }
        b = StrategyDocBuilder(workspace=ws, votes=[], prototypes={})
        result = b.build()
        assert 'class="phone-frame"' not in result


class TestAct3CollapsiblePanels:
    def test_act3_collapsible_panels(self, product_builder):
        result = product_builder.build()
        assert result.count("collapsible-toggle") >= 3  # at least 3 panels for sol-001


class TestAct3HeatMap:
    def test_act3_heat_map(self, product_builder):
        result = product_builder.build()
        assert "heat-map" in result
        assert "market-analyst" in result


class TestAct3CompoundCarousel:
    def test_act3_compound_carousel(self, product_builder):
        result = product_builder.build()
        # sol-003 depends_on has 2+ entries -> carousel should exist
        assert "carousel" in result


class TestAct3SanitizesPrototype:
    def test_act3_sanitizes_prototype(self, product_builder):
        result = product_builder.build()
        assert "Prototype content" in result
        # alert(1) should be fully stripped by sanitizer (entire script block removed)
        assert "alert(1)" not in result
        # The srcdoc attribute should not contain a raw <script> tag
        # (the document's own <script> for JS is fine — we check the prototype is clean)
        srcdoc_match = re.search(r'srcdoc="([^"]*)"', result)
        assert srcdoc_match is not None
        srcdoc_content = html.unescape(srcdoc_match.group(1))
        assert "<script>" not in srcdoc_content
        assert "alert" not in srcdoc_content
