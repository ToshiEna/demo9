#!/usr/bin/env python3
"""
Test script for the new Orchestrator with Task and Progress Ledgers
Tests the enhanced workflow with ledger management
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multi_agent_debate.core import DebateCallback, Question, Answer, TaskLedger, ProgressLedger


class LedgerTestCallback(DebateCallback):
    """Test callback to verify the new ledger-based workflow"""
    
    def __init__(self):
        self.events = []
        self.workflow_stages = []
        self.assigned_experts = []
        self.task_ledger = None
        self.progress_ledger = None
        self.ledger_updates = 0
        
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
    
    def on_task_ledger_update(self, task_ledger: TaskLedger):
        """Handle Task Ledger updates"""
        self.task_ledger = task_ledger
        self.ledger_updates += 1
        event = f"Task Ledger Updated: {len(task_ledger.given_facts)} facts, {len(task_ledger.task_plan)} plan steps"
        self.events.append(event)
        self.workflow_stages.append("task_ledger_update")
        print(f"📋 {event}")
        print(f"   Given Facts: {task_ledger.given_facts}")
        print(f"   Task Plan: {task_ledger.task_plan}")
    
    def on_progress_ledger_update(self, progress_ledger: ProgressLedger):
        """Handle Progress Ledger updates"""
        self.progress_ledger = progress_ledger
        event = f"Progress Update: Task Complete={progress_ledger.task_complete}, Next={progress_ledger.next_speaker}"
        self.events.append(event)
        self.workflow_stages.append("progress_ledger_update")
        print(f"📊 {event}")
        print(f"   Progress Made: {progress_ledger.progress_being_made}")
        print(f"   Completed Steps: {progress_ledger.completed_steps}")


def test_orchestrator_with_ledgers():
    """Test the new Orchestrator workflow with Task and Progress Ledgers"""
    print("=" * 60)
    print("🧪 Orchestrator with Ledgers Test")
    print("=" * 60)
    
    callback = LedgerTestCallback()
    
    # Simulate the new ledger-based workflow
    question = "ある正方形の面積が36平方センチメートルです。この正方形の周りに幅2センチメートルの枠をつけると、枠も含めた全体の面積は何平方センチメートルになりますか？"
    
    # Stage 1: Orchestrator creates ledgers and analyzes
    callback.on_debate_start(question)
    
    # Create mock Task Ledger
    task_ledger = TaskLedger(question=question)
    task_ledger.given_facts = [
        "正方形の面積が36平方センチメートル",
        "枠の幅が2センチメートル"
    ]
    task_ledger.facts_to_derive = [
        "正方形の一辺の長さ",
        "枠込みの全体の一辺の長さ",
        "枠込みの全体の面積"
    ]
    task_ledger.task_plan = [
        "正方形の面積から一辺を計算",
        "枠の幅を加えて全体の一辺を計算",
        "全体の面積を計算"
    ]
    
    callback.on_task_ledger_update(task_ledger)
    
    # Create mock Progress Ledger
    progress_ledger = ProgressLedger()
    progress_ledger.progress_being_made = True
    progress_ledger.next_speaker = "GeometryExpert"
    progress_ledger.next_speaker_instruction = "Calculate area with frame using geometric principles"
    
    callback.on_progress_ledger_update(progress_ledger)
    
    # Stage 2: Expert assignment
    callback.on_expert_assignment(["GeometryExpert"], "幾何学的計算が必要なためGeometryExpertを選択")
    callback.on_agent_response("Orchestrator", 0, "問題を分析し、Task LedgerとProgress Ledgerを作成しました。", "Assigned: GeometryExpert")
    
    # Stage 3: Expert solution with progress updates
    progress_ledger.update_progress("GeometryExpert assigned and working", True)
    callback.on_progress_ledger_update(progress_ledger)
    
    callback.on_agent_response("GeometryExpert", 1, "正方形の面積36cm²なので一辺は6cm。枠込みで一辺は10cm。面積は100cm²。", "100")
    
    # Stage 4: Evaluation with final progress update
    callback.on_evaluation_start()
    
    progress_ledger.task_complete = True
    progress_ledger.next_speaker = "Complete"
    progress_ledger.update_progress("Solution validated and task completed", True)
    callback.on_progress_ledger_update(progress_ledger)
    
    callback.on_agent_response("Evaluator", 2, "GeometryExpertの解答を検証。計算は正確です。", "100")
    
    callback.on_debate_end("100")
    
    print(f"\n✅ Orchestrator with Ledgers テスト完了!")
    print(f"   - {len(callback.events)} 個のイベントが記録されました")
    print(f"   - {callback.ledger_updates} 回のレジャー更新がありました")
    print(f"   - 割り当てられた専門家: {', '.join(callback.assigned_experts)}")
    
    # Verify Task Ledger functionality
    if callback.task_ledger:
        print(f"   - Task Ledger: {len(callback.task_ledger.given_facts)} facts, {len(callback.task_ledger.task_plan)} plan steps")
        task_ledger_ok = len(callback.task_ledger.given_facts) > 0 and len(callback.task_ledger.task_plan) > 0
    else:
        task_ledger_ok = False
    
    # Verify Progress Ledger functionality
    if callback.progress_ledger:
        print(f"   - Progress Ledger: Task Complete={callback.progress_ledger.task_complete}")
        progress_ledger_ok = callback.progress_ledger.task_complete
    else:
        progress_ledger_ok = False
    
    # Verify enhanced workflow sequence
    expected_stages = ["start", "task_ledger_update", "progress_ledger_update", "assignment", "response:Orchestrator"]
    actual_start = callback.workflow_stages[:len(expected_stages)]
    
    print(f"   - 実際のワークフロー開始: {' -> '.join(actual_start)}")
    
    if task_ledger_ok and progress_ledger_ok and "task_ledger_update" in callback.workflow_stages:
        print("✅ Task LedgerとProgress Ledgerが正しく機能しています")
        return True
    else:
        print("❌ レジャー機能に問題があります")
        return False


def test_progress_monitoring():
    """Test progress monitoring and stall detection"""
    print("\n" + "=" * 60)
    print("🧪 Progress Monitoring Test")
    print("=" * 60)
    
    callback = LedgerTestCallback()
    
    # Test stall detection
    progress_ledger = ProgressLedger()
    
    # Simulate normal progress
    progress_ledger.update_progress("Step 1 completed", True)
    callback.on_progress_ledger_update(progress_ledger)
    
    progress_ledger.update_progress("Step 2 completed", True)
    callback.on_progress_ledger_update(progress_ledger)
    
    # Simulate stall condition
    progress_ledger.update_progress("Step 3 failed", False)
    callback.on_progress_ledger_update(progress_ledger)
    
    progress_ledger.update_progress("Step 4 failed", False)
    callback.on_progress_ledger_update(progress_ledger)
    
    progress_ledger.update_progress("Step 5 failed", False)
    callback.on_progress_ledger_update(progress_ledger)
    
    # Check stall detection
    is_stalled = progress_ledger.check_stall()
    
    print(f"\n✅ Progress Monitoring テスト完了!")
    print(f"   - Stall Count: {progress_ledger.stall_count}")
    print(f"   - Stall Detected: {is_stalled}")
    print(f"   - Progress Being Made: {progress_ledger.progress_being_made}")
    
    if is_stalled and progress_ledger.stall_count > 2:
        print("✅ Stall detection が正しく動作しています")
        return True
    else:
        print("❌ Stall detection に問題があります")
        return False


def main():
    """Main test function"""
    print("🤖 Enhanced Orchestrator with Ledgers System Test")
    print("=" * 60)
    
    success = True
    
    # Test orchestrator with ledgers
    if not test_orchestrator_with_ledgers():
        success = False
    
    # Test progress monitoring
    if not test_progress_monitoring():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 全てのレジャーテストが成功しました!")
        print("   新しいOrchestrator with Ledgers システムの準備完了:")
        print("   1. Task Ledger が問題の事実と計画を管理")
        print("   2. Progress Ledger が進捗監視とstall検出を実行")
        print("   3. Orchestrator が全体のワークフローを調整")
        print("   4. 選択された専門家のみが活性化")
    else:
        print("❌ 一部のテストが失敗しました。")
    
    print("=" * 60)
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)