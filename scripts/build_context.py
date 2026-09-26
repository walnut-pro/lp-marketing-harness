"""原則カタログ（knowledge/principles/catalog.yaml）から、使いやすいコンテキストデータを生成する。

生成物（knowledge/context/）:
  README.md         どのファイルをいつ使うかの案内
  stages/<工程>.md  各工程のLLMプロンプトに含める知識パック
  rubric.yaml       審査・運用で使う採点項目
  playbook.md       人が読むための要約

使い方:
  python3 scripts/build_context.py          生成して書き出す
  python3 scripts/build_context.py --check  生成物がカタログと一致しているか確認（不一致なら終了コード1）
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "knowledge/principles/catalog.yaml"
OUT = ROOT / "knowledge/context"

STAGES = {
    "brief": ("ブリーフ", "商品・オファー・証拠素材を整理する"),
    "research": ("リサーチ", "売れている競合LPと顧客の悩みを調べる"),
    "strategy": ("戦略", "訴求の切り口と競合に勝つ点を決める"),
    "structure": ("構成", "セクションの種類・順番と購入導線を決める"),
    "copy": ("コピー", "ファーストビューと本文の文章を書く"),
    "build": ("実装", "HTML・部品・表示速度を作り込む"),
    "review": ("審査", "原則による採点と法令チェックを行う"),
    "publish": ("公開", "配信を始め、予算を増やす判断をする"),
    "operate": ("運用", "計測し、ABテストで改善し続ける"),
}
STAGE_OF_PRINCIPLE = {  # playbook の見出し用（catalog の stage）
    "research": "リサーチ", "strategy": "戦略", "structure": "構成", "copy": "コピー・ファーストビュー",
    "design": "デザイン・導線", "offer": "オファー", "operation": "運用",
}
CHECK_TYPE = {"rule": "機械判定", "llm": "LLM判定", "metric": "計測データで判定", "process": "手順・記録で判定"}
CONFIDENCE = {"high": "高", "medium": "中", "low": "低"}
GENERATED = "<!-- 自動生成: scripts/build_context.py。直接編集せず knowledge/principles/catalog.yaml を修正して再生成すること -->"
# コピー実例の verdict をパック・プレイブックでの分類にまとめる
VERDICT_GROUPS = [
    ("good", "良い例・改善後", {"良い例", "改善後"}),
    ("bad", "悪い例・改善前", {"悪い例", "改善前"}),
    ("candidate", "候補（ABテストの案。勝ち負けは不明）", {"候補（結果不明）"}),
]
SOURCE_NOTE = "出典: Gemini Notebook「lp marketing harness」（売れるLPに関する動画群）から抽出した知識。監査人の判断により信頼済みデータとして扱う（ADR-0002）。"


def load():
    catalog = yaml.safe_load(CATALOG.read_text())
    catalog["principles"] = [p for p in catalog["principles"] if p["status"] != "rejected"]
    return catalog


def order(principles):
    rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(principles, key=lambda p: rank[p["confidence"]])  # 安定ソートなのでカタログ順は保たれる


def principle_block(p):
    lines = [f"### {p['id']}｜{p['title']}", "", f"- やること: {p['statement'].strip()}"]
    if p["applies_when"] != "常に":
        lines.append(f"- 適用条件: {p['applies_when']}")
    lines.append(f"- 理由: {p['rationale']}")
    if p.get("anti_patterns"):
        lines.append("- 避けること:")
        lines += [f"  - {a}" for a in p["anti_patterns"]]
    lines.append(f"- 確認方法（{CHECK_TYPE[p['check_type']]}）: {p['check']}")
    if p.get("caveats"):
        lines.append("- 注意:")
        lines += [f"  - {c}" for c in p["caveats"]]
    if p.get("evidence"):
        lines.append("- ソースの発言: " + " / ".join(f"「{e}」" for e in p["evidence"][:2]))
    lines.append(f"- 確度: {CONFIDENCE[p['confidence']]}")
    return "\n".join(lines)


def example_block(e):
    lines = [f"### {e['id']}｜{e['name']}（{e['industry']}／{e['role']}）", "",
             "- 話に出てきたセクション・要素:"]
    lines += [f"  {i}. {s}" for i, s in enumerate(e["sections_in_order"], 1)]
    lines.append("- 語られている点:")
    lines += [f"  - {pt}" for pt in e["points"]]
    lines.append(f"- ソースの発言: 「{e['quote']}」")
    lines.append(f"- 関連: {', '.join(e['related'])}")
    if e.get("caveats"):
        lines.append("- 注意:")
        lines += [f"  - {c}" for c in e["caveats"]]
    return "\n".join(lines)


def copy_line(c):
    if c["kind"] == "FV画像":
        head = f"- [画像の説明] {c['text']}（{c['product']}）"
    elif c.get("normalized"):
        head = f"- 「{c['normalized']}」（{c['kind']}／{c['product']}。字幕の原文は「{c['text']}」）"
    else:
        head = f"- 「{c['text']}」（{c['kind']}／{c['product']}）"
    lines = [f"{head} {c['id']}", f"  - 理由: {c['why']}", f"  - 関連: {', '.join(c['related'])}"]
    lines += [f"  - 注意: {cv}" for cv in c.get("caveats", [])]
    return "\n".join(lines)


def examples_section(stage, catalog):
    exs = [e for e in catalog.get("examples", []) if stage in e["used_in"]]
    if not exs:
        return []
    out = [f"## LP実例（{len(exs)}件）", "",
           "ソースで紹介された実在のLP・サイト。構成と考え方の参考にする。",
           "ソースはLP全体のセクション順を明言していない。「話に出てきたセクション・要素」は話に出たものを Gemini が上から順に並べたもので、全セクションではない。",
           "「注意」に避ける例とあるものは真似ない。",
           "商品名・人物・文章・数値（価格・件数・割引率）を生成物や目標値にそのまま使わない。", ""]
    for e in exs:
        out += [example_block(e), ""]
    return out


def copy_examples_section(stage, catalog):
    cxs = [c for c in catalog.get("copy_examples", []) if stage in c["used_in"]]
    if not cxs:
        return []
    out = [f"## コピー実例（{len(cxs)}件）", "",
           "ソースに出てきたコピー・FV画像の実例（原文のまま。字幕の誤変換を直したものは原文を併記）。言い回しの手本ではなく、何が良い／悪いとされたかの判断材料にする。",
           "「改善後」は改善で採用された案という意味で、単独で効果が検証されたとは限らない。",
           "実例の文言・商品名・人物名・数値（割引率など）を生成物にそのまま使わない。価格・割引・根拠は Brief の事実に従う。", ""]
    for _, label, verdicts in VERDICT_GROUPS:
        group = [c for c in cxs if c["verdict"] in verdicts]
        if group:
            out += [f"### {label}（{len(group)}件）", ""]
            out += [copy_line(c) for c in group]
            out.append("")
    return out


def stage_pack(stage, catalog):
    name, purpose = STAGES[stage]
    ps = order([p for p in catalog["principles"] if stage in p["used_in"]])
    core = [p for p in ps if p["scope"] == "core"]
    optional = [p for p in ps if p["scope"] == "optional"]
    gaps = [g for g in catalog["gaps"] if stage in g.get("affects", [])]

    out = [GENERATED, "", f"# 工程コンテキスト: {name}（{stage}）", "",
           f"この工程の目的: {purpose}。", "",
           "このファイルは LP 生成ハーネスの工程エージェントに渡す知識パックです。", SOURCE_NOTE,
           f"カタログ v{catalog['meta']['version']}（原則の個別判定前）。", "",
           "## 使い方のルール", "",
           "1. 出力には、根拠にした原則の ID を `principle_ids` として必ず記録する",
           "2. 「必ず守る」は適用条件（書かれていなければ全案件）を満たす限り必ず適用する。「条件付き」は適用条件を満たす場合に適用を検討し、適用しなかった理由も記録する",
           "3. [RAG外] の注意は法令などの一般知識による補足で、ソースの原則より優先する",
           "4. 「ソースに無いこと」に当たる判断は推測で埋めず、出力の `gaps` に明記する",
           ""]
    if not ps:
        out += ["この工程に直接当てはまる原則はありません。", ""]
    if core:
        out += [f"## 必ず守る（{len(core)}件）", ""]
        for p in core:
            out += [principle_block(p), ""]
    if optional:
        out += [f"## 条件付き（{len(optional)}件）", ""]
        for p in optional:
            out += [principle_block(p), ""]
    out += examples_section(stage, catalog)
    out += copy_examples_section(stage, catalog)
    if gaps:
        out += ["## ソースに無いこと（推測で補わない）", ""]
        out += [f"- {g['id']}: {g['title']}" for g in gaps]
        out.append("")
    return "\n".join(out)


def rubric(catalog):
    items = []
    for p in catalog["principles"]:
        items.append({
            "id": f"R-{p['id']}",
            "principle": p["id"],
            "title": p["title"],
            "check": p["check"],
            "check_type": p["check_type"],
            "stages": p["used_in"],
            "severity": "must" if p["scope"] == "core" else "should",
            "applies": "always" if p["scope"] == "core" else "conditional",
            "applies_when": p["applies_when"],
            "confidence": p["confidence"],
        })
    header = ("# 自動生成: scripts/build_context.py。直接編集しないこと\n"
              "# severity: must = 必須（core） / should = 適用条件を満たす場合に必須（optional）\n"
              "# check_type: rule = 機械判定 / llm = LLM判定 / metric = 計測データ / process = 手順・記録\n")
    body = {"version": catalog["meta"]["version"], "items": items}
    return header + yaml.safe_dump(body, allow_unicode=True, sort_keys=False, width=1000)


def playbook(catalog):
    ps = catalog["principles"]
    out = [GENERATED, "", "# 売れるLPプレイブック", "", SOURCE_NOTE,
           f"カタログ v{catalog['meta']['version']}：原則 {len(ps)} 件（必須 {sum(p['scope'] == 'core' for p in ps)}／条件付き "
           f"{sum(p['scope'] == 'optional' for p in ps)}）、事例 {len(catalog['cases'])} 件、LP実例 {len(catalog.get('examples', []))} 件、"
           f"コピー実例 {len(catalog.get('copy_examples', []))} 件、ソースに無いこと {len(catalog['gaps'])} 件。", "",
           "## ひとことで言うと", ""]
    out += [f"{i}. {s}" for i, s in enumerate(catalog["summary"], 1)]
    out.append("")

    out += ["## 原則一覧", "", "確度: 高 = 一般原則として繰り返し語られる／中 = 1つの事例から／低 = Gemini がまとめた比重が大きい", ""]
    for key, label in STAGE_OF_PRINCIPLE.items():
        group = [p for p in ps if p["stage"] == key]
        if not group:
            continue
        out += [f"### {label}", ""]
        for p in group:
            tag = "必須" if p["scope"] == "core" else "条件付き"
            line = f"- **{p['title']}**（{p['id']}／{tag}／確度{CONFIDENCE[p['confidence']]}）  \n  {p['statement'].strip()}"
            if p["scope"] == "optional":
                line += f"  \n  適用条件: {p['applies_when']}"
            out.append(line)
        out.append("")

    out += ["## 事例の数値（参考。合格基準には使わない）", ""]
    out += [f"- {c['summary']}（{c['id']}）" for c in catalog["cases"]]
    out.append("")

    out += ["## LP実例", "", "ソースで紹介された実在のLP・サイト（Q1）。リサーチ・戦略・構成の工程に渡す。", "",
            "| ID | 実例 | 業種 | 位置づけ | 関連する原則 |", "|---|---|---|---|---|"]
    for e in catalog.get("examples", []):
        out.append(f"| {e['id']} | {e['name']} | {e['industry']} | {e['role']} | {', '.join(e['related'])} |")
    out.append("")

    out += ["## コピー実例", "", "ソースに出てきたコピー・FV画像（Q2、原文のまま）。コピー・審査の工程に渡す。", ""]
    for _, label, verdicts in VERDICT_GROUPS:
        group = [c for c in catalog.get("copy_examples", []) if c["verdict"] in verdicts]
        if not group:
            continue
        out += [f"### {label}", ""]
        for c in group:
            text = f"[画像] {c['text']}" if c["kind"] == "FV画像" else f"「{c.get('normalized', c['text'])}」"
            if c.get("normalized"):
                text += f"（原文「{c['text']}」を表記修正）"
            out.append(f"- {text}（{c['kind']}／{c['product']}／{c['id']}）— {c['why']}")
        out.append("")

    out += ["## ソースに無いこと", "", "ハーネスはこれらを推測で埋めず、補い方を監査人が決める（roadmap の D1）。",
            "「Q3で確認」は、Gemini への追加質問 Q3 で「言及なし」と確認済みの項目。", "",
            "| ID | 内容 | 影響する工程 | Q3で確認 |", "|---|---|---|---|"]
    for g in catalog["gaps"]:
        affects = "、".join(STAGES[s][0] for s in g.get("affects", [])) or "スコープ外"
        confirmed = "、".join(g.get("confirmed_by", [])) or "－"
        out.append(f"| {g['id']} | {g['title']} | {affects} | {confirmed} |")
    out.append("")

    out += ["## 参考（ハーネスの採点対象外）", ""]
    out += [f"- {r['title']}（{r['id']}）— {r['reason']}" for r in catalog["reference"]]
    out.append("")
    if catalog.get("rejected"):
        out += ["## 却下", ""]
        out += [f"- {r['title']}（{r['id']}）— {r['reason']}" for r in catalog["rejected"]]
        out.append("")
    return "\n".join(out)


def readme(catalog):
    def count(section, s):
        return sum(s in x["used_in"] for x in catalog.get(section, []))
    out = [GENERATED, "", "# knowledge/context — 使いやすいコンテキストデータ", "",
           "原則カタログ（`knowledge/principles/catalog.yaml`）から自動生成した、用途別のファイルです。", "",
           "| ファイル | 誰が使う | 用途 |", "|---|---|---|",
           "| [playbook.md](playbook.md) | 人（監査人・チーム） | 全体像を把握する。原則の判定に使う |",
           "| [stages/](stages/) | 工程エージェント（LLM） | 各工程のプロンプトに含める知識 |",
           "| [rubric.yaml](rubric.yaml) | 審査・運用の仕組み | 採点項目の一覧 |", "",
           "## 工程別パック", "", "| 工程 | ファイル | 原則数 | LP実例 | コピー実例 |", "|---|---|---|---|---|"]
    for s, (name, _) in STAGES.items():
        out.append(f"| {name} | [stages/{s}.md](stages/{s}.md) | {count('principles', s)} | "
                   f"{count('examples', s)} | {count('copy_examples', s)} |")
    out += ["", "## 更新方法", "", "```",
            "# 1. knowledge/principles/catalog.yaml を編集",
            "python3 scripts/validate_catalog.py   # 2. 整合性チェック",
            "python3 scripts/build_context.py      # 3. このディレクトリを再生成",
            "```", ""]
    return "\n".join(out)


def render(catalog):
    files = {"README.md": readme(catalog), "playbook.md": playbook(catalog), "rubric.yaml": rubric(catalog)}
    for s in STAGES:
        files[f"stages/{s}.md"] = stage_pack(s, catalog)
    return files


def main() -> int:
    files = render(load())
    if "--check" in sys.argv:
        stale = [name for name, text in files.items()
                 if not (OUT / name).exists() or (OUT / name).read_text() != text]
        for name in stale:
            print(f"STALE: knowledge/context/{name}")
        return 1 if stale else 0
    for name, text in files.items():
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    print(f"generated {len(files)} files in knowledge/context/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
