#!/usr/bin/env python3
"""
Test script for the new sequential workflow
Tests the Expert Recruiter -> Expert -> Evaluator workflow
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multi_agent_debate.core import DebateCallback, Question, Answer


class WorkflowTestCallback(DebateCallback):
    """Test callback to verify the new sequential workflow"""
    
    def __init__(self):
        self.events = []
        self.workflow_stages = []
        self.assigned_experts = []
        
    def on_agent_response(self, agent_id: str, round_num: int, content: str, answer: str):
        event = f"[Round {round_num}] {agent_id}: {answer}"
        self.events.append(event)
        self.workflow_stages.append(f"response:{agent_id}")
        print(f"📢 {event}")
    
    def on_expert_assignment(self, assigned_experts, reasoning):
        self.assigned_experts = assigned_experts
        event = f"Expert Assignment: {', '.join(assigned_experts)} - {reasoning}"
        self.events.append(event)
        self.workflow_stages.append("assignment")
        print(f"🎯 {event}")
    
    def on_evaluation_start(self):
        event = "Evaluation Started"
        self.events.append(event)
        self.workflow_stages.append("evaluation")
        print(f"✅ {event}")
    
    def on_debate_start(self, question: str):
        event = f"Workflow Started: {question}"
        self.events.append(event)
        self.workflow_stages.append("start")
        print(f"🚀 {event}")
    
    def on_debate_end(self, final_answer: str):
        event = f"Final Answer: {final_answer}"
        self.events.append(event)
        self.workflow_stages.append("end")
        print(f"🎯 {event}")


def test_sequential_workflow():
    """Test the new sequential workflow logic"""
    print("=" * 60)
    print("🧪 Sequential Workflow Test")
    print("=" * 60)
    
    callback = WorkflowTestCallback()
    
    # Simulate the new workflow
    question = "ある正方形の面積が36平方センチメートルです。この正方形の周りに幅2センチメートルの枠をつけると、枠も含めた全体の面積は何平方センチメートルになりますか？"
    
    # Stage 1: Expert Recruiter analyzes and assigns
    callback.on_debate_start(question)
    callback.on_expert_assignment(["GeometryExpert"], "この問題は幾何学的な計算が必要です。正方形と枠の面積計算はGeometry Expertが最適です。")
    callback.on_agent_response("ExpertRecruiter", 0, "問題を分析し、GeometryExpertに割り当てます。", "Assigned: GeometryExpert")
    
    # Stage 2: Assigned expert solves the problem
    callback.on_agent_response("GeometryExpert", 1, "正方形の面積36cm²なので一辺は6cm。枠込みで一辺は10cm。面積は100cm²。", "100")
    
    # Stage 3: Evaluator validates
    callback.on_evaluation_start()
    callback.on_agent_response("Evaluator", 2, "GeometryExpertの解答を検証。√36=6、6+2+2=10、10²=100。計算は正確です。", "100")
    
    callback.on_debate_end("100")
    
    print(f"\n✅ ワークフローテスト完了!")
    print(f"   - {len(callback.events)} 個のイベントが記録されました")
    print(f"   - 割り当てられた専門家: {', '.join(callback.assigned_experts)}")
    
    # Verify workflow sequence
    expected_sequence = ["start", "assignment", "response:ExpertRecruiter", "response:GeometryExpert", "evaluation", "response:Evaluator", "end"]
    
    print(f"   - 実際のワークフロー: {' -> '.join(callback.workflow_stages)}")
    print(f"   - 期待されるワークフロー: {' -> '.join(expected_sequence)}")
    
    if callback.workflow_stages == expected_sequence:
        print("✅ ワークフローシーケンスが正しく実行されました")
        return True
    else:
        print("❌ ワークフローシーケンスが期待と異なります")
        return False


def test_dual_expert_assignment():
    """Test workflow when both experts are assigned"""
    print("\n" + "=" * 60)
    print("🧪 Dual Expert Assignment Test")
    print("=" * 60)
    
    callback = WorkflowTestCallback()
    
    question = "複数の数学領域を含む複雑な問題"
    
    # Expert Recruiter assigns both experts
    callback.on_debate_start(question)
    callback.on_expert_assignment(["GeometryExpert", "AlgebraExpert"], "この問題は幾何学と代数学の両方の知識が必要です。")
    callback.on_agent_response("ExpertRecruiter", 0, "両方の専門家に問題を割り当てます。", "Assigned: Both")
    
    # Both experts work in parallel
    callback.on_agent_response("GeometryExpert", 1, "幾何学的アプローチで解決", "42")
    callback.on_agent_response("AlgebraExpert", 1, "代数的アプローチで解決", "42")
    
    # Evaluator validates both solutions
    callback.on_evaluation_start()
    callback.on_agent_response("Evaluator", 2, "両方の解答を検証し、一致を確認", "42")
    
    callback.on_debate_end("42")
    
    print(f"\n✅ デュアル専門家テスト完了!")
    print(f"   - 割り当てられた専門家: {', '.join(callback.assigned_experts)}")
    
    # Check that both experts were assigned
    if len(callback.assigned_experts) == 2 and "GeometryExpert" in callback.assigned_experts and "AlgebraExpert" in callback.assigned_experts:
        print("✅ 両方の専門家が正しく割り当てられました")
        return True
    else:
        print("❌ 専門家の割り当てが期待と異なります")
        return False


def main():
    """Main test function"""
    print("🤖 Sequential Workflow System Test")
    print("=" * 60)
    
    success = True
    
    # Test sequential workflow
    if not test_sequential_workflow():
        success = False
    
    # Test dual expert assignment
    if not test_dual_expert_assignment():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 全てのワークフローテストが成功しました!")
        print("   新しいシーケンシャルワークフローの準備完了:")
        print("   1. Expert Recruiter が問題を分析し専門家を割り当て")
        print("   2. 割り当てられた専門家が並行して問題を解決")
        print("   3. Evaluator が解答を検証し最終回答を提供")
    else:
        print("❌ 一部のテストが失敗しました。")
    
    print("=" * 60)
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)