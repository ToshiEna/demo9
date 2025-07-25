#!/usr/bin/env python3
"""
Multi-Agent Debate システム使用例
実際のOpenAI APIキーが設定されている場合のデモンストレーション
"""

import os
import asyncio
from dotenv import load_dotenv
from src.multi_agent_debate import DebateManager, DebateCallback

class DemoCallback(DebateCallback):
    """デモ用のコールバック実装"""
    
    def on_agent_response(self, agent_id: str, round_num: int, content: str, answer: str):
        print(f"\n{'='*60}")
        print(f"🤖 {agent_id} (ラウンド {round_num})")
        print(f"{'='*60}")
        print(f"回答内容: {content}")
        print(f"数値回答: {answer}")
    
    def on_debate_start(self, question: str):
        print(f"\n🚀 議論開始!")
        print(f"問題: {question}")
        print("="*80)
    
    def on_debate_end(self, final_answer: str):
        print(f"\n🎯 議論終了!")
        print(f"最終回答: {final_answer}")
        print("="*80)
    
    def on_round_complete(self, round_num: int):
        print(f"\n✅ ラウンド {round_num} 完了 - 次のラウンドに進みます...")

async def run_demo():
    """デモの実行"""
    # 環境変数の読み込み
    load_dotenv()
    
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    if not azure_api_key:
        print("❌ エラー: Azure OpenAI APIキーが設定されていません。")
        print("   .envファイルを作成し、AZURE_OPENAI_API_KEY=your_api_key_here を設定してください。")
        return
    if not azure_endpoint:
        print("❌ エラー: Azure OpenAI エンドポイントが設定されていません。")
        print("   .envファイルを作成し、AZURE_OPENAI_ENDPOINT=your_endpoint_here を設定してください。")
        return
    if not azure_deployment:
        print("❌ エラー: Azure OpenAI デプロイメント名が設定されていません。")
        print("   .envファイルを作成し、AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name_here を設定してください。")
        return
    
    # 解決する問題
    question = "太郎くんは4月に友達48人にクリップを売りました。5月には4月の半分の数のクリップを売りました。太郎くんは4月と5月で合計何個のクリップを売ったでしょうか？"
    
    print("🤖 Multi-Agent Debate システムデモ")
    print("="*80)
    print("このデモでは、4つのAIエージェントが協力して数学問題を解決します。")
    print("各エージェントは他のエージェントの回答を参考に、自身の回答を改善していきます。")
    
    # コールバックの設定
    callback = DemoCallback()
    
    # 議論システムの初期化と実行
    try:
        manager = DebateManager(
            azure_api_key=azure_api_key,
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment,
            model_name="gpt-4o-mini",  # より高性能なモデルに変更可能
            num_solvers=4,
            max_rounds=3
        )
        manager.set_callback(callback)
        
        # 議論の実行
        await manager.solve_problem(question)
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print("Azure OpenAI APIキーが有効か、APIの使用量制限に達していないかを確認してください。")

def main():
    """メイン関数"""
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n⏹️ デモが中断されました。")
    except Exception as e:
        print(f"\n❌ エラー: {e}")

if __name__ == "__main__":
    main()