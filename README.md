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
| [docs/footguns.md](docs/footguns.md) | 踏んだ・踏みうる落とし穴と対策 |
| [knowledge/principles/catalog.yaml](knowledge/principles/catalog.yaml) | 原則カタログ（知識の正本） |
| [knowledge/context/](knowledge/context/) | **使いやすいコンテキストデータ**（プレイブック・工程別パック・採点項目。自動生成） |
| [knowledge/extraction-prompts.md](knowledge/extraction-prompts.md) | Gemini Notebook から知識を抽出するためのプロンプト集 |

## 現在のステップ

**Step 1: 知識の抽出と構造化（RAG → 原則カタログ）** — 抽出（97件）→ 統合（原則27件）→ コンテキスト化 → 追加質問 Q1〜Q3 の反映（カタログ v0.4：LP実例7件・コピー実例16件）が完了。次は欠落の補い方（D1）の判断と、原則ごとの監査人判定（1e）。
まず読むもの: [knowledge/context/playbook.md](knowledge/context/playbook.md)
判断待ちの一覧は [docs/roadmap.md](docs/roadmap.md#判断待ち監査人) を参照。
詳細は [docs/roadmap.md](docs/roadmap.md) を参照。
