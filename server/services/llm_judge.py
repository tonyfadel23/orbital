"""LLM-as-Judge service — Layer 2 quality evaluation using Claude Haiku."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

RUBRICS = [
    "evidence_grounding",
    "relevance",
    "actionability",
    "non_obviousness",
    "self_review_quality",
]

RUBRIC_PROMPTS = {
    "evidence_grounding": (
        "Does this finding cite a specific, verifiable source? "
        "A pass means the source is named and the claim could be checked. "
        "A fail means the finding makes unsupported assertions."
    ),
    "relevance": (
        "Is this finding directly relevant to the opportunity being investigated? "
        "A pass means the finding addresses a question the investigation needs answered. "
        "A fail means it is tangential or off-topic."
    ),
    "actionability": (
        "Does this finding lead to a concrete next step or decision? "
        "A pass means a product team could act on this information. "
        "A fail means it is too vague or abstract to inform action."
    ),
    "non_obviousness": (
        "Does this finding surface something that is not already common knowledge? "
        "A pass means it provides genuine insight beyond what is trivially known. "
        "A fail means it restates the obvious."
    ),
    "self_review_quality": (
        "Did the agent's self-review demonstrate critical thinking about its own work? "
        "A pass means the self-review notes are substantive and address methodology or limitations. "
        "A fail means the self-review is perfunctory or missing."
    ),
}


@dataclass
class RubricResult:
    rubric: str
    passed: bool
    reasoning: str

    def to_dict(self) -> dict:
        return {
            "rubric": self.rubric,
            "passed": self.passed,
            "reasoning": self.reasoning,
        }


@dataclass
class FindingJudgment:
    finding_id: str
    rubrics: list[RubricResult] = field(default_factory=list)

    @property
    def score(self) -> float:
        if not self.rubrics:
            return 0.0
        return sum(1 for r in self.rubrics if r.passed) / len(self.rubrics)

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "score": round(self.score, 3),
            "rubrics": [r.to_dict() for r in self.rubrics],
        }


@dataclass
class LayerTwoReport:
    opp_id: str
    judgments: list[FindingJudgment] = field(default_factory=list)
    pass_threshold: float = 0.6
    degraded: bool = False
    degraded_reason: str | None = None

    @property
    def overall_score(self) -> float:
        if not self.judgments:
            return 0.0
        return sum(j.score for j in self.judgments) / len(self.judgments)

    @property
    def overall_passed(self) -> bool:
        if not self.judgments:
            return False
        return self.overall_score >= self.pass_threshold

    def to_dict(self) -> dict:
        return {
            "opp_id": self.opp_id,
            "overall_passed": self.overall_passed,
            "overall_score": round(self.overall_score, 3),
            "pass_threshold": self.pass_threshold,
            "degraded": self.degraded,
            "degraded_reason": self.degraded_reason,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "judgments": [j.to_dict() for j in self.judgments],
        }


class LLMJudgeService:
    def __init__(self, workspace_svc, config: dict, api_key: str | None = None):
        self.workspace_svc = workspace_svc
        self._config = config
        self._l2_config = config.get("quality_gates", {}).get("layer_2", {})
        self._model = self._l2_config.get("model", "claude-haiku-4-5-20251001")
        self._pass_threshold = self._l2_config.get("pass_threshold", 0.6)
        self._enabled = self._l2_config.get("enabled", True)
        self._api_key = api_key

    async def evaluate_all(self, opp_id: str) -> LayerTwoReport:
        opp = self.workspace_svc.get_opportunity(opp_id)
        if opp is None:
            raise ValueError(f"Workspace {opp_id} not found")

        if not self._enabled:
            return LayerTwoReport(
                opp_id=opp_id,
                pass_threshold=self._pass_threshold,
                degraded=True,
                degraded_reason="Layer 2 disabled in config",
            )

        if not self._api_key:
            return LayerTwoReport(
                opp_id=opp_id,
                pass_threshold=self._pass_threshold,
                degraded=True,
                degraded_reason="No API key configured",
            )

        opp_context = f"{opp.get('title', '')} — {opp.get('description', '')}"
        contributions = self._load_contributions(opp_id)

        if not contributions:
            report = LayerTwoReport(opp_id=opp_id, pass_threshold=self._pass_threshold)
            self._persist(opp_id, report)
            return report

        judgments = []
        had_total_failure = False

        try:
            for contrib in contributions:
                self_review = contrib.get("self_review", {})
                for finding in contrib.get("findings", []):
                    judgment = await self.evaluate_finding(finding, self_review, opp_context)
                    judgments.append(judgment)
        except Exception as exc:
            logger.error("LLM Judge failed for %s: %s", opp_id, exc)
            had_total_failure = True

        if had_total_failure and not judgments:
            report = LayerTwoReport(
                opp_id=opp_id,
                pass_threshold=self._pass_threshold,
                degraded=True,
                degraded_reason=f"API error: {exc}",
            )
            self._persist(opp_id, report)
            return report

        report = LayerTwoReport(
            opp_id=opp_id,
            judgments=judgments,
            pass_threshold=self._pass_threshold,
        )
        self._persist(opp_id, report)
        return report

    async def evaluate_finding(
        self, finding: dict, self_review: dict, opp_context: str
    ) -> FindingJudgment:
        rubric_results = []
        for rubric_name in RUBRICS:
            try:
                result = await self._call_rubric(rubric_name, finding, self_review, opp_context)
                rubric_results.append(result)
            except Exception as exc:
                logger.warning("Rubric %s failed for %s: %s", rubric_name, finding.get("id"), exc)
                rubric_results.append(RubricResult(
                    rubric=rubric_name,
                    passed=False,
                    reasoning=f"Evaluation error: {exc}",
                ))
        return FindingJudgment(finding_id=finding.get("id", "unknown"), rubrics=rubric_results)

    async def _call_rubric(
        self, rubric_name: str, finding: dict, self_review: dict, opp_context: str
    ) -> RubricResult:
        import anthropic

        prompt = RUBRIC_PROMPTS[rubric_name]
        finding_text = json.dumps(finding, indent=2)
        self_review_text = json.dumps(self_review, indent=2)

        system_msg = (
            "You are a quality judge evaluating findings from a product investigation. "
            "Evaluate the finding against the rubric and respond with a JSON object: "
            '{"pass": true/false, "reasoning": "one-sentence explanation"}'
        )
        user_msg = (
            f"Opportunity context: {opp_context}\n\n"
            f"Finding:\n{finding_text}\n\n"
            f"Self-review:\n{self_review_text}\n\n"
            f"Rubric — {rubric_name}:\n{prompt}\n\n"
            "Respond with JSON only."
        )

        client = anthropic.Anthropic(api_key=self._api_key)
        response = client.messages.create(
            model=self._model,
            max_tokens=256,
            system=system_msg,
            messages=[{"role": "user", "content": user_msg}],
        )

        text = response.content[0].text
        parsed = json.loads(text)
        return RubricResult(
            rubric=rubric_name,
            passed=bool(parsed.get("pass", False)),
            reasoning=str(parsed.get("reasoning", "")),
        )

    def _load_contributions(self, opp_id: str) -> list[dict]:
        contrib_dir = self.workspace_svc.workspaces_dir / opp_id / "contributions"
        if not contrib_dir.exists():
            return []
        result = []
        for f in sorted(contrib_dir.iterdir()):
            if f.suffix != ".json":
                continue
            try:
                result.append(json.loads(f.read_text()))
            except Exception:
                continue
        return result

    def _persist(self, opp_id: str, report: LayerTwoReport) -> None:
        quality_dir = self.workspace_svc.workspaces_dir / opp_id / "quality"
        quality_dir.mkdir(parents=True, exist_ok=True)
        (quality_dir / "llm-judge.json").write_text(json.dumps(report.to_dict(), indent=2))
