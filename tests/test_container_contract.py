from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_api_container_listens_on_cloud_run_port_and_all_interfaces():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "--host 0.0.0.0" in dockerfile
    assert "--port ${PORT:-8000}" in dockerfile
    assert "USER appuser" in dockerfile


def test_release_docker_context_excludes_local_runtime_and_governance_artifacts():
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    for required in (".env", "data/lifecycle", "data/raw", "tests", "gates", "_agent_ops"):
        assert required in dockerignore


def test_compose_keeps_explicit_local_api_and_streamlit_commands():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "app.main:app" in compose
    assert "frontend/streamlit_app.py" in compose
    assert '"8000"' in compose
    assert '"8501"' in compose


def test_gcp_retention_policies_are_valid_and_deployment_templates_are_immutable():
    storage_policy = json.loads((ROOT / "deploy" / "gcp" / "storage-lifecycle.json").read_text(encoding="utf-8"))
    artifact_policy = json.loads(
        (ROOT / "deploy" / "gcp" / "artifact-cleanup-policy.json").read_text(encoding="utf-8")
    )
    assert storage_policy["rule"]
    assert artifact_policy
    for path in (ROOT / "deploy" / "gcp" / "api-service.yaml", ROOT / "deploy" / "gcp" / "web-service.yaml"):
        content = path.read_text(encoding="utf-8")
        assert "@sha256:REPLACE_WITH_" in content
        assert "latest" not in content.casefold()
