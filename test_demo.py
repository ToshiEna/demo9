#!/usr/bin/env python3
"""
テスト用デモスクリプト
OpenAI APIキーなしでシステムの基本構造をテストします
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multi_agent_debate.core import DebateCallback, Question, Answer

class MockDebateCallback(DebateCallback):
    """テスト用のモックコールバック"""
    
    def __init__(self):
        self.events = []
    
    def on_agent_response(self, agent_id: str, round_num: int, content: str, answer: str):
        event = f"Agent {agent_id} (Round {round_num}): {answer}"
        self.events.append(event)
        print(f"📢 {event}")
    
    def on_debate_start(self, question: str):
        event = f"議論開始: {question}"
        self.events.append(event)
        print(f"🚀 {event}")
    
    def on_debate_end(self, final_answer: str):
        event = f"最終回答: {final_answer}"
        self.events.append(event)
        print(f"🎯 {event}")
    
    def on_round_complete(self, round_num: int):
        event = f"ラウンド {round_num} 完了"
        self.events.append(event)
        print(f"✅ {event}")

def test_basic_structure():
    """基本構造のテスト"""
    print("=" * 60)
    print("🧪 Multi-Agent Debate システム 基本構造テスト")
    print("=" * 60)
    
    # コールバックのテスト
    callback = MockDebateCallback()
    
    # 模擬的な議論フローの実行
    question = "太郎くんは4月に友達48人にクリップを売りました。5月には4月の半分の数のクリップを売りました。太郎くんは4月と5月で合計何個のクリップを売ったでしょうか？"
    
    callback.on_debate_start(question)
    
    # 模擬エージェント応答
    agents = ["MathSolverA", "MathSolverB", "MathSolverC", "MathSolverD"]
    for round_num in range(3):
        print(f"\n--- ラウンド {round_num} ---")
        for agent in agents:
            content = f"ラウンド{round_num}での{agent}の回答内容です。"
            answer = "72"  # 模擬回答
            callback.on_agent_response(agent, round_num, content, answer)
        callback.on_round_complete(round_num)
    
    callback.on_debate_end("72")
    
    print(f"\n✅ テスト完了! {len(callback.events)} 個のイベントが記録されました。")
    return True

def test_web_structure():
    """Web構造のテスト"""
    print("\n" + "=" * 60)
    print("🌐 Web アプリケーション構造テスト")
    print("=" * 60)
    
    # 必要なファイルの存在確認
    required_files = [
        "main.py",
        "templates/index.html",
        "static/style.css",
        "static/script.js",
        "src/multi_agent_debate/__init__.py",
        "src/multi_agent_debate/core.py",
        "src/multi_agent_debate/manager.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ 不足ファイル: {missing_files}")
        return False
    
    print(f"\n✅ 全必要ファイルが存在します!")
    return True

def main():
    """メインテスト関数"""
    print("🤖 Multi-Agent Debate Demo システムテスト")
    print("=" * 60)
    
    success = True
    
    # 基本構造テスト
    if not test_basic_structure():
        success = False
    
    # Web構造テスト
    if not test_web_structure():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 全てのテストが成功しました!")
        print("\n次のステップ:")
        print("1. .envファイルにOpenAI APIキーを設定")
        print("2. python main.py でサーバー起動")
        print("3. http://localhost:8000 にアクセス")
    else:
        print("❌ 一部のテストが失敗しました。")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)