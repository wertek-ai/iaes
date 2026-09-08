"""Armed at zero against the crossings that were really in this repository.

A guard that passes proves nothing on its own. Each case below plants a real
historical violation and asserts the guard fails on it, and each legitimate
mention asserts it does not -- because a guard that fires on correct content is
a guard somebody switches off.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from check_frontier import scan  # noqa: E402


def kinds(tmp_path, name, body):
    (tmp_path / name).write_text(body, encoding="utf-8")
    return {k for _, _, k, _ in scan(tmp_path)}


# --- the standard must not point at us ---------------------------------------

@pytest.mark.parametrize("name,body,kind", [
    # n8n shipped this as the credential default: install the node, click
    # through, and every event lands on our production server.
    ("c.ts", "default: 'https://api.wertek.ai/iaes/ingest',", "host"),
    # Opta shipped this as the broker in three examples.
    ("m.cpp", 'const char* BROKER = "mqtt.wertek.ai";', "host"),
    # The base that never resolved, left behind in a comment after 1.4.
    ("v.py", "# $id is like https://iaes.wertek.ai/schema/v2/asset.measurement", "host"),
    # The normative schema taught our namespace as what a producer looks like.
    ("s.json", '"description": "producer identity (e.g. wertek.ai.diagnosis)"', "namespace"),
    ("e.json", '"source": "wertek.energy.cdr_rules"', "namespace"),
    # Multi-tenancy is our operating model, not part of naming an event.
    ("t.ts", "description: 'published to {prefix}/{org_id}/{asset_id}'", "model"),
])
def test_catches_real_crossing(tmp_path, name, body, kind):
    assert kind in kinds(tmp_path, name, body)


def test_catches_it_inside_a_markdown_code_fence(tmp_path):
    # A reader copies what is in the fence.
    body = 'Configure it:\n\n```json\n{ "url": "https://api.wertek.ai" }\n```\n'
    assert "host" in kinds(tmp_path, "README.md", body)


# --- and it must be free to name us in prose ---------------------------------

@pytest.mark.parametrize("body", [
    "IAES is maintained by Wertek AI.",
    "Copyright (c) 2026 Wertek AI",
    # The changelog's job is to record which of our defaults were removed.
    "`httpEndpoint` defaulted to `https://api.wertek.ai/iaes/ingest` -- removed in 0.2.0.",
    # The specification's history says which host never resolved.
    "The schemas declared `$id` under `https://iaes.wertek.ai/schema/v2/`, which never resolved.",
])
def test_leaves_prose_alone(tmp_path, body):
    assert kinds(tmp_path, "PROSE.md", body) == set()


def test_a_path_is_not_infrastructure(tmp_path):
    # Anyone can mount this route on their own server. The host in front of it
    # is the dependency, and the host rule is what catches that.
    assert kinds(tmp_path, "n.js", 'const DEFAULT_PATH = "/iaes/ingest";') == set()


def test_the_repository_is_clean(tmp_path):
    assert scan() == []
