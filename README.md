# 🤖 Multi-Agent Debate Demo

マルチエージェント議論システムのプロトタイプ - 数学問題を複数のAIエージェントが協力して解決するリアルタイム可視化システム

## 📋 概要

このプロジェクトは、[AutoGen](https://github.com/microsoft/autogen)フレームワークを使用して実装されたMulti-Agent Debateシステムのプロトタイプです。複数のAIエージェントが数学問題について議論し、最終的に合意に達するプロセスをWebブラウザでリアルタイムに可視化できます。

### 🎯 主な機能

- **マルチエージェント議論**: 4つのAIエージェント（Agent A, B, C, D）が数学問題について議論
- **リアルタイム可視化**: WebSocketを使用した議論プロセスのリアルタイム表示
- **ラウンドベース議論**: 各ラウンドでエージェントが他のエージェントの回答を参考に自身の回答を改善
- **多数決による最終決定**: 全エージェントの最終回答から多数決で最終答案を決定
- **直感的なWebUI**: 日本語対応のユーザーフレンドリーなインターフェース

## 🏗️ システム構成

### アーキテクチャ

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │◄──►│   FastAPI Server │◄──►│  AutoGen Agents │
│                 │    │                  │    │                 │
│ - HTML/CSS/JS   │    │ - WebSocket      │    │ - MathSolver    │
│ - Real-time UI  │    │ - REST API       │    │ - Aggregator    │
│ - Visualization │    │ - Event Handling │    │ - OpenAI LLM    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### エージェント構成

```
Agent A ◄──► Agent B
   ▲             ▲
   │             │
   ▼             ▼
Agent D ◄──► Agent C
```

各エージェントは隣接する2つのエージェントと情報を交換し、スパースコミュニケーション構造を形成します。

## 🚀 セットアップ手順

### 1. 必要な環境

- Python 3.8以上
- OpenAI APIキー

### 2. インストール

```bash
# リポジトリのクローン
git clone https://github.com/ToshiEna/demo9.git
cd demo9

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

```bash
# .envファイルを作成
cp .env.example .env

# .envファイルを編集してOpenAI APIキーを設定
# OPENAI_API_KEY=your_actual_api_key_here
```

### 4. アプリケーションの起動

```bash
# サーバーの起動
python main.py
```

アプリケーションは `http://localhost:8000` で利用可能になります。

## 📖 使用方法

### 1. 問題の入力
- Webブラウザで `http://localhost:8000` にアクセス
- テキストエリアに数学問題を入力（日本語・英語対応）
- 「🚀 議論開始」ボタンをクリック

### 2. 議論の観察
- 各エージェントの応答がリアルタイムで表示されます
- ラウンド進行状況を視覚的に確認できます
- 議論ログで詳細な進行状況を追跡できます

### 3. 結果の確認
- 議論終了後、最終回答が表示されます
- 各エージェントの思考プロセスを確認できます

### サンプル問題

```
太郎くんは4月に友達48人にクリップを売りました。
5月には4月の半分の数のクリップを売りました。
太郎くんは4月と5月で合計何個のクリップを売ったでしょうか？
```

## 🔧 技術仕様

### バックエンド技術
- **AutoGen Core**: マルチエージェントフレームワーク
- **FastAPI**: WebAPIフレームワーク
- **WebSocket**: リアルタイム通信
- **OpenAI GPT-4o-mini**: 言語モデル

### フロントエンド技術
- **HTML5/CSS3**: ユーザーインターフェース
- **JavaScript**: インタラクティブ機能
- **WebSocket Client**: リアルタイム通信

### 主要ライブラリ
```
autogen-core>=0.4.0          # マルチエージェントフレームワーク
autogen-ext[openai]>=0.4.0   # OpenAI統合
fastapi>=0.104.0             # WebAPIフレームワーク
uvicorn[standard]>=0.24.0    # ASGIサーバー
websockets>=11.0             # WebSocket通信
openai>=1.3.0                # OpenAI API
```

## 📁 プロジェクト構成

```
demo9/
├── main.py                          # メインアプリケーション
├── requirements.txt                 # 依存関係
├── .env.example                     # 環境変数テンプレート
├── .gitignore                       # Git除外設定
├── README.md                        # このファイル
├── src/
│   └── multi_agent_debate/
│       ├── __init__.py              # パッケージ初期化
│       ├── core.py                  # コアエージェント実装
│       └── manager.py               # 議論管理システム
├── templates/
│   └── index.html                   # メインWebページ
└── static/
    ├── style.css                    # スタイルシート
    └── script.js                    # JavaScriptファイル
```

## 🎮 議論プロセス

### 1. 議論開始
- ユーザーが数学問題を入力
- アグリゲーターエージェントが問題を全ソルバーエージェントに配信

### 2. 初期回答（ラウンド0）
- 各エージェントが独立して問題を解決
- 初期回答を隣接エージェントと共有

### 3. 議論ラウンド（ラウンド1-2）
- 各エージェントが他のエージェントの回答を参考に自身の回答を改善
- 改良された回答を隣接エージェントと共有

### 4. 最終回答（ラウンド3）
- 各エージェントが最終回答を提出
- アグリゲーターが多数決により最終答案を決定

## 🛠️ カスタマイズ

### エージェント数の変更
```python
# main.pyまたはmanager.pyで設定
manager = DebateManager(
    openai_api_key=openai_api_key,
    num_solvers=4,  # エージェント数を変更
    max_rounds=3    # ラウンド数を変更
)
```

### モデルの変更
```python
# OpenAIモデルを変更
manager = DebateManager(
    openai_api_key=openai_api_key,
    model_name="gpt-4"  # より高性能なモデルに変更
)
```

## 🐛 トラブルシューティング

### よくある問題

1. **OpenAI APIエラー**
   - `.env`ファイルでAPIキーが正しく設定されているか確認
   - APIキーの使用量制限を確認

2. **WebSocket接続エラー**
   - ブラウザのコンソールでエラーメッセージを確認
   - ファイアウォール設定を確認

3. **依存関係エラー**
   - Python版本を確認（3.8以上が必要）
   - `pip install -r requirements.txt`を再実行

## 📚 参考資料

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Multi-Agent Debate Paper](https://arxiv.org/abs/2406.11776)

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🤝 貢献

プルリクエストや課題報告を歓迎します。大きな変更を行う前に、まず課題を開いて変更内容について議論してください。

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesで報告してください。