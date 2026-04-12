"""Quality gate service — Layer 1 deterministic checks for workspace quality."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    gate: str
    passed: bool
    score: float
    threshold: float
    blocking: bool
    details: str

    def to_dict(self) -> dict:
        return {
            "gate": self.gate,
            "passed": self.passed,
            "score": self.score,
            "threshold": self.threshold,
            "blocking": self.blocking,
            "details": self.details,
        }


@dataclass
class QualityReport:
    opp_id: str
    gates: list[GateResult] = field(default_factory=list)

    @property
    def overall_passed(self) -> bool:
        blocking_gates = [g for g in self.gates if g.blocking]
        if not blocking_gates:
            return True
        return all(g.passed for g in blocking_gates)

    @property
    def overall_score(self) -> float:
        if not self.gates:
            return 1.0
        return sum(g.score for g in self.gates) / len(self.gates)

    def to_dict(self) -> dict:
        return {
            "opp_id": self.opp_id,
            "overall_passed": self.overall_passed,
            "overall_score": round(self.overall_score, 3),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "gates": [g.to_dict() for g in self.gates],
        }


class QualityGateService:
    def __init__(self, workspace_svc, config: dict):
        self.workspace_svc = workspace_svc
        self.config = config
        self._qg_config = config.get("quality_gates", {})
        self._l1 = self._qg_config.get("layer_1", {})

    # --- Individual gate checks ---

    def check_assumption_coverage(self, opp_id: str) -> GateResult:
        cfg = self._l1.get("assumption_coverage", {})
        threshold = cfg.get("min_coverage", 1.0)
        blocking = cfg.get("blocking", True)

        opp = self.workspace_svc.get_opportunity(opp_id)
        assumptions = opp.get("assumptions", []) if opp else []
        if not assumptions:
            return GateResult("assumption_coverage", True, 1.0, threshold, blocking, "No assumptions defined")

        assumption_ids = {a["id"] for a in assumptions if isinstance(a, dict) and "id" in a}
        addressed = set()

        contributions = self._load_contributions(opp_id)
        for contrib in contributions:
            for finding in contrib.get("findings", []):
                for asm_id in finding.get("assumptions_addressed", []):
                    addressed.add(asm_id)

        covered = assumption_ids & addressed
        score = len(covered) / len(assumption_ids) if assumption_ids else 1.0
        passed = score >= threshold
        uncovered = assumption_ids - addressed
        details = f"{len(covered)}/{len(assumption_ids)} assumptions addressed"
        if uncovered:
            details += f"; uncovered: {', '.join(sorted(uncovered))}"

        return GateResult("assumption_coverage", passed, round(score, 3), threshold, blocking, details)

    def check_confidence_floor(self, opp_id: str) -> GateResult:
        cfg = self._l1.get("confidence_floor", {})
        threshold = cfg.get("threshold", 0.4)
        blocking = cfg.get("blocking", True)

        contributions = self._load_contributions(opp_id)
        all_confidences = []
        low_contribs = []

        for contrib in contributions:
            findings = contrib.get("findings", [])
            if not findings:
                continue
            confidences = [f.get("confidence", 0) for f in findings]
            mean_conf = sum(confidences) / len(confidences)
            all_confidences.append(mean_conf)
            if mean_conf < threshold:
                low_contribs.append(contrib.get("agent_function", "unknown"))

        if not all_confidences:
            return GateResult("confidence_floor", False, 0.0, threshold, blocking, "No findings to evaluate")

        min_mean = min(all_confidences)
        passed = min_mean >= threshold
        details = f"Min mean confidence: {min_mean:.2f}"
        if low_contribs:
            details += f"; low: {', '.join(low_contribs)}"

        return GateResult("confidence_floor", passed, round(min_mean, 3), threshold, blocking, details)

    def check_solution_distinctiveness(self, opp_id: str) -> GateResult:
        cfg = self._l1.get("solution_distinctiveness", {})
        max_jaccard = cfg.get("max_jaccard", 0.7)
        blocking = cfg.get("blocking", False)

        synthesis = self.workspace_svc._read_json_or_none(
            self.workspace_svc.workspaces_dir / opp_id / "synthesis.json"
        )
        if not synthesis:
            return GateResult("solution_distinctiveness", True, 0.0, max_jaccard, blocking, "No synthesis yet")

        solutions = synthesis.get("solutions", [])
        if len(solutions) < 2:
            return GateResult("solution_distinctiveness", True, 0.0, max_jaccard, blocking, "Fewer than 2 solutions")

        worst_jaccard = 0.0
        worst_pair = ("", "")
        for i, sol_a in enumerate(solutions):
            refs_a = set(sol_a.get("evidence_refs", []))
            for sol_b in solutions[i + 1:]:
                refs_b = set(sol_b.get("evidence_refs", []))
                union = refs_a | refs_b
                if not union:
                    continue
                jaccard = len(refs_a & refs_b) / len(union)
                if jaccard > worst_jaccard:
                    worst_jaccard = jaccard
                    worst_pair = (sol_a.get("id", "?"), sol_b.get("id", "?"))

        passed = worst_jaccard <= max_jaccard
        details = f"Max Jaccard: {worst_jaccard:.2f}"
        if not passed:
            details += f" between {worst_pair[0]} and {worst_pair[1]}"

        return GateResult("solution_distinctiveness", passed, round(worst_jaccard, 3), max_jaccard, blocking, details)

    def check_evidence_freshness(self, opp_id: str) -> GateResult:
        cfg = self._l1.get("evidence_freshness", {})
        max_age_days = cfg.get("max_age_days", 180)
        blocking = cfg.get("blocking", False)

        evidence_list = self.workspace_svc.list_evidence(opp_id)
        if not evidence_list:
            return GateResult("evidence_freshness", True, 1.0, max_age_days, blocking, "No evidence to check")

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=max_age_days)
        stale = []

        for ev in evidence_list:
            created = ev.get("created_at", "")
            if not created:
                continue
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if dt < cutoff:
                    stale.append(ev.get("id", "unknown"))
            except (ValueError, TypeError):
                continue

        fresh_count = len(evidence_list) - len(stale)
        score = fresh_count / len(evidence_list) if evidence_list else 1.0
        passed = len(stale) == 0
        details = f"{fresh_count}/{len(evidence_list)} evidence items fresh (within {max_age_days} days)"
        if stale:
            details += f"; stale: {', '.join(stale)}"

        return GateResult("evidence_freshness", passed, round(score, 3), max_age_days, blocking, details)

    def check_vote_quorum(self, opp_id: str) -> GateResult:
        cfg = self._l1.get("vote_quorum", {})
        min_pct = cfg.get("min_pct", 0.8)
        blocking = cfg.get("blocking", True)

        opp = self.workspace_svc.get_opportunity(opp_id)
        roster = opp.get("roster", []) if opp else []
        if not roster:
            return GateResult("vote_quorum", True, 1.0, min_pct, blocking, "No roster defined")

        roster_functions = {r["function"] for r in roster}
        votes = self.workspace_svc.get_votes(opp_id)
        voted_functions = {v["voter_function"] for v in votes}

        score = len(voted_functions & roster_functions) / len(roster_functions)
        passed = score >= min_pct
        missing = roster_functions - voted_functions
        details = f"{len(voted_functions & roster_functions)}/{len(roster_functions)} roster members voted"
        if missing:
            details += f"; missing: {', '.join(sorted(missing))}"

        return GateResult("vote_quorum", passed, round(score, 3), min_pct, blocking, details)

    def check_finding_density(self, opp_id: str) -> GateResult:
        cfg = self._l1.get("finding_density", {})
        min_findings = cfg.get("min_findings", 3)
        blocking = cfg.get("blocking", True)

        contributions = self._load_contributions(opp_id)
        if not contributions:
            return GateResult("finding_density", False, 0.0, min_findings, blocking, "No contributions")

        sparse = []
        min_count = float("inf")
        for contrib in contributions:
            count = len(contrib.get("findings", []))
            if count < min_findings:
                sparse.append(f"{contrib.get('agent_function', '?')}({count})")
            if count < min_count:
                min_count = count

        score = min_count / min_findings if min_findings > 0 else 1.0
        score = min(score, 1.0)
        passed = len(sparse) == 0
        details = f"Min findings per contribution: {min_count}"
        if sparse:
            details += f"; sparse: {', '.join(sparse)}"

        return GateResult("finding_density", passed, round(score, 3), min_findings, blocking, details)

    # --- Orchestration ---

    def evaluate_all(self, opp_id: str) -> QualityReport:
        opp = self.workspace_svc.get_opportunity(opp_id)
        if opp is None:
            raise ValueError(f"Workspace {opp_id} not found")

        gates = []
        checks = [
            ("assumption_coverage", self.check_assumption_coverage),
            ("confidence_floor", self.check_confidence_floor),
            ("solution_distinctiveness", self.check_solution_distinctiveness),
            ("evidence_freshness", self.check_evidence_freshness),
            ("vote_quorum", self.check_vote_quorum),
            ("finding_density", self.check_finding_density),
        ]

        for gate_name, check_fn in checks:
            gate_cfg = self._l1.get(gate_name, {})
            if not gate_cfg.get("enabled", True):
                continue
            gates.append(check_fn(opp_id))

        return QualityReport(opp_id=opp_id, gates=gates)

    def can_transition(self, opp_id: str, phase: str) -> tuple[bool, list[str], list[str]]:
        if not self._qg_config.get("enabled", True):
            return True, [], []

        report = self.evaluate_all(opp_id)
        blockers = []
        warnings = []

        for gate in report.gates:
            if not gate.passed:
                msg = f"{gate.gate}: {gate.details}"
                if gate.blocking:
                    blockers.append(msg)
                else:
                    warnings.append(msg)

        can = len(blockers) == 0
        return can, blockers, warnings

    # --- Helpers ---

    def _load_contributions(self, opp_id: str) -> list[dict]:
        contrib_dir = self.workspace_svc.workspaces_dir / opp_id / "contributions"
        if not contrib_dir.exists():
            return []
        result = []
        for f in sorted(contrib_dir.iterdir()):
            if f.suffix != ".json":
                continue
            try:
                import json
                result.append(json.loads(f.read_text()))
            except Exception:
                continue
        return result
