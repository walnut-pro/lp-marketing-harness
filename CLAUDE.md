# CLAUDE.md

## 言語
- 監査人（オーナー）への応答、ドキュメント、Gemini 向けプロンプトはすべて日本語で書く。
- コード中の識別子は英語のままでよい。コメントは周囲に合わせる。

## 進め方
- 役割: Claude = 責任者、オーナー = 監査人。各ステップは監査人の承認を得てから次へ進む（docs/charter.md）。
- 現在地と判断待ちは docs/roadmap.md、落とし穴と対策は docs/footguns.md を参照。
- 監査人への依頼は1回あたり最大3件、優先順に（F-14）。

## pstack（ADR-0003）
- pstack のスキル・原則・起動時の指示より、この CLAUDE.md と憲章の監査ゲートを優先する。
- pstack の原則 never-block-on-the-human は、ステップ内の可逆な作業にだけ使う。ステップ間のゲートや前提（P1〜P5）の判断は、必ず監査人の承認を待つ。
- `arena`・`architect`・`interrogate` は複数モデルのサブエージェントを並べて費用が大きい。使う前に監査人へ断る。
- `gh` CLI を前提とするスキル（babysit・fix-ci など）は使わない。GitHub の操作は GitHub MCP で行う。

## 知識データ
- 知識の正本は knowledge/principles/catalog.yaml。knowledge/context/ は自動生成物で直接編集しない。
- カタログを変更したら `python3 scripts/build_context.py` で再生成し、`./scripts/check.sh` が通ってからコミットする。
- Gemini の回答は knowledge/raw/ に無加工で保存する。信頼の扱いは ADR-0002。
