# アーキテクチャ（ドラフト v0.1）

## 全体像

```
                ┌──────────────────────────────────────────┐
                │ Knowledge Layer                           │
                │  Gemini Notebook (RAG) ──► 原則カタログ    │
                │   (動画ソース群)        knowledge/principles│
                │        ▲  live query        │ ルーブリック生成│
                └────────┼────────────────────┼─────────────┘
                         │                    ▼
 Brief ─► Research ─► Strategy ─► Structure ─► Copy ─► Build ─► Review ─► Publish ─► Measure
 (入力)    (調査)     (訴求軸×N)   (構成)      (コピー) (HTML)  (採点+法令) (公開)    (計測)
                                                                  │ ▲                   │
                                                          人の承認 ┘ └── 次のABパターン ◄─┘
```

## コンポーネント

### 1. Knowledge Layer（知識層）

RAGとの接続は **アダプタ抽象** で扱い、接続方式を差し替え可能にする（[ADR-0001](decisions/0001-rag-integration.md)）。

| 資産 | 説明 |
|---|---|
| 原則カタログ `knowledge/principles/*.yaml` | Gemini から抽出し、監査人が承認した原則。各原則は ID・工程・内容・根拠・出典動画・適用条件・検証方法を持つ |
| ルーブリック | 原則カタログから自動生成する採点基準。Review 工程で使用 |
| Live Query アダプタ | カタログで答えられない個別質問を RAG に投げる経路（接続方式は ADR-0001） |

原則スキーマ（案）:

```yaml
id: FV-001
stage: copy            # research / strategy / structure / copy / design / offer / operation
title: FVで3秒以内に「自分ごと」と思わせる
statement: ...
rationale: ...
check: "FVのヘッドラインにターゲットの悩み語が含まれるか"   # 自動採点可能な形
applies_when: ...
anti_patterns: [...]
sources:
  - video: "【青汁王子】CVR(成約率)があがる魔法..."
    timestamp: "12:34"
confidence: high       # high / medium / low（ソース間で矛盾があれば low）
status: approved       # draft / approved / rejected（監査人が判定）
```

### 2. Pipeline（工程エージェント）

各工程は「入力スキーマ → LLM処理（原則を注入）→ 出力スキーマ」の純粋な関数として実装し、
中間成果物はすべて JSON/Markdown でファイル保存する（再実行・差分監査が可能）。

| 工程 | 主な出力 | 参照する原則 stage |
|---|---|---|
| Brief | `brief.json`（商品・価格・証拠素材・制約） | – |
| Research | `research.json`（悩み語・競合訴求・口コミ） | research |
| Strategy | `angles.json`（訴求軸 N パターン） | strategy, offer |
| Structure | `structure.json`（セクション順と各役割） | structure |
| Copy | `copy.<angle>.json` | copy, offer |
| Build | `lp/<angle>/index.html` | design |
| Review | `review.json`（ルーブリック点数・法令指摘・原則IDトレース） | 全て |
| Publish | デプロイURL・計測タグ | – |
| Measure | `experiment.json`（結果・勝ち判定・次の仮説） | operation |

### 3. Orchestrator

- 工程の実行順制御、再実行、人の承認待ちの管理
- 各出力に `principle_ids` と `model` / `prompt_version` を記録（監査用）

### 4. 品質ゲート（Review）

- **ルーブリック採点**: 原則カタログの `check` をLLM-as-judgeで採点。閾値未満は該当工程へ差し戻し（自動ループ、上限回数あり）
- **法令チェック**: 薬機法・景表法・特商法のNG表現検出（化粧品・健康食品で特に重要）
- **人の承認**: 公開前に必須

## 技術スタック（案・ADR化予定）

- 言語: Python 3.12（RAG非公式クライアントの選択肢があるため）
- 生成LLM: Claude API（コピー・構成・審査）
- LP出力: 静的 HTML/CSS（Tailwind）
- 公開: Cloudflare Pages または Vercel
- 計測: GA4 + 自前の ABテスト振り分け
