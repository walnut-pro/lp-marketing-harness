"""原則カタログの整合性チェック。

- YAML として読めること
- knowledge/raw/ の全 ID が principles / reference / rejected のどこかに割り当てられていること
- 必須フィールドと列挙値が正しいこと
"""
import glob
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "knowledge/principles/catalog.draft.yaml"
REQUIRED = ["id", "stage", "scope", "title", "statement", "applies_when", "check", "merged_from", "confidence", "status"]
ENUMS = {
    "stage": {"research", "strategy", "structure", "copy", "design", "offer", "operation"},
    "scope": {"core", "optional"},
    "confidence": {"high", "medium", "low"},
    "status": {"draft", "approved", "rejected"},
}


def main() -> int:
    catalog = yaml.safe_load(CATALOG.read_text())
    principles, reference, rejected = catalog["principles"], catalog["reference"], catalog["rejected"]
    errors = []

    for p in principles:
        for key in REQUIRED:
            if key not in p:
                errors.append(f"{p.get('id')}: missing {key}")
        for key, allowed in ENUMS.items():
            if key in p and p[key] not in allowed:
                errors.append(f"{p['id']}: {key}={p[key]!r} not in {sorted(allowed)}")

    ids = [p["id"] for p in principles + reference + rejected]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"duplicate ids: {sorted(dupes)}")

    raw = set()
    for f in glob.glob(str(ROOT / "knowledge/raw/P*.md")):
        raw |= set(re.findall(r"^- id: (\S+)", Path(f).read_text(), re.M))
    covered = {i for p in principles + reference for i in p["merged_from"]} | {r["id"] for r in rejected}
    if raw - covered:
        errors.append(f"raw ids not covered: {sorted(raw - covered)}")
    if covered - raw:
        errors.append(f"unknown raw ids referenced: {sorted(covered - raw)}")

    meta = catalog["meta"]
    counts = {"raw_items": len(raw), "merged_principles": len(principles),
              "reference_items": len(reference), "rejected_items": len(rejected)}
    for key, n in counts.items():
        if meta.get(key) != n:
            errors.append(f"meta.{key}={meta.get(key)} but actual {n}")

    for e in errors:
        print("ERROR:", e)
    print(f"raw={len(raw)} principles={len(principles)} reference={len(reference)} rejected={len(rejected)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
