# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

原文を保持した一つの対訳マスターを作ります。エージェントは原文全体を読み、意味に基づく分割位置を選び、制限内のグループを保存した後、すべての原文・訳文を別工程で照合します。

スキルのディレクトリ全体をインストールします。JSONL ヘルパーには Python 3.11+ と POSIX ファイルロックが必要です。外部パッケージやネットワークサービスは不要です。Markdown インポーターで表現できない内容には、ネイティブ対訳 TeX も同等に使えます。

依頼例：「bilingual-translation でこのガイドをフランス語に訳し、段落と表のセルを一つのレビュー済み原稿に保持してください。」原文、対象言語、読者、用語を指定します。

エージェントの入口は scripts/workflow.py です。prepare で原文を読み初期化し、translate は原文合計 2048 コードポイント以内の単位群を渡し、review は独立した全体照合を記録します。保存・承認は次のグループを返します。短い参照がハッシュの手入力に代わり、改訂・ハッシュ・再試行の検証はツール内部で維持されます。修正後は該当する対訳だけを再確認します。

[エージェント手順](SKILL.md) · [コマンドと制約](references/workflow-v2.md)

レビュー済み JSONL は別途検出した bilingual-pdf に直接渡せます。HTML は独自の組版 JSON または旧 v1 インポートを使い、JSONL を直接読みません。既存の対訳を翻訳し直す必要はありません。

## 旧 v1 との互換性

元の [v1 契約](references/contract-v1.md)、[英仏の実例](references/example-guide.md)、translation_contract.py API は維持されます。これらはゲート付き JSONL 手順とは別です。利用先が v1 JSON を必要とする場合だけ workflow.py export を使い、JSONL をマスターとして保持します。

自動検証は構造とレビュー記録の有効性を確認します。意味はエージェントが確認し、PDF の見た目は実際の描画ページで別途確認します。

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
