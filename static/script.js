// WebSocket connection
let ws = null;
let currentRound = 0;
let maxRounds = 3;

// DOM elements
const questionInput = document.getElementById('questionInput');
const solveButton = document.getElementById('solveButton');
const status = document.getElementById('status');
const currentQuestion = document.getElementById('currentQuestion');
const questionText = document.getElementById('questionText');
const finalResult = document.getElementById('finalResult');
const finalAnswer = document.getElementById('finalAnswer');
const debateLog = document.getElementById('debateLog');
const roundsProgress = document.getElementById('roundsProgress');

// Initialize WebSocket connection
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function(event) {
        console.log('WebSocket connected');
        updateStatus('waiting', '接続完了 - 問題を入力してください');
    };
    
    ws.onmessage = function(event) {
        const message = JSON.parse(event.data);
        handleMessage(message);
    };
    
    ws.onclose = function(event) {
        console.log('WebSocket disconnected');
        updateStatus('waiting', '接続が切断されました - ページを再読み込みしてください');
        // Attempt to reconnect after 3 seconds
        setTimeout(initWebSocket, 3000);
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateStatus('error', 'WebSocket接続エラー');
    };
}

// Get friendly agent name for display
function getFriendlyAgentName(agentId) {
    const id = agentId.toLowerCase();
    if (id.includes('expertrecruiter')) {
        return 'Expert Recruiter (専門家採用担当者)';
    } else if (id.includes('geometryexpert')) {
        return 'Geometry Expert (幾何学専門家)';
    } else if (id.includes('algebraexpert')) {
        return 'Algebra Expert (代数学専門家)';
    } else if (id.includes('evaluator')) {
        return 'Evaluator (評価者)';
    }
    return agentId; // fallback to original ID
}

// Handle incoming WebSocket messages
function handleMessage(message) {
    switch (message.type) {
        case 'debate_start':
            handleDebateStart(message);
            break;
        case 'agent_thinking':
            handleAgentThinking(message);
            break;
        case 'agent_response':
            handleAgentResponse(message);
            break;
        case 'expert_assignment':
            handleExpertAssignment(message);
            break;
        case 'evaluation_start':
            handleEvaluationStart(message);
            break;
        case 'round_complete':
            handleRoundComplete(message);
            break;
        case 'debate_end':
            handleDebateEnd(message);
            break;
        case 'error':
            handleError(message);
            break;
    }
    
    // Add to log
    addLogEntry(message);
}

// Update status display
function updateStatus(type, message) {
    status.className = `status ${type}`;
    status.textContent = message;
}

// Handle debate start
function handleDebateStart(message) {
    updateStatus('running', '協調推論実行中...');
    questionText.textContent = message.question;
    currentQuestion.style.display = 'block';
    finalResult.style.display = 'none';
    
    // Clear previous results
    clearAgentResponses();
    currentRound = 0;
    initializeRoundsProgress();
    
    // Set all agents to thinking state
    document.querySelectorAll('.agent-card').forEach(card => {
        setAgentState(card, 'thinking');
    });
    
    solveButton.disabled = true;
    solveButton.textContent = '協調推論実行中...';
}

// Handle agent thinking
function handleAgentThinking(message) {
    const agentId = message.agent_id.toLowerCase();
    let agentElement = null;
    
    // Map agent IDs to HTML element IDs
    if (agentId.includes('expertrecruiter')) {
        agentElement = document.getElementById('agentExpertRecruiter');
    } else if (agentId.includes('geometryexpert')) {
        agentElement = document.getElementById('agentGeometryExpert');
    } else if (agentId.includes('algebraexpert')) {
        agentElement = document.getElementById('agentAlgebraExpert');
    } else if (agentId.includes('evaluator')) {
        agentElement = document.getElementById('agentEvaluator');
    }
    
    if (agentElement) {
        setAgentState(agentElement, 'thinking');
    }
}

// Handle agent response
function handleAgentResponse(message) {
    const agentId = message.agent_id.toLowerCase();
    let agentElement = null;
    
    // Map agent IDs to HTML element IDs
    if (agentId.includes('expertrecruiter')) {
        agentElement = document.getElementById('agentExpertRecruiter');
    } else if (agentId.includes('geometryexpert')) {
        agentElement = document.getElementById('agentGeometryExpert');
    } else if (agentId.includes('algebraexpert')) {
        agentElement = document.getElementById('agentAlgebraExpert');
    } else if (agentId.includes('evaluator')) {
        agentElement = document.getElementById('agentEvaluator');
    }
    
    if (agentElement) {
        // Set agent to active state
        setAgentState(agentElement, 'active');
        
        // Add response to agent card
        const responsesContainer = agentElement.querySelector('.agent-responses');
        const responseElement = document.createElement('div');
        responseElement.className = 'agent-response';
        
        responseElement.innerHTML = `
            <div class="response-meta">ラウンド ${message.round}</div>
            <div class="response-content">${message.content}</div>
            <div class="response-answer">回答: ${message.answer}</div>
        `;
        
        responsesContainer.appendChild(responseElement);
        
        // Update round progress
        updateRoundProgress(message.round);
        
        // After a delay, set agent to completed state for this round
        setTimeout(() => {
            setAgentState(agentElement, 'completed');
        }, 2000);
    }
}

// Handle expert assignment
function handleExpertAssignment(message) {
    // Update status to show expert assignment
    updateStatus('running', `専門家を割り当て中: ${message.assigned_experts.join(', ')}`);
    
    // Highlight assigned experts
    const allAgents = ['ExpertRecruiter', 'GeometryExpert', 'AlgebraExpert', 'Evaluator'];
    allAgents.forEach(agentName => {
        const element = document.getElementById(`agent${agentName}`);
        if (element) {
            if (message.assigned_experts.includes(agentName)) {
                element.classList.add('assigned');
                setAgentState(element, 'thinking');
            } else {
                element.classList.remove('assigned');
                setAgentState(element, 'waiting');
            }
        }
    });
}

// Handle evaluation start
function handleEvaluationStart(message) {
    updateStatus('running', '評価者が解答を検証中...');
    
    // Set Evaluator to thinking state
    const evaluatorElement = document.getElementById('agentEvaluator');
    if (evaluatorElement) {
        setAgentState(evaluatorElement, 'thinking');
    }
}

// Handle round completion
function handleRoundComplete(message) {
    // Mark round as completed
    markRoundCompleted(message.round);
    
    // Set all agents back to thinking for next round (if not final round)
    if (message.round < maxRounds) {
        setTimeout(() => {
            document.querySelectorAll('.agent-card').forEach(card => {
                setAgentState(card, 'thinking');
            });
        }, 1000);
    }
}

// Handle debate end
function handleDebateEnd(message) {
    updateStatus('completed', '協調推論完了！');
    finalAnswer.textContent = message.final_answer;
    finalResult.style.display = 'block';
    
    // Set all agents to completed state
    document.querySelectorAll('.agent-card').forEach(card => {
        setAgentState(card, 'completed');
    });
    
    // Re-enable solve button
    solveButton.disabled = false;
    solveButton.textContent = '🚀 協調推論開始';
}

// Handle errors
function handleError(message) {
    updateStatus('error', `エラー: ${message.message}`);
    solveButton.disabled = false;
    solveButton.textContent = '🚀 協調推論開始';
    
    // Reset all agents to waiting state
    document.querySelectorAll('.agent-card').forEach(card => {
        setAgentState(card, 'waiting');
    });
}

// Clear agent responses
function clearAgentResponses() {
    document.querySelectorAll('.agent-responses').forEach(container => {
        container.innerHTML = '';
    });
    
    // Reset all agents to waiting state
    document.querySelectorAll('.agent-card').forEach(card => {
        setAgentState(card, 'waiting');
    });
}

// Set agent state (waiting, thinking, active, completed)
function setAgentState(agentElement, state) {
    // Remove all state classes
    agentElement.classList.remove('thinking', 'active', 'completed');
    
    const statusElement = agentElement.querySelector('.agent-status');
    const thinkingIndicator = agentElement.querySelector('.thinking-indicator');
    
    switch (state) {
        case 'waiting':
            statusElement.textContent = '待機中';
            thinkingIndicator.style.display = 'none';
            break;
        case 'thinking':
            agentElement.classList.add('thinking');
            statusElement.textContent = '考え中...';
            thinkingIndicator.style.display = 'flex';
            break;
        case 'active':
            agentElement.classList.add('active');
            statusElement.textContent = '回答中';
            thinkingIndicator.style.display = 'none';
            break;
        case 'completed':
            agentElement.classList.add('completed');
            statusElement.textContent = '完了';
            thinkingIndicator.style.display = 'none';
            break;
    }
}

// Initialize rounds progress
function initializeRoundsProgress() {
    roundsProgress.innerHTML = '';
    for (let i = 1; i <= maxRounds; i++) {
        const roundElement = document.createElement('div');
        roundElement.className = 'round-indicator pending';
        roundElement.textContent = i;
        roundElement.id = `round-${i}`;
        roundsProgress.appendChild(roundElement);
    }
}

// Update round progress
function updateRoundProgress(round) {
    const roundElement = document.getElementById(`round-${round}`);
    if (roundElement) {
        roundElement.className = 'round-indicator active';
    }
}

// Mark round as completed
function markRoundCompleted(round) {
    const roundElement = document.getElementById(`round-${round}`);
    if (roundElement) {
        roundElement.className = 'round-indicator completed';
    }
}

// Add log entry
function addLogEntry(message) {
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${message.type.replace('_', '-')}`;
    
    const timestamp = new Date(message.timestamp).toLocaleTimeString('ja-JP');
    
    let content = '';
    switch (message.type) {
        case 'debate_start':
            content = `協調推論開始: ${message.question}`;
            break;
        case 'agent_thinking':
            content = `${getFriendlyAgentName(message.agent_id)} が分析中... (ラウンド${message.round})`;
            break;
        case 'agent_response':
            content = `${getFriendlyAgentName(message.agent_id)} (ラウンド${message.round}): ${message.answer}`;
            break;
        case 'expert_assignment':
            content = `Expert Recruiterが専門家を割り当て: ${message.assigned_experts.join(', ')} - 理由: ${message.reasoning}`;
            break;
        case 'evaluation_start':
            content = `Evaluatorが解答の検証を開始`;
            break;
        case 'round_complete':
            content = `ラウンド ${message.round} 完了`;
            break;
        case 'debate_end':
            content = `協調推論終了 - 最終回答: ${message.final_answer}`;
            break;
        case 'error':
            content = `エラー: ${message.message}`;
            break;
    }
    
    logEntry.innerHTML = `
        <div class="log-timestamp">${timestamp}</div>
        <div>${content}</div>
    `;
    
    debateLog.appendChild(logEntry);
    debateLog.scrollTop = debateLog.scrollHeight;
}

// Start debate
async function startDebate() {
    const question = questionInput.value.trim();
    if (!question) {
        alert('問題を入力してください');
        return;
    }
    
    try {
        const response = await fetch('/api/solve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question }),
        });
        
        const result = await response.json();
        
        if (result.error) {
            alert(`エラー: ${result.error}`);
            return;
        }
        
        updateStatus('running', '議論を開始しています...');
        
    } catch (error) {
        alert(`エラー: ${error.message}`);
    }
}

// Set example question
function setExample(button) {
    const question = button.getAttribute('data-question');
    questionInput.value = question;
}

// Handle Enter key in textarea
questionInput.addEventListener('keydown', function(event) {
    if (event.ctrlKey && event.key === 'Enter') {
        startDebate();
    }
});

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initWebSocket();
    updateStatus('waiting', '接続中...');
});

// Handle page visibility change to reconnect if needed
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && (!ws || ws.readyState === WebSocket.CLOSED)) {
        initWebSocket();
    }
});