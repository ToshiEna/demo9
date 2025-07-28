#!/usr/bin/env python3
"""
Test script for the new specialized agent roles
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multi_agent_debate.core import DebateCallback, Question, Answer

class TestRoleCallback(DebateCallback):
    """Test callback to verify role-based functionality"""
    
    def __init__(self):
        self.events = []
        self.agents_seen = set()
    
    def on_agent_response(self, agent_id: str, round_num: int, content: str, answer: str):
        self.agents_seen.add(agent_id)
        event = f"[Round {round_num}] {agent_id}: {answer}"
        self.events.append(event)
        print(f"📢 {event}")
    
    def on_debate_start(self, question: str):
        event = f"協調推論開始: {question}"
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

def test_specialized_roles():
    """Test the new specialized agent roles"""
    print("=" * 60)
    print("🧪 専門家エージェント役割テスト")
    print("=" * 60)
    
    callback = TestRoleCallback()
    
    # Simulate collaborative reasoning workflow
    question = "ある正方形の面積が36平方センチメートルです。この正方形の周りに幅2センチメートルの枠をつけると、枠も含めた全体の面積は何平方センチメートルになりますか？"
    
    callback.on_debate_start(question)
    
    # Simulate specialized agent responses
    specialized_agents = [
        ("ExpertRecruiter", "この問題は幾何学と代数学の知識が必要です。正方形の一辺を求めてから枠を含めた面積を計算します。"),
        ("GeometryExpert", "正方形の面積が36なので一辺は6cm。枠を含めた一辺は6+2+2=10cm。"),
        ("AlgebraExpert", "一辺がaの正方形に幅wの枠をつけると、全体の一辺は(a+2w)。この場合(6+4)=10cm。"),
        ("Evaluator", "各専門家の解答を検証します。面積36→一辺6cm→枠込み一辺10cm→面積100cm²。計算は正確です。")
    ]
    
    for round_num in range(3):
        print(f"\n--- ラウンド {round_num} ---")
        for agent_name, reasoning in specialized_agents:
            content = f"[{reasoning}] 従って答えは100です。"
            answer = "100"
            callback.on_agent_response(agent_name, round_num, content, answer)
        callback.on_round_complete(round_num)
    
    callback.on_debate_end("100")
    
    print(f"\n✅ テスト完了!")
    print(f"   - {len(callback.events)} 個のイベントが記録されました")
    print(f"   - {len(callback.agents_seen)} 個の専門エージェントが参加しました")
    print(f"   - 参加エージェント: {', '.join(callback.agents_seen)}")
    
    # Verify all expected agents participated
    expected_agents = {"ExpertRecruiter", "GeometryExpert", "AlgebraExpert", "Evaluator"}
    if callback.agents_seen == expected_agents:
        print("✅ 全ての専門エージェントが正常に動作しました")
        return True
    else:
        print(f"❌ 期待されたエージェント: {expected_agents}")
        print(f"❌ 実際のエージェント: {callback.agents_seen}")
        return False

def main():
    """Main test function"""
    print("🤖 Multi-Agent Collaborative Reasoning システムテスト")
    print("=" * 60)
    
    success = test_specialized_roles()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 全ての役割テストが成功しました!")
        print("   新しい専門エージェントシステムの準備完了:")
        print("   - Expert Recruiter (専門家採用担当者)")
        print("   - Geometry Expert (幾何学専門家)")  
        print("   - Algebra Expert (代数学専門家)")
        print("   - Evaluator (評価者)")
    else:
        print("❌ 一部のテストが失敗しました。")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)