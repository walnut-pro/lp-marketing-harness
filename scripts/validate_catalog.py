"""原則カタログの整合性チェック。

- YAML として読めること
- knowledge/raw/ の全 ID が principles / reference / cases / gaps / rejected のどこかに割り当てられていること
- 必須フィールドと列挙値が正しいこと
- examples / copy_examples が raw（Q1・Q2）の原文と一致し、related が既存の ID を指すこと
- gaps.confirmed_by が Q3 で「言及なし」の項目を指すこと
- knowledge/raw/Q*.md の全項目がどこかから参照されていること
"""
import glob
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "knowledge/principles/catalog.yaml"
REQUIRED = ["id", "stage", "used_in", "scope", "title", "statement", "rationale", "applies_when",
            "check", "check_type", "merged_from", "confidence", "status"]
PIPELINE = {"brief", "research", "strategy", "structure", "copy", "build", "review", "publish", "operate"}
ENUMS = {
    "stage": {"research", "strategy", "structure", "copy", "design", "offer", "operation"},
    "scope": {"core", "optional"},
    "confidence": {"high", "medium", "low"},
    "status": {"draft", "approved", "rejected"},
    "check_type": {"rule", "llm", "metric", "process"},
}
EXAMPLE_REQUIRED = ["id", "name", "industry", "role", "sections_in_order", "points", "quote", "raw", "used_in", "related"]
COPY_REQUIRED = ["id", "text", "kind", "product", "verdict", "why", "raw", "used_in", "related"]
VERDICTS = {"良い例", "改善後", "悪い例", "改善前", "候補（結果不明）"}
ITEM_RE = re.compile(r"^ \* (example|text|item):", re.M)
# Q ファイルのうち、番号付き項目以外の問い（Q1 末尾の2問）
NAMED_REFS = {"Q1": {"探し方", "構成順"}}


def parse_followups():
    """knowledge/raw/Q*.md を {"Q1": [項目dict, ...]} に読む。項目は 1 始まりで Qn#i と参照する。"""
    result = {}
    for f in sorted(glob.glob(str(ROOT / "knowledge/raw/Q*.md"))):
        name = Path(f).stem
        text = Path(f).read_text()
        items, cur, list_key = [], None, None
        for line in text.splitlines():
            m = re.match(r"^ \* (example|text|item): (.*)$", line)
            if m:
                cur = {m.group(1): m.group(2).strip()}
                items.append(cur)
                list_key = None
                continue
            if cur is None:
                continue
            if line.startswith("=== END") or re.match(r"^ \* ", line):
                cur = None  # 項目の後ろに続く自由回答（Q1 の2問）
                continue
            m = re.match(r"^\s+(\w+):\s*(.*)$", line)
            if m and not line.lstrip().startswith("* "):
                key, val = m.group(1), m.group(2).strip()
                if key in ("sections_in_order", "points"):
                    cur[key], list_key = [], key
                else:
                    cur[key], list_key = val, None
                continue
            m = re.match(r"^\s+\* (.*)$", line)
            if m and list_key:
                cur[list_key].append(m.group(1).strip())
        n_items = len(ITEM_RE.findall(text))
        end = re.search(r"^=== END \S+ \S+=(\d+) ===", text, re.M)
        result[name] = {"items": items, "count": n_items, "end": int(end.group(1)) if end else None}
    return result


def check_followups(catalog, errors):
    followups = parse_followups()
    for name, q in followups.items():
        if len(q["items"]) != q["count"]:
            errors.append(f"raw/{name}.md: parsed {len(q['items'])} items but regex counts {q['count']}")
        if q["end"] != q["count"]:
            errors.append(f"raw/{name}.md: END marker says {q['end']} but found {q['count']} items")

    def resolve(ref, owner):
        m = re.fullmatch(r"(Q\d+)#(.+)", ref)
        if not m or m.group(1) not in followups:
            errors.append(f"{owner}: bad follow-up ref {ref!r}")
            return None
        name, key = m.groups()
        if key.isdigit():
            if not 1 <= int(key) <= followups[name]["count"]:
                errors.append(f"{owner}: {ref} out of range (1..{followups[name]['count']})")
                return None
            return followups[name]["items"][int(key) - 1]
        if key not in NAMED_REFS.get(name, set()):
            errors.append(f"{owner}: unknown named ref {ref!r}")
        return None

    all_ids = {x["id"] for sec in ("principles", "reference", "cases", "gaps", "examples", "copy_examples")
               for x in catalog.get(sec, [])}
    referenced = set()

    for e in catalog.get("examples", []):
        for key in EXAMPLE_REQUIRED:
            if key not in e:
                errors.append(f"{e.get('id')}: missing {key}")
        if not str(e.get("id", "")).startswith("EX-"):
            errors.append(f"{e.get('id')}: example id must start with EX-")
        if not str(e.get("raw", "")).startswith("Q1#"):
            errors.append(f"{e.get('id')}: example raw must be Q1#n")
        referenced.add(e.get("raw"))
        item = resolve(e.get("raw", ""), e.get("id"))
        if item:  # 原文のコピーであること（F-18）
            pairs = [("name", "example"), ("industry", "industry"), ("role", "role"), ("quote", "quote"),
                     ("sections_in_order", "sections_in_order"), ("points", "points")]
            for mine, theirs in pairs:
                if e.get(mine) != item.get(theirs):
                    errors.append(f"{e['id']}: {mine} differs from raw {e['raw']}")

    for c in catalog.get("copy_examples", []):
        for key in COPY_REQUIRED:
            if key not in c:
                errors.append(f"{c.get('id')}: missing {key}")
        if not str(c.get("id", "")).startswith("CX-"):
            errors.append(f"{c.get('id')}: copy example id must start with CX-")
        if not str(c.get("raw", "")).startswith("Q2#"):
            errors.append(f"{c.get('id')}: copy example raw must be Q2#n")
        if c.get("verdict") not in VERDICTS:
            errors.append(f"{c.get('id')}: verdict={c.get('verdict')!r} not in {sorted(VERDICTS)}")
        if "normalized" in c and not c.get("audit_notes"):
            errors.append(f"{c['id']}: normalized requires audit_notes with the original and the reason")
        referenced.add(c.get("raw"))
        item = resolve(c.get("raw", ""), c.get("id"))
        if item:
            for key in ("text", "kind", "product", "verdict", "why"):
                if c.get(key) != item.get(key):
                    errors.append(f"{c['id']}: {key} differs from raw {c['raw']}")

    for x in catalog.get("examples", []) + catalog.get("copy_examples", []):
        bad = set(x.get("used_in", [])) - PIPELINE
        if bad:
            errors.append(f"{x['id']}: unknown used_in {sorted(bad)}")
        missing = set(x.get("related", [])) - all_ids
        if missing:
            errors.append(f"{x['id']}: related to unknown ids {sorted(missing)}")

    for g in catalog.get("gaps", []):
        for ref in g.get("confirmed_by", []):
            referenced.add(ref)
            if not ref.startswith("Q3#"):
                errors.append(f"{g['id']}: confirmed_by must be Q3#n, got {ref!r}")
                continue
            item = resolve(ref, g["id"])
            if item and item.get("mentioned") != "言及なし":
                errors.append(f"{g['id']}: {ref} is not 言及なし (mentioned={item.get('mentioned')!r})")

    for x in catalog["principles"] + catalog["reference"] + catalog.get("cases", []) + catalog.get("gaps", []):
        for ref in x.get("merged_from", []):
            if ref.startswith("Q"):
                referenced.add(ref)
                resolve(ref, x["id"])

    expected = {f"{name}#{i}" for name, q in followups.items() for i in range(1, q["count"] + 1)}
    expected |= {f"{name}#{k}" for name, keys in NAMED_REFS.items() for k in keys}
    if expected - referenced:
        errors.append(f"follow-up items not referenced: {sorted(expected - referenced, key=lambda r: (r.split('#')[0], r.split('#')[1].zfill(3)))}")
    return sum(q["count"] for q in followups.values())


def main() -> int:
    catalog = yaml.safe_load(CATALOG.read_text())
    principles, reference, rejected = catalog["principles"], catalog["reference"], catalog["rejected"]
    cases, gaps = catalog.get("cases", []), catalog.get("gaps", [])
    errors = []

    for p in principles:
        for key in REQUIRED:
            if key not in p:
                errors.append(f"{p.get('id')}: missing {key}")
        for key, allowed in ENUMS.items():
            if key in p and p[key] not in allowed:
                errors.append(f"{p['id']}: {key}={p[key]!r} not in {sorted(allowed)}")

    for p in principles:
        bad = set(p.get("used_in", [])) - PIPELINE
        if bad:
            errors.append(f"{p['id']}: unknown used_in {sorted(bad)}")
    for g in gaps:
        bad = set(g.get("affects", [])) - PIPELINE
        if bad:
            errors.append(f"{g['id']}: unknown affects {sorted(bad)}")

    examples, copy_examples = catalog.get("examples", []), catalog.get("copy_examples", [])
    ids = [p["id"] for p in principles + reference + rejected + cases + gaps + examples + copy_examples]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"duplicate ids: {sorted(dupes)}")

    raw = set()
    for f in glob.glob(str(ROOT / "knowledge/raw/P*.md")):
        raw |= set(re.findall(r"^- id: (\S+)", Path(f).read_text(), re.M))
    covered = {i for p in principles + reference + cases + gaps for i in p.get("merged_from", [])
               if not re.match(r"Q\d+#", i)}
    covered |= {r["id"] for r in rejected}
    if raw - covered:
        errors.append(f"raw ids not covered: {sorted(raw - covered)}")
    if covered - raw:
        errors.append(f"unknown raw ids referenced: {sorted(covered - raw)}")

    followup_items = check_followups(catalog, errors)

    meta = catalog["meta"]
    counts = {"raw_items": len(raw), "followup_items": followup_items, "merged_principles": len(principles),
              "reference_items": len(reference), "rejected_items": len(rejected),
              "cases": len(cases), "examples": len(examples), "copy_examples": len(copy_examples),
              "gaps": len(gaps)}
    for key, n in counts.items():
        if meta.get(key) != n:
            errors.append(f"meta.{key}={meta.get(key)} but actual {n}")

    for e in errors:
        print("ERROR:", e)
    print(f"raw={len(raw)} followup={followup_items} principles={len(principles)} reference={len(reference)} "
          f"rejected={len(rejected)} cases={len(cases)} examples={len(examples)} "
          f"copy_examples={len(copy_examples)} gaps={len(gaps)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
