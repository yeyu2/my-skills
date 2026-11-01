#!/usr/bin/env python3
"""Guard a Markdown or Obsidian vault against agent edits that break it.

Workflow:

  python3 vault_check.py init     ~/vault          # write vault-check.json (optional)
  python3 vault_check.py draft    ~/vault          # snapshot + copy to ~/vault.draft
  ... let the agent edit ~/vault.draft ...
  python3 vault_check.py verify   ~/vault.draft    # what would fail, without touching ~/vault
  python3 vault_check.py promote  ~/vault.draft ~/vault

Or without a copy:

  python3 vault_check.py snapshot ~/vault
  ... agent edits ~/vault ...
  python3 vault_check.py verify   ~/vault

Checks are relative to the snapshot, so an existing vault with old broken
links still passes. Only damage introduced since the snapshot counts:

  raw_modified      a file under a raw dir changed or disappeared (new files are fine)
  notes_deleted     a note that existed at snapshot time is gone
  prose_changed     a locked note's text outside agent:auto markers changed
  new_broken_links  a link that resolves to nothing, and did not exist before
  new_orphans       a note created since the snapshot that nothing links to
  missing_keys      a new or edited note lacks a required frontmatter key
  log_not_appended  notes changed but the log file did not grow, or was rewritten

A note is locked if it contains <!-- agent:auto:start --> markers, or its
frontmatter has `owner: human`. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import shutil
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

CONFIG_NAME = "vault-check.json"
STATE_DIR = ".vault-check"
SNAPSHOT_NAME = "snapshot.json"

DEFAULT_CONFIG = {
    "raw_dirs": ["raw"],
    "log_file": "log.md",
    "required_frontmatter": ["type", "status", "sources"],
    "link_keys": ["sources", "supports", "contradicts", "supersedes"],
    "exempt": ["index.md", "log.md", "CLAUDE.md", "AGENTS.md", "SCHEMA.md", "README.md"],
    "ignore_dirs": [".obsidian", ".git", ".trash", STATE_DIR],
}

FENCE_RE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.DOTALL | re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
WIKILINK_RE = re.compile(r"!?\[\[([^\]\|#\^]*)(?:[#\^][^\]\|]*)?(?:\|[^\]]*)?\]\]")
MDLINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---[ \t]*\n?", re.DOTALL)
AUTO_RE = re.compile(r"<!--\s*agent:auto:start\s*-->.*?<!--\s*agent:auto:end\s*-->", re.DOTALL)


# ---------- reading a vault ----------

def load_config(vault: Path) -> dict:
    config = dict(DEFAULT_CONFIG)
    path = vault / CONFIG_NAME
    if path.exists():
        config.update(json.loads(path.read_text(encoding="utf-8")))
    return config


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def list_files(vault: Path, config: dict) -> Dict[str, str]:
    ignored = set(config["ignore_dirs"])
    files: Dict[str, str] = {}
    for path in sorted(vault.rglob("*")):
        rel = path.relative_to(vault)
        if any(part in ignored for part in rel.parts) or not path.is_file():
            continue
        files[rel.as_posix()] = sha(path.read_bytes())
    return files


def is_raw(rel: str, config: dict) -> bool:
    return any(rel == d or rel.startswith(d.rstrip("/") + "/") for d in config["raw_dirs"])


def is_note(rel: str, config: dict) -> bool:
    return rel.endswith(".md") and not is_raw(rel, config)


def parse_frontmatter(text: str) -> Dict[str, object]:
    """Minimal YAML: `key: value`, `key: [a, b]`, and block lists under a key."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: Dict[str, object] = {}
    current: Optional[str] = None
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and current is not None:
            value = data.setdefault(current, [])
            if isinstance(value, list):
                value.append(clean_value(stripped[2:]))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        current = key
        if not value:
            data[key] = []
        elif value.startswith("[") and value.endswith("]") and not value.startswith("[["):
            data[key] = [clean_value(v) for v in value[1:-1].split(",") if v.strip()]
        else:
            data[key] = clean_value(value)
    return data


def clean_value(value: str) -> str:
    return value.strip().strip("'\"").strip()


def link_targets(text: str, frontmatter: Dict[str, object], config: dict) -> List[str]:
    body = FRONTMATTER_RE.sub("", text, count=1)
    body = INLINE_CODE_RE.sub("", FENCE_RE.sub("", body))
    targets = [m.group(1).strip() for m in WIKILINK_RE.finditer(body)]
    for raw_target in MDLINK_RE.findall(body):
        if re.match(r"^[a-z][a-z0-9+.-]*:", raw_target, re.I) or raw_target.startswith("#"):
            continue
        targets.append("./" + urllib.parse.unquote(raw_target.split("#", 1)[0]))
    for key in config["link_keys"]:
        values = frontmatter.get(key, [])
        for value in values if isinstance(values, list) else [values]:
            value = str(value).strip().strip("[]").strip()
            if value:
                targets.append(value)
    return [t for t in targets if t and t != "./"]


class Resolver:
    def __init__(self, files: Dict[str, str]):
        self.paths = {p.lower() for p in files}
        self.by_stem: Set[str] = set()
        self.by_name: Set[str] = set()
        for p in files:
            name = p.rsplit("/", 1)[-1].lower()
            self.by_name.add(name)
            if name.endswith(".md"):
                self.by_stem.add(name[:-3])
        self.stem_to_path: Dict[str, List[str]] = {}
        for p in files:
            if p.endswith(".md"):
                self.stem_to_path.setdefault(p.rsplit("/", 1)[-1][:-3].lower(), []).append(p)

    def resolve(self, source: str, target: str) -> Optional[str]:
        """Return the matched vault path (lowercased) or None."""
        if target.startswith("./"):
            base = posixpath.dirname(source)
            path = posixpath.normpath(posixpath.join(base, target[2:])).lower()
            for candidate in (path, path + ".md"):
                if candidate in self.paths:
                    return candidate
            return None
        t = target.lower().lstrip("/")
        for candidate in (t, t + ".md"):
            if candidate in self.paths:
                return candidate
            if "/" in candidate:
                for p in self.paths:
                    if p.endswith("/" + candidate):
                        return p
        if "/" not in t:
            if t in self.stem_to_path:
                return sorted(self.stem_to_path[t], key=len)[0].lower()
            if t in self.by_name:
                return next(p for p in self.paths if p.rsplit("/", 1)[-1] == t)
        return None


def outside_markers(text: str) -> str:
    return AUTO_RE.sub("", FRONTMATTER_RE.sub("", text, count=1)).strip()


def is_locked(text: str) -> bool:
    return bool(AUTO_RE.search(text)) or parse_frontmatter(text).get("owner") == "human"


def scan(vault: Path, config: dict) -> dict:
    files = list_files(vault, config)
    resolver = Resolver(files)
    notes = [p for p in files if is_note(p, config)]
    broken: List[str] = []
    inbound: Dict[str, int] = {p.lower(): 0 for p in notes}
    locked: Dict[str, str] = {}
    frontmatter: Dict[str, Dict[str, object]] = {}
    for rel in notes:
        text = (vault / rel).read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        frontmatter[rel] = fm
        if is_locked(text):
            locked[rel] = sha(outside_markers(text).encode("utf-8"))
        for target in link_targets(text, fm, config):
            hit = resolver.resolve(rel, target)
            if hit is None:
                broken.append(f"{rel} -> {target.removeprefix('./')}")
            elif hit != rel.lower() and hit in inbound:
                inbound[hit] += 1
    return {
        "files": files,
        "notes": notes,
        "raw": {p: h for p, h in files.items() if is_raw(p, config)},
        "locked": locked,
        "broken": sorted(set(broken)),
        "inbound": inbound,
        "frontmatter": frontmatter,
    }


# ---------- snapshot and verify ----------

def snapshot(vault: Path) -> dict:
    config = load_config(vault)
    state = scan(vault, config)
    log_rel = config["log_file"]
    log_path = vault / log_rel
    log_bytes = log_path.read_bytes() if log_path.exists() else b""
    snap = {
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": state["files"],
        "notes": state["notes"],
        "raw": state["raw"],
        "locked": state["locked"],
        "broken": state["broken"],
        "log": {"size": len(log_bytes), "sha": sha(log_bytes)},
    }
    out = vault / STATE_DIR / SNAPSHOT_NAME
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    return snap


def load_snapshot(vault: Path) -> dict:
    path = vault / STATE_DIR / SNAPSHOT_NAME
    if not path.exists():
        raise SystemExit(f"no snapshot at {path}. Run: vault_check.py snapshot {vault}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify(vault: Path, snap: dict) -> dict:
    config = load_config(vault)
    state = scan(vault, config)
    files = state["files"]
    old_files = snap["files"]

    raw_modified = sorted(
        f"{p} ({'deleted' if p not in files else 'changed'})"
        for p, h in snap["raw"].items() if files.get(p) != h
    )
    notes_deleted = sorted(p for p in snap["notes"] if p not in files)

    prose_changed = []
    for rel, digest in snap["locked"].items():
        if rel in files:
            text = (vault / rel).read_text(encoding="utf-8", errors="replace")
            if sha(outside_markers(text).encode("utf-8")) != digest:
                prose_changed.append(rel)

    new_broken_links = sorted(set(state["broken"]) - set(snap["broken"]))

    exempt = set(config["exempt"])
    new_notes = [p for p in state["notes"] if p not in old_files]
    new_orphans = sorted(
        p for p in new_notes
        if p.rsplit("/", 1)[-1] not in exempt and state["inbound"].get(p.lower(), 0) == 0
    )

    touched = [p for p in state["notes"] if old_files.get(p) != files[p]]
    missing_keys = []
    for rel in touched:
        if rel.rsplit("/", 1)[-1] in exempt:
            continue
        missing = [k for k in config["required_frontmatter"] if k not in state["frontmatter"][rel]]
        if missing:
            missing_keys.append(f"{rel}: {', '.join(missing)}")

    log_not_appended = []
    log_rel = config["log_file"]
    log_path = vault / log_rel
    if log_path.exists() or snap["log"]["size"]:
        data = log_path.read_bytes() if log_path.exists() else b""
        old_size = snap["log"]["size"]
        if sha(data[:old_size]) != snap["log"]["sha"]:
            log_not_appended.append(f"{log_rel} was rewritten, not appended")
        elif [p for p in touched + notes_deleted if p != log_rel] and len(data) <= old_size:
            log_not_appended.append(f"notes changed but {log_rel} has no new entry")

    result = {
        "raw_modified": raw_modified,
        "notes_deleted": notes_deleted,
        "prose_changed": sorted(prose_changed),
        "new_broken_links": new_broken_links,
        "new_orphans": new_orphans,
        "missing_keys": missing_keys,
        "log_not_appended": log_not_appended,
    }
    result["passed"] = not any(result.values())
    result["changed_notes"] = sorted(p for p in touched if p not in new_notes)
    result["new_notes"] = sorted(new_notes)
    return result


def link_lint_only(result: dict) -> bool:
    """What a typical vault linter checks: links and orphans, nothing else."""
    return not result["new_broken_links"] and not result["new_orphans"]


# ---------- draft and promote ----------

def default_draft_path(vault: Path) -> Path:
    return vault.with_name(vault.name + ".draft")


def make_draft(vault: Path, draft: Optional[Path] = None) -> Path:
    draft = draft or default_draft_path(vault)
    if draft.exists():
        raise SystemExit(f"{draft} already exists. Promote or delete it first.")
    snapshot(vault)
    shutil.copytree(vault, draft, ignore=shutil.ignore_patterns(".git", ".trash"))
    return draft


def promote(draft: Path, vault: Path) -> Tuple[dict, List[str]]:
    snap = load_snapshot(vault)
    config = load_config(vault)
    live_now = list_files(vault, config)
    if live_now != snap["files"]:
        changed = sorted(set(live_now.items()) ^ set(snap["files"].items()))
        names = sorted({p for p, _ in changed})
        raise SystemExit(
            "live vault changed since the draft was made: "
            + ", ".join(names[:5]) + (" ..." if len(names) > 5 else "")
            + "\nRe-run draft so the agent sees the current vault."
        )
    result = verify(draft, snap)
    copied: List[str] = []
    if result["passed"]:
        for rel, digest in list_files(draft, config).items():
            if live_now.get(rel) != digest:
                target = vault / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(draft / rel, target)
                copied.append(rel)
        snapshot(vault)
    return result, copied


# ---------- CLI ----------

LABELS = {
    "raw_modified": "raw source changed",
    "notes_deleted": "note deleted",
    "prose_changed": "locked prose edited",
    "new_broken_links": "new broken link",
    "new_orphans": "new note with no inbound link",
    "missing_keys": "missing frontmatter",
    "log_not_appended": "log",
}


def print_result(result: dict) -> None:
    for key, label in LABELS.items():
        for item in result[key]:
            print(f"  FAIL  {label}: {item}")
    print(f"  {len(result['new_notes'])} new note(s), {len(result['changed_notes'])} edited note(s)")
    print("PASS" if result["passed"] else "REJECT")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("init", "snapshot", "verify", "draft"):
        p = sub.add_parser(name)
        p.add_argument("vault", type=Path)
        if name == "verify":
            p.add_argument("--json", action="store_true")
        if name == "draft":
            p.add_argument("--to", type=Path)
    p = sub.add_parser("promote")
    p.add_argument("draft", type=Path)
    p.add_argument("vault", type=Path)
    args = parser.parse_args(argv)

    if args.cmd == "init":
        path = args.vault / CONFIG_NAME
        if path.exists():
            print(f"{path} exists")
        else:
            path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
            print(f"wrote {path}")
        return 0
    if args.cmd == "snapshot":
        snap = snapshot(args.vault)
        print(f"snapshot: {len(snap['notes'])} notes, {len(snap['raw'])} raw files, "
              f"{len(snap['locked'])} locked, {len(snap['broken'])} existing broken links")
        return 0
    if args.cmd == "draft":
        draft = make_draft(args.vault, args.to)
        print(f"draft: {draft}\nPoint the agent at the draft, then run: promote {draft} {args.vault}")
        return 0
    if args.cmd == "verify":
        result = verify(args.vault, load_snapshot(args.vault))
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_result(result)
        return 0 if result["passed"] else 1
    if args.cmd == "promote":
        result, copied = promote(args.draft, args.vault)
        print_result(result)
        if result["passed"]:
            print(f"promoted {len(copied)} file(s) into {args.vault}")
        else:
            print(f"live vault unchanged. Fix the draft at {args.draft} and promote again.")
        return 0 if result["passed"] else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
