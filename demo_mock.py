#!/usr/bin/env python3
"""
Mock demo script to test the UI enhancements without requiring API keys
"""
import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Mock Multi-Agent Debate Demo")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global state
connected_clients = []
debate_history = []

async def broadcast_message(message):
    """Broadcast message to all connected clients"""
    if connected_clients:
        tasks = []
        for client in connected_clients[:]:
            tasks.append(send_to_client(client, message))
        await asyncio.gather(*tasks, return_exceptions=True)

async def send_to_client(websocket, message):
    """Send message to individual client"""
    try:
        await websocket.send_text(json.dumps(message, ensure_ascii=False))
    except Exception as e:
        print(f"Failed to send message to client: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    
    # Send existing debate history to new client
    for message in debate_history:
        await websocket.send_text(json.dumps(message, ensure_ascii=False))
    
    try:
        while True:
            await websocket.receive_text()
    except:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

@app.post("/api/solve")
async def solve_problem(request: Request):
    """Mock solve endpoint that simulates the debate"""
    body = await request.json()
    question = body.get("question", "")
    
    # Start the mock debate
    asyncio.create_task(run_mock_debate(question))
    
    return {"status": "started", "message": "議論を開始しました"}

async def run_mock_debate(question: str):
    """Run a mock debate simulation"""
    try:
        # Start debate
        await broadcast_message({
            "type": "debate_start",
            "question": question,
            "timestamp": datetime.now().isoformat()
        })
        
        # Simulate different rounds
        agents = [
            {"id": "ExpertRecruiter", "name": "Expert Recruiter (専門家採用担当者)"},
            {"id": "GeometryExpert", "name": "Geometry Expert (幾何学専門家)"},
            {"id": "AlgebraExpert", "name": "Algebra Expert (代数学専門家)"},
            {"id": "Evaluator", "name": "Evaluator (評価者)"}
        ]
        
        # Mock responses for different types of questions
        if "クリップ" in question:
            mock_answers = ["72", "72", "72", "72"]
            mock_contents = [
                "この問題は算数の基本的な計算問題です。4月48個、5月24個の合計を求めます。",
                "幾何学的には関係ありませんが、数の配列として考えると48+24=72個です。",
                "代数的に表現すると、x=48, y=x/2=24, 答え=x+y=72となります。",
                "各専門家の回答を検証します。計算は正確で、答えは72個で一致しています。"
            ]
        elif "正方形" in question and "面積" in question:
            mock_answers = ["100", "100", "100", "100"]
            mock_contents = [
                "この問題は幾何学と代数学の複合問題です。正方形の性質と面積計算が必要です。",
                "面積36から一辺6cm、枠2cm加えて全体10cm、面積100cm²です。",
                "代数的に：√36=6, (6+2×2)²=10²=100平方センチメートルです。",
                "計算過程を検証：36→6cm→10cm→100cm²。全て正確です。"
            ]
        elif "時間" in question and "倍" in question:
            mock_answers = ["4", "4", "4", "4"]
            mock_contents = [
                "時間配分の問題です。通常60分の準備を15分で行う計算が必要です。",
                "幾何学的時間配置として考えると、60分→15分は1/4の時間です。",
                "代数的に：60÷15=4倍の速度が必要という計算になります。",
                "各専門家の分析は正確です。4倍の速度で準備する必要があります。"
            ]
        elif "パーティー" in question:
            mock_answers = ["12", "6", "0", "8"]
            mock_contents = [
                "全員が何かを食べたと仮定すると、何も食べなかった人は0人になります。",
                "重複を考慮せず単純計算すると、24-(12+8+6)=何も食べない人は計算できません。",
                "ピザ12人、サラダ8人、デザート6人の重複があるため、正確な計算には追加情報が必要です。",
                "最小で12人（ピザのみ）、最大で26人が何かを食べたので、何も食べなかった人は0-2人程度。"
            ]
        else:
            mock_answers = ["240", "240", "240", "240"]
            mock_contents = [
                "この問題は分数計算です。全体の3分の2を求める基本的な割合問題です。",
                "幾何学的配置として考えても、360の2/3は240人となります。",
                "代数的表現：360 × (2/3) = 360 × 0.667 = 240人です。",
                "各専門家の計算を確認。360×2÷3=240人で一致しています。"
            ]
        
        for round_num in range(3):
            # Thinking phase
            for i, agent in enumerate(agents):
                await asyncio.sleep(0.5)
                await broadcast_message({
                    "type": "agent_thinking",
                    "agent_id": agent["id"],
                    "round": round_num,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Response phase
            for i, agent in enumerate(agents):
                await asyncio.sleep(2)  # Simulate thinking time
                await broadcast_message({
                    "type": "agent_response",
                    "agent_id": agent["id"],
                    "round": round_num,
                    "content": mock_contents[i],
                    "answer": mock_answers[i],
                    "timestamp": datetime.now().isoformat()
                })
            
            # Round complete
            await asyncio.sleep(1)
            await broadcast_message({
                "type": "round_complete",
                "round": round_num,
                "timestamp": datetime.now().isoformat()
            })
        
        # Final answer (majority vote)
        from collections import Counter
        final_answer = Counter(mock_answers).most_common(1)[0][0]
        
        await asyncio.sleep(1)
        await broadcast_message({
            "type": "debate_end",
            "final_answer": final_answer,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        await broadcast_message({
            "type": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        })

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Mock Multi-Agent Debate Demo at http://localhost:8000")
    print("This demo simulates the agent behavior without requiring API keys")
    uvicorn.run(app, host="0.0.0.0", port=8000)