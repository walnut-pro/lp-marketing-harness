# CLAUDE.md

## 言語
- 監査人（オーナー）への応答、ドキュメント、Gemini 向けプロンプトはすべて日本語で書く。
- コード中の識別子は英語のままでよい。コメントは周囲に合わせる。

## 進め方（pstack が基本。ADR-0003）
- 作業の進め方は pstack（`.claude/skills/`・`.claude/agents/`）に従う。次のどれかに当たる作業は `poteto-mode` スキルを呼び、その指示に従う。
  - 複数のファイルに触れる、または他のファイルが呼ぶシグネチャを変える
  - 設計・アーキテクチャの判断を含む
  - 原因が分かっていないバグ、または性能の問題
- 1ファイルで完結する小さな変更、質問への回答、1行の修正は直接行い、実物で確かめる。意図がはっきりしていれば `tdd`・`architect`・`how`・`why`・`arena`・`interrogate` を直接呼ぶ。
- 役割: Claude = 責任者、オーナー = 監査人（docs/charter.md）。pstack の原則 never-block-on-the-human に従い、**やり直せる作業は承認を待たずに進め、結果を示して監査人が事後に修正する**。
- 監査人が決めるもの（承認を待つもの）は次に限る。
  - 製品の方向性: Step 0 の前提（P1〜P4）、欠落の補い方（D1）、原則の承認・却下、KPI・予算
  - やり直せない操作: 公開、`main` へのマージ、外部への送信、データの削除、force-push
  - 法令適合（薬機法・景表法・特商法）の最終判断
- 現在地と判断待ちは docs/roadmap.md、落とし穴と対策は docs/footguns.md を参照。
- 監査人への依頼は1回あたり最大3件、優先順に（F-14）。

## pstack の取り込み
- `.claude/skills/` と `.claude/agents/` の pstack 由来のファイルは直接編集しない。更新は `scripts/vendor_pstack.py` の固定コミットを変えて取り込み直す（`third_party/pstack/` に出典とライセンス）。
- この環境に `gh` CLI は無い。`gh` を使う手順（babysit・fix-ci・get-pr-comments など）は GitHub MCP で読み替える。

## 知識データ
- 知識の正本は knowledge/principles/catalog.yaml。knowledge/context/ は自動生成物で直接編集しない。
- カタログを変更したら `python3 scripts/build_context.py` で再生成し、`./scripts/check.sh` が通ってからコミットする。
- Gemini の回答は knowledge/raw/ に無加工で保存する。信頼の扱いは ADR-0002。
