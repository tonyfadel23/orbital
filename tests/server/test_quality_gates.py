"""Tests for quality gate service — Layer 1 deterministic checks."""

import json
from datetime import datetime, timezone, timedelta

import pytest

from server.services.workspace import WorkspaceService
from server.services.quality_gates import QualityGateService, GateResult, QualityReport


# --- Helpers ---

def _make_quality_workspace(tmp_data_dir, opp_id="opp-quality-test", assumptions=None,
                             contributions=None, solutions=None, votes=None,
                             roster=None, evidence=None):
    """Create a workspace with specific data for quality gate testing."""
    ws_dir = tmp_data_dir / "workspaces" / opp_id
    ws_dir.mkdir(parents=True, exist_ok=True)
    for d in ("contributions", "reviews", "artifacts", "votes", "evidence"):
        (ws_dir / d).mkdir(exist_ok=True)

    if assumptions is None:
        assumptions = [
            {"id": "asm-001", "content": "Users want savings visibility", "status": "untested", "importance": "critical"},
            {"id": "asm-002", "content": "Gamification drives engagement", "status": "untested", "importance": "medium"},
        ]

    if roster is None:
        roster = [
            {"function": "product", "rationale": "Orchestrate", "investigation_tracks": [], "tool_access": []},
            {"function": "data", "rationale": "Baselines", "investigation_tracks": [], "tool_access": []},
            {"function": "design", "rationale": "UX audit", "investigation_tracks": [], "tool_access": []},
            {"function": "engineering", "rationale": "Feasibility", "investigation_tracks": [], "tool_access": []},
        ]

    opp = {
        "id": opp_id,
        "type": "hypothesis",
        "title": "Quality gate test opportunity",
        "description": "Testing quality gates",
        "context_refs": [],
        "assumptions": assumptions,
        "success_signals": ["Metric improves"],
        "kill_signals": ["No change"],
        "status": "orbiting",
        "roster": roster,
        "decision": None,
        "created_at": "2026-04-05T12:00:00Z",
        "updated_at": "2026-04-05T14:00:00Z",
    }
    (ws_dir / "opportunity.json").write_text(json.dumps(opp, indent=2))

    if contributions:
        for i, contrib in enumerate(contributions):
            fname = f"{contrib.get('agent_function', 'agent')}-round-{contrib.get('round', i+1)}.json"
            (ws_dir / "contributions" / fname).write_text(json.dumps(contrib, indent=2))

    if solutions:
        synthesis = {
            "id": "synth-test",
            "opportunity_id": opp_id,
            "status": "presented",
            "solutions": solutions,
        }
        (ws_dir / "synthesis.json").write_text(json.dumps(synthesis, indent=2))

    if votes:
        for vote in votes:
            fname = f"{vote['voter_function']}-vote.json"
            (ws_dir / "votes" / fname).write_text(json.dumps(vote, indent=2))

    if evidence:
        for ev in evidence:
            fname = f"{ev['id']}.json"
            (ws_dir / "evidence" / fname).write_text(json.dumps(ev, indent=2))

    return ws_dir


def _default_config():
    return {
        "quality_gates": {
            "enabled": True,
            "blocking_mode": "warn",
            "layer_1": {
                "assumption_coverage": {"enabled": True, "min_coverage": 1.0, "blocking": True},
                "confidence_floor": {"enabled": True, "threshold": 0.4, "blocking": True},
                "solution_distinctiveness": {"enabled": True, "max_jaccard": 0.7, "blocking": False},
                "evidence_freshness": {"enabled": True, "max_age_days": 180, "blocking": False},
                "vote_quorum": {"enabled": True, "min_pct": 0.8, "blocking": True},
                "finding_density": {"enabled": True, "min_findings": 3, "blocking": True},
            },
        }
    }


def _make_svc(tmp_data_dir, config=None):
    ws_svc = WorkspaceService(tmp_data_dir)
    return QualityGateService(ws_svc, config or _default_config())


# --- GateResult / QualityReport dataclass tests ---

class TestGateResultDataclass:
    def test_gate_result_creation(self):
        result = GateResult(
            gate="assumption_coverage",
            passed=True,
            score=1.0,
            threshold=1.0,
            blocking=True,
            details="All assumptions covered",
        )
        assert result.gate == "assumption_coverage"
        assert result.passed is True
        assert result.score == 1.0

    def test_gate_result_to_dict(self):
        result = GateResult(
            gate="confidence_floor",
            passed=False,
            score=0.3,
            threshold=0.4,
            blocking=True,
            details="Below threshold",
        )
        d = result.to_dict()
        assert d["gate"] == "confidence_floor"
        assert d["passed"] is False
        assert d["score"] == 0.3


class TestQualityReportDataclass:
    def test_report_creation(self):
        gates = [
            GateResult("g1", True, 1.0, 1.0, True, "ok"),
            GateResult("g2", False, 0.3, 0.4, True, "fail"),
        ]
        report = QualityReport(
            opp_id="opp-test",
            gates=gates,
        )
        assert report.opp_id == "opp-test"
        assert report.overall_passed is False  # one blocking gate failed
        assert len(report.gates) == 2

    def test_report_all_pass(self):
        gates = [
            GateResult("g1", True, 1.0, 1.0, True, "ok"),
            GateResult("g2", True, 0.8, 0.4, False, "ok"),
        ]
        report = QualityReport(opp_id="opp-ok", gates=gates)
        assert report.overall_passed is True

    def test_report_non_blocking_failure_still_passes(self):
        gates = [
            GateResult("g1", True, 1.0, 1.0, True, "ok"),
            GateResult("g2", False, 0.3, 0.7, False, "below"),  # non-blocking
        ]
        report = QualityReport(opp_id="opp-warn", gates=gates)
        assert report.overall_passed is True

    def test_report_to_dict(self):
        gates = [GateResult("g1", True, 1.0, 1.0, True, "ok")]
        report = QualityReport(opp_id="opp-test", gates=gates)
        d = report.to_dict()
        assert d["opp_id"] == "opp-test"
        assert d["overall_passed"] is True
        assert "overall_score" in d
        assert "timestamp" in d
        assert len(d["gates"]) == 1


# --- Workspace service quality methods ---

class TestWorkspaceQualityMethods:
    def test_save_and_get_quality_results(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-qsave")
        svc = WorkspaceService(tmp_data_dir)
        results = {"opp_id": "opp-qsave", "overall_passed": True, "gates": []}
        svc.save_quality_results("opp-qsave", results)
        loaded = svc.get_quality_results("opp-qsave")
        assert loaded["opp_id"] == "opp-qsave"
        assert loaded["overall_passed"] is True

    def test_get_quality_results_not_found(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-noq")
        svc = WorkspaceService(tmp_data_dir)
        assert svc.get_quality_results("opp-noq") is None


# --- Individual gate checks ---

class TestAssumptionCoverage:
    def test_full_coverage_passes(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-asmcov-pass", contributions=[
            {
                "id": "contrib-1", "opportunity_id": "opp-asmcov-pass",
                "agent_function": "data", "round": 1,
                "findings": [
                    {"id": "f1", "type": "measurement", "content": "x", "confidence": 0.8,
                     "source": "test", "assumptions_addressed": ["asm-001"], "direction": "supports"},
                    {"id": "f2", "type": "measurement", "content": "y", "confidence": 0.7,
                     "source": "test", "assumptions_addressed": ["asm-002"], "direction": "supports"},
                ],
                "artifacts_produced": [], "cross_references": [],
                "self_review": {"self_checked": True, "self_check_notes": "ok"},
                "created_at": "2026-04-05T14:00:00Z",
            },
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_assumption_coverage("opp-asmcov-pass")
        assert result.passed is True
        assert result.score == 1.0

    def test_partial_coverage_fails(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-asmcov-fail", contributions=[
            {
                "id": "contrib-1", "opportunity_id": "opp-asmcov-fail",
                "agent_function": "data", "round": 1,
                "findings": [
                    {"id": "f1", "type": "measurement", "content": "x", "confidence": 0.8,
                     "source": "test", "assumptions_addressed": ["asm-001"], "direction": "supports"},
                ],
                "artifacts_produced": [], "cross_references": [],
                "self_review": {"self_checked": True, "self_check_notes": "ok"},
                "created_at": "2026-04-05T14:00:00Z",
            },
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_assumption_coverage("opp-asmcov-fail")
        assert result.passed is False
        assert result.score == 0.5  # 1 of 2 assumptions covered

    def test_no_contributions_zero_coverage(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-asmcov-empty")
        svc = _make_svc(tmp_data_dir)
        result = svc.check_assumption_coverage("opp-asmcov-empty")
        assert result.passed is False
        assert result.score == 0.0

    def test_no_assumptions_passes(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-asmcov-none", assumptions=[])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_assumption_coverage("opp-asmcov-none")
        assert result.passed is True
        assert result.score == 1.0


class TestConfidenceFloor:
    def test_all_above_threshold_passes(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-conf-pass", contributions=[
            {
                "id": "contrib-1", "opportunity_id": "opp-conf-pass",
                "agent_function": "data", "round": 1,
                "findings": [
                    {"id": "f1", "type": "measurement", "content": "x", "confidence": 0.8, "source": "test", "assumptions_addressed": [], "direction": "supports"},
                    {"id": "f2", "type": "measurement", "content": "y", "confidence": 0.6, "source": "test", "assumptions_addressed": [], "direction": "supports"},
                ],
                "artifacts_produced": [], "cross_references": [],
                "self_review": {"self_checked": True, "self_check_notes": "ok"},
                "created_at": "2026-04-05T14:00:00Z",
            },
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_confidence_floor("opp-conf-pass")
        assert result.passed is True

    def test_below_threshold_fails(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-conf-fail", contributions=[
            {
                "id": "contrib-1", "opportunity_id": "opp-conf-fail",
                "agent_function": "data", "round": 1,
                "findings": [
                    {"id": "f1", "type": "measurement", "content": "x", "confidence": 0.2, "source": "test", "assumptions_addressed": [], "direction": "supports"},
                    {"id": "f2", "type": "measurement", "content": "y", "confidence": 0.3, "source": "test", "assumptions_addressed": [], "direction": "supports"},
                ],
                "artifacts_produced": [], "cross_references": [],
                "self_review": {"self_checked": True, "self_check_notes": "ok"},
                "created_at": "2026-04-05T14:00:00Z",
            },
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_confidence_floor("opp-conf-fail")
        assert result.passed is False

    def test_no_findings_fails(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-conf-empty", contributions=[
            {
                "id": "contrib-1", "opportunity_id": "opp-conf-empty",
                "agent_function": "data", "round": 1,
                "findings": [],
                "artifacts_produced": [], "cross_references": [],
                "self_review": {"self_checked": True, "self_check_notes": "ok"},
                "created_at": "2026-04-05T14:00:00Z",
            },
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_confidence_floor("opp-conf-empty")
        assert result.passed is False


class TestSolutionDistinctiveness:
    def test_distinct_solutions_pass(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-distinct-pass", solutions=[
            {"id": "sol-001", "evidence_refs": ["ev-001", "ev-002"]},
            {"id": "sol-002", "evidence_refs": ["ev-003", "ev-004"]},
            {"id": "sol-003", "evidence_refs": ["ev-005", "ev-006"]},
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_solution_distinctiveness("opp-distinct-pass")
        assert result.passed is True

    def test_overlapping_solutions_fail(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-distinct-fail", solutions=[
            {"id": "sol-001", "evidence_refs": ["ev-001", "ev-002", "ev-003"]},
            {"id": "sol-002", "evidence_refs": ["ev-001", "ev-002", "ev-004"]},  # 2/4 overlap
            {"id": "sol-003", "evidence_refs": ["ev-005", "ev-006"]},
        ])
        svc = _make_svc(tmp_data_dir)
        # Jaccard of sol-001 vs sol-002: intersection=2, union=4 => 0.5
        # With max_jaccard=0.7, this should pass (0.5 < 0.7)
        result = svc.check_solution_distinctiveness("opp-distinct-fail")
        assert result.passed is True

    def test_near_identical_solutions_fail(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-distinct-identical", solutions=[
            {"id": "sol-001", "evidence_refs": ["ev-001", "ev-002", "ev-003"]},
            {"id": "sol-002", "evidence_refs": ["ev-001", "ev-002", "ev-003"]},  # identical
            {"id": "sol-003", "evidence_refs": ["ev-005"]},
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_solution_distinctiveness("opp-distinct-identical")
        assert result.passed is False
        assert result.score == 1.0  # max jaccard = 1.0

    def test_no_synthesis_passes(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-distinct-none")
        svc = _make_svc(tmp_data_dir)
        result = svc.check_solution_distinctiveness("opp-distinct-none")
        assert result.passed is True  # no solutions to compare


class TestEvidenceFreshness:
    def test_fresh_evidence_passes(self, tmp_data_dir):
        now = datetime.now(timezone.utc)
        _make_quality_workspace(tmp_data_dir, "opp-fresh-pass", evidence=[
            {"id": "ev-001", "source_type": "data-query", "query": "test",
             "status": "completed", "findings": [], "created_at": now.isoformat()},
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_evidence_freshness("opp-fresh-pass")
        assert result.passed is True

    def test_stale_evidence_fails(self, tmp_data_dir):
        old = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
        _make_quality_workspace(tmp_data_dir, "opp-stale", evidence=[
            {"id": "ev-001", "source_type": "data-query", "query": "test",
             "status": "completed", "findings": [], "created_at": old},
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_evidence_freshness("opp-stale")
        assert result.passed is False

    def test_no_evidence_passes(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-noev")
        svc = _make_svc(tmp_data_dir)
        result = svc.check_evidence_freshness("opp-noev")
        assert result.passed is True

    def test_mixed_evidence(self, tmp_data_dir):
        now = datetime.now(timezone.utc)
        old = (now - timedelta(days=200)).isoformat()
        _make_quality_workspace(tmp_data_dir, "opp-mixed-ev", evidence=[
            {"id": "ev-001", "source_type": "data-query", "query": "test",
             "status": "completed", "findings": [], "created_at": now.isoformat()},
            {"id": "ev-002", "source_type": "data-query", "query": "old",
             "status": "completed", "findings": [], "created_at": old},
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_evidence_freshness("opp-mixed-ev")
        assert result.passed is False


class TestVoteQuorum:
    def test_full_quorum_passes(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-quorum-pass",
            roster=[
                {"function": "product", "rationale": "test", "investigation_tracks": [], "tool_access": []},
                {"function": "data", "rationale": "test", "investigation_tracks": [], "tool_access": []},
                {"function": "design", "rationale": "test", "investigation_tracks": [], "tool_access": []},
                {"function": "engineering", "rationale": "test", "investigation_tracks": [], "tool_access": []},
            ],
            votes=[
                {"id": "vote-product-1", "voter_function": "product", "votes": []},
                {"id": "vote-data-1", "voter_function": "data", "votes": []},
                {"id": "vote-design-1", "voter_function": "design", "votes": []},
                {"id": "vote-engineering-1", "voter_function": "engineering", "votes": []},
            ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_vote_quorum("opp-quorum-pass")
        assert result.passed is True
        assert result.score == 1.0

    def test_partial_quorum_fails(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-quorum-fail",
            roster=[
                {"function": "product", "rationale": "test", "investigation_tracks": [], "tool_access": []},
                {"function": "data", "rationale": "test", "investigation_tracks": [], "tool_access": []},
                {"function": "design", "rationale": "test", "investigation_tracks": [], "tool_access": []},
                {"function": "engineering", "rationale": "test", "investigation_tracks": [], "tool_access": []},
            ],
            votes=[
                {"id": "vote-product-1", "voter_function": "product", "votes": []},
                {"id": "vote-data-1", "voter_function": "data", "votes": []},
            ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_vote_quorum("opp-quorum-fail")
        assert result.passed is False
        assert result.score == 0.5

    def test_no_roster_passes(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-quorum-noroster", roster=[])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_vote_quorum("opp-quorum-noroster")
        assert result.passed is True


class TestFindingDensity:
    def test_sufficient_findings_passes(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-density-pass", contributions=[
            {
                "id": "contrib-1", "opportunity_id": "opp-density-pass",
                "agent_function": "data", "round": 1,
                "findings": [
                    {"id": "f1", "type": "m", "content": "x", "confidence": 0.8, "source": "s", "assumptions_addressed": [], "direction": "supports"},
                    {"id": "f2", "type": "m", "content": "y", "confidence": 0.8, "source": "s", "assumptions_addressed": [], "direction": "supports"},
                    {"id": "f3", "type": "m", "content": "z", "confidence": 0.8, "source": "s", "assumptions_addressed": [], "direction": "supports"},
                ],
                "artifacts_produced": [], "cross_references": [],
                "self_review": {"self_checked": True, "self_check_notes": "ok"},
                "created_at": "2026-04-05T14:00:00Z",
            },
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_finding_density("opp-density-pass")
        assert result.passed is True

    def test_insufficient_findings_fails(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-density-fail", contributions=[
            {
                "id": "contrib-1", "opportunity_id": "opp-density-fail",
                "agent_function": "data", "round": 1,
                "findings": [
                    {"id": "f1", "type": "m", "content": "x", "confidence": 0.8, "source": "s", "assumptions_addressed": [], "direction": "supports"},
                ],
                "artifacts_produced": [], "cross_references": [],
                "self_review": {"self_checked": True, "self_check_notes": "ok"},
                "created_at": "2026-04-05T14:00:00Z",
            },
        ])
        svc = _make_svc(tmp_data_dir)
        result = svc.check_finding_density("opp-density-fail")
        assert result.passed is False

    def test_no_contributions_fails(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-density-empty")
        svc = _make_svc(tmp_data_dir)
        result = svc.check_finding_density("opp-density-empty")
        assert result.passed is False


# --- Evaluate all + can_transition ---

class TestEvaluateAll:
    def test_evaluate_all_returns_report(self, tmp_data_dir):
        now = datetime.now(timezone.utc)
        _make_quality_workspace(tmp_data_dir, "opp-eval-all",
            contributions=[{
                "id": "contrib-1", "opportunity_id": "opp-eval-all",
                "agent_function": "data", "round": 1,
                "findings": [
                    {"id": "f1", "type": "m", "content": "x", "confidence": 0.8, "source": "s",
                     "assumptions_addressed": ["asm-001", "asm-002"], "direction": "supports"},
                    {"id": "f2", "type": "m", "content": "y", "confidence": 0.7, "source": "s",
                     "assumptions_addressed": [], "direction": "supports"},
                    {"id": "f3", "type": "m", "content": "z", "confidence": 0.6, "source": "s",
                     "assumptions_addressed": [], "direction": "supports"},
                ],
                "artifacts_produced": [], "cross_references": [],
                "self_review": {"self_checked": True, "self_check_notes": "ok"},
                "created_at": "2026-04-05T14:00:00Z",
            }],
            solutions=[
                {"id": "sol-001", "evidence_refs": ["ev-001"]},
                {"id": "sol-002", "evidence_refs": ["ev-002"]},
                {"id": "sol-003", "evidence_refs": ["ev-003"]},
            ],
            votes=[
                {"id": "vote-product-1", "voter_function": "product", "votes": []},
                {"id": "vote-data-1", "voter_function": "data", "votes": []},
                {"id": "vote-design-1", "voter_function": "design", "votes": []},
                {"id": "vote-engineering-1", "voter_function": "engineering", "votes": []},
            ],
            evidence=[
                {"id": "ev-001", "source_type": "data-query", "query": "test",
                 "status": "completed", "findings": [], "created_at": now.isoformat()},
            ])
        svc = _make_svc(tmp_data_dir)
        report = svc.evaluate_all("opp-eval-all")
        assert isinstance(report, QualityReport)
        assert len(report.gates) == 6
        assert report.opp_id == "opp-eval-all"

    def test_evaluate_all_nonexistent_workspace(self, tmp_data_dir):
        svc = _make_svc(tmp_data_dir)
        with pytest.raises(ValueError, match="not found"):
            svc.evaluate_all("opp-nonexistent")

    def test_disabled_gates_skipped(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-disabled")
        config = _default_config()
        config["quality_gates"]["layer_1"]["assumption_coverage"]["enabled"] = False
        config["quality_gates"]["layer_1"]["confidence_floor"]["enabled"] = False
        config["quality_gates"]["layer_1"]["solution_distinctiveness"]["enabled"] = False
        config["quality_gates"]["layer_1"]["evidence_freshness"]["enabled"] = False
        config["quality_gates"]["layer_1"]["vote_quorum"]["enabled"] = False
        config["quality_gates"]["layer_1"]["finding_density"]["enabled"] = False
        svc = _make_svc(tmp_data_dir, config)
        report = svc.evaluate_all("opp-disabled")
        assert len(report.gates) == 0
        assert report.overall_passed is True


class TestCanTransition:
    def test_can_transition_passes_when_gates_pass(self, tmp_data_dir):
        now = datetime.now(timezone.utc)
        _make_quality_workspace(tmp_data_dir, "opp-trans-pass",
            contributions=[{
                "id": "contrib-1", "opportunity_id": "opp-trans-pass",
                "agent_function": "data", "round": 1,
                "findings": [
                    {"id": "f1", "type": "m", "content": "x", "confidence": 0.8, "source": "s",
                     "assumptions_addressed": ["asm-001", "asm-002"], "direction": "supports"},
                    {"id": "f2", "type": "m", "content": "y", "confidence": 0.7, "source": "s",
                     "assumptions_addressed": [], "direction": "supports"},
                    {"id": "f3", "type": "m", "content": "z", "confidence": 0.6, "source": "s",
                     "assumptions_addressed": [], "direction": "supports"},
                ],
                "artifacts_produced": [], "cross_references": [],
                "self_review": {"self_checked": True, "self_check_notes": "ok"},
                "created_at": "2026-04-05T14:00:00Z",
            }],
            votes=[
                {"id": "v1", "voter_function": "product", "votes": []},
                {"id": "v2", "voter_function": "data", "votes": []},
                {"id": "v3", "voter_function": "design", "votes": []},
                {"id": "v4", "voter_function": "engineering", "votes": []},
            ])
        svc = _make_svc(tmp_data_dir)
        can, blockers, warnings = svc.can_transition("opp-trans-pass", "scoring")
        assert can is True
        assert blockers == []

    def test_can_transition_returns_blockers(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-trans-block")
        svc = _make_svc(tmp_data_dir)
        can, blockers, warnings = svc.can_transition("opp-trans-block", "scoring")
        assert can is False
        assert len(blockers) > 0

    def test_can_transition_disabled_always_passes(self, tmp_data_dir):
        _make_quality_workspace(tmp_data_dir, "opp-trans-off")
        config = _default_config()
        config["quality_gates"]["enabled"] = False
        svc = _make_svc(tmp_data_dir, config)
        can, blockers, warnings = svc.can_transition("opp-trans-off", "scoring")
        assert can is True
        assert blockers == []
        assert warnings == []


# --- Framing quality gate tests ---

class TestFramingQuality:
    """check_framing_quality() scores opportunity framing completeness."""

    def _make_framing_workspace(self, tmp_data_dir, opp_id, **overrides):
        """Create a minimal opportunity for framing quality tests."""
        ws_dir = tmp_data_dir / "workspaces" / opp_id
        ws_dir.mkdir(parents=True, exist_ok=True)
        opp = {
            "id": opp_id,
            "title": overrides.get("title", ""),
            "type": overrides.get("type", None),
            "description": overrides.get("description", ""),
            "assumptions": overrides.get("assumptions", []),
            "success_signals": overrides.get("success_signals", []),
            "kill_signals": overrides.get("kill_signals", []),
            "context_refs": overrides.get("context_refs", []),
            "status": "aligning",
        }
        (ws_dir / "opportunity.json").write_text(json.dumps(opp))
        return _make_svc(tmp_data_dir)

    def test_empty_opportunity_scores_near_zero(self, tmp_data_dir):
        svc = self._make_framing_workspace(tmp_data_dir, "opp-frame-empty")
        report = svc.check_framing_quality("opp-frame-empty")
        assert report.overall_score < 0.1
        assert report.overall_passed is False

    def test_hmw_title_scores_full(self, tmp_data_dir):
        svc = self._make_framing_workspace(tmp_data_dir, "opp-frame-hmw",
            title="HMW reduce first-order drop-off for new users?")
        report = svc.check_framing_quality("opp-frame-hmw")
        hmw_gate = next(g for g in report.gates if g.gate == "hmw_title")
        assert hmw_gate.score == 1.0
        assert hmw_gate.passed is True

    def test_no_hmw_prefix_scores_zero(self, tmp_data_dir):
        svc = self._make_framing_workspace(tmp_data_dir, "opp-frame-nohmw",
            title="Reduce first-order drop-off")
        report = svc.check_framing_quality("opp-frame-nohmw")
        hmw_gate = next(g for g in report.gates if g.gate == "hmw_title")
        assert hmw_gate.score == 0.0
        assert hmw_gate.passed is False

    def test_fully_complete_passes(self, tmp_data_dir):
        svc = self._make_framing_workspace(tmp_data_dir, "opp-frame-full",
            title="HMW make fresh groceries a habitual purchase on tMart?",
            type="hypothesis",
            description="Investigate whether recipe-based merchandising can shift grocery from transactional to habitual purchasing behavior among UAE users.",
            assumptions=[
                {"id": "asm-001", "content": "Recipe content drives basket size", "status": "untested", "importance": "critical"},
                {"id": "asm-002", "content": "Users browse before buying", "status": "untested", "importance": "medium"},
                {"id": "asm-003", "content": "Fresh produce quality is top concern", "status": "untested", "importance": "high"},
            ],
            success_signals=["Add-to-cart rate up 15%", "Repeat grocery orders up 20%", "Recipe page engagement > 30s"],
            kill_signals=["No basket size change", "Recipe pages bounce > 80%", "Support tickets increase"],
            context_refs=["L1/global", "L2a/groceries"],
        )
        report = svc.check_framing_quality("opp-frame-full")
        assert report.overall_score >= 0.8
        assert report.overall_passed is True

    def test_partial_scores_mid_range(self, tmp_data_dir):
        svc = self._make_framing_workspace(tmp_data_dir, "opp-frame-partial",
            title="HMW improve grocery experience?",
            type="question",
            description="Short description",
            assumptions=[{"id": "asm-001", "content": "One assumption", "status": "untested", "importance": "medium"}],
            success_signals=["One signal"],
            kill_signals=[],
            context_refs=[],
        )
        report = svc.check_framing_quality("opp-frame-partial")
        assert 0.3 < report.overall_score < 0.8
        assert report.overall_passed is False

    def test_framing_report_has_all_dimensions(self, tmp_data_dir):
        svc = self._make_framing_workspace(tmp_data_dir, "opp-frame-dims",
            title="HMW test?", type="hypothesis")
        report = svc.check_framing_quality("opp-frame-dims")
        gate_names = {g.gate for g in report.gates}
        expected = {"hmw_title", "type_set", "assumptions", "success_signals",
                    "kill_signals", "context_refs", "description_depth"}
        assert gate_names == expected
