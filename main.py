import asyncio
import json
import os
from typing import Dict, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

from src.multi_agent_debate import DebateManager, DebateCallback

# Load environment variables
load_dotenv()

app = FastAPI(title="Multi-Agent Debate Demo", description="リアルタイムマルチエージェント議論システム")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global state
connected_clients: List[WebSocket] = []
debate_history: List[Dict] = []


class QuestionRequest(BaseModel):
    question: str


class WebSocketCallback(DebateCallback):
    """WebSocket用のコールバック実装"""
    
    def on_agent_response(self, agent_id: str, round_num: int, content: str, answer: str):
        message = {
            "type": "agent_response",
            "agent_id": str(agent_id),  # Convert AgentId to string for JSON serialization
            "round": round_num,
            "content": content,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        }
        debate_history.append(message)
        asyncio.create_task(broadcast_message(message))
    
    def on_agent_thinking(self, agent_id: str, round_num: int):
        message = {
            "type": "agent_thinking",
            "agent_id": str(agent_id),
            "round": round_num,
            "timestamp": datetime.now().isoformat()
        }
        debate_history.append(message)
        asyncio.create_task(broadcast_message(message))
    
    def on_debate_start(self, question: str):
        message = {
            "type": "debate_start",
            "question": question,
            "timestamp": datetime.now().isoformat()
        }
        debate_history.clear()  # Clear previous history
        debate_history.append(message)
        asyncio.create_task(broadcast_message(message))
    
    def on_debate_end(self, final_answer: str):
        message = {
            "type": "debate_end",
            "final_answer": final_answer,
            "timestamp": datetime.now().isoformat()
        }
        debate_history.append(message)
        asyncio.create_task(broadcast_message(message))
    
    def on_round_complete(self, round_num: int):
        message = {
            "type": "round_complete",
            "round": round_num,
            "timestamp": datetime.now().isoformat()
        }
        debate_history.append(message)
        asyncio.create_task(broadcast_message(message))

    def on_expert_assignment(self, assigned_experts: List[str], reasoning: str):
        message = {
            "type": "expert_assignment",
            "assigned_experts": assigned_experts,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        }
        debate_history.append(message)
        asyncio.create_task(broadcast_message(message))
    
    def on_evaluation_start(self):
        message = {
            "type": "evaluation_start",
            "timestamp": datetime.now().isoformat()
        }
        debate_history.append(message)
        asyncio.create_task(broadcast_message(message))


async def broadcast_message(message: Dict):
    """全ての接続されたクライアントにメッセージをブロードキャスト"""
    if connected_clients:
        # Create tasks for all clients
        tasks = []
        for client in connected_clients[:]:  # Copy the list to avoid modification during iteration
            tasks.append(send_to_client(client, message))
        
        # Wait for all sends to complete
        await asyncio.gather(*tasks, return_exceptions=True)


async def send_to_client(websocket: WebSocket, message: Dict):
    """個別のクライアントにメッセージを送信"""
    try:
        await websocket.send_text(json.dumps(message, ensure_ascii=False))
    except Exception as e:
        print(f"Failed to send message to client: {e}")
        # Remove disconnected client
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
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


@app.post("/api/solve")
async def solve_problem(request: QuestionRequest):
    """数学問題を解決する"""
    try:
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        if not azure_api_key:
            return {"error": "Azure OpenAI API key not configured"}
        if not azure_endpoint:
            return {"error": "Azure OpenAI endpoint not configured"}
        if not azure_deployment:
            return {"error": "Azure OpenAI deployment name not configured"}
        
        # Create debate manager with callback
        callback = WebSocketCallback()
        manager = DebateManager(
            azure_api_key=azure_api_key,
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment
        )
        manager.set_callback(callback)
        
        # Run debate in background
        asyncio.create_task(run_debate(manager, request.question))
        
        return {"status": "started", "message": "議論を開始しました"}
    
    except Exception as e:
        return {"error": str(e)}


async def run_debate(manager: DebateManager, question: str):
    """バックグラウンドで議論を実行"""
    try:
        async with manager:
            await manager.solve_problem(question)
    except Exception as e:
        error_message = {
            "type": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
        await broadcast_message(error_message)


@app.get("/api/history")
async def get_debate_history():
    """議論履歴を取得"""
    return {"history": debate_history}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)