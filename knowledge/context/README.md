<!-- 自動生成: scripts/build_context.py。直接編集せず knowledge/principles/catalog.yaml を修正して再生成すること -->

# knowledge/context — 使いやすいコンテキストデータ

原則カタログ（`knowledge/principles/catalog.yaml`）から自動生成した、用途別のファイルです。

| ファイル | 誰が使う | 用途 |
|---|---|---|
| [playbook.md](playbook.md) | 人（監査人・チーム） | 全体像を把握する。原則の判定に使う |
| [stages/](stages/) | 工程エージェント（LLM） | 各工程のプロンプトに含める知識 |
| [rubric.yaml](rubric.yaml) | 審査・運用の仕組み | 採点項目の一覧 |

## 工程別パック

| 工程 | ファイル | 原則数 |
|---|---|---|
| ブリーフ | [stages/brief.md](stages/brief.md) | 4 |
| リサーチ | [stages/research.md](stages/research.md) | 4 |
| 戦略 | [stages/strategy.md](stages/strategy.md) | 7 |
| 構成 | [stages/structure.md](stages/structure.md) | 7 |
| コピー | [stages/copy.md](stages/copy.md) | 10 |
| 実装 | [stages/build.md](stages/build.md) | 10 |
| 審査 | [stages/review.md](stages/review.md) | 16 |
| 公開 | [stages/publish.md](stages/publish.md) | 2 |
| 運用 | [stages/operate.md](stages/operate.md) | 9 |

## 更新方法

```
# 1. knowledge/principles/catalog.yaml を編集
python3 scripts/validate_catalog.py   # 2. 整合性チェック
python3 scripts/build_context.py      # 3. このディレクトリを再生成
```
