"""Tests for CLI bridge — generate claude commands for investigations."""

import pytest

from server.services.cli_bridge import CliBridge


class TestCliBridge:
    def test_generate_command_open_with_roster(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260405-120000")
        assert "claude" in cmd
        assert "opp-20260405-120000" in cmd
        assert "/orbit" in cmd.lower() or "orbit" in cmd.lower()

    def test_generate_command_aligning_raises(self, tmp_project_root, tmp_data_dir):
        import json
        # Create an aligning workspace
        ws = tmp_data_dir / "workspaces" / "opp-20260412-090000"
        ws.mkdir(parents=True)
        (ws / "contributions").mkdir()
        (ws / "reviews").mkdir()
        (ws / "artifacts").mkdir()
        opp = {
            "id": "opp-20260412-090000", "type": "hypothesis",
            "title": "Drafting opportunity test title",
            "description": "This opportunity is still being aligned",
            "context_refs": [], "assumptions": [],
            "success_signals": ["Something"], "kill_signals": ["Nothing"],
            "status": "aligning", "decision": None,
            "created_at": "2026-04-12T09:00:00Z", "updated_at": "2026-04-12T09:00:00Z"
        }
        (ws / "opportunity.json").write_text(json.dumps(opp))
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(ValueError, match="aligning"):
            bridge.generate_command("opp-20260412-090000")

    def test_generate_command_not_found(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(FileNotFoundError):
            bridge.generate_command("opp-nonexistent")

    def test_command_includes_project_dir(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260405-120000")
        assert str(tmp_project_root) in cmd

    def test_command_includes_stream_json(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260405-120000")
        assert "--output-format stream-json" in cmd
        assert "--verbose" in cmd

    def test_command_includes_append_system_prompt(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260405-120000")
        assert "--append-system-prompt" in cmd

    def test_command_scoping_rules(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260405-120000")
        assert "do NOT read other workspaces" in cmd.lower() or "do not read other workspaces" in cmd.lower()

    def test_command_includes_roster_agents(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260405-120000")
        assert "product" in cmd
        assert "data" in cmd
        assert "design" in cmd
        assert "engineering" in cmd

    def test_phase2_prompt_instructs_agent_tool_calls(self, tmp_project_root):
        """Phase 2 prompt must explicitly tell the orchestrator to call the Agent tool."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260405-120000")
        lower = cmd.lower()
        # Must mention using the Agent tool explicitly
        assert "agent tool" in lower or "agent subagent" in lower
        # Must instruct writing contribution JSON files
        assert "contribution" in lower
        assert "contributions/" in lower
        # Must instruct writing artifact markdown files
        assert "artifact" in lower
        assert "artifacts/" in lower
        # Must reference the contribution schema
        assert "contribution.schema.json" in lower or "schema" in lower
        # Must tell agents to use Write tool for output
        assert "write" in lower

    def test_phase2_prompt_includes_investigation_tracks(self, tmp_project_root):
        """Phase 2 prompt must pass investigation tracks to each agent."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260405-120000")
        lower = cmd.lower()
        # Must mention investigation tracks from roster
        assert "investigation" in lower and "track" in lower

    def test_phase2_prompt_includes_context_loading(self, tmp_project_root):
        """Phase 2 prompt must instruct agents to read context layers."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260405-120000")
        lower = cmd.lower()
        assert "data/context/" in lower
        assert "opportunity.json" in lower

    # --- Per-function command generation for Phase 2 parallel launch ---

    def test_generate_function_commands_returns_dict(self, tmp_project_root):
        """generate_function_commands returns a dict keyed by function name."""
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_function_commands("opp-20260405-120000")
        assert isinstance(cmds, dict)
        assert set(cmds.keys()) == {"product", "data", "design", "engineering"}

    def test_function_command_includes_function_role(self, tmp_project_root):
        """Each function command must identify the agent's role."""
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_function_commands("opp-20260405-120000")
        for fn, cmd in cmds.items():
            assert fn in cmd.lower()

    def test_function_command_writes_contribution(self, tmp_project_root):
        """Each function command must instruct writing a contribution JSON."""
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_function_commands("opp-20260405-120000")
        for fn, cmd in cmds.items():
            lower = cmd.lower()
            assert f"contributions/{fn}-round-1.json" in lower

    def test_function_command_writes_artifact(self, tmp_project_root):
        """Each function command must instruct writing a markdown artifact."""
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_function_commands("opp-20260405-120000")
        for fn, cmd in cmds.items():
            lower = cmd.lower()
            assert f"artifacts/{fn}.md" in lower

    def test_function_command_reads_context(self, tmp_project_root):
        """Each function command must instruct reading context layers."""
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_function_commands("opp-20260405-120000")
        for fn, cmd in cmds.items():
            lower = cmd.lower()
            assert "data/context/" in lower
            assert "opportunity.json" in lower

    def test_function_command_includes_schema(self, tmp_project_root):
        """Each function command must reference the contribution schema."""
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_function_commands("opp-20260405-120000")
        for fn, cmd in cmds.items():
            lower = cmd.lower()
            assert "contribution.schema.json" in lower or "schema" in lower

    def test_function_command_uses_accept_edits(self, tmp_project_root):
        """Each function command must use --permission-mode acceptEdits."""
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_function_commands("opp-20260405-120000")
        for fn, cmd in cmds.items():
            assert "--permission-mode acceptEdits" in cmd

    def test_function_command_no_roster_raises(self, tmp_project_root, tmp_data_dir):
        """generate_function_commands raises if no roster."""
        import json
        ws = tmp_data_dir / "workspaces" / "opp-20260412-200000"
        ws.mkdir(parents=True)
        (ws / "contributions").mkdir()
        (ws / "reviews").mkdir()
        (ws / "artifacts").mkdir()
        opp = {
            "id": "opp-20260412-200000", "type": "hypothesis",
            "title": "No roster", "description": "Test",
            "context_refs": [], "assumptions": [],
            "success_signals": [], "kill_signals": [],
            "status": "assembled", "roster": None, "decision": None,
            "created_at": "2026-04-12T20:00:00Z",
            "updated_at": "2026-04-12T20:00:00Z",
        }
        (ws / "opportunity.json").write_text(json.dumps(opp))
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(ValueError, match="roster"):
            bridge.generate_function_commands("opp-20260412-200000")

    def test_command_includes_title(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260405-120000")
        assert "Test opportunity for server tests" in cmd

    def test_generate_command_no_roster_phase0(self, tmp_project_root, tmp_data_dir):
        import json
        ws = tmp_data_dir / "workspaces" / "opp-20260412-100000"
        ws.mkdir(parents=True)
        (ws / "contributions").mkdir()
        (ws / "reviews").mkdir()
        (ws / "artifacts").mkdir()
        opp = {
            "id": "opp-20260412-100000", "type": "hypothesis",
            "title": "No roster opportunity for Phase 0",
            "description": "This opportunity has no roster yet",
            "context_refs": [], "assumptions": [],
            "success_signals": ["Something"], "kill_signals": ["Nothing"],
            "status": "assembled", "roster": None, "decision": None,
            "created_at": "2026-04-12T10:00:00Z", "updated_at": "2026-04-12T10:00:00Z"
        }
        (ws / "opportunity.json").write_text(json.dumps(opp))
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260412-100000")
        assert "phase 0" in cmd.lower() or "product strategist" in cmd.lower()
        assert "opp-20260412-100000" in cmd
        assert "--append-system-prompt" in cmd
        # Turn-aware: agent knows conversation mechanics
        assert "conversation mechanics" in cmd.lower() or "multi-turn" in cmd.lower()
        # Agent must NOT use AskUserQuestion (auto-resolves in -p mode)
        assert "do not use askuserquestion" in cmd.lower()
        # One question per turn, not a dump of everything
        assert "one" in cmd.lower() and "question" in cmd.lower()
        # Conversational tone
        assert "conversational" in cmd.lower()

    def test_phase0_prompt_has_output_format(self, tmp_project_root, tmp_data_dir):
        """Phase 0 prompt must specify an explicit output structure so the agent
        reliably produces context insights + a question, not just a brief ack."""
        import json
        ws = tmp_data_dir / "workspaces" / "opp-20260412-100000"
        ws.mkdir(parents=True, exist_ok=True)
        (ws / "contributions").mkdir(exist_ok=True)
        (ws / "reviews").mkdir(exist_ok=True)
        (ws / "artifacts").mkdir(exist_ok=True)
        opp = {
            "id": "opp-20260412-100000", "type": "hypothesis",
            "title": "Test output format",
            "description": "Testing the prompt structure",
            "context_refs": [], "assumptions": [],
            "success_signals": ["X"], "kill_signals": ["Y"],
            "status": "assembled", "roster": None, "decision": None,
            "created_at": "2026-04-12T10:00:00Z",
            "updated_at": "2026-04-12T10:00:00Z",
        }
        (ws / "opportunity.json").write_text(json.dumps(opp))
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260412-100000")
        lower = cmd.lower()
        # Must prescribe a response structure (not just numbered steps)
        assert "respond with exactly" in lower or "structure" in lower
        # Must include context insights section
        assert "context" in lower
        # Must include a question section
        assert "sharpen" in lower or "question" in lower

    def test_phase0_subsequent_turns_require_file_write(self, tmp_project_root, tmp_data_dir):
        """Phase 0 prompt must make opportunity.json update mandatory, not advisory."""
        import json
        ws = tmp_data_dir / "workspaces" / "opp-20260412-130000"
        ws.mkdir(parents=True)
        (ws / "contributions").mkdir()
        (ws / "reviews").mkdir()
        (ws / "artifacts").mkdir()
        opp = {
            "id": "opp-20260412-130000", "type": "hypothesis",
            "title": "Test mandatory writes",
            "description": "Testing prompt",
            "context_refs": [], "assumptions": [],
            "success_signals": ["X"], "kill_signals": ["Y"],
            "status": "assembled", "roster": None, "decision": None,
            "created_at": "2026-04-12T13:00:00Z",
            "updated_at": "2026-04-12T13:00:00Z",
        }
        (ws / "opportunity.json").write_text(json.dumps(opp))
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260412-130000")
        lower = cmd.lower()
        # Must use CRITICAL or MUST to make file write mandatory
        assert "must" in lower and "opportunity.json" in lower
        # The update instruction should come BEFORE the response instruction
        must_pos = lower.find("must")
        respond_pos = lower.find("share what you updated")
        assert must_pos < respond_pos, "File write must be instructed before response text"

    def test_phase0_disallows_interactive_tools(self, tmp_project_root, tmp_data_dir):
        """Phase 0 must use --disallowedTools to block plan mode and interactive tools."""
        import json
        ws = tmp_data_dir / "workspaces" / "opp-20260412-140000"
        ws.mkdir(parents=True)
        (ws / "contributions").mkdir()
        (ws / "reviews").mkdir()
        (ws / "artifacts").mkdir()
        opp = {
            "id": "opp-20260412-140000", "type": "signal",
            "title": "Test disallowed tools",
            "description": "Testing",
            "context_refs": [], "assumptions": [],
            "success_signals": [], "kill_signals": [],
            "status": "assembled", "roster": None, "decision": None,
            "created_at": "2026-04-12T14:00:00Z",
            "updated_at": "2026-04-12T14:00:00Z",
        }
        (ws / "opportunity.json").write_text(json.dumps(opp))
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260412-140000")
        assert "--disallowedTools" in cmd or "--disallowed-tools" in cmd
        assert "EnterPlanMode" in cmd
        assert "AskUserQuestion" in cmd

    def test_phase0_uses_accept_edits_permission(self, tmp_project_root, tmp_data_dir):
        """Phase 0 must use --permission-mode acceptEdits so agent can write files."""
        import json
        ws = tmp_data_dir / "workspaces" / "opp-20260412-150000"
        ws.mkdir(parents=True)
        (ws / "contributions").mkdir()
        (ws / "reviews").mkdir()
        (ws / "artifacts").mkdir()
        opp = {
            "id": "opp-20260412-150000", "type": "signal",
            "title": "Test permission mode",
            "description": "Testing",
            "context_refs": [], "assumptions": [],
            "success_signals": [], "kill_signals": [],
            "status": "assembled", "roster": None, "decision": None,
            "created_at": "2026-04-12T15:00:00Z",
            "updated_at": "2026-04-12T15:00:00Z",
        }
        (ws / "opportunity.json").write_text(json.dumps(opp))
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260412-150000")
        assert "--permission-mode acceptEdits" in cmd

    def test_command_includes_enabled_tools_in_phase0(self, tmp_project_root, tmp_data_dir):
        import json
        ws = tmp_data_dir / "workspaces" / "opp-20260412-110000"
        ws.mkdir(parents=True)
        (ws / "contributions").mkdir()
        (ws / "reviews").mkdir()
        (ws / "artifacts").mkdir()
        opp = {
            "id": "opp-20260412-110000", "type": "hypothesis",
            "title": "Opportunity with enabled tools",
            "description": "Has connectors enabled",
            "context_refs": [], "assumptions": [],
            "success_signals": ["Something"], "kill_signals": ["Nothing"],
            "status": "assembled", "roster": None, "decision": None,
            "enabled_tools": ["figma", "bigquery"],
            "created_at": "2026-04-12T11:00:00Z", "updated_at": "2026-04-12T11:00:00Z"
        }
        (ws / "opportunity.json").write_text(json.dumps(opp))
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260412-110000")
        assert "available tools" in cmd.lower()
        assert "figma" in cmd
        assert "bigquery" in cmd

    def test_command_no_tools_line_when_empty(self, tmp_project_root, tmp_data_dir):
        import json
        ws = tmp_data_dir / "workspaces" / "opp-20260412-120000"
        ws.mkdir(parents=True)
        (ws / "contributions").mkdir()
        (ws / "reviews").mkdir()
        (ws / "artifacts").mkdir()
        opp = {
            "id": "opp-20260412-120000", "type": "hypothesis",
            "title": "Opportunity without enabled tools",
            "description": "No connectors",
            "context_refs": [], "assumptions": [],
            "success_signals": ["Something"], "kill_signals": ["Nothing"],
            "status": "assembled", "roster": None, "decision": None,
            "enabled_tools": [],
            "created_at": "2026-04-12T12:00:00Z", "updated_at": "2026-04-12T12:00:00Z"
        }
        (ws / "opportunity.json").write_text(json.dumps(opp))
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-20260412-120000")
        assert "available tools" not in cmd.lower()

    def test_generate_resume_command(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_resume_command("user reply here")
        assert "claude" in cmd
        assert "--resume" in cmd
        assert "user reply here" in cmd
        assert "--output-format stream-json" in cmd
        assert "-p" in cmd
        assert str(tmp_project_root) in cmd

    def test_generate_resume_command_with_session_id(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_resume_command("reply", session_id="abc-123-def")
        assert "--resume abc-123-def" in cmd
        assert "reply" in cmd

    def test_generate_resume_command_without_session_id(self, tmp_project_root):
        """Without session_id, bare --resume is used (backwards compat)."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_resume_command("reply")
        assert "--resume" in cmd
        # Should not have a UUID after --resume
        parts = cmd.split("--resume")
        after = parts[1].strip()
        assert after.startswith("--") or after == ""  # next flag or end

    def test_generate_resume_command_quotes_message(self, tmp_project_root):
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_resume_command("it's a test with 'quotes'")
        # Should not break shell parsing
        assert "--resume" in cmd
        assert "claude" in cmd

    def test_resume_command_includes_disallowed_tools(self, tmp_project_root):
        """Resume must carry forward --disallowedTools so agent can't enter plan mode."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_resume_command("reply", session_id="abc-123")
        assert "--disallowedTools" in cmd or "--disallowed-tools" in cmd
        assert "EnterPlanMode" in cmd
        assert "AskUserQuestion" in cmd
        assert "ExitPlanMode" in cmd

    def test_resume_command_includes_permission_mode(self, tmp_project_root):
        """Resume must carry forward --permission-mode acceptEdits."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_resume_command("reply", session_id="abc-123")
        assert "--permission-mode acceptEdits" in cmd

    # --- Assemble command generation ---

    def _make_open_workspace(self, tmp_data_dir, opp_id="opp-20260412-160000", **overrides):
        """Helper: create a workspace with status=assembled, roster=null."""
        import json
        ws = tmp_data_dir / "workspaces" / opp_id
        ws.mkdir(parents=True, exist_ok=True)
        for d in ("contributions", "reviews", "artifacts"):
            (ws / d).mkdir(exist_ok=True)
        opp = {
            "id": opp_id, "type": "hypothesis",
            "title": "Framed opportunity ready for assembly",
            "description": "A well-framed opportunity",
            "context_refs": ["L1-global", "L2a-groceries"],
            "assumptions": [
                {"id": "asm-001", "content": "Users want weekly baskets", "status": "untested", "importance": "critical"}
            ],
            "success_signals": ["Basket creation rate > 5%"],
            "kill_signals": ["No engagement after 2 weeks"],
            "status": "assembled", "roster": None, "decision": None,
            "created_at": "2026-04-12T16:00:00Z",
            "updated_at": "2026-04-12T16:00:00Z",
        }
        opp.update(overrides)
        (ws / "opportunity.json").write_text(json.dumps(opp))
        return opp_id

    def test_assemble_command_reads_config_and_agents(self, tmp_project_root, tmp_data_dir):
        """Assemble prompt must instruct agent to read config.json and .claude/agents/."""
        opp_id = self._make_open_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_assemble_command(opp_id)
        lower = cmd.lower()
        assert "config.json" in lower
        assert ".claude/agents" in lower

    def test_assemble_rejects_non_assembled_status(self, tmp_project_root, tmp_data_dir):
        """Assemble must reject opportunities not in 'assembled' status."""
        for status in ("aligning", "orbiting", "landed"):
            opp_id = self._make_open_workspace(
                tmp_data_dir,
                opp_id=f"opp-reject-{status}",
                status=status,
            )
            bridge = CliBridge(tmp_project_root)
            with pytest.raises(ValueError, match="assembled"):
                bridge.generate_assemble_command(opp_id)

    def test_assemble_rejects_existing_roster(self, tmp_project_root, tmp_data_dir):
        """Assemble must reject if roster is already populated."""
        opp_id = self._make_open_workspace(
            tmp_data_dir,
            opp_id="opp-has-roster",
            roster=[{"function": "product", "rationale": "test", "investigation_tracks": [], "tool_access": []}],
        )
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(ValueError, match="roster"):
            bridge.generate_assemble_command(opp_id)

    def test_assemble_includes_context_refs(self, tmp_project_root, tmp_data_dir):
        """Assemble prompt must reference context layer paths."""
        opp_id = self._make_open_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_assemble_command(opp_id)
        lower = cmd.lower()
        assert "data/context/" in lower

    def test_assemble_has_mandatory_write_instruction(self, tmp_project_root, tmp_data_dir):
        """Assemble prompt must make opportunity.json writes mandatory."""
        opp_id = self._make_open_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_assemble_command(opp_id)
        lower = cmd.lower()
        assert "must" in lower and "opportunity.json" in lower
        assert "write" in lower

    def test_assemble_command_not_found(self, tmp_project_root):
        """Assemble raises FileNotFoundError for missing workspace."""
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(FileNotFoundError):
            bridge.generate_assemble_command("opp-nonexistent")

    def test_assemble_uses_accept_edits(self, tmp_project_root, tmp_data_dir):
        """Assemble must use --permission-mode acceptEdits."""
        opp_id = self._make_open_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_assemble_command(opp_id)
        assert "--permission-mode acceptEdits" in cmd

    def test_assemble_disallows_interactive_tools(self, tmp_project_root, tmp_data_dir):
        """Assemble must block plan mode and interactive tools."""
        opp_id = self._make_open_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_assemble_command(opp_id)
        assert "--disallowedTools" in cmd or "--disallowed-tools" in cmd
        assert "EnterPlanMode" in cmd
        assert "AskUserQuestion" in cmd

    def test_assemble_includes_roster_template_reference(self, tmp_project_root, tmp_data_dir):
        """Assemble prompt must mention roster templates."""
        opp_id = self._make_open_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_assemble_command(opp_id)
        lower = cmd.lower()
        assert "roster" in lower and "template" in lower

    def test_agree_prompt_leads_with_recommendation(self, tmp_project_root, tmp_data_dir):
        """Phase 0 prompt must put 'My recommendation' BEFORE 'What supports this'."""
        import json
        ws = tmp_data_dir / "workspaces" / "opp-rec-order"
        ws.mkdir(parents=True, exist_ok=True)
        for d in ("contributions", "reviews", "artifacts"):
            (ws / d).mkdir(exist_ok=True)
        opp = {
            "id": "opp-rec-order", "type": "hypothesis",
            "title": "Test recommendation order",
            "description": "Recommendation should come first",
            "context_refs": [], "assumptions": [],
            "success_signals": ["X"], "kill_signals": ["Y"],
            "status": "assembled", "roster": None, "decision": None,
            "created_at": "2026-04-12T10:00:00Z",
            "updated_at": "2026-04-12T10:00:00Z",
        }
        (ws / "opportunity.json").write_text(json.dumps(opp))
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_command("opp-rec-order")
        lower = cmd.lower()
        rec_pos = lower.index("my recommendation")
        supports_pos = lower.index("what supports")
        assert rec_pos < supports_pos, "Recommendation must appear before supporting evidence"

    def test_assemble_prompt_leads_with_recommendation(self, tmp_project_root, tmp_data_dir):
        """Phase 1 prompt must put 'My recommendation' BEFORE 'What supports this'."""
        opp_id = self._make_open_workspace(tmp_data_dir, opp_id="opp-asm-rec-order")
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_assemble_command(opp_id)
        lower = cmd.lower()
        rec_pos = lower.index("my recommendation")
        supports_pos = lower.index("what supports")
        assert rec_pos < supports_pos, "Recommendation must appear before supporting evidence"

    # --- Dot-vote command generation ---

    def _make_synthesized_workspace(self, tmp_data_dir, opp_id="opp-20260412-170000", **overrides):
        """Helper: create a workspace with status=converging and a roster."""
        import json
        ws = tmp_data_dir / "workspaces" / opp_id
        ws.mkdir(parents=True, exist_ok=True)
        for d in ("contributions", "reviews", "artifacts", "votes"):
            (ws / d).mkdir(exist_ok=True)
        opp = {
            "id": opp_id, "type": "hypothesis",
            "title": "Synthesized opportunity ready for dot-vote",
            "description": "Has synthesis with 3+ solutions",
            "context_refs": ["L1-global"],
            "assumptions": [
                {"id": "asm-001", "content": "Users want savings", "status": "untested", "importance": "critical"}
            ],
            "success_signals": ["Conversion > 5%"],
            "kill_signals": ["No engagement"],
            "status": "converging",
            "roster": [
                {"function": "product", "rationale": "Orchestrator", "investigation_tracks": [{"track": "framing", "question": "What is core question?", "expected_artifacts": ["product.md"]}], "tool_access": ["google-drive"]},
                {"function": "data", "rationale": "Baselines", "investigation_tracks": [{"track": "baselines", "question": "What are metrics?", "expected_artifacts": ["data.md"]}], "tool_access": ["google-sheets"]},
                {"function": "design", "rationale": "UX audit", "investigation_tracks": [{"track": "audit", "question": "UX gaps?", "expected_artifacts": ["design.md"]}], "tool_access": ["figma"]},
            ],
            "decision": None,
            "created_at": "2026-04-12T17:00:00Z",
            "updated_at": "2026-04-12T17:00:00Z",
        }
        opp.update(overrides)
        (ws / "opportunity.json").write_text(json.dumps(opp))
        # Write a minimal synthesis.json
        synthesis = {
            "id": f"synth-{opp_id.replace('opp-', '')}",
            "opportunity_id": opp_id,
            "status": "presented",
            "solutions": [
                {"id": "sol-001", "title": "Solution A", "archetype": "incremental"},
                {"id": "sol-002", "title": "Solution B", "archetype": "moderate"},
                {"id": "sol-003", "title": "Solution C", "archetype": "ambitious"},
            ],
        }
        (ws / "synthesis.json").write_text(json.dumps(synthesis))
        return opp_id

    def test_dot_vote_commands_returns_dict_per_roster(self, tmp_project_root, tmp_data_dir):
        """generate_dot_vote_commands returns one command per rostered agent."""
        opp_id = self._make_synthesized_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_dot_vote_commands(opp_id)
        assert isinstance(cmds, dict)
        assert set(cmds.keys()) == {"product", "data", "design"}

    def test_dot_vote_command_references_synthesis(self, tmp_project_root, tmp_data_dir):
        """Each dot-vote command instructs the agent to read synthesis.json."""
        opp_id = self._make_synthesized_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_dot_vote_commands(opp_id)
        for fn, cmd in cmds.items():
            assert "synthesis.json" in cmd.lower()

    def test_dot_vote_command_writes_vote_file(self, tmp_project_root, tmp_data_dir):
        """Each dot-vote command instructs writing to votes/{function}-vote.json."""
        opp_id = self._make_synthesized_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_dot_vote_commands(opp_id)
        for fn, cmd in cmds.items():
            assert f"votes/{fn}-vote.json" in cmd.lower()

    def test_dot_vote_command_mentions_scoring(self, tmp_project_root, tmp_data_dir):
        """Each dot-vote command mentions scoring solutions."""
        opp_id = self._make_synthesized_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_dot_vote_commands(opp_id)
        for fn, cmd in cmds.items():
            lower = cmd.lower()
            assert "score" in lower or "scoring" in lower

    def test_dot_vote_command_references_schema(self, tmp_project_root, tmp_data_dir):
        """Each dot-vote command references the dot-vote schema."""
        opp_id = self._make_synthesized_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_dot_vote_commands(opp_id)
        for fn, cmd in cmds.items():
            assert "dot-vote.schema.json" in cmd.lower() or "dot-vote" in cmd.lower()

    def test_dot_vote_command_uses_accept_edits(self, tmp_project_root, tmp_data_dir):
        """Each dot-vote command uses --permission-mode acceptEdits."""
        opp_id = self._make_synthesized_workspace(tmp_data_dir)
        bridge = CliBridge(tmp_project_root)
        cmds = bridge.generate_dot_vote_commands(opp_id)
        for fn, cmd in cmds.items():
            assert "--permission-mode acceptEdits" in cmd

    def test_dot_vote_no_roster_raises(self, tmp_project_root, tmp_data_dir):
        """generate_dot_vote_commands raises if no roster."""
        opp_id = self._make_synthesized_workspace(
            tmp_data_dir, opp_id="opp-norost-dv", roster=None,
        )
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(ValueError, match="roster"):
            bridge.generate_dot_vote_commands(opp_id)

    def test_dot_vote_not_found_raises(self, tmp_project_root):
        """generate_dot_vote_commands raises FileNotFoundError for missing workspace."""
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(FileNotFoundError):
            bridge.generate_dot_vote_commands("opp-nonexistent")

    # --- Decision brief command generation ---

    def test_decision_brief_command_returns_string(self, tmp_project_root, tmp_data_dir):
        """generate_decision_brief_command returns a string command."""
        opp_id = self._make_synthesized_workspace(tmp_data_dir, opp_id="opp-20260412-180000")
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_decision_brief_command(opp_id)
        assert isinstance(cmd, str)
        assert "claude" in cmd

    def test_decision_brief_references_synthesis(self, tmp_project_root, tmp_data_dir):
        """Decision brief command instructs reading synthesis.json."""
        opp_id = self._make_synthesized_workspace(tmp_data_dir, opp_id="opp-20260412-180100")
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_decision_brief_command(opp_id)
        assert "synthesis.json" in cmd.lower()

    def test_decision_brief_writes_artifact(self, tmp_project_root, tmp_data_dir):
        """Decision brief command instructs writing decision-brief.md."""
        opp_id = self._make_synthesized_workspace(tmp_data_dir, opp_id="opp-20260412-180200")
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_decision_brief_command(opp_id)
        assert "decision-brief.md" in cmd.lower()

    def test_decision_brief_reads_votes(self, tmp_project_root, tmp_data_dir):
        """Decision brief command instructs reading votes/ directory."""
        opp_id = self._make_synthesized_workspace(tmp_data_dir, opp_id="opp-20260412-180300")
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_decision_brief_command(opp_id)
        assert "votes" in cmd.lower()

    def test_decision_brief_not_found_raises(self, tmp_project_root):
        """generate_decision_brief_command raises FileNotFoundError for missing workspace."""
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(FileNotFoundError):
            bridge.generate_decision_brief_command("opp-nonexistent")


    # --- Evidence command generation ---

    def test_evidence_command_returns_string(self, tmp_project_root, tmp_data_dir):
        """generate_evidence_command returns a command string."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores for tmart fresh food"
        )
        assert isinstance(cmd, str)
        assert "claude" in cmd

    def test_evidence_command_includes_source_type(self, tmp_project_root, tmp_data_dir):
        """Evidence command must reference the source type."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores"
        )
        assert "data-query" in cmd

    def test_evidence_command_includes_query(self, tmp_project_root, tmp_data_dir):
        """Evidence command must include the user's query."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores for tmart fresh food"
        )
        assert "NPS scores for tmart fresh food" in cmd

    def test_evidence_command_includes_workspace_path(self, tmp_project_root, tmp_data_dir):
        """Evidence command must reference the workspace path."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores"
        )
        assert "data/workspaces/opp-20260405-120000" in cmd

    def test_evidence_command_includes_evidence_schema(self, tmp_project_root, tmp_data_dir):
        """Evidence command must reference the evidence schema."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores"
        )
        assert "evidence.schema.json" in cmd.lower()

    def test_evidence_command_includes_skill_reference(self, tmp_project_root, tmp_data_dir):
        """Evidence command must reference the skill template."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores"
        )
        assert "skills/evidence/data-query" in cmd.lower()

    def test_evidence_command_writes_to_evidence_dir(self, tmp_project_root, tmp_data_dir):
        """Evidence command must instruct writing to evidence/ directory."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores"
        )
        assert "evidence/" in cmd.lower()

    def test_evidence_command_uses_accept_edits(self, tmp_project_root, tmp_data_dir):
        """Evidence command must use --permission-mode acceptEdits."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores"
        )
        assert "--permission-mode acceptEdits" in cmd

    def test_evidence_command_disallows_interactive_tools(self, tmp_project_root, tmp_data_dir):
        """Evidence command must block interactive tools."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores"
        )
        assert "--disallowedTools" in cmd or "--disallowed-tools" in cmd
        assert "EnterPlanMode" in cmd
        assert "AskUserQuestion" in cmd

    def test_evidence_command_not_found_raises(self, tmp_project_root):
        """generate_evidence_command raises FileNotFoundError for missing workspace."""
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(FileNotFoundError):
            bridge.generate_evidence_command("opp-nonexistent", "data-query", "NPS")

    def test_evidence_command_invalid_source_type_raises(self, tmp_project_root, tmp_data_dir):
        """generate_evidence_command raises ValueError for unknown source type."""
        bridge = CliBridge(tmp_project_root)
        with pytest.raises(ValueError, match="source_type"):
            bridge.generate_evidence_command(
                "opp-20260405-120000", "crystal-ball", "NPS scores"
            )

    def test_evidence_command_all_source_types(self, tmp_project_root, tmp_data_dir):
        """Evidence command works for all six source types."""
        bridge = CliBridge(tmp_project_root)
        for src in ("data-query", "doc-search", "app-reviews",
                     "slack-signal", "market-intel", "metrics-pull"):
            cmd = bridge.generate_evidence_command(
                "opp-20260405-120000", src, "test query"
            )
            assert src in cmd
            assert "claude" in cmd

    def test_evidence_command_includes_opportunity_context(self, tmp_project_root, tmp_data_dir):
        """Evidence command must include opportunity title for context."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores"
        )
        assert "Test opportunity for server tests" in cmd

    def test_evidence_command_has_scoping_rules(self, tmp_project_root, tmp_data_dir):
        """Evidence command must have scoping rules to stay focused."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores"
        )
        lower = cmd.lower()
        assert "do not read other workspaces" in lower

    def test_evidence_command_stream_json(self, tmp_project_root, tmp_data_dir):
        """Evidence command must use stream-json output format."""
        bridge = CliBridge(tmp_project_root)
        cmd = bridge.generate_evidence_command(
            "opp-20260405-120000", "data-query", "NPS scores"
        )
        assert "--output-format stream-json" in cmd
        assert "--verbose" in cmd


@pytest.mark.asyncio
class TestLaunchRouter:
    async def test_launch_command(self, client):
        resp = await client.post("/api/launch/opp-20260405-120000")
        assert resp.status_code == 200
        data = resp.json()
        assert "command" in data
        assert "opp-20260405-120000" in data["command"]

    async def test_launch_not_found(self, client):
        resp = await client.post("/api/launch/opp-nonexistent")
        assert resp.status_code == 404

    async def test_launch_start(self, client):
        resp = await client.post("/api/launch/opp-20260405-120000/start")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "launched"
        assert data["opp_id"] == "opp-20260405-120000"

    async def test_launch_start_not_found(self, client):
        resp = await client.post("/api/launch/opp-nonexistent/start")
        assert resp.status_code == 404

    async def test_launch_status(self, client):
        resp = await client.get("/api/launch/opp-20260405-120000/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data

    async def test_launch_stop_not_running(self, client):
        resp = await client.post("/api/launch/opp-nonexistent/stop")
        assert resp.status_code == 200
        assert resp.json()["stopped"] is False

    async def test_send_message(self, client):
        # Launch first so there's a process
        await client.post("/api/launch/opp-20260405-120000/start")
        resp = await client.post(
            "/api/launch/opp-20260405-120000/send",
            json={"message": "hello agent"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "sent" in data

    async def test_send_message_not_running_resumes(self, client):
        """Send to a non-running process attempts resume via --resume."""
        resp = await client.post(
            "/api/launch/opp-nonexistent/send",
            json={"message": "hello"},
        )
        assert resp.status_code == 200
        # Now attempts resume instead of returning False
        assert resp.json()["sent"] is True

    async def test_send_resumes_when_not_running(self, client):
        # Launch and let it "complete" (mock process exits)
        await client.post("/api/launch/opp-20260405-120000/start")
        # Send when process not running — should resume via --resume
        resp = await client.post(
            "/api/launch/opp-20260405-120000/send",
            json={"message": "my follow-up"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["sent"] is True

    async def test_approve_plan(self, client):
        # Launch first so there's a process
        await client.post("/api/launch/opp-20260405-120000/start")
        resp = await client.post("/api/launch/opp-20260405-120000/approve")
        assert resp.status_code == 200
        data = resp.json()
        assert "approved" in data

    async def test_approve_not_running(self, client):
        resp = await client.post("/api/launch/opp-nonexistent/approve")
        assert resp.status_code == 200
        assert resp.json()["approved"] is False


@pytest.mark.asyncio
class TestEvidenceRouter:
    async def test_gather_evidence(self, client):
        """POST /api/evidence/{opp_id}/gather launches an evidence subprocess."""
        resp = await client.post(
            "/api/evidence/opp-20260405-120000/gather",
            json={"source_type": "data-query", "query": "NPS scores for tmart"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "launched"
        assert data["opp_id"] == "opp-20260405-120000"
        assert data["source_type"] == "data-query"

    async def test_gather_evidence_not_found(self, client):
        """POST /api/evidence for missing workspace returns 404."""
        resp = await client.post(
            "/api/evidence/opp-nonexistent/gather",
            json={"source_type": "data-query", "query": "test"},
        )
        assert resp.status_code == 404

    async def test_gather_evidence_bad_source_type(self, client):
        """POST /api/evidence with invalid source_type returns 400."""
        resp = await client.post(
            "/api/evidence/opp-20260405-120000/gather",
            json={"source_type": "crystal-ball", "query": "test"},
        )
        assert resp.status_code == 400

    async def test_evidence_status(self, client):
        """GET /api/evidence/{opp_id}/status returns evidence subprocess state."""
        resp = await client.get("/api/evidence/opp-20260405-120000/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data

    async def test_gather_multiple_evidence(self, client):
        """Multiple evidence gathers can run in parallel (different source types)."""
        resp1 = await client.post(
            "/api/evidence/opp-20260405-120000/gather",
            json={"source_type": "data-query", "query": "NPS scores"},
        )
        resp2 = await client.post(
            "/api/evidence/opp-20260405-120000/gather",
            json={"source_type": "slack-signal", "query": "fresh food complaints"},
        )
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        # Both should launch independently
        assert resp1.json()["status"] == "launched"
        assert resp2.json()["status"] == "launched"
