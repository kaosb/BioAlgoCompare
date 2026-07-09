"""
Provenance stamping for experiment outputs.

Every result JSON that backs a claim in the thesis/paper should be traceable to
the exact code + environment that produced it. ``provenance()`` returns a dict
with the git commit (and dirty flag), UTC timestamp, Python/OS, hostname and the
versions of the scientific stack. Attach it under a ``"provenance"`` key.
"""

import os
import platform
import socket
import subprocess
from datetime import datetime, timezone


_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Packages whose version can change results; stamp all that are importable.
_TRACKED = ["numpy", "scipy", "scikit-learn", "minionpy", "mealpy", "opfunu",
            "cma"]


def _git(*args) -> str:
    try:
        out = subprocess.check_output(["git", "-C", _REPO_ROOT, *args],
                                      stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return "unknown"


def _versions() -> dict:
    from importlib import metadata
    vers = {}
    for pkg in _TRACKED:
        try:
            vers[pkg] = metadata.version(pkg)
        except Exception:
            vers[pkg] = "not-installed"
    return vers


def provenance(extra: dict | None = None) -> dict:
    """Return a provenance record. ``extra`` merges experiment-specific fields."""
    commit = _git("rev-parse", "HEAD")
    dirty = _git("status", "--porcelain") != ""
    rec = {
        "git_commit": commit,
        "git_dirty": dirty,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "package_versions": _versions(),
    }
    if extra:
        rec.update(extra)
    return rec
