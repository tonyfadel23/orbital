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
