"""Tests for LLM-as-Judge service — Layer 2 quality evaluation."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.services.llm_judge import (
    LLMJudgeService,
    RubricResult,
    FindingJudgment,
    LayerTwoReport,
    RUBRICS,
)
from server.services.workspace import WorkspaceService


# --- Helpers ---

def _make_workspace_with_contributions(tmp_data_dir, opp_id="opp-judge-test",
                                        contributions=None):
    """Create a workspace with contributions for LLM judge testing."""
    ws_dir = tmp_data_dir / "workspaces" / opp_id
    ws_dir.mkdir(parents=True, exist_ok=True)
    for d in ("contributions", "reviews", "artifacts", "votes", "evidence", "quality"):
        (ws_dir / d).mkdir(exist_ok=True)

    opp = {
        "id": opp_id,
        "type": "hypothesis",
        "title": "LLM Judge test opportunity",
        "description": "Testing Layer 2 LLM-as-Judge evaluation",
        "context_refs": [],
        "assumptions": [
            {"id": "asm-001", "content": "Users want savings visibility", "status": "untested", "importance": "critical"},
        ],
        "success_signals": ["Metric improves"],
        "kill_signals": ["No change"],
        "status": "orbiting",
        "roster": [
            {"function": "data", "rationale": "Baselines", "investigation_tracks": [], "tool_access": []},
        ],
        "decision": None,
        "created_at": "2026-04-05T12:00:00Z",
        "updated_at": "2026-04-05T14:00:00Z",
    }
    (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))

    if contributions is None:
        contributions = [_default_contribution(opp_id)]

    for i, contrib in enumerate(contributions):
        fname = f"{contrib.get('agent_function', 'agent')}-round-{contrib.get('round', i+1)}.json"
        (ws_dir / "contributions" / fname).write_text(json.dumps(contrib, indent=2))

    return ws_dir


def _default_contribution(opp_id="opp-judge-test"):
    return {
        "id": "contrib-data-20260405-140000",
        "opportunity_id": opp_id,
        "agent_function": "data",
        "round": 1,
        "findings": [
            {
                "id": "find-001",
                "type": "measurement",
                "content": "Add-to-cart rate is 12% blended across all users, which is below the 18% benchmark for grocery e-commerce",
                "confidence": 0.9,
                "source": "analytics dashboard",
                "assumptions_addressed": ["asm-001"],
                "direction": "supports",
            },
            {
                "id": "find-002",
                "type": "risk",
                "content": "Data collection methodology changed 6 months ago making historical comparisons unreliable for trending analysis",
                "confidence": 0.7,
                "source": "data team interview",
                "assumptions_addressed": [],
                "direction": "neutral",
            },
        ],
        "artifacts_produced": [],
        "cross_references": [],
        "self_review": {"self_checked": True, "self_check_notes": "Verified data sources are current and methodology is sound"},
        "created_at": "2026-04-05T14:00:00Z",
    }


def _mock_anthropic_response(passed: bool):
    """Create a mock Anthropic API response for a rubric evaluation."""
    return MagicMock(
        content=[MagicMock(text=json.dumps({"pass": passed, "reasoning": "Test reasoning"}))]
    )


def _make_svc(tmp_data_dir, api_key="test-key"):
    ws_svc = WorkspaceService(tmp_data_dir)
    config = json.loads((tmp_data_dir / "config.json").read_text())
    return LLMJudgeService(ws_svc, config, api_key=api_key)


# --- Dataclass tests ---

class TestRubricResult:
    def test_creation(self):
        r = RubricResult(rubric="evidence_grounding", passed=True, reasoning="Well grounded")
        assert r.rubric == "evidence_grounding"
        assert r.passed is True
        assert r.reasoning == "Well grounded"

    def test_to_dict(self):
        r = RubricResult(rubric="relevance", passed=False, reasoning="Off topic")
        d = r.to_dict()
        assert d == {"rubric": "relevance", "passed": False, "reasoning": "Off topic"}


class TestFindingJudgment:
    def test_creation(self):
        rubrics = [
            RubricResult("evidence_grounding", True, "ok"),
            RubricResult("relevance", True, "ok"),
            RubricResult("actionability", False, "vague"),
            RubricResult("non_obviousness", True, "ok"),
            RubricResult("self_review_quality", True, "ok"),
        ]
        j = FindingJudgment(finding_id="find-001", rubrics=rubrics)
        assert j.finding_id == "find-001"
        assert j.score == 0.8  # 4/5
        assert len(j.rubrics) == 5

    def test_score_all_pass(self):
        rubrics = [RubricResult(r, True, "ok") for r in RUBRICS]
        j = FindingJudgment(finding_id="find-001", rubrics=rubrics)
        assert j.score == 1.0

    def test_score_all_fail(self):
        rubrics = [RubricResult(r, False, "bad") for r in RUBRICS]
        j = FindingJudgment(finding_id="find-001", rubrics=rubrics)
        assert j.score == 0.0

    def test_score_empty_rubrics(self):
        j = FindingJudgment(finding_id="find-001", rubrics=[])
        assert j.score == 0.0

    def test_to_dict(self):
        rubrics = [RubricResult("evidence_grounding", True, "ok")]
        j = FindingJudgment(finding_id="find-001", rubrics=rubrics)
        d = j.to_dict()
        assert d["finding_id"] == "find-001"
        assert d["score"] == 1.0
        assert len(d["rubrics"]) == 1


class TestLayerTwoReport:
    def test_creation(self):
        j1 = FindingJudgment("find-001", [RubricResult("r1", True, "ok")])
        j2 = FindingJudgment("find-002", [RubricResult("r1", False, "bad")])
        report = LayerTwoReport(opp_id="opp-test", judgments=[j1, j2])
        assert report.opp_id == "opp-test"
        assert report.overall_score == 0.5

    def test_overall_passed_above_threshold(self):
        j = FindingJudgment("find-001", [RubricResult("r1", True, "ok")])
        report = LayerTwoReport(opp_id="opp-test", judgments=[j], pass_threshold=0.6)
        assert report.overall_passed is True

    def test_overall_passed_below_threshold(self):
        j = FindingJudgment("find-001", [RubricResult("r1", False, "bad")])
        report = LayerTwoReport(opp_id="opp-test", judgments=[j], pass_threshold=0.6)
        assert report.overall_passed is False

    def test_empty_judgments(self):
        report = LayerTwoReport(opp_id="opp-test", judgments=[])
        assert report.overall_score == 0.0
        assert report.overall_passed is False

    def test_to_dict(self):
        j = FindingJudgment("find-001", [RubricResult("r1", True, "ok")])
        report = LayerTwoReport(opp_id="opp-test", judgments=[j], pass_threshold=0.6)
        d = report.to_dict()
        assert d["opp_id"] == "opp-test"
        assert d["overall_passed"] is True
        assert d["overall_score"] == 1.0
        assert d["pass_threshold"] == 0.6
        assert "timestamp" in d
        assert len(d["judgments"]) == 1


# --- Service tests ---

class TestLLMJudgeServiceInit:
    def test_init_with_api_key(self, tmp_data_dir):
        svc = _make_svc(tmp_data_dir, api_key="sk-test-123")
        assert svc._api_key == "sk-test-123"
        assert svc._model == "claude-haiku-4-5-20251001"

    def test_init_reads_config(self, tmp_data_dir):
        svc = _make_svc(tmp_data_dir)
        assert svc._pass_threshold == 0.6

    def test_init_no_api_key(self, tmp_data_dir):
        svc = _make_svc(tmp_data_dir, api_key=None)
        assert svc._api_key is None


class TestLLMJudgeServiceRubrics:
    def test_rubrics_constant(self):
        assert "evidence_grounding" in RUBRICS
        assert "relevance" in RUBRICS
        assert "actionability" in RUBRICS
        assert "non_obviousness" in RUBRICS
        assert "self_review_quality" in RUBRICS
        assert len(RUBRICS) == 5


class TestEvaluateFinding:
    @pytest.mark.asyncio
    async def test_evaluate_finding_all_pass(self, tmp_data_dir):
        svc = _make_svc(tmp_data_dir)
        finding = {
            "id": "find-001",
            "type": "measurement",
            "content": "ATC rate is 12%",
            "confidence": 0.9,
            "source": "dashboard",
        }
        self_review = {"self_checked": True, "self_check_notes": "Verified sources"}
        opp_context = "Test opportunity about grocery conversion"

        with patch.object(svc, "_call_rubric", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = RubricResult("test", True, "ok")
            judgment = await svc.evaluate_finding(finding, self_review, opp_context)

        assert isinstance(judgment, FindingJudgment)
        assert judgment.finding_id == "find-001"
        assert judgment.score == 1.0
        assert len(judgment.rubrics) == 5

    @pytest.mark.asyncio
    async def test_evaluate_finding_mixed_results(self, tmp_data_dir):
        svc = _make_svc(tmp_data_dir)
        finding = {
            "id": "find-002",
            "type": "risk",
            "content": "Something risky",
            "confidence": 0.5,
            "source": "interview",
        }
        self_review = {"self_checked": True, "self_check_notes": "Quick check"}
        opp_context = "Test opportunity"

        call_count = 0

        async def _alternating(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            passed = call_count % 2 == 1  # alternate pass/fail
            return RubricResult(args[0], passed, "test")

        with patch.object(svc, "_call_rubric", side_effect=_alternating):
            judgment = await svc.evaluate_finding(finding, self_review, opp_context)

        assert judgment.finding_id == "find-002"
        assert 0.0 < judgment.score < 1.0


class TestEvaluateAll:
    @pytest.mark.asyncio
    async def test_evaluate_all_returns_report(self, tmp_data_dir):
        _make_workspace_with_contributions(tmp_data_dir)
        svc = _make_svc(tmp_data_dir)

        with patch.object(svc, "_call_rubric", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = RubricResult("test", True, "ok")
            report = await svc.evaluate_all("opp-judge-test")

        assert isinstance(report, LayerTwoReport)
        assert report.opp_id == "opp-judge-test"
        assert len(report.judgments) == 2  # 2 findings in default contribution
        assert report.overall_passed is True

    @pytest.mark.asyncio
    async def test_evaluate_all_nonexistent_workspace(self, tmp_data_dir):
        svc = _make_svc(tmp_data_dir)
        with pytest.raises(ValueError, match="not found"):
            await svc.evaluate_all("opp-nonexistent")

    @pytest.mark.asyncio
    async def test_evaluate_all_no_contributions(self, tmp_data_dir):
        _make_workspace_with_contributions(tmp_data_dir, "opp-empty", contributions=[])
        svc = _make_svc(tmp_data_dir)
        # Create workspace with no contributions dir content
        report = await svc.evaluate_all("opp-empty")
        assert isinstance(report, LayerTwoReport)
        assert len(report.judgments) == 0
        assert report.overall_passed is False

    @pytest.mark.asyncio
    async def test_evaluate_all_persists_results(self, tmp_data_dir):
        _make_workspace_with_contributions(tmp_data_dir)
        svc = _make_svc(tmp_data_dir)

        with patch.object(svc, "_call_rubric", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = RubricResult("test", True, "ok")
            await svc.evaluate_all("opp-judge-test")

        # Check persistence
        result_path = tmp_data_dir / "workspaces" / "opp-judge-test" / "quality" / "llm-judge.json"
        assert result_path.exists()
        saved = json.loads(result_path.read_text())
        assert saved["opp_id"] == "opp-judge-test"
        assert saved["overall_passed"] is True


class TestGracefulDegradation:
    @pytest.mark.asyncio
    async def test_no_api_key_returns_degraded_report(self, tmp_data_dir):
        _make_workspace_with_contributions(tmp_data_dir, "opp-no-key")
        svc = _make_svc(tmp_data_dir, api_key=None)
        report = await svc.evaluate_all("opp-no-key")
        assert isinstance(report, LayerTwoReport)
        assert len(report.judgments) == 0
        assert report.overall_passed is False
        assert report.degraded is True
        assert "no api key" in report.degraded_reason.lower()

    @pytest.mark.asyncio
    async def test_api_error_marks_rubrics_failed(self, tmp_data_dir):
        """When all rubric calls error, findings get zero scores but report completes."""
        _make_workspace_with_contributions(tmp_data_dir, "opp-api-err")
        svc = _make_svc(tmp_data_dir)

        with patch.object(svc, "_call_rubric", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("API connection failed")
            report = await svc.evaluate_all("opp-api-err")

        assert isinstance(report, LayerTwoReport)
        assert report.degraded is False  # individual rubric errors don't degrade the report
        assert len(report.judgments) == 2
        # All rubrics should be failed
        for j in report.judgments:
            assert j.score == 0.0
            for r in j.rubrics:
                assert r.passed is False
                assert "error" in r.reasoning.lower()

    @pytest.mark.asyncio
    async def test_single_rubric_error_doesnt_fail_entire_finding(self, tmp_data_dir):
        _make_workspace_with_contributions(tmp_data_dir, "opp-partial-err")
        svc = _make_svc(tmp_data_dir)

        call_count = 0

        async def _error_on_third(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                raise Exception("Transient error")
            return RubricResult(args[0], True, "ok")

        with patch.object(svc, "_call_rubric", side_effect=_error_on_third):
            report = await svc.evaluate_all("opp-partial-err")

        # Should still produce judgments, with failed rubric marked as failed
        assert len(report.judgments) > 0
        assert report.degraded is False  # partial errors don't mark entire report as degraded

    @pytest.mark.asyncio
    async def test_layer2_disabled_returns_empty(self, tmp_data_dir):
        _make_workspace_with_contributions(tmp_data_dir, "opp-disabled")
        # Modify config to disable layer 2
        config = json.loads((tmp_data_dir / "config.json").read_text())
        config["quality_gates"]["layer_2"]["enabled"] = False
        (tmp_data_dir / "config.json").write_text(json.dumps(config, indent=2))

        ws_svc = WorkspaceService(tmp_data_dir)
        config = json.loads((tmp_data_dir / "config.json").read_text())
        svc = LLMJudgeService(ws_svc, config, api_key="test-key")
        report = await svc.evaluate_all("opp-disabled")
        assert len(report.judgments) == 0
        assert report.degraded is True
        assert "disabled" in report.degraded_reason.lower()


# --- Router integration tests ---

@pytest.mark.asyncio
class TestQualityRouterLayer2:
    async def test_evaluate_layer2_endpoint(self, client, tmp_data_dir):
        # The default fixture has a workspace with one contribution
        # Mock the llm_judge_svc on the app to avoid real API calls
        app = client._transport.app
        mock_svc = AsyncMock()
        mock_report = LayerTwoReport(
            opp_id="opp-20260405-120000",
            judgments=[],
            pass_threshold=0.6,
        )
        mock_svc.evaluate_all.return_value = mock_report
        app.state.llm_judge_svc = mock_svc

        resp = await client.post("/api/workspaces/opp-20260405-120000/quality/evaluate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["opp_id"] == "opp-20260405-120000"
        assert data["overall_passed"] is False  # no judgments
        assert data["pass_threshold"] == 0.6
