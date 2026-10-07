# 対訳の作成

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

原文と訳文を対応付けた一つの原稿を作成します。まず対象の原文全体を読み、段落や意味上の単位ごとに翻訳・確認し、同じ原稿に保存してから次へ進みます。固定 ID で対応関係を保ち、原文を変更した場合は訳文を再確認します。

ホストのスキルインストーラーでディレクトリ全体をインストールしてください。対訳を直接記述する TeX も同等の選択肢です。プレーンテキストの JSON と Python 3.11+ 標準ライブラリの検証ツールは任意で、PDF・HTML レンダラーから独立しています。

依頼例：「bilingual-translation を使って、このガイドをフランス語に訳し、各段落と表の各セルを一つの対訳原稿に残して。」原文、対象言語、読者や用語の条件を指定してください。既存の対訳はレンダラーに直接渡せます。

[ワークフロー](SKILL.md)、[任意の形式仕様](references/contract-v1.md)、[完全なオリジナル英仏例](references/example-guide.md)を参照してください。例には原文、表、共通の図を含みます。スキルのディレクトリから実行します：

```sh
python3 -B scripts/translation_contract.py validate examples/guide/translation.json --ready
```

このコマンドは構造、原文ハッシュ、記録された確認状態を検証します。意味の正確さは原文と訳文を読んで確認する必要があります。

[設計の参考資料](references/design-provenance.md) · [MIT ライセンス](LICENSE)
