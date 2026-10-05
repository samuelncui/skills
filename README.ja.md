# 二言語 PDF・学習ノート・テストのための Agent スキル

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

二言語文書、学習資料、コストを考慮したソフトウェア検証のためのスキルです。

- [bilingual-pdf](skills/bilingual-pdf/README.ja.md)：物理的に固定された左右の列で、段落の開始位置、表の行、リスト項目を揃えます。長い段落はページをまたぐかどうかを選択でき、その次の組は再び揃います。ネイティブ LaTeX と JSON は同じレンダラーを使い、LTR、RTL、CJK の言語プロファイルに対応します。
- [study-notes](skills/study-notes/README.ja.md)：解説ノート、統合クイックリファレンス、キーワード索引、決定木を作成します。1 つだけでも、複数を組み合わせても使えます。ネイティブ LaTeX のレコードは、インストール済みの二言語レンダラーを再利用します。
- [testing-workflow](skills/testing-workflow/SKILL.md)：プロジェクト既存のテストランナーで自動テストとベンチマークを設計・保守します。チェックをまとめて実行し、リスクとコストに見合う検証範囲を選びます。

[![二言語の使い方ガイド](skills/bilingual-pdf/examples/en-zh-Hans/preview.png)](skills/bilingual-pdf/examples/en-zh-Hans/output.pdf)

サンプルはスキル自体の使い方を説明しながら、出力を実演します。ソース、PDF、プレビューは同じ場所に置かれています。利用者向けガイド、ネイティブ API リファレンス、設定ドキュメント、JSON Schema は、それぞれ独立した読みやすいテキストとして提供します。

## タスクから選ぶ

- 対応する二言語の文章から、左右対照の記事・レポート・配布資料を作るなら `bilingual-pdf`：[最小 LaTeX とビルドコマンド](skills/bilingual-pdf/references/latex.md#project-and-build-contract)、または[最小 JSON・事前検査・レンダリング](skills/bilingual-pdf/references/input.md#minimal-input)。どちらも編集可能なソースを出力します。先に[フォントと言語の要件](skills/bilingual-pdf/references/languages.md)を確認してください。
- 学習資料から解説や検索しやすい参考資料を作るなら [study-notes](skills/study-notes/README.ja.md)。描画用の依存スキルも明示的にインストールします。
- ソフトウェアのテスト計画・回帰テスト・ベンチマークなら [testing-workflow](skills/testing-workflow/SKILL.md)。

PDF の経路は提供済みの対訳を組版します。OCR、既存 PDF の内容抽出、自動翻訳、元の PDF のページレイアウト維持は対象外です。

## インストール

[Skills CLI](https://github.com/vercel-labs/skills) または互換インストーラーを使います。

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
```

通常の対訳文書には `bilingual-pdf` だけで十分です。`study-notes` はこのスキルを必要とします。必要なスキルのディレクトリ一式を、ホストが対応する場所へコピーしても構いません。 `testing-workflow` は独立して使え、どちらの PDF スキルも必要としません。

ホストを通じて `bilingual-pdf` の実際のインストール先を調べ、学習文書のビルド時に `BILINGUAL_PDF_SKILL` として指定します。両スキルが隣接してインストールされているとは想定せず、依存関係を自動ダウンロードすることもありません。TeX、フォント、任意の Python 品質チェック用依存関係は、各ガイドを参照してください。

## 実装を一元化し、役割を明確にする

`bilingual-pdf` は `paralleltext.sty`、構造化入力、レイアウト、レンダリングチェックを管理します。`study-notes` は小さなネイティブのレコード・ナビゲーション層と学習資料の執筆手順を追加し、別のレンダラーは持ちません。利用側の文書プロジェクトでは、テスト済みのリビジョンを固定し、独自の内容と設定を分けて管理してください。

呼び出し元のエージェントが内容と意味上の対応付けを用意し、レイアウトツールが配置を制御します。ネイティブ TeX はコードを実行できます。shell escape を無効にしても、ファイルシステムのサンドボックスにはなりません。公開、外部処理、原資料の利用権は、それぞれ別に許可を確認する必要があります。

再現可能なテストと、過去の結果と現在の結果の区別については、[検証ガイド](tests/README.md)を参照してください。選定したサンプル PDF はソースとともにバージョン管理します。Actions はリポジトリのチェックに使い、サンプルの配布経路にはしません。

オリジナルのコードとサンプル内容は [MIT ライセンス](LICENSE)です。依存関係には[それぞれのライセンス](THIRD_PARTY_NOTICES.md)が適用されます。すべての言語、プリンター、アクセシビリティ要件への適合を認証するものではありません。
