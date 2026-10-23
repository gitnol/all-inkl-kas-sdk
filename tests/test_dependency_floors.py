"""Security floors for (transitive) dependencies.

Reads the lower bounds from pyproject.toml and compares them with the versions
installed in the running environment (importlib.metadata). No network access.
A stale environment (e.g. an old certifi bundle) makes these tests fail.
"""

import sys
import unittest
from importlib import metadata
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]

# Packages pinned from below only because of security fixes (see
# docs/security/DEPENDENCY_AUDIT.md, sweep 2026-10-23).
SECURITY_FLOOR_PACKAGES = ("certifi", "urllib3", "python-dotenv")


def _project_requirements():
    with open(ROOT / "pyproject.toml", "rb") as fh:
        data = tomllib.load(fh)
    return [Requirement(line) for line in data["project"]["dependencies"]]


def _requirements_txt():
    reqs = []
    for raw in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            reqs.append(Requirement(line))
    return reqs


def _floor(req):
    floors = [Version(spec.version) for spec in req.specifier if spec.operator == ">="]
    return max(floors) if floors else None


def _for(reqs, name):
    """All entries for ``name`` (a package may be listed once per Python-version marker)."""
    key = canonicalize_name(name)
    return [r for r in reqs if canonicalize_name(r.name) == key]


def _applicable(reqs):
    """Entries whose environment marker holds for the running interpreter."""
    return [r for r in reqs if r.marker is None or r.marker.evaluate()]


class TestSecurityFloors(unittest.TestCase):
    def test_pyproject_declares_security_floors(self):
        reqs = _project_requirements()
        for name in SECURITY_FLOOR_PACKAGES:
            with self.subTest(package=name):
                entries = _for(reqs, name)
                self.assertTrue(
                    entries, f"{name} has no entry in [project].dependencies"
                )
                self.assertTrue(
                    any(_floor(r) is not None for r in entries),
                    f"{name} has no '>=' lower bound",
                )

    def test_requirements_txt_matches_pyproject(self):
        project = _project_requirements()
        txt = _requirements_txt()
        for name in SECURITY_FLOOR_PACKAGES:
            with self.subTest(package=name):
                expected = sorted(str(r) for r in _for(project, name))
                self.assertTrue(expected, f"{name} missing in pyproject.toml")
                self.assertEqual(sorted(str(r) for r in _for(txt, name)), expected)

    def test_installed_versions_meet_floors(self):
        reqs = _project_requirements()
        for name in SECURITY_FLOOR_PACKAGES:
            with self.subTest(package=name):
                entries = _for(reqs, name)
                self.assertTrue(
                    entries, f"{name} has no entry in [project].dependencies"
                )
                floors = [f for f in map(_floor, _applicable(entries)) if f is not None]
                if not floors:
                    continue  # no floor applies to this interpreter (e.g. urllib3 on 3.9)
                floor = max(floors)
                installed = Version(metadata.version(name))
                self.assertGreaterEqual(
                    installed,
                    floor,
                    f"{name} {installed} is below the security floor {floor}",
                )


if __name__ == "__main__":
    unittest.main()
