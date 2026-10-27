# 文書とソフトウェア作業のための Agent スキル

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

翻訳、文書組版、学習資料、ソフトウェア品質、スキル改善を支える八つのスキルです。

## 翻訳と文書

- [bilingual-translation](skills/bilingual-translation/README.ja.md): 原文全体を読み、制限内の意味単位群を保存して、一つの対訳原稿を独立した工程でレビューします。
- [bilingual-html](skills/bilingual-html/README.ja.md): 対応する文章から、論理的な読み順、RTL、表、共有画像を備えたレスポンシブ HTML を生成します。
- [bilingual-pdf](skills/bilingual-pdf/README.ja.md): 対応する文章から、左右対照の二言語記事・レポート・配布資料を作成します。
- [study-notes](skills/study-notes/README.ja.md): 学習資料から解説ノート、クイックリファレンス、キーワード索引、決定木を作成します。
- [reader-doc-review](skills/reader-doc-review/README.ja.md): 新しいコンテキストの読者によるタスク試読と修正の反復で、実際の読者に向けて一つの文書をレビュー・改訂します。
## ソフトウェアとスキルの品質

- [testing-workflow](skills/testing-workflow/README.ja.md): ソフトウェアの変更に対し、コストとリスクを考慮した自動テストとベンチマークを設計・実行します。
- [write-if-statements](skills/write-if-statements/README.ja.md)：読みやすい if 文の作成・レビューと、動作を保った条件分岐のリファクタリング。
- [skill-optimization](skills/skill-optimization/README.ja.md): 新しいコンテキストでの実践的な試行と的を絞った修正でスキルを改善。

## インストール

[Skills CLI](https://github.com/vercel-labs/skills) または互換インストーラーを使います。

```sh
npx skills add samuelncui/skills --skill bilingual-translation
npx skills add samuelncui/skills --skill bilingual-html
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill reader-doc-review
npx skills add samuelncui/skills --skill testing-workflow
npx skills add samuelncui/skills --skill write-if-statements
npx skills add samuelncui/skills --skill skill-optimization
```

必要なスキルのディレクトリ全体をインストールします。既存の対訳には bilingual-pdf または bilingual-html だけで十分です。reader-doc-review は任意の補助スクリプトにのみ Python 3 を使います。原文の翻訳には bilingual-translation が必要です。PDF はレビュー済み JSONL を直接受け取り、HTML は独自の組版 JSON または意味情報の交換形式インポーターを使います。study-notes は bilingual-pdf に依存します。品質関連の三つのガイド自体にランタイム依存はなく、対象プロジェクトのツールを使います。依存先はホストで検出し、自動インストールしません。設定と例は各ガイドを参照してください。

## リポジトリの規約

各スキルが自身の実装とドキュメントを管理します。利用者向けガイドはスキルの README、エージェント向けの手順は SKILL.md に置きます。共有実装の管理元は一つとし、依存先は隣接ディレクトリを仮定せず、ホストからインストール先を確認します。利用側のプロジェクトではテスト済みのリビジョンを固定してください。

再現可能なリポジトリのチェックと、過去の結果と現在の結果の区別は[検証ガイド](tests/README.md)を参照してください。選定したサンプルは所属するスキル内に置きます。非公開の内容をこの公開リポジトリに含めず、外部処理や公開には必要な許可を得てください。

オリジナルのコードとサンプル内容は [MIT ライセンス](LICENSE)です。依存関係には[それぞれのライセンス](THIRD_PARTY_NOTICES.md)が適用されます。
