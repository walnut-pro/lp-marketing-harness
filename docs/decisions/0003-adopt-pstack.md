# ADR-0003: 開発の進め方の補助として pstack（Claude Code 移植版）を導入する

- ステータス: **提案**（監査人の承認待ち。導入には監査人による環境の Setup script への追記が必要）
- 日付: 2026-09-26

## 背景

監査人から pstack の導入依頼があった（2026-09-26）。調査の結果、pstack は次のものと判断した。

- Cursor の Lauren Tan 氏（poteto）が作った、AI エージェント向けのスキル集（MIT）。原本は [cursor/plugins の pstack](https://github.com/cursor/plugins/tree/main/pstack)
- 目的は「もっともらしいが検証されていないコード」を減らすこと。入口の `/poteto-mode` が、調査・バグ修正・機能追加などの作業に応じて手順を選ぶ。`how`（仕組みの説明）、`why`（原因調査）、`architect`（設計比較）、`interrogate`（複数モデルによるレビュー）などのスキルと、約20の設計原則を含む
- 同名の Linux デバッグツール（peadar/pstack）とは無関係

監査人の指示: 移植版は pstack-claude、導入先はこのリポジトリ（責任者の推奨どおり）。デフォルトブランチは現状のままとする。

## 決定

- **[michael-denyer/pstack-claude](https://github.com/michael-denyer/pstack-claude) v0.9.45（commit `c02fd49`）を導入する**。バージョンはタグで固定し、更新は ADR 追記と PR で行う
- **入れ方は環境の Setup script とする**（下記）。リポジトリの `.claude/settings.json` には書かない（理由は「パイロットの結果」）
- **優先順位**: CLAUDE.md・憲章（docs/charter.md）の監査ゲートは、pstack の指示や原則より常に優先する。特に pstack の原則 `never-block-on-the-human`（可逆な作業は人に聞かず進める）は、このプロジェクトでは**ステップ間のゲートに適用しない**。CLAUDE.md に明記した
- pstack は開発の進め方の道具であり、製品の技術スタック（Step 0 の前提 P4: Python + Claude API + 静的HTML）は変えない。したがって F-12 の「準備（未承認）」扱いの対象外とする

### Setup script に追記する内容（監査人が行う）

クラウド環境の設定（セッションのタイトルバーの環境メニュー → Edit → Setup script）に次の2行を追加する。失敗してもセッションは開始できるよう `|| true` を付ける。

```sh
claude plugin marketplace add 'michael-denyer/pstack-claude#v0.9.45' || true
claude plugin install pstack@pstack-claude || true
```

## パイロットの結果（F-01）

隔離した設定ディレクトリ（作業用の一時領域）で、上の2コマンドを実行して確かめた。

| 確認項目 | 結果 |
|---|---|
| インストール | 成功。スキル54、フック1（SessionStart）、MCP サーバーなし |
| 常時のコンテキスト消費 | 1セッションあたり約4,300トークン（`claude plugin details` の見積もり） |
| 起動時フック | 「複数ファイルに触れる作業・設計判断・原因不明のバグでは `poteto-mode` を使え」という指示を毎セッション注入する。「CLAUDE.md が優先」とも明記されている |
| スキル1件の実行 | `/pstack:how` に「validate_catalog.py は実例と raw の一致をどう検査しているか」を聞いた。サブエージェント（opus）に委ねて、日本語で正確な説明を返した（約2分・約0.60ドル）。指摘された注意点（正規化なし、principles 本文は検査対象外など）はコードと一致することを確認した |
| バージョン固定 | `owner/repo#v0.9.45` でタグに固定できる（固定先 = `c02fd49`） |
| リポジトリの `.claude/settings.json` で宣言 | **クラウドセッションでは読み込まれない**。公式ドキュメント（plugins/loading）にも「クラウドセッションは `extraKnownMarketplaces` を追加しない（信頼ダイアログが出ないため）」とある。`claude -p` でも自動インストールされなかった |
| リポジトリの SessionStart フックでインストール | インストール自体はできるが、**有効になるのは次のセッションから**。クラウドは毎回新しいコンテナなので、実質使えない |

このため、最初の推奨（リポジトリに登録）では動かないと分かり、Setup script 方式に変更した（F-28）。

## 代替案

| 案 | 採らない理由 |
|---|---|
| リポジトリの `.claude/settings.json` に登録 | クラウドセッションでは読み込まれない（パイロットで確認） |
| スキルを `.claude/skills/` に複製 | 54スキルの複製と追従が負担。フック・エージェントが動かない。ライセンス表示の管理も増える |
| irg1008/cstack（別の移植版） | 利用実績が少ない（スター4、9コミット）。pstack-claude（スター607、106コミット）の方が原本に忠実で保守されている |
| 原本（Cursor 用） | Claude Code 用ではない |
| 導入しない | 監査人の依頼に反する。検証（`how` / `why` / `interrogate`）の手順はこのプロジェクトの品質方針と合う |

## 影響

- **良い影響**: 原因調査・設計比較・レビューの手順が揃い、「実行して確かめる」が徹底される（footguns の多くと同じ方向）
- **コスト**: 常時約4,300トークン／セッション。`arena`・`architect`・`interrogate` は複数モデル（opus / fable / sonnet）のサブエージェントを並べるため、1回あたりの費用が大きい。既定では使わず、必要なときに監査人へ断ってから使う
- **使えないスキル**: `babysit`・`fix-ci`・`make-pr-easy-to-review` と、`poteto-mode` の PR 関連手順は `gh` CLI を前提とするが、この環境には `gh` が無い（GitHub の操作は GitHub MCP で行う）
- **進め方の衝突**: pstack の「人を待たない」原則と、憲章の「承認なしに次へ進まない」が衝突しうる。CLAUDE.md の優先順位で解決する（F-29）
- **供給元のリスク**: 起動時フックは外部リポジトリの文章を毎セッション注入する。タグ固定で、意図しない更新を防ぐ（F-30）
- **無効にする方法**: Setup script の2行を消す。起動時フックだけ止める場合は `~/.claude/pstack-models.md` に `session hook: off` と書く（クラウドでは Setup script で書く）
