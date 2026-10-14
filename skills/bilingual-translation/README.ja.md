# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

原文を保持した一つの対訳マスターを作ります。既定では現在のメインエージェントが全文を読み、意味に基づく分割位置を選び、制限内のグループを保存してから全対訳を照合します。独立したレビューとは、同じエージェントによる別の読み直し工程です。

進捗は約5%ごとに各段階の実際の完了数・総数・割合を報告し、完了や修正による校閲進捗の後退も明示します。

サブエージェントは文脈を失い、用語・文体・細部が不統一になる場合があります。委任にはこのリスクの説明と、具体的な範囲への明示的な許可が必要です。急ぎというだけでは許可になりません。今回の依頼で明示的に許可済みの委任を再確認する必要はありません。

スキルのディレクトリ全体をインストールします。JSONL ヘルパーには Python 3.11+ と POSIX ファイルロックが必要です。外部パッケージやネットワークサービスは不要です。Markdown インポーターで表現できない内容には、ネイティブ対訳 TeX も同等に使えます。

依頼例：「bilingual-translation でこのガイドをフランス語に訳し、段落と表のセルを一つのレビュー済み原稿に保持してください。」原文、対象言語、読者、用語を指定します。

エージェントの入口は scripts/workflow.py です。prepare で原文を読み初期化し、translate は原文合計 2048 コードポイント以内の単位群を渡し、review は別の段階で全体を照合します。保存・承認は次のグループを返します。ツールが返した参照値を変更せず返してください。修正後は該当する対訳だけを再確認します。

[エージェント手順](SKILL.md) · [コマンドと制約](references/workflow.md)

レビュー済み JSONL は別途検出した bilingual-pdf に直接渡せます。HTML は独自の組版 JSON または意味構造の交換形式のインポートを使い、JSONL を直接読みません。既存の対訳を翻訳し直す必要はありません。

## 意味構造の交換形式

[意味構造の交換形式](references/semantic-exchange.md)と[英仏の実例](references/example-guide.md)は描画側への受け渡しを説明します。利用先が交換用 JSON を必要とする場合は workflow.py export を使い、JSONL をマスターとして保持します。利用側は translation_contract.py の読み取り専用 validate_document API で交換文書を検証します。

自動検証は構造とレビュー記録の有効性を確認します。意味はエージェントが確認し、PDF の見た目は実際の描画ページで別途確認します。

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
