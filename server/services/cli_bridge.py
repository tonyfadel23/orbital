"""CLI bridge — generate claude commands for launching investigations."""

import json
import shlex
from pathlib import Path


class CliBridge:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.workspaces_dir = project_root / "data" / "workspaces"

    def generate_command(self, opp_id: str) -> str:
        opp_path = self.workspaces_dir / opp_id / "opportunity.json"
        if not opp_path.exists():
            raise FileNotFoundError(f"Workspace {opp_id} not found")

        opp = json.loads(opp_path.read_text())
        status = opp.get("status", "unknown")

        if status == "aligning":
            raise ValueError(
                f"Opportunity {opp_id} is still in aligning status. "
                "Confirm the opportunity before launching."
            )

        roster = opp.get("roster")
        has_roster = roster is not None and len(roster) > 0
        title = opp.get("title", opp_id)
        enabled_tools = opp.get("enabled_tools", [])
        ws_path = f"data/workspaces/{opp_id}"

        if has_roster:
            agents = ", ".join(r["function"] for r in roster)
            roster_detail = json.dumps(roster, indent=2)
            prompt = (
                f"You are the Product Agent orchestrating Phase 2 (INVESTIGATE) "
                f"of an Orbital investigation.\n\n"
                f"WORKSPACE: {ws_path}/\n"
                f"OPPORTUNITY: {title}\n"
                f"ROSTER: {agents}\n\n"
                f"ROSTER DETAIL:\n{roster_detail}\n\n"
                f"STEP 1: Read {ws_path}/opportunity.json and context layers in data/context/. "
                f"Read schemas/contribution.schema.json for the required output format.\n\n"
                f"STEP 2: For EACH rostered function, use the Agent tool to spawn a subagent. "
                f"Each Agent call must include:\n"
                f"- The function name and its investigation tracks from the roster\n"
                f"- The full opportunity context (title, description, assumptions, success/kill signals)\n"
                f"- Instructions to read the context layers in data/context/\n"
                f"- Instructions to use the Write tool to save a contribution JSON file to "
                f"{ws_path}/contributions/{{function}}-round-1.json matching schemas/contribution.schema.json\n"
                f"- Instructions to use the Write tool to save a markdown artifact to "
                f"{ws_path}/artifacts/{{function}}.md with human-readable analysis\n"
                f"- The contribution schema structure: id, opportunity_id, agent_function, round, "
                f"findings (each with id, type, content, confidence, source, assumptions_addressed, direction), "
                f"artifacts_produced, cross_references, self_review, created_at\n\n"
                f"STEP 3: After all agents complete, summarize what was produced and what's ready for peer review.\n\n"
                f"CRITICAL: You MUST actually call the Agent tool — do NOT just describe what you would do. "
                f"Launch all agent subagents in parallel for maximum efficiency."
            )
        else:
            tools_line = (
                f"AVAILABLE TOOLS: {', '.join(enabled_tools)}\n"
                if enabled_tools else ""
            )
            prompt = (
                f"You are a product strategist helping frame an investigation opportunity.\n\n"
                f"WORKSPACE: {ws_path}/\n"
                f"OPPORTUNITY: {title}\n"
                f"{tools_line}\n"
                f"CONVERSATION MECHANICS:\n"
                f"You are invoked via `claude -p` and exit after each response.\n"
                f"The user replies, and you resume with `--resume`.\n"
                f"Do NOT use AskUserQuestion, EnterPlanMode, or any interactive tools.\n"
                f"Just write your response as plain text.\n\n"
                f"NOW — read {ws_path}/opportunity.json, then load relevant context from data/context/:\n"
                f"- L1/global.json (always)\n"
                f"- Matching L2a/ file (business line) and L2b/ file (market) if relevant\n\n"
                f"Then respond with EXACTLY this structure:\n\n"
                f"## My recommendation\n"
                f"[How I'd frame this as an investigation — the real question underneath, 1-2 sentences]\n\n"
                f"## What supports this\n"
                f"[2-3 bullet points connecting their idea to real data/strategy from the context files you just read]\n\n"
                f"## To sharpen\n"
                f"[ONE specific question — challenge an assumption, surface a gap, or test scope]\n\n"
                f"ON SUBSEQUENT TURNS (via --resume):\n"
                f"- Process the user's answer\n"
                f"- You MUST update {ws_path}/opportunity.json with refined framing "
                f"BEFORE producing your response. Use the Write tool to save changes to "
                f"title, type, description, assumptions, success_signals, kill_signals, and context_refs. "
                f"This file write is mandatory on every turn — do not skip it.\n"
                f"- Share what you updated and why\n"
                f"- Ask the next refining question — one per turn\n"
                f"- When the framing is solid (3-5 turns), recommend a roster and summarize the investigation plan\n\n"
                f"Be conversational. Share context insights, don't just interrogate.\n"
                f"Follow skills/orbit/SKILL.md Phase 0 for the refinement protocol."
            )

        system_append = (
            f"SCOPING RULES: Only read files in {ws_path}/ and data/context/. "
            f"Do NOT read other workspaces. Do NOT run /explore or other skills. "
            f"Stay focused on this investigation."
        )

        disallowed = ""
        permission = ""
        if not has_roster:
            disallowed = '--disallowedTools "EnterPlanMode,AskUserQuestion,ExitPlanMode" '
            permission = "--permission-mode acceptEdits "

        return (
            f"cd {self.project_root} && "
            f"claude -p {shlex.quote(prompt)} "
            f"--append-system-prompt {shlex.quote(system_append)} "
            f"{disallowed}{permission}"
            f"--output-format stream-json --verbose"
        )

    def generate_assemble_command(self, opp_id: str) -> str:
        """Generate a claude -p command for the /assemble skill (Phase 1)."""
        opp_path = self.workspaces_dir / opp_id / "opportunity.json"
        if not opp_path.exists():
            raise FileNotFoundError(f"Workspace {opp_id} not found")

        opp = json.loads(opp_path.read_text())
        status = opp.get("status", "unknown")

        if status != "assembled":
            raise ValueError(
                f"Opportunity {opp_id} has status '{status}' — "
                "must be 'assembled' to assemble a roster."
            )

        roster = opp.get("roster")
        if roster is not None and len(roster) > 0:
            raise ValueError(
                f"Opportunity {opp_id} already has a roster. "
                "Cannot assemble — roster already exists."
            )

        title = opp.get("title", opp_id)
        description = opp.get("description", "")
        context_refs = opp.get("context_refs", [])
        context_text = ", ".join(context_refs) if context_refs else "none specified"
        ws_path = f"data/workspaces/{opp_id}"

        prompt = (
            f"You are a product strategist assembling the investigation team "
            f"for an Orbital opportunity.\n\n"
            f"WORKSPACE: {ws_path}/\n"
            f"OPPORTUNITY: {title}\n"
            f"DESCRIPTION: {description}\n"
            f"CONTEXT REFS: {context_text}\n\n"
            f"CONVERSATION MECHANICS:\n"
            f"You are invoked via `claude -p` and exit after each response.\n"
            f"The user replies, and you resume with `--resume`.\n"
            f"Do NOT use AskUserQuestion, EnterPlanMode, or any interactive tools.\n"
            f"Just write your response as plain text.\n\n"
            f"STEP 1 — Read these files:\n"
            f"- {ws_path}/opportunity.json (the framed opportunity)\n"
            f"- data/config.json (roster templates, available agents, tool registry)\n"
            f"- .claude/agents/*.md (agent definitions — skim Role and Investigation Tracks)\n"
            f"- data/context/ layers per context_refs ({context_text})\n\n"
            f"STEP 2 — Present your recommendation with EXACTLY this structure:\n\n"
            f"## My recommendation\n"
            f"[Which roster template (core, market_entry, technical_deep_dive, full_spectrum), "
            f"agent count, 1-sentence rationale]\n\n"
            f"## Per-Agent Breakdown\n"
            f"[For each recommended agent: function, why needed for THIS opportunity, "
            f"2-3 investigation tracks (specific questions from assumptions/signals), "
            f"expected artifacts, tool access]\n\n"
            f"## What supports this\n"
            f"[2-3 bullets connecting the opportunity to loaded context data]\n\n"
            f"## To Finalize\n"
            f"[ONE question: missing function? Drop any? Adjust tracks?]\n\n"
            f"STEP 3 — Write the roster to disk:\n"
            f"After presenting your recommendation, you MUST use the Write tool to update "
            f"{ws_path}/opportunity.json with your recommended roster array and append to "
            f"refinement_history. This file write is mandatory on EVERY turn including the first.\n\n"
            f"ON SUBSEQUENT TURNS (via --resume):\n"
            f"- Process the user's feedback (add/remove agents, modify tracks, adjust tools)\n"
            f"- Update {ws_path}/opportunity.json with the revised roster draft "
            f"BEFORE producing your response.\n"
            f"- Present updated roster with changes highlighted\n"
            f"- When user confirms: set status to 'orbiting', append roster_confirmed "
            f"to refinement_history, print summary with agent count and track count\n\n"
            f"CRITICAL: You MUST use the Write tool to update opportunity.json on EVERY turn. "
            f"Do NOT skip the file write."
        )

        system_append = (
            f"SCOPING RULES: Only read files in {ws_path}/, data/context/, data/config.json, "
            f"and .claude/agents/. Do NOT read other workspaces. "
            f"Stay focused on assembling the roster."
        )

        return (
            f"cd {self.project_root} && "
            f"claude -p {shlex.quote(prompt)} "
            f"--append-system-prompt {shlex.quote(system_append)} "
            f'--disallowedTools "EnterPlanMode,AskUserQuestion,ExitPlanMode" '
            f"--permission-mode acceptEdits "
            f"--output-format stream-json --verbose "
            f"< /dev/null"
        )

    def generate_function_commands(self, opp_id: str) -> dict[str, str]:
        """Generate one claude -p command per rostered function for parallel Phase 2."""
        opp_path = self.workspaces_dir / opp_id / "opportunity.json"
        if not opp_path.exists():
            raise FileNotFoundError(f"Workspace {opp_id} not found")

        opp = json.loads(opp_path.read_text())
        roster = opp.get("roster")
        if not roster or len(roster) == 0:
            raise ValueError(
                f"Opportunity {opp_id} has no roster. "
                "Cannot generate function commands without a roster."
            )

        title = opp.get("title", opp_id)
        description = opp.get("description", "")
        assumptions = opp.get("assumptions", [])
        success_signals = opp.get("success_signals", [])
        kill_signals = opp.get("kill_signals", [])
        context_refs = opp.get("context_refs", [])
        ws_path = f"data/workspaces/{opp_id}"

        assumptions_text = "\n".join(
            f"- {a}" if isinstance(a, str)
            else f"- [{a.get('id','')}] {a.get('content','')}"
            for a in assumptions
        )
        success_text = "\n".join(f"- {s}" for s in success_signals)
        kill_text = "\n".join(f"- {k}" for k in kill_signals)
        context_text = ", ".join(context_refs) if context_refs else "none specified"

        commands = {}
        for entry in roster:
            fn = entry["function"]
            tracks = entry.get("investigation_tracks", [])
            tracks_lines = []
            for t in tracks:
                if isinstance(t, str):
                    tracks_lines.append(f"- {t}")
                else:
                    tracks_lines.append(
                        f"- Track: {t['track']}\n  Question: {t['question']}\n  "
                        f"Expected artifacts: {', '.join(t.get('expected_artifacts', []))}"
                    )
            tracks_text = "\n".join(tracks_lines)

            prompt = (
                f"You are the {fn} agent conducting Phase 2 (INVESTIGATE) "
                f"of an Orbital investigation.\n\n"
                f"WORKSPACE: {ws_path}/\n"
                f"OPPORTUNITY: {title}\n"
                f"DESCRIPTION: {description}\n\n"
                f"ASSUMPTIONS TO TEST:\n{assumptions_text}\n\n"
                f"SUCCESS SIGNALS:\n{success_text}\n\n"
                f"KILL SIGNALS:\n{kill_text}\n\n"
                f"CONTEXT LAYERS: {context_text}\n\n"
                f"YOUR INVESTIGATION TRACKS:\n{tracks_text}\n\n"
                f"INSTRUCTIONS:\n"
                f"1. Read {ws_path}/opportunity.json for full details\n"
                f"2. Read relevant context layers in data/context/ "
                f"(L1/global.json always, plus matching L2a and L2b files)\n"
                f"3. Read schemas/contribution.schema.json for the required output format\n"
                f"4. Investigate your assigned tracks thoroughly\n"
                f"5. Use the Write tool to save your contribution JSON to "
                f"{ws_path}/contributions/{fn}-round-1.json\n"
                f"   The contribution must match the schema: id (contrib-{fn}-YYYYMMDD-HHMMSS), "
                f"opportunity_id, agent_function, round, findings (each with id, type, content, "
                f"confidence, source, assumptions_addressed, direction), "
                f"artifacts_produced, cross_references, self_review, created_at\n"
                f"6. Use the Write tool to save a markdown artifact to "
                f"{ws_path}/artifacts/{fn}.md with human-readable analysis\n\n"
                f"CRITICAL: You MUST actually write both files using the Write tool. "
                f"Do NOT just describe what you would write — execute the writes."
            )

            system_append = (
                f"SCOPING RULES: Only read files in {ws_path}/ and data/context/ and schemas/. "
                f"Do NOT read other workspaces. Stay focused on this investigation."
            )

            commands[fn] = (
                f"cd {self.project_root} && "
                f"claude -p {shlex.quote(prompt)} "
                f"--append-system-prompt {shlex.quote(system_append)} "
                f"--permission-mode acceptEdits "
                f"--output-format stream-json --verbose "
                f"< /dev/null"
            )

        return commands

    def generate_dot_vote_commands(self, opp_id: str) -> dict[str, str]:
        """Generate one claude -p command per rostered agent for Phase 4b dot-vote."""
        opp_path = self.workspaces_dir / opp_id / "opportunity.json"
        if not opp_path.exists():
            raise FileNotFoundError(f"Workspace {opp_id} not found")

        opp = json.loads(opp_path.read_text())
        roster = opp.get("roster")
        if not roster or len(roster) == 0:
            raise ValueError(
                f"Opportunity {opp_id} has no roster. "
                "Cannot generate dot-vote commands without a roster."
            )

        title = opp.get("title", opp_id)
        ws_path = f"data/workspaces/{opp_id}"

        commands = {}
        for entry in roster:
            fn = entry["function"]

            prompt = (
                f"You are the {fn} agent conducting Phase 4b (DOT-VOTE) "
                f"of an Orbital investigation.\n\n"
                f"WORKSPACE: {ws_path}/\n"
                f"OPPORTUNITY: {title}\n\n"
                f"INSTRUCTIONS:\n"
                f"1. Read {ws_path}/synthesis.json to understand all proposed solutions\n"
                f"2. Read schemas/dot-vote.schema.json for the required output format\n"
                f"3. Score EVERY solution (1-10) on your function-specific scoring dimensions\n"
                f"   (see your agent definition in .claude/agents/{fn}.md for your dimensions)\n"
                f"4. Write a rationale (min 20 chars) for each solution score\n"
                f"5. Flag blockers, risks, opportunities, or needs_more_data as appropriate\n"
                f"6. If you cannot score a solution, add it to abstentions with a reason\n"
                f"7. Use the Write tool to save your vote to "
                f"{ws_path}/votes/{fn}-vote.json matching schemas/dot-vote.schema.json\n\n"
                f"CRITICAL: You MUST write your vote file using the Write tool. "
                f"Do NOT just describe what you would write — execute the write."
            )

            system_append = (
                f"SCOPING RULES: Only read files in {ws_path}/ and schemas/. "
                f"Do NOT read other workspaces. Stay focused on scoring solutions."
            )

            commands[fn] = (
                f"cd {self.project_root} && "
                f"claude -p {shlex.quote(prompt)} "
                f"--append-system-prompt {shlex.quote(system_append)} "
                f"--permission-mode acceptEdits "
                f"--output-format stream-json --verbose "
                f"< /dev/null"
            )

        return commands

    def generate_decision_brief_command(self, opp_id: str) -> str:
        """Generate a claude -p command for Phase 4c decision brief generation."""
        opp_path = self.workspaces_dir / opp_id / "opportunity.json"
        if not opp_path.exists():
            raise FileNotFoundError(f"Workspace {opp_id} not found")

        opp = json.loads(opp_path.read_text())
        title = opp.get("title", opp_id)
        ws_path = f"data/workspaces/{opp_id}"

        prompt = (
            f"You are the Product Agent generating a Phase 4c DECISION BRIEF "
            f"for an Orbital investigation.\n\n"
            f"WORKSPACE: {ws_path}/\n"
            f"OPPORTUNITY: {title}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Read {ws_path}/opportunity.json for full context\n"
            f"2. Read {ws_path}/synthesis.json for solutions, convergence, conflicts, counter-signals\n"
            f"3. Read all files in {ws_path}/votes/ for dot-vote scores and rationales\n"
            f"4. Generate a decision brief following the template in .claude/agents/product.md "
            f"(Decision Brief Generation section)\n"
            f"5. Use the Write tool to save the brief to "
            f"{ws_path}/artifacts/decision-brief.md\n\n"
            f"The brief must be readable by non-technical leadership. "
            f"Include: executive summary, key findings, ranked solutions with heat map, "
            f"evidence trail, risks, recommendation, and quality assessment.\n\n"
            f"CRITICAL: You MUST write the decision-brief.md file using the Write tool."
        )

        system_append = (
            f"SCOPING RULES: Only read files in {ws_path}/ and .claude/agents/product.md. "
            f"Do NOT read other workspaces. Stay focused on generating the decision brief."
        )

        return (
            f"cd {self.project_root} && "
            f"claude -p {shlex.quote(prompt)} "
            f"--append-system-prompt {shlex.quote(system_append)} "
            f"--permission-mode acceptEdits "
            f"--output-format stream-json --verbose "
            f"< /dev/null"
        )

    EVIDENCE_SOURCE_TYPES = (
        "data-query", "doc-search", "app-reviews",
        "slack-signal", "market-intel", "metrics-pull",
    )

    def generate_evidence_command(self, opp_id: str, source_type: str, query: str) -> str:
        """Generate a claude -p command for an evidence-gathering subprocess."""
        if source_type not in self.EVIDENCE_SOURCE_TYPES:
            raise ValueError(
                f"Invalid source_type '{source_type}'. "
                f"Must be one of: {', '.join(self.EVIDENCE_SOURCE_TYPES)}"
            )

        opp_path = self.workspaces_dir / opp_id / "opportunity.json"
        if not opp_path.exists():
            raise FileNotFoundError(f"Workspace {opp_id} not found")

        opp = json.loads(opp_path.read_text())
        title = opp.get("title", opp_id)
        ws_path = f"data/workspaces/{opp_id}"

        prompt = (
            f"You are an evidence-gathering agent for an Orbital investigation.\n\n"
            f"WORKSPACE: {ws_path}/\n"
            f"OPPORTUNITY: {title}\n"
            f"SOURCE TYPE: {source_type}\n"
            f"QUERY: {query}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Read {ws_path}/opportunity.json for full opportunity context\n"
            f"2. Read skills/evidence/{source_type}/SKILL.md for your process and output format\n"
            f"3. Read schemas/evidence.schema.json for the required JSON schema\n"
            f"4. Follow the skill process to gather evidence for the query\n"
            f"5. Use the Write tool to save your evidence JSON to "
            f"{ws_path}/evidence/ with an ID like ev-YYYYMMDD-HHMMSS\n\n"
            f"CRITICAL: You MUST write the evidence file using the Write tool. "
            f"Do NOT just describe what you would write — execute the write.\n"
            f"The evidence file MUST match schemas/evidence.schema.json."
        )

        system_append = (
            f"SCOPING RULES: Only read files in {ws_path}/, skills/evidence/{source_type}/, "
            f"and schemas/. Do NOT read other workspaces. "
            f"Stay focused on gathering evidence for this specific query."
        )

        return (
            f"cd {self.project_root} && "
            f"claude -p {shlex.quote(prompt)} "
            f"--append-system-prompt {shlex.quote(system_append)} "
            f'--disallowedTools "EnterPlanMode,AskUserQuestion,ExitPlanMode" '
            f"--permission-mode acceptEdits "
            f"--output-format stream-json --verbose "
            f"< /dev/null"
        )

    def generate_judge_command(self, opp_id: str) -> str:
        """Generate a claude -p command for the quality judge agent (Layer 3)."""
        opp_path = self.workspaces_dir / opp_id / "opportunity.json"
        if not opp_path.exists():
            raise FileNotFoundError(f"Workspace {opp_id} not found")

        opp = json.loads(opp_path.read_text())
        title = opp.get("title", opp_id)
        ws_path = f"data/workspaces/{opp_id}"

        prompt = (
            f"You are the Quality Judge agent performing an independent Layer 3 "
            f"evaluation of an Orbital investigation.\n\n"
            f"WORKSPACE: {ws_path}/\n"
            f"OPPORTUNITY: {title}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Read {ws_path}/opportunity.json for full opportunity context\n"
            f"2. Read all files in {ws_path}/contributions/ for agent contributions\n"
            f"3. Read {ws_path}/synthesis.json for the synthesized solutions\n"
            f"4. Read all files in {ws_path}/votes/ for dot-vote scores\n"
            f"5. Evaluate 5 cross-agent rubrics, scoring each 0.0-1.0:\n"
            f"   - contradictions_surfaced: Are contradictions between agents explicitly surfaced?\n"
            f"   - minority_viewpoints: Are minority viewpoints represented in synthesis?\n"
            f"   - evidence_based_recommendation: Does the recommendation follow from evidence?\n"
            f"   - risk_weighting: Are risk signals proportionally weighted?\n"
            f"   - solution_diversity: Is the solution portfolio genuinely diverse?\n"
            f"6. For each rubric provide: score (0.0-1.0), rationale (min 30 chars), "
            f"evidence_refs (specific finding/solution IDs)\n"
            f"7. Compute overall_score as average of rubric scores\n"
            f"8. Set overall_passed = true if overall_score >= 0.6\n"
            f"9. Use the Write tool to save results to "
            f"{ws_path}/quality/judge-evaluation.json\n\n"
            f"OUTPUT SCHEMA:\n"
            f'{{"opp_id": "{opp_id}", "rubrics": {{'
            f'"contradictions_surfaced": {{"score": 0.0, "rationale": "...", "evidence_refs": []}}, '
            f'...}}, "overall_score": 0.0, "overall_passed": false, '
            f'"timestamp": "ISO-8601"}}\n\n'
            f"CRITICAL: You MUST write the judge-evaluation.json file using the Write tool. "
            f"Do NOT just describe what you would write — execute the write."
        )

        system_append = (
            f"SCOPING RULES: Only read files in {ws_path}/. "
            f"Do NOT read other workspaces. "
            f"Stay focused on evaluating the quality of this investigation."
        )

        return (
            f"cd {self.project_root} && "
            f"claude -p {shlex.quote(prompt)} "
            f"--append-system-prompt {shlex.quote(system_append)} "
            f'--disallowedTools "EnterPlanMode,AskUserQuestion,ExitPlanMode" '
            f"--permission-mode acceptEdits "
            f"--output-format stream-json --verbose "
            f"< /dev/null"
        )

    def generate_resume_command(self, message: str, session_id: str | None = None) -> str:
        """Generate a command to resume conversation with a follow-up message."""
        resume_flag = f"--resume {session_id}" if session_id else "--resume"
        return (
            f"cd {self.project_root} && "
            f"claude -p {shlex.quote(message)} "
            f"{resume_flag} "
            f'--disallowedTools "EnterPlanMode,AskUserQuestion,ExitPlanMode" '
            f"--permission-mode acceptEdits "
            f"--output-format stream-json --verbose"
        )
