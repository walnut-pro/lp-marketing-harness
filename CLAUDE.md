# CLAUDE.md

## 言語
- 監査人（オーナー）への応答、ドキュメント、Gemini 向けプロンプトはすべて日本語で書く。
- コード中の識別子は英語のままでよい。コメントは周囲に合わせる。

## 進め方
- 役割: Claude = 責任者、オーナー = 監査人。各ステップは監査人の承認を得てから次へ進む（docs/charter.md）。
- 現在地と判断待ちは docs/roadmap.md、落とし穴と対策は docs/footguns.md を参照。
- 監査人への依頼は1回あたり最大3件、優先順に（F-14）。

## 知識データ
- 知識の正本は knowledge/principles/catalog.yaml。knowledge/context/ は自動生成物で直接編集しない。
- カタログを変更したら `python3 scripts/build_context.py` で再生成し、`./scripts/check.sh` が通ってからコミットする。
- Gemini の回答は knowledge/raw/ に無加工で保存する。信頼の扱いは ADR-0002。
