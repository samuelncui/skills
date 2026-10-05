# 二言語 PDF・学習ノート・テストのための Agent スキル

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

二言語文書、学習資料、コストを考慮したソフトウェア検証のためのスキルです。

- [bilingual-pdf](skills/bilingual-pdf/README.ja.md): 対応する文章から、左右対照の二言語記事・レポート・配布資料を作成します。
- [study-notes](skills/study-notes/README.ja.md): 学習資料から解説ノート、クイックリファレンス、キーワード索引、決定木を作成します。
- [testing-workflow](skills/testing-workflow/SKILL.md): ソフトウェアの変更に対し、コストとリスクを考慮した自動テストとベンチマークを設計・実行します。

## インストール

[Skills CLI](https://github.com/vercel-labs/skills) または互換インストーラーを使います。

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
```

上記のコマンド、またはホストが対応する方法で、必要なスキルのディレクトリ一式をインストールしてください。`study-notes` には `bilingual-pdf` も必要です。`testing-workflow` は独立して使えます。設定、使い方、サンプルは上記リンク先の各スキルのガイドを参照してください。

## リポジトリの規約

各スキルが自身の実装とドキュメントを管理します。利用者向けガイドはスキルの README、エージェント向けの手順は SKILL.md に置きます。共有実装の管理元は一つとし、依存先は隣接ディレクトリを仮定せず、ホストからインストール先を確認します。利用側のプロジェクトではテスト済みのリビジョンを固定してください。

再現可能なリポジトリのチェックと、過去の結果と現在の結果の区別は[検証ガイド](tests/README.md)を参照してください。選定したサンプルは所属するスキル内に置きます。非公開の内容をこの公開リポジトリに含めず、外部処理や公開には必要な許可を得てください。

オリジナルのコードとサンプル内容は [MIT ライセンス](LICENSE)です。依存関係には[それぞれのライセンス](THIRD_PARTY_NOTICES.md)が適用されます。
