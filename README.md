# LP Marketing Harness

Gemini Notebook（旧 NotebookLM）に蓄積した「売れるLP」の知識（RAG）を引き出しながら、
LP制作〜運用改善までの全工程をAIで自動化するハーネス製品。

- 責任者: Claude（設計・実装・品質責任）
- 監査人: プロジェクトオーナー（各ステップのゲート承認）

## ドキュメント

| ファイル | 内容 |
|---|---|
| [docs/charter.md](docs/charter.md) | 目的・スコープ・役割・監査ゲートの運用ルール |
| [docs/architecture.md](docs/architecture.md) | パイプライン全体像とコンポーネント設計 |
| [docs/roadmap.md](docs/roadmap.md) | Step-by-step の開発ロードマップと各ゲートの合格基準 |
| [docs/decisions/](docs/decisions/) | 意思決定記録（ADR） |
| [knowledge/extraction-prompts.md](knowledge/extraction-prompts.md) | Gemini Notebook から知識を抽出するためのプロンプト集 |

## 現在のステップ

**Step 1: 知識の抽出と構造化（RAG → 原則カタログ）** — P1〜P7 受領、統合カタログ v0.1（26原則）作成済み。P8・P9 と動画別索引（V1）待ち。
中間レビュー: [knowledge/review/step1-interim-P4-P7.md](knowledge/review/step1-interim-P4-P7.md)
詳細は [docs/roadmap.md](docs/roadmap.md) を参照。
