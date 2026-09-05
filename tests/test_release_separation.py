"""A specification tag must not be able to publish a package.

The two kinds of release were never separated because only one existed:
`release.yml` reacted to package tags and published to npm and PyPI, and there
was no way to say "this is IAES 1.4, the document" without also publishing
something.

The separation could have been asserted by reading the workflow files and
checking that the words are right. That proves what the files say today. These
tests prove the *property* instead: they take candidate tags and work out which
workflows each one would actually trigger, using the same glob semantics
GitHub does. A future edit that makes the two sets overlap fails here, whatever
the comments say.
"""

import fnmatch
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

PUBLISHING = WORKFLOWS / "release.yml"
SPEC = WORKFLOWS / "spec-release.yml"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def tag_patterns(workflow: dict) -> list:
    # `on` is parsed as the boolean True by YAML 1.1, which is a well-known
    # trap and the reason this is a helper rather than a subscript.
    on = workflow.get("on", workflow.get(True, {}))
    return list(on.get("push", {}).get("tags", []) or [])


def workflows_triggered_by(tag: str) -> set:
    hit = set()
    for path in (PUBLISHING, SPEC):
        if any(fnmatch.fnmatch(tag, p) for p in tag_patterns(load(path))):
            hit.add(path.name)
    return hit


# One realistic tag per release kind, plus the shapes a mistyped tag takes.
IMPLEMENTATION_TAGS = ["sdk-v1.4.1", "nodered-v1.4.1", "n8n-v1.4.1", "py-v1.4.1"]
SPECIFICATION_TAGS = ["spec-v1.4", "spec-v1.5", "spec-v2.0"]
NEITHER = ["v1.4", "1.4", "release-1.4", "spec1.4", "sdkv1.4.1"]


class TestTheTwoReleaseKindsAreDisjoint(unittest.TestCase):
    def test_no_specification_tag_reaches_the_publishing_workflow(self):
        for tag in SPECIFICATION_TAGS:
            with self.subTest(tag=tag):
                self.assertNotIn(
                    PUBLISHING.name, workflows_triggered_by(tag),
                    f"{tag} would reach the workflow that publishes to npm and PyPI",
                )

    def test_specification_tags_reach_the_specification_workflow(self):
        for tag in SPECIFICATION_TAGS:
            with self.subTest(tag=tag):
                self.assertEqual({SPEC.name}, workflows_triggered_by(tag))

    def test_implementation_tags_keep_their_current_behaviour(self):
        # The point of the separation is that nothing about publishing changes.
        for tag in IMPLEMENTATION_TAGS:
            with self.subTest(tag=tag):
                self.assertEqual({PUBLISHING.name}, workflows_triggered_by(tag))

    def test_no_tag_can_trigger_both(self):
        for tag in IMPLEMENTATION_TAGS + SPECIFICATION_TAGS + NEITHER:
            with self.subTest(tag=tag):
                self.assertLessEqual(
                    len(workflows_triggered_by(tag)), 1,
                    f"{tag} triggers more than one release workflow",
                )

    def test_the_two_pattern_sets_cannot_overlap(self):
        # Stronger than the samples above: no pattern from one side may match
        # any pattern from the other, treating each as a literal prefix.
        pub = tag_patterns(load(PUBLISHING))
        spec = tag_patterns(load(SPEC))
        self.assertTrue(pub and spec, "a workflow lost its tag triggers")
        for p in pub:
            for s in spec:
                self.assertFalse(
                    fnmatch.fnmatch(s.rstrip("*") + "0.0", p)
                    or fnmatch.fnmatch(p.rstrip("*") + "0.0", s),
                    f"tag patterns overlap: {p!r} and {s!r}",
                )


class TestTheSpecificationWorkflowPublishesNothing(unittest.TestCase):
    def test_it_contains_no_publishing_step(self):
        text = SPEC.read_text(encoding="utf-8")
        for forbidden in ("npm publish", "pypi-publish", "twine", "registry-url", "id-token"):
            self.assertNotIn(
                forbidden, text,
                f"the specification workflow contains {forbidden!r}, which publishes",
            )

    def test_it_asks_for_read_only_permissions(self):
        wf = load(SPEC)
        self.assertEqual({"contents": "read"}, wf.get("permissions"))

    def test_the_publishing_workflow_still_publishes(self):
        # Guard against fixing the separation by breaking the thing that works.
        text = PUBLISHING.read_text(encoding="utf-8")
        self.assertIn("npm publish", text)
        self.assertIn("pypi-publish", text)


class TestTheTagShapesAreDistinguishable(unittest.TestCase):
    def test_a_specification_version_has_two_components(self):
        # spec-v1.4 against sdk-v1.4.1: the prefix separates them, and so does
        # the shape. Two signals rather than one.
        for tag in SPECIFICATION_TAGS:
            self.assertEqual(2, len(tag.removeprefix("spec-v").split(".")))
        for tag in IMPLEMENTATION_TAGS:
            self.assertEqual(3, len(re.sub(r"^[a-z0-9-]+-v", "", tag).split(".")))



class TestTheManifestKeepsAuthorityStraight(unittest.TestCase):
    """RFC-000 settled that an incorporated RFC is rationale, not authority.

    The first version of the manifest builder put `rfc/*.md` under `normative`,
    contradicting the memo it shipped alongside. The tool has to obey the rule
    it helps publish.
    """

    def _manifest(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "build_release_manifest", ROOT / "tools" / "build_release_manifest.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.build(tag=None, out=None), mod

    def test_no_rfc_appears_under_normative(self):
        manifest, _ = self._manifest()
        offenders = [p for p in manifest["normative"] if p.startswith("rfc/")]
        self.assertEqual(
            offenders, [],
            "an accepted RFC is rationale, not normative authority (RFC-000 §4.2)",
        )

    def test_the_rfcs_are_still_in_the_release(self):
        # Demoting them must not drop them: they travel in the same release and
        # carry the same digest treatment.
        manifest, _ = self._manifest()
        self.assertTrue(
            all(p.startswith("rfc/") for p in manifest["rationale"]),
            "rationale should hold the RFCs and nothing else",
        )
        self.assertGreater(len(manifest["rationale"]), 0, "the RFCs vanished from the release")

    def test_the_globs_themselves_cannot_drift(self):
        _, mod = self._manifest()
        self.assertNotIn("rfc/*.md", mod.NORMATIVE_GLOBS)
        self.assertIn("rfc/*.md", mod.RATIONALE_GLOBS)

if __name__ == "__main__":
    unittest.main()
