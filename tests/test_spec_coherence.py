"""The specification must agree with the code it specifies, and with itself.

Three drifts happened without anyone deciding they should, and none of them was
reported by anything:

  - the document titled itself v1.3 while its body described 1.4 and both SDKs
    emitted spec_version "1.4";
  - the canonical envelope example declared asset.health and pointed dataschema
    at asset.measurement, contradicting the derivation rule that example exists
    to demonstrate;
  - two references sent the reader to documents that do not exist -- one of them
    a path inside a private repository.

Each is mechanical, so each is checked mechanically. A specification that
contradicts its own packages is worse than an out-of-date one, because a reader
has no way to tell which half is true.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "IAES_SPEC.md"


def spec_text():
    return SPEC.read_text(encoding="utf-8")


class TestSpecDeclaresTheVersionTheCodeEmits(unittest.TestCase):
    def _spec_version_from_sdk(self):
        # The Python SDK is the reference; the TS SDK is checked against it
        # elsewhere. Read the constant rather than importing, so this test does
        # not depend on the package being installed.
        src = (ROOT / "src" / "iaes" / "envelope.py").read_text(encoding="utf-8")
        m = re.search(r'^SPEC_VERSION\s*=\s*["\']([^"\']+)["\']', src, re.M)
        self.assertIsNotNone(m, "SPEC_VERSION not found in the Python SDK")
        return m.group(1)

    def test_title_matches_the_emitted_spec_version(self):
        version = self._spec_version_from_sdk()
        title = spec_text().split("\n", 1)[0]
        self.assertIn(
            f"v{version}", title,
            f"the document titles itself differently from what events declare "
            f"(SDK emits spec_version {version!r}); title was: {title!r}",
        )

    def test_footer_matches_the_title(self):
        text = spec_text()
        title_v = re.search(r"v(\d+\.\d+)\s*$", text.split("\n", 1)[0])
        footer_v = re.search(r"\*IAES v(\d+\.\d+) —", text)
        self.assertIsNotNone(title_v, "no version in the title")
        self.assertIsNotNone(footer_v, "no version in the footer")
        self.assertEqual(title_v.group(1), footer_v.group(1))

    def test_version_history_is_in_order(self):
        # A row out of order is how the 1.4 entry hid between 1.2 and 1.3.
        rows = re.findall(r"^\| (\d+\.\d+) \| (?:March|April|May|June|July|August|September) \d{4} \|",
                          spec_text(), re.M)
        as_numbers = [tuple(int(p) for p in v.split(".")) for v in rows]
        self.assertEqual(as_numbers, sorted(as_numbers),
                         f"version history is out of order: {rows}")

    def test_the_history_records_the_current_version(self):
        version = self._spec_version_from_sdk()
        self.assertRegex(spec_text(), rf"(?m)^\| {re.escape(version)} \|",
                         f"version {version} has no row in the version history")


class TestExamplesObeyTheRulesTheyDemonstrate(unittest.TestCase):
    def test_every_dataschema_matches_its_own_event_type(self):
        # dataschema is derivable from event_type: the spec says so, and both
        # SDKs derive it. An example where they disagree teaches the opposite.
        text = spec_text()
        blocks = re.findall(r"```jsonc?\n(.*?)```", text, re.S)
        checked = 0
        for block in blocks:
            et = re.search(r'"event_type"\s*:\s*"([^"]+)"', block)
            ds = re.search(r'"dataschema"\s*:\s*"([^"]+)"', block)
            if not (et and ds):
                continue
            checked += 1
            self.assertEqual(
                ds.group(1), f"https://iaes.dev/schema/v1/{et.group(1)}",
                f"example declares {et.group(1)} but points dataschema elsewhere",
            )
        self.assertGreater(checked, 0, "no example carries both fields — did the check stop finding them?")

    def test_examples_use_published_event_types_or_a_namespaced_custom_one(self):
        published = {p.stem.replace("-", ".") for p in (ROOT / "schema").glob("*.schema.json")}
        published.discard("iaes.envelope")
        for block in re.findall(r"```jsonc?\n(.*?)```", spec_text(), re.S):
            for et in re.findall(r'"event_type"\s*:\s*"([^"]+)"', block):
                if et in published:
                    continue
                self.assertRegex(et, r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_.]*$",
                                 f"example event_type {et!r} is neither published nor well-formed")


class TestTheSpecOnlyPointsAtThingsAReaderCanReach(unittest.TestCase):
    def test_no_reference_to_a_missing_local_document(self):
        # Markdown links and bare backticked filenames both count: the
        # architecture reference that 404'd was a backticked name, not a link.
        text = spec_text()
        named = set(re.findall(r"`([A-Za-z0-9_\-]+\.md)`", text))
        named |= {m for m in re.findall(r"\]\(([A-Za-z0-9_\-./]+\.md)\)", text)}
        missing = sorted(n for n in named if not (ROOT / n).exists())
        self.assertEqual(missing, [], "the specification points at documents that do not exist here")

    def test_no_reference_into_a_private_repository(self):
        # `skills/` is a directory of the private monorepo. A reader following
        # it finds nothing and cannot tell the destination was never public.
        for pattern in (r"skills/", r"visiondiag/", r"wertek_platform/", r"wertek_admin/"):
            self.assertNotRegex(spec_text(), pattern,
                                f"the public specification references {pattern!r}, which is private")


if __name__ == "__main__":
    unittest.main()
