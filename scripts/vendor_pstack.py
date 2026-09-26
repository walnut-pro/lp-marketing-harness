#!/usr/bin/env python3
"""pstack（michael-denyer/pstack-claude）のスキルとエージェントを .claude/ に取り込む（ADR-0003）。

使い方:
  python3 scripts/vendor_pstack.py <pstack-claude のクローン>  # 取り込み。クローンが固定コミットであることを確認する
  python3 scripts/vendor_pstack.py --check                       # 取り込んだファイルが手で変更されていないか検査する

取り込んだファイルは直接編集しない。更新は UPSTREAM_COMMIT を変えて取り込み直す。
"""
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_REPO = "https://github.com/michael-denyer/pstack-claude"
UPSTREAM_TAG = "v0.9.45"
UPSTREAM_COMMIT = "c02fd4922b25ee005f42042463d741d236c2c35e"

SKILLS_DIR = ROOT / ".claude/skills"
AGENTS_DIR = ROOT / ".claude/agents"
NOTICE_DIR = ROOT / "third_party/pstack"
MANIFEST = NOTICE_DIR / "manifest.sha256"
NOTICE_FILES = ["LICENSE", "LICENSE-cursor-team-kit", "NOTICE.md", "NOTICE-skills.md"]

# プラグインではなくプロジェクトのエージェントとして置くため、名前空間 "pstack:" を外す。
# (旧文字列, 新文字列, 期待する置換数)。期待数と違えば黙って進まず失敗する（F-13）。
EXACT_SUBS = [
    ("Plugin agents register under the plugin namespace. The bare name `poteto-agent` errors.",
     "In this repository the agents are project agents in `.claude/agents/`, so they register under their bare names.",
     1),
]
AGENT_REF_RE = re.compile(r"pstack:(poteto-agent|effort-|comment-sicko)")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rewrite(text, counts):
    for old, new, _ in EXACT_SUBS:
        counts[old] += text.count(old)
        text = text.replace(old, new)
    return AGENT_REF_RE.sub(r"\1", text)


def read_manifest():
    if not MANIFEST.exists():
        return {}
    entries = {}
    for line in MANIFEST.read_text().splitlines():
        digest, rel = line.split("  ", 1)
        entries[rel] = digest
    return entries


def vendor(src):
    head = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    if head != UPSTREAM_COMMIT:
        sys.exit(f"ERROR: {src} is at {head}, expected {UPSTREAM_COMMIT} ({UPSTREAM_TAG})")
    plugin = src / "plugins/pstack"

    previous = read_manifest()
    for rel in previous:
        (ROOT / rel).unlink(missing_ok=True)
    for d in sorted(SKILLS_DIR.glob("**/"), key=lambda p: len(p.parts), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()

    copies = []
    for f in sorted((plugin / "skills").rglob("*")):
        if f.is_file():
            copies.append((f, SKILLS_DIR / f.relative_to(plugin / "skills")))
    for sub in ("agents", "effort-agents"):
        for f in sorted((plugin / sub).glob("*.md")):
            copies.append((f, AGENTS_DIR / f.name))
    for name in NOTICE_FILES:
        copies.append((src / name, NOTICE_DIR / name))

    counts = {old: 0 for old, _, _ in EXACT_SUBS}
    written = []
    for f, dst in copies:
        if dst.exists() and dst.relative_to(ROOT).as_posix() not in previous:
            sys.exit(f"ERROR: {dst.relative_to(ROOT)} exists and is not pstack's; refusing to overwrite")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if f.suffix == ".md":
            dst.write_text(rewrite(f.read_text(), counts))
            shutil.copymode(f, dst)
        else:
            shutil.copy2(f, dst)
        written.append(dst)

    bad = [f"{old!r}: {counts[old]} (expected {n})" for old, _, n in EXACT_SUBS if counts[old] != n]
    leftover = [p.relative_to(ROOT).as_posix() for p in written
                if p.suffix == ".md" and AGENT_REF_RE.search(p.read_text())]
    if bad or leftover:
        sys.exit("ERROR: substitution mismatch\n  " + "\n  ".join(bad + leftover))

    lines = sorted(f"{sha256(p)}  {p.relative_to(ROOT).as_posix()}" for p in written)
    MANIFEST.write_text("\n".join(lines) + "\n")
    skills = len({p.relative_to(SKILLS_DIR).parts[0] for p in written if SKILLS_DIR in p.parents})
    agents = len([p for p in written if p.parent == AGENTS_DIR])
    print(f"vendored pstack {UPSTREAM_TAG}: skills={skills} agents={agents} files={len(written)}")


def check():
    entries = read_manifest()
    if not entries:
        sys.exit(f"ERROR: {MANIFEST.relative_to(ROOT)} is missing")
    errors = []
    for rel, digest in entries.items():
        p = ROOT / rel
        if not p.exists():
            errors.append(f"missing: {rel}")
        elif sha256(p) != digest:
            errors.append(f"modified: {rel}")
    skill_dirs = {Path(rel).parts[2] for rel in entries if rel.startswith(".claude/skills/")}
    for d in sorted(skill_dirs):
        for p in (SKILLS_DIR / d).rglob("*"):
            if p.is_file() and p.relative_to(ROOT).as_posix() not in entries:
                errors.append(f"unexpected: {p.relative_to(ROOT).as_posix()}")
    if errors:
        print("ERROR: vendored pstack differs from the manifest (re-run scripts/vendor_pstack.py):")
        print("\n".join(f"  {e}" for e in errors))
        return 1
    print(f"pstack {UPSTREAM_TAG}: {len(entries)} vendored files match the manifest")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        sys.exit(check())
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    vendor(Path(sys.argv[1]).resolve())
