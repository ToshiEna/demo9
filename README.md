# 🤖 Multi-Agent Collaborative Reasoning Demo

マルチエージェント協調推論システム - 専門家AIエージェントが順次連携して数学問題を解決するリアルタイム可視化システム

## 📋 概要

このプロジェクトは、[AutoGen](https://github.com/microsoft/autogen)フレームワークを使用して実装されたMulti-Agent Collaborative Reasoningシステムです。4つの専門AIエージェントが順次連携して数学問題を分析・解決し、その過程をWebブラウザでリアルタイムに可視化できます。

### 🎯 主な機能

- **専門家協調推論**: 4つの専門AIエージェントによる順次連携ワークフロー
- **インテリジェント問題分析**: Expert Recruiterが問題を分析し適切な専門家を選択
- **並行専門家処理**: 複数の専門家が必要に応じて並行して問題解決
- **解答検証システム**: Evaluatorによる解答と解法の厳密な検証
- **リアルタイム可視化**: WebSocketを使用したワークフロープロセスのリアルタイム表示
- **直感的なWebUI**: 専門家の役割と連携を視覚化する日本語対応インターフェース

## 🏗️ システム構成

### 新しいワークフローアーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sequential Expert Workflow                  │
└─────────────────────────────────────────────────────────────────┘

1️⃣ Problem Analysis & Expert Assignment
   ┌─────────────────┐    🔍 Analyzes problem
   │ Expert Recruiter│────➤ Identifies required expertise  
   │   (採用担当者)   │    🌐 Uses internet search
   └─────────────────┘    ⬇️ Assigns appropriate expert(s)

2️⃣ Parallel Expert Problem Solving
   ┌─────────────────┐    📐 Geometry problems
   │ Geometry Expert │────➤ Spatial reasoning
   │   (幾何学専門家) │    📏 Area, perimeter, shapes
   └─────────────────┘
            ⬇️
   ┌─────────────────┐    🔢 Algebra problems  
   │ Algebra Expert  │────➤ Equations, variables
   │   (代数学専門家) │    📊 Mathematical relationships
   └─────────────────┘
            ⬇️
3️⃣ Solution Validation & Final Answer
   ┌─────────────────┐    ✅ Validates solutions
   │   Evaluator     │────➤ Checks accuracy & reasoning
   │    (評価者)     │    🎯 Provides final verified answer
   └─────────────────┘
```

### エージェント役割

#### 🎯 Expert Recruiter (専門家採用担当者)
- **役割**: 問題分析と専門家割り当て
- **機能**: 
  - 数学問題の領域分析（幾何学、代数学、算術等）
  - インターネット検索による問題分類支援
  - 適切な専門家の選択（GeometryExpert、AlgebraExpert、または両方）
- **出力**: 専門家割り当てと選択理由

#### 📐 Geometry Expert (幾何学専門家)
- **役割**: 幾何学問題の専門解決
- **専門分野**: 
  - 図形の面積・周囲・体積計算
  - 空間認識と座標幾何学
  - 角度と三角法
- **出力**: 幾何学的アプローチによる解答

#### 🔢 Algebra Expert (代数学専門家)
- **役割**: 代数学問題の専門解決
- **専門分野**:
  - 方程式と連立方程式
  - 変数と数学的関係性
  - パターン認識と代数操作
- **出力**: 代数的アプローチによる解答

#### ✅ Evaluator (評価者)
- **役割**: 解答検証と最終判定
- **検証項目**:
  - 数学的正確性の確認
  - 論理的推論の妥当性
  - 解法の完全性
  - 複数解答の一致性確認
- **出力**: 検証済み最終回答

## 🚀 セットアップ手順

### 1. 必要な環境

- Python 3.8以上
- Azure OpenAI APIキー

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

# .envファイルを編集してAzure OpenAI APIキーを設定
# AZURE_OPENAI_API_KEY=your_api_key_here
# AZURE_OPENAI_ENDPOINT=your_endpoint_here
# AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name_here
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
- 「🚀 協調推論開始」ボタンをクリック

### 2. ワークフローの観察
- **ステップ1**: Expert Recruiterが問題を分析し、適切な専門家を割り当て
- **ステップ2**: 割り当てられた専門家が並行して問題を解決
- **ステップ3**: Evaluatorが解答を検証し、最終回答を提供

### 3. 結果の確認
- 各段階での専門家の思考プロセスをリアルタイムで確認
- 最終検証済み回答の表示
- 詳細な協調推論ログの確認

### サンプル問題

#### 幾何学問題（Geometry Expertが担当）
```
ある正方形の面積が36平方センチメートルです。
この正方形の周りに幅2センチメートルの枠をつけると、
枠も含めた全体の面積は何平方センチメートルになりますか？
```

#### 代数学問題（Algebra Expertが担当）
```
太郎くんは4月に友達48人にクリップを売りました。
5月には4月の半分の数のクリップを売りました。
太郎くんは4月と5月で合計何個のクリップを売ったでしょうか？
```

#### 複合問題（両方の専門家が担当）
```
ある学校の体育館は長方形で、長辺がx+10メートル、短辺がxメートルです。
体育館の面積が600平方メートルの時、体育館の周囲は何メートルですか？
```

## 🔧 技術仕様

### バックエンド技術
- **AutoGen Core**: マルチエージェント協調推論フレームワーク
- **FastAPI**: WebAPIフレームワーク
- **WebSocket**: リアルタイム通信
- **Azure OpenAI GPT-4o-mini**: 言語モデル

### フロントエンド技術
- **HTML5/CSS3**: ユーザーインターフェース
- **JavaScript**: ワークフロー可視化とインタラクティブ機能
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
│       ├── core.py                  # 専門エージェント実装
│       └── manager.py               # 協調推論管理システム
├── templates/
│   └── index.html                   # メインWebページ
├── static/
│   ├── style.css                    # スタイルシート
│   └── script.js                    # JavaScriptファイル
└── test_*.py                        # テストスイート
```

## 🎮 協調推論プロセス

### ステップ1: 問題分析と専門家割り当て
- ユーザーが数学問題を入力
- Expert Recruiterが問題領域を分析
- インターネット検索による分類支援
- 適切な専門家を選択・割り当て

### ステップ2: 専門家による並行問題解決
- 割り当てられた専門家が同時に問題を解決
- 各専門家が専門知識を活用したアプローチで解答
- リアルタイムで解決プロセスを可視化

### ステップ3: 解答検証と最終回答
- Evaluatorが全ての専門家の解答を検証
- 数学的正確性と論理的妥当性を確認
- 最終的な検証済み回答を提供

## 🛠️ カスタマイズ

### 新しい専門家の追加
```python
# 新しい専門家エージェントを追加する例
@default_subscription
class StatisticsExpert(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, callback: DebateCallback = None):
        # 統計学専門家の実装
        pass
```

### Expert Recruiterの判定ロジック調整
```python
# Expert Recruiterの専門家選択ロジックをカスタマイズ
# core.pyのExpertRecruiterクラス内で調整可能
```

## 🐛 トラブルシューティング

### よくある問題

1. **Azure OpenAI APIエラー**
   - `.env`ファイルでAPIキー、エンドポイント、デプロイメント名が正しく設定されているか確認
   - APIキーの使用量制限を確認

2. **WebSocket接続エラー**
   - ブラウザのコンソールでエラーメッセージを確認
   - ファイアウォール設定を確認

3. **専門家割り当てエラー**
   - 問題文が明確に記述されているか確認
   - Expert Recruiterの分析ログを確認

## 📚 参考資料

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Multi-Agent Collaboration Research](https://arxiv.org/abs/2406.11776)

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🤝 貢献

プルリクエストや課題報告を歓迎します。大きな変更を行う前に、まず課題を開いて変更内容について議論してください。

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesで報告してください。