"""Every list of published event types is the list the schemas define.

Each SDK names the published event types in three places, and forgetting one
does not fail -- it degrades in silence:

    PUBLISHED_EVENT_TYPES   missing -> no `dataschema` is emitted for the type
    _SCHEMA_FILES           missing -> validate() falls back to envelope-only
    EVENT_TYPES             missing -> from_object() cannot build the type

The Node-RED route and validate nodes keep their own tables, and the n8n Emit
node its own options. Found by a read-only review on 2026-10-06: no test tied
any of these to `schema/`, and one comment claimed a "golden test" that did
not exist. The published set is derived here from the schemas themselves (the
`$id` of every schema except the envelope), which is what "published" means.

The TypeScript, Node-RED and n8n sources are read as text, anchored to the
declaration of each named constant, because this suite runs without a build.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TYPE = re.compile(r"""["']([a-z][a-z0-9_]*\.[a-z][a-z0-9_.]*)["']""")
KEY = re.compile(r"""["']([a-z][a-z0-9_]*\.[a-z][a-z0-9_.]*)["']\s*:""")


def published() -> set:
    out = set()
    for p in (ROOT / "schema").glob("*.schema.json"):
        last = json.loads(p.read_text(encoding="utf-8"))["$id"].rsplit("/", 1)[-1]
        if last != "envelope":
            out.add(last)
    return out


def block_after(src: str, anchor: str) -> str:
    """The bracketed literal that follows the first match of `anchor`."""
    m = re.search(anchor, src)
    assert m, f"declaration not found: {anchor}"
    start = next(i for i in range(m.end(), len(src)) if src[i] in "[{")
    pairs = {"[": "]", "{": "}"}
    stack = []
    for i in range(start, len(src)):
        c = src[i]
        if c in pairs:
            stack.append(pairs[c])
        elif stack and c == stack[-1]:
            stack.pop()
            if not stack:
                return src[start:i + 1]
    raise AssertionError(f"unterminated literal after {anchor}")


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_the_published_set_is_not_empty():
    # Positive control: if the schemas stopped being read, every comparison
    # below would compare two empty sets and pass.
    assert "asset.measurement" in published()
    assert len(published()) >= 7


def test_the_python_sdk_lists_exactly_the_published_types():
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from iaes import envelope, models, validation

    want = published()
    assert set(envelope.PUBLISHED_EVENT_TYPES) == want, "src/iaes/envelope.py PUBLISHED_EVENT_TYPES"
    assert set(validation._SCHEMA_FILES) == want, "src/iaes/validation.py _SCHEMA_FILES"
    assert set(models.EVENT_TYPES) == want, "src/iaes/models.py EVENT_TYPES"


def test_the_typescript_sdk_lists_exactly_the_published_types():
    want = published()
    cases = [
        ("npm/src/envelope.ts", r"export const PUBLISHED_EVENT_TYPES\b", TYPE),
        ("npm/src/validation.ts", r"const SCHEMA_FILES\b", KEY),
        ("npm/src/models.ts", r"const EVENT_TYPES\b[^=]*=", KEY),
    ]
    for rel, anchor, pattern in cases:
        got = set(pattern.findall(block_after(read(rel), anchor)))
        assert got == want, f"{rel}: missing {sorted(want - got)}, extra {sorted(got - want)}"


def test_the_node_red_tables_list_exactly_the_published_types():
    want = published()
    cases = [
        ("node-red/nodes/iaes-route.js", r"var EVENT_TYPES\b", TYPE),
        ("node-red/nodes/iaes-validate.js", r"const REQUIRED_DATA_FIELDS\b", KEY),
    ]
    for rel, anchor, pattern in cases:
        got = set(pattern.findall(block_after(read(rel), anchor)))
        assert got == want, f"{rel}: missing {sorted(want - got)}, extra {sorted(got - want)}"


def test_the_n8n_emit_node_offers_only_published_types():
    # A subset on purpose: the Emit node does not build every type, and that gap
    # is declared in implementations.json. What it must never offer is a type
    # that is not published.
    src = read("n8n-nodes/nodes/IaesEmit/IaesEmit.node.ts")
    options = block_after(src, r"name: 'eventType'")
    got = set(re.findall(r"value: '([a-z][a-z0-9_]*\.[a-z][a-z0-9_.]*)'", options))
    assert got, "no event type options found"
    assert got <= published(), f"n8n Emit offers unpublished types: {sorted(got - published())}"
