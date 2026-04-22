import json

import ai.mcp_config_loader as mcp_loader


class DummyStdioServerParameters:
    def __init__(self, command, args=None, env=None):
        self.command = command
        self.args = args or []
        self.env = env or {}


class DummyStdioConnectionParams:
    def __init__(self, server_params, timeout=5):
        self.server_params = server_params
        self.timeout = timeout


class DummySseConnectionParams:
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers or {}


class DummyStreamableHTTPConnectionParams:
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers or {}


class DummyMcpToolset:
    def __init__(self, connection_params, tool_filter=None):
        self.connection_params = connection_params
        self.tool_filter = tool_filter


def _toolset_params(toolset):
    if hasattr(toolset, "connection_params"):
        return toolset.connection_params
    return getattr(toolset, "_connection_params")


class TestExpandConfigValues:
    def test_expands_env_and_workspace_vars_recursively(self, monkeypatch, tmp_path):
        monkeypatch.setenv("MCP_TEST_TOKEN", "secret-token")
        monkeypatch.chdir(tmp_path)

        payload = {
            "url": "https://example.com/mcp",
            "headers": {
                "Authorization": "Bearer ${env:MCP_TEST_TOKEN}",
            },
            "args": ["${workspaceFolder}", "${env:MISSING_VAR}"],
        }

        expanded = mcp_loader.expand_config_values(payload)

        assert expanded["headers"]["Authorization"] == "Bearer secret-token"
        assert expanded["args"][0] == str(tmp_path)
        assert expanded["args"][1] == ""


class TestCreateToolsetFromConfig:
    def _patch_classes(self, monkeypatch):
        monkeypatch.setattr(
            mcp_loader, "StdioServerParameters", DummyStdioServerParameters
        )
        monkeypatch.setattr(
            mcp_loader, "StdioConnectionParams", DummyStdioConnectionParams
        )
        monkeypatch.setattr(mcp_loader, "SseConnectionParams", DummySseConnectionParams)
        monkeypatch.setattr(
            mcp_loader,
            "StreamableHTTPConnectionParams",
            DummyStreamableHTTPConnectionParams,
        )
        monkeypatch.setattr(mcp_loader, "McpToolset", DummyMcpToolset)

    def test_creates_stdio_toolset_with_timeout_and_merged_env(self, monkeypatch):
        self._patch_classes(monkeypatch)
        monkeypatch.setenv("HOST_VALUE", "host")

        toolset = mcp_loader.create_toolset_from_config(
            "local",
            {
                "command": "npx",
                "args": ["-y", "server"],
                "env": {"LOCAL_ONLY": "1"},
                "tool_filter": ["read_file"],
            },
        )

        params = _toolset_params(toolset)
        assert isinstance(params, DummyStdioConnectionParams)
        assert params.timeout == 30
        assert params.server_params.command == "npx"
        assert params.server_params.args == ["-y", "server"]
        assert params.server_params.env["LOCAL_ONLY"] == "1"
        assert params.server_params.env["HOST_VALUE"] == "host"
        assert toolset.tool_filter == ["read_file"]

    def test_routes_sse_url_to_sse_connection_params(self, monkeypatch):
        self._patch_classes(monkeypatch)

        toolset = mcp_loader.create_toolset_from_config(
            "remote",
            {
                "url": "https://example.com/sse",
                "headers": {"Authorization": "Bearer x"},
            },
        )

        params = _toolset_params(toolset)
        assert isinstance(params, DummySseConnectionParams)
        assert params.url == "https://example.com/sse"
        assert params.headers == {"Authorization": "Bearer x"}

    def test_routes_other_urls_to_streamable_http_connection_params(self, monkeypatch):
        self._patch_classes(monkeypatch)

        toolset = mcp_loader.create_toolset_from_config(
            "remote",
            {
                "url": "https://example.com/mcp",
                "headers": {"Authorization": "Bearer y"},
            },
        )

        params = _toolset_params(toolset)
        assert isinstance(params, DummyStreamableHTTPConnectionParams)
        assert params.url == "https://example.com/mcp"
        assert params.headers == {"Authorization": "Bearer y"}

    def test_invalid_config_without_command_or_url_raises(self):
        try:
            mcp_loader.create_toolset_from_config("invalid", {"headers": {}})
            assert False, "expected ValueError"
        except ValueError as exc:
            assert "command" in str(exc) or "url" in str(exc)


class TestLoadMcpToolsetsFromFile:
    def test_missing_config_file_returns_empty_list(self, caplog, tmp_path):
        missing = tmp_path / "does-not-exist.json"

        result = mcp_loader.load_mcp_toolsets_from_file(str(missing))

        assert result == []
        assert any("not found" in record.message for record in caplog.records)

    def test_invalid_json_returns_empty_list(self, tmp_path):
        path = tmp_path / "mcpServers.json"
        path.write_text("{ not-json", encoding="utf-8")

        result = mcp_loader.load_mcp_toolsets_from_file(str(path))

        assert result == []

    def test_loads_multiple_servers_and_skips_failures(self, monkeypatch, tmp_path):
        path = tmp_path / "mcpServers.json"
        path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "good": {"url": "https://example.com/mcp"},
                        "bad": {"url": ""},
                        "good2": {"command": "npx", "args": ["-y", "x"]},
                    }
                }
            ),
            encoding="utf-8",
        )

        sentinel = object()
        sentinel2 = object()

        def fake_create(name, config):
            _ = config
            if name == "bad":
                raise ValueError("broken")
            if name == "good":
                return sentinel
            if name == "good2":
                return sentinel2
            raise AssertionError("unexpected server")

        monkeypatch.setattr(mcp_loader, "create_toolset_from_config", fake_create)

        result = mcp_loader.load_mcp_toolsets_from_file(str(path))

        assert result == [sentinel, sentinel2]

    def test_ignores_non_object_server_entries(self, tmp_path):
        path = tmp_path / "mcpServers.json"
        path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "bad": "not-an-object",
                    }
                }
            ),
            encoding="utf-8",
        )

        result = mcp_loader.load_mcp_toolsets_from_file(str(path))

        assert result == []

    def test_invalid_mcp_servers_shape_returns_empty_list(self, tmp_path):
        path = tmp_path / "mcpServers.json"
        path.write_text(json.dumps({"mcpServers": []}), encoding="utf-8")

        result = mcp_loader.load_mcp_toolsets_from_file(str(path))

        assert result == []
