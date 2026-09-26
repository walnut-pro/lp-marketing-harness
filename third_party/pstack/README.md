# pstack（取り込み元とライセンス）

- 取り込み元: [michael-denyer/pstack-claude](https://github.com/michael-denyer/pstack-claude) `v0.9.45`（commit `c02fd4922b25ee005f42042463d741d236c2c35e`）
- 原本: Lauren Tan（poteto）の [pstack](https://github.com/cursor/plugins/tree/main/pstack)。一部スキルは Cursor の cursor-team-kit 由来
- ライセンス: MIT（[LICENSE](LICENSE)、[LICENSE-cursor-team-kit](LICENSE-cursor-team-kit)、[NOTICE.md](NOTICE.md)、[NOTICE-skills.md](NOTICE-skills.md)）
- 経緯: [ADR-0003](../../docs/decisions/0003-adopt-pstack.md)

## 取り込んだもの

| 取り込み先 | 元 | 内容 |
|---|---|---|
| `.claude/skills/` | `plugins/pstack/skills/` | スキル54（全部。上流が「原則の参照を含め、全ディレクトリを残す」と案内しているため） |
| `.claude/agents/` | `plugins/pstack/agents/`・`effort-agents/` | サブエージェント12 |

取り込まなかったもの: プラグインの起動時フック（その内容は CLAUDE.md の「進め方」に日本語で書いた）、Codex 用の設定、上流のテストと保守用ツール。

## 上流からの変更

プラグインではなくプロジェクトのエージェントとして置くため、エージェント名の接頭辞 `pstack:` を外した（`pstack:poteto-agent` → `poteto-agent` など）。あわせて、`poteto-mode/SKILL.md` の「プラグインのエージェントは名前空間付きで登録される」という1文を、プロジェクトのエージェントの説明に置き換えた。変更はこの2種類だけで、`scripts/vendor_pstack.py` が機械的に行う。

## 更新のしかた

1. `scripts/vendor_pstack.py` の `UPSTREAM_TAG` と `UPSTREAM_COMMIT` を新しい版に変える
2. 上流をその commit でクローンし、`python3 scripts/vendor_pstack.py <クローン>` を実行する
3. `./scripts/check.sh` が通ることを確かめ、差分を PR にする

`manifest.sha256` には取り込んだ全ファイルのハッシュが入っている。`check.sh` が手による変更を検出する。
