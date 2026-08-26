import base64
from pathlib import Path

import pytest

from hermes_cli import web_server

pytest.importorskip("starlette.testclient")
from starlette.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    previous_auth_required = getattr(web_server.app.state, "auth_required", None)
    web_server.app.state.auth_required = False
    test_client = TestClient(web_server.app)
    test_client.headers[web_server._SESSION_HEADER_NAME] = web_server._SESSION_TOKEN
    try:
        yield test_client
    finally:
        if previous_auth_required is None:
            try:
                delattr(web_server.app.state, "auth_required")
            except AttributeError:
                pass
        else:
            web_server.app.state.auth_required = previous_auth_required


def test_fs_list_sorts_and_hides_noise(client, tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "b.txt").write_text("b")
    (root / "a_dir").mkdir()
    (root / "a.txt").write_text("a")
    (root / "node_modules").mkdir()
    (root / ".git").mkdir()

    response = client.get("/api/fs/list", params={"path": str(root)})

    assert response.status_code == 200
    entries = response.json()["entries"]
    assert [entry["name"] for entry in entries] == ["a_dir", "a.txt", "b.txt"]
    assert entries[0] == {"name": "a_dir", "path": str(root / "a_dir"), "isDirectory": True}
    assert all(entry["name"] not in {".git", "node_modules"} for entry in entries)


def test_fs_read_data_url_rejects_over_cap(client, tmp_path, monkeypatch):
    monkeypatch.setattr(web_server, "_FS_DATA_URL_MAX_BYTES", 3)
    target = tmp_path / "image.png"
    target.write_bytes(b"1234")

    response = client.get("/api/fs/read-data-url", params={"path": str(target)})

    assert response.status_code == 413


def test_fs_download_streams_file_without_data_url_cap(client, tmp_path, monkeypatch):
    monkeypatch.setattr(web_server, "_FS_DATA_URL_MAX_BYTES", 3)
    target = tmp_path / "report with spaces.pdf"
    target.write_bytes(b"123456")

    response = client.get("/api/fs/download", params={"path": str(target)})

    assert response.status_code == 200
    assert response.content == b"123456"
    assert response.headers["content-type"].startswith("application/pdf")
    assert "report%20with%20spaces.pdf" in response.headers["content-disposition"]


def test_fs_download_rejects_sensitive_files(client, tmp_path):
    target = tmp_path / ".env"
    target.write_text("SECRET=1")

    response = client.get("/api/fs/download", params={"path": str(target)})

    assert response.status_code == 403


# ── #95306: the spot-editor write path must honor the same credential
# boundary as the read side — an authenticated session must not be able to
# overwrite .env/auth.json or plant files in credential directory trees. ────


def _write(client, path: str, content: str):
    return client.post("/api/fs/write-text", json={"path": path, "content": content})


def test_fs_write_text_rejects_env_file(client, tmp_path):
    target = tmp_path / ".env"
    target.write_text("KEEP=1", encoding="utf-8")

    response = _write(client, str(target), "EVIL=1")

    assert response.status_code == 403
    assert target.read_text(encoding="utf-8") == "KEEP=1"


def test_fs_write_text_rejects_auth_json(client, tmp_path):
    target = tmp_path / "auth.json"
    target.write_text("{}", encoding="utf-8")

    response = _write(client, str(target), "{}")

    assert response.status_code == 403


def test_fs_write_text_rejects_config_yaml_overwrite(client, tmp_path):
    """config.yaml is the MCP-registration vector — overwrite must fail."""
    target = tmp_path / "config.yaml"
    target.write_text("model: {}\n", encoding="utf-8")

    response = _write(client, str(target), "mcp_servers:\n  evil:\n    command: sh\n")

    assert response.status_code == 403
    assert "evil" not in target.read_text(encoding="utf-8")


def test_fs_write_text_rejects_credential_dir_trees(client, tmp_path):
    target = tmp_path / "mcp-tokens" / "server.json"

    response = _write(client, str(target), '{"token": "x"}')

    assert response.status_code == 403
    assert not target.exists()


def test_fs_write_text_allows_regular_files(client, tmp_path):
    target = tmp_path / "notes.md"

    response = _write(client, str(target), "# hello\n")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert target.read_text(encoding="utf-8") == "# hello\n"


def test_fs_endpoints_require_auth(tmp_path):
    client = TestClient(web_server.app)
    target = tmp_path / "secret.txt"
    target.write_text("secret")

    list_response = client.get("/api/fs/list", params={"path": str(tmp_path)})
    read_response = client.get("/api/fs/read-text", params={"path": str(target)})
    default_response = client.get("/api/fs/default-cwd")

    assert list_response.status_code == 401
    assert read_response.status_code == 401
    assert default_response.status_code == 401
