import logging


from ai.utils import _FALLBACK_SYSTEM_INSTRUCTION, load_system_instruction


class TestLoadSystemInstruction:
    """Tests for ai.utils.load_system_instruction."""

    def test_env_var_takes_highest_priority(self, tmp_path, monkeypatch):
        """Env var wins even when AGENTS.md is present."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("From file", encoding="utf-8")
        monkeypatch.setenv("DEFAULT_SYSTEM_INSTRUCTION", "From env var")
        monkeypatch.setenv("AGENTS_MD_PATH", str(agents_md))

        assert load_system_instruction() == "From env var"

    def test_env_var_used_when_no_file(self, monkeypatch):
        """Env var is returned when AGENTS.md does not exist."""
        monkeypatch.setenv("DEFAULT_SYSTEM_INSTRUCTION", "Env only")
        monkeypatch.setenv("AGENTS_MD_PATH", "/nonexistent/AGENTS.md")

        assert load_system_instruction() == "Env only"

    def test_agents_md_used_when_no_env_var(self, tmp_path, monkeypatch):
        """AGENTS.md content is returned when env var is not set."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("  From file  \n", encoding="utf-8")
        monkeypatch.delenv("DEFAULT_SYSTEM_INSTRUCTION", raising=False)
        monkeypatch.setenv("AGENTS_MD_PATH", str(agents_md))

        assert load_system_instruction() == "From file"

    def test_custom_agents_md_path_via_env(self, tmp_path, monkeypatch):
        """AGENTS_MD_PATH env var controls which file is read."""
        custom = tmp_path / "my-agent.md"
        custom.write_text("Custom agent persona", encoding="utf-8")
        monkeypatch.delenv("DEFAULT_SYSTEM_INSTRUCTION", raising=False)
        monkeypatch.setenv("AGENTS_MD_PATH", str(custom))

        assert load_system_instruction() == "Custom agent persona"

    def test_fallback_when_file_missing(self, monkeypatch):
        """Falls back to hardcoded default when AGENTS.md does not exist."""
        monkeypatch.delenv("DEFAULT_SYSTEM_INSTRUCTION", raising=False)
        monkeypatch.setenv("AGENTS_MD_PATH", "/nonexistent/AGENTS.md")

        assert load_system_instruction() == _FALLBACK_SYSTEM_INSTRUCTION

    def test_fallback_when_file_empty(self, tmp_path, monkeypatch):
        """Falls back to hardcoded default when AGENTS.md is empty."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("   \n  ", encoding="utf-8")
        monkeypatch.delenv("DEFAULT_SYSTEM_INSTRUCTION", raising=False)
        monkeypatch.setenv("AGENTS_MD_PATH", str(agents_md))

        assert load_system_instruction() == _FALLBACK_SYSTEM_INSTRUCTION

    def test_fallback_when_nothing_configured(self, monkeypatch, tmp_path, caplog):
        """Falls back to default when neither env var nor AGENTS.md is present."""
        monkeypatch.delenv("DEFAULT_SYSTEM_INSTRUCTION", raising=False)
        # Point to a guaranteed non-existent path
        monkeypatch.setenv("AGENTS_MD_PATH", str(tmp_path / "AGENTS.md"))

        result = load_system_instruction()

        assert result == _FALLBACK_SYSTEM_INSTRUCTION

    # ── Logging assertions ────────────────────────────────────────────────────

    def test_logs_env_var_source(self, monkeypatch, caplog):
        monkeypatch.setenv("DEFAULT_SYSTEM_INSTRUCTION", "From env")
        with caplog.at_level(logging.INFO, logger="ai.utils"):
            load_system_instruction()
        assert any(
            "DEFAULT_SYSTEM_INSTRUCTION env var" in r.message for r in caplog.records
        )

    def test_logs_file_source(self, tmp_path, monkeypatch, caplog):
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("Persona", encoding="utf-8")
        monkeypatch.delenv("DEFAULT_SYSTEM_INSTRUCTION", raising=False)
        monkeypatch.setenv("AGENTS_MD_PATH", str(agents_md))
        with caplog.at_level(logging.INFO, logger="ai.utils"):
            load_system_instruction()
        assert any("loaded from file" in r.message for r in caplog.records)

    def test_logs_debug_when_file_missing(self, monkeypatch, caplog):
        monkeypatch.delenv("DEFAULT_SYSTEM_INSTRUCTION", raising=False)
        monkeypatch.setenv("AGENTS_MD_PATH", "/nonexistent/AGENTS.md")
        with caplog.at_level(logging.DEBUG, logger="ai.utils"):
            load_system_instruction()
        assert any("No AGENTS.md found" in r.message for r in caplog.records)

    def test_logs_warning_when_file_empty(self, tmp_path, monkeypatch, caplog):
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("", encoding="utf-8")
        monkeypatch.delenv("DEFAULT_SYSTEM_INSTRUCTION", raising=False)
        monkeypatch.setenv("AGENTS_MD_PATH", str(agents_md))
        with caplog.at_level(logging.WARNING, logger="ai.utils"):
            load_system_instruction()
        assert any("empty" in r.message for r in caplog.records)
