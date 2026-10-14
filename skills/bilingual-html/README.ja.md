# Bilingual HTML

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

対訳がそろったテキストを、オフラインで閲覧できる持ち運び可能な文書にします。各文章の二つの言語を一組に保ち、デスクトップでは二段組み、狭い画面では原文、訳文の順に表示します。ブラウザーで対照しながら読む記事、説明書、配布資料に適しています。

対応するテキストは呼び出し元が用意します。このスキルは文言を保持して配置します。原文の抽出、翻訳、文章同士の対応関係の判断は、呼び出し元のワークフローが担当します。

## 主な機能

- 対になる見出し、段落、リスト項目の開始位置を揃える
- 実際の表の行とセルを使い、各セルに両言語を配置する。幅広い表はキーボードで横スクロールできる
- 図ごとに共通の画像を一枚表示し、対訳キャプションと代替説明を付ける
- 各言語の LTR/RTL 方向と、デスクトップの物理的な列順を分けて設定する
- 幅、間隔、色、言語別のフォントを設定する
- JavaScript、リモートフォント、実行用サーバーなしで HTML、CSS、ローカル素材を出力する

## 完全なサンプルとプレビュー

オリジナルの英語／フランス語チュートリアルは、このスキルの使い方を題材に、見出し、本文、番号付き／番号なしリスト、表、図を示します。

- [編集可能なレイアウト JSON](examples/tutorial/layout.json)
- [生成済み HTML 全体](examples/tutorial/site/index.html)。閲覧するには `site/` ディレクトリ全体をダウンロードします
- [オリジナルの図](examples/tutorial/images/pairs.png)と[サンプルのマニフェスト](examples/MANIFEST.json)

このスキルのインストール先で実行します。

```sh
set -eu
python3 --version
python3 scripts/bilingual_html.py render examples/tutorial/layout.json --output page
```

Python 3.11 以降が必要です。出力先 `page` は未作成で、その親ディレクトリは存在している必要があります。ブラウザーで `page/index.html` を直接開きます。閲覧用サーバーやビルドツールは不要です。リポジトリのウェブサイトでは、ページではなく HTML ソースが表示される場合があります。

## 構造化 JSON：用意済みの対訳

[そのまま実行できる最小例](references/rendering.md#minimal-structured-example)、[フィールドの仕様](references/rendering.md#embedded-pair-layout)、[JSON Schema](schemas/layout.schema.json)に従い、対訳を埋め込んだレイアウトを作成します。元のサンプルを残して完全なチュートリアルを編集するには、次のようにコピーします。

```sh
set -eu
mkdir html-work
cp examples/tutorial/layout.json html-work/layout.json
cp -R examples/tutorial/images html-work/images
python3 scripts/bilingual_html.py render html-work/layout.json --output html-work/page
```

コピーした `layout.json` を編集し、見出し、段落、リスト項目、表のセル、キャプション、代替テキストの各ペアに一意の ID を付けます。原文／訳文の役割を変えず、言語タグと方向を明示します。画像パスは JSON ファイルのあるディレクトリを基準にします。

`render` は文書と素材を検査してから、`index.html`、`style.css`、`LICENSE`、必要な画像を書き出します。入力は変更しません。更新時は `html-work/page-v2` など別の新しいディレクトリへ出力します。増分 `build` や独立した `preflight` コマンドはありません。[CLI と出力の仕様](references/rendering.md#commands-and-output-lifecycle)を参照してください。

## ネイティブ HTML：信頼できる内容の手動編集

生成ページは通常の編集可能な HTML です。Python なしで完全なサンプルから始められます。

```sh
set -eu
test ! -e native-page && cp -R examples/tutorial/site native-page
```

`native-page/index.html` と `native-page/style.css` を編集し、ページを開き直します。[最小ネイティブページと DOM の規則](references/rendering.md#native-html-authoring)では、一つの `.pair` コンテナー内に、言語タグ付きの原文と訳文を保つ方法を示します。このスキルのスタイルシート、実際の表構造、両言語の図の説明を再利用してください。

この経路では HTML/CSS を手動でレビューします。JSON レンダラーは HTML の取り込みや手動編集の検証を行わず、リッチなマークアップを JSON に往復変換できません。JSON または編集後のネイティブページのどちらかを編集元にします。追加するマークアップ、リンク、素材、動作は別途確認してください。信頼できない HTML はコード実行やネットワークアクセスを伴う可能性があります。

## 翻訳からレイアウトへ

原文から翻訳する場合は、ホストで別途インストール済みの `bilingual-translation` を検出し、その翻訳・レビューワークフローに従います。確認したインストール先を `TRANSLATION_SKILL` に設定します。最新の翻訳がレビュー済みの `master.jsonl` に対して実行します。

```sh
set -eu
python3 "$TRANSLATION_SKILL/scripts/workflow.py" export master.jsonl --output reviewed.json
python3 scripts/bilingual_html.py import-pairs reviewed.json \
  --translation-skill "$TRANSLATION_SKILL" --output imported
python3 scripts/bilingual_html.py render imported/layout.json --output translated-page
```

入力パスはプロジェクトに合わせ、出力には未作成の場所を使います。最初のコマンドは翻訳交換形式 を出力し、次のコマンドはそれを HTML 独自のレイアウト形式 に変換します。HTML は JSONL を直接読みません。レビュー済みの交換形式 JSON があれば `import-pairs` から開始できます。

取り込みでは指定した翻訳スキルの検証器を呼び出し、未完成・古い訳文を拒否し、文字列、ID、順序を保持します。出力は `layout.json`、コピーされた対応画像、`import-record.json` です。翻訳履歴のために JSONL 原稿と交換ファイルを保管します。レイアウト JSON は表示用の派生物です。エクスポート時に分割チャンクは親のペアに再結合されるため、HTML は子チャンク単位の整列やレビュー記録を保持しません。[素材の準備、バージョン／ハッシュ固定、受け渡しの制限](references/rendering.md#optional-translation-import)を参照してください。用意済みのレイアウト対訳には翻訳スキルは不要で、不足する依存関係を自動インストールしません。

## 設定と確認

既定値は追加設定なしで使えます。任意の `config` には `browser_title`、`desktop_order`、必要な項目だけを指定する `styles` を設定できます。

```json
{"desktop_order":"target-first","styles":{"column_gap":"2rem","source_weight":1,"target_weight":1.25,"source_font":["Noto Sans","sans-serif"],"target_font":["Noto Naskh Arabic","serif"]}}
```

このオブジェクトを `config` に置き、宣言した言語に合わせてフォントを選びます。[全項目、単位、既定値](references/rendering.md#styling)は一つのリファレンスにまとめています。列順はデスクトップの CSS 表示だけを変えます。DOM とモバイル表示は原文、訳文の順のままで、切り替え幅は 48rem です。フォントは閲覧端末に必要です。このスキルはダウンロードや同梱をしません。

納品前に[チェックリスト](references/rendering.md#review-boundaries)を実施します。

1. 提供された資料と照合して両言語を読み、内容の網羅性と意味を確認する。
2. 実際のページをオフラインで開き、デスクトップ幅と狭い幅、反転した列順、該当する RTL/CJK テキストを確認する。字形、文字の連結処理、折り返し、長いセル、数字、ブラウザーのズームを調べる。
3. キーボードで幅広い表にフォーカスしてスクロールする。画像、キャプション、両言語の代替説明、想定読者に必要なコントラストと支援技術での動作を確認する。
4. 構造検査、言語レビュー、表示／アクセシビリティのレビューを分け、失敗と未実施項目も報告する。生成成功だけでは翻訳承認やアクセシビリティ認証にはならない。

## 独立インストール、依存関係、納品

ホストのスキルインストール手順で `bilingual-html` ディレクトリ全体を入れ、`SKILL.md`、スクリプト、素材、スキーマ、リファレンス、サンプル、`LICENSE` を保持します。リポジトリのチェックアウト、保守用ツール、`bilingual-pdf`、`bilingual-translation` は不要です。インストール先以外で実行する場合は検出済みスクリプトのパスを使い、インストール先が読み取り専用なら書き込み可能なプロジェクトディレクトリで作業します。

生成と取り込みは Python 3.11+ の標準ライブラリで動作します。既存のネイティブ一式の閲覧・編集には、ブラウザー／テキストエディターと適切なローカルフォントだけが必要です。翻訳の取り込みだけは、明示的に検出した互換性のある翻訳スキルを追加で使います。

相対パスを保持した出力ディレクトリ全体と、必要に応じて編集可能な JSON／ネイティブソースを渡します。取り込み記録と翻訳原稿も使用したプロジェクト内に保管します。CSS や画像に依存する `index.html` だけを渡さないでください。

## 制限と安全性

レイアウト は Unicode のプレーンテキストとローカル PNG/JPEG を扱います。HTML、Markdown、TeX は文字どおりに表示し、JSON にリッチテキスト、数式、リンク、スクリプト用の構文はありません。OCR、翻訳、既存ページのレイアウト抽出は対象外です。印刷 CSS はブラウザー印刷の簡単な補助であり、PDF の厳密な改ページ処理ではありません。

画像のパス、サイズ、構造には制限があり、リモート URL、ディレクトリトラバーサル、シンボリックリンク、SVG 入力は拒否されます。[素材の制約](references/rendering.md#assets-and-output)と[信頼できる SVG からの忠実なラスター変換](references/rendering.md#faithful-derivatives-of-trusted-svg-originals)を参照してください。ヘッダー検査は画像全体のデコードではありません。実際のブラウザー表示を確認し、少数の言語サンプルから全言語への対応やアクセシビリティ適合を断定しないでください。

[エージェント向け手順](SKILL.md)に簡潔な流れをまとめています。コード、文書、オリジナルの素材は [MIT ライセンス](LICENSE)です。追加素材のライセンスを保持し、公開サンプルに非公開情報を入れないでください。
