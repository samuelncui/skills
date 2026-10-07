# Bilingual HTML

対訳がそろったテキストから、オフラインで閲覧できる持ち運び可能な HTML ページを生成します。各文章の二つの言語を一組に保ち、デスクトップでは横並び、モバイルでは原文、訳文の順に表示します。表、リスト、共有画像、対訳キャプションの意味的な構造を維持します。

Python 3.11 以降が必要です。対訳済みの入力には、外部の Python パッケージや翻訳スキルは不要です。

```sh
python3 scripts/bilingual_html.py render examples/tutorial/layout.json --output page
```

このスキルのディレクトリで実行してください。出力先は未作成のディレクトリを選び、親ディレクトリは先に用意します。`page/index.html` を開き、成果物はディレクトリ全体で渡してください。

- [完全なチュートリアル入力](examples/tutorial/layout.json)と[生成済みページ](examples/tutorial/site/index.html)
- [形式、スタイル、フォント、画像、確認方法](references/rendering.md)
- [レンダリング用スキーマ](schemas/layout.schema.json)
- [エージェント向け手順](SKILL.md)

バージョン 1 はプレーンテキストとローカルの PNG/JPEG を扱い、HTML、Markdown、TeX を解釈しません。フォントは言語ごとに設定できますが、実際の字形を確認してください。フォント名だけでは文字の対応範囲を保証できません。構造テストとは別に、翻訳、表示、アクセシビリティを確認する必要があります。

原文から翻訳する場合は、別途インストールした `bilingual-translation` をホストのスキル検索で見つけてください。明示的な `--translation-skill` パスを指定すると、確認済みの v1 対訳を取り込めます。依存スキルは自動インストールされません。[取り込みとバージョンの固定](references/rendering.md#optional-translation-import)。

コード、文書、オリジナルのサンプル素材は [MIT ライセンス](LICENSE)で提供します。
