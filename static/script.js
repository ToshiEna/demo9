// WebSocket connection
let ws = null;
let executionInProgress = false;

// DOM elements
const questionInput = document.getElementById('questionInput');
const solveButton = document.getElementById('solveButton');
const status = document.getElementById('status');
const currentQuestion = document.getElementById('currentQuestion');
const questionText = document.getElementById('questionText');
const finalResult = document.getElementById('finalResult');
const finalAnswer = document.getElementById('finalAnswer');
const debateLog = document.getElementById('debateLog');
const executionStatus = document.getElementById('executionStatus');
const currentStep = document.getElementById('currentStep');
const executionState = document.getElementById('executionState');

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
    if (id.includes('orchestrator')) {
        return 'Orchestrator (指揮者)';
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
        case 'debate_end':
            handleDebateEnd(message);
            break;
        case 'task_ledger_update':
            handleTaskLedgerUpdate(message);
            break;
        case 'progress_ledger_update':
            handleProgressLedgerUpdate(message);
            break;
        case 'task_delegation':
            handleTaskDelegation(message);
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
    executionInProgress = true;
    questionText.textContent = message.question;
    currentQuestion.style.display = 'block';
    finalResult.style.display = 'none';
    
    // Clear previous results
    clearAgentResponses();
    clearLedgers();
    updateExecutionStep('問題分析開始');
    
    // Reset all agents to waiting state
    document.querySelectorAll('.agent-card').forEach(card => {
        setAgentState(card, 'waiting');
    });
    
    solveButton.disabled = true;
    solveButton.textContent = '協調推論実行中...';
}

// Handle agent thinking
function handleAgentThinking(message) {
    const agentId = message.agent_id.toLowerCase();
    let agentElement = null;
    
    // Map agent IDs to HTML element IDs
    if (agentId.includes('orchestrator')) {
        agentElement = document.getElementById('agentOrchestrator');
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
    if (agentId.includes('orchestrator')) {
        agentElement = document.getElementById('agentOrchestrator');
        updateExecutionStep('Orchestrator による問題分析完了');
    } else if (agentId.includes('geometryexpert')) {
        agentElement = document.getElementById('agentGeometryExpert');
        updateExecutionStep('Geometry Expert による解答完了');
    } else if (agentId.includes('algebraexpert')) {
        agentElement = document.getElementById('agentAlgebraExpert');
        updateExecutionStep('Algebra Expert による解答完了');
    } else if (agentId.includes('evaluator')) {
        agentElement = document.getElementById('agentEvaluator');
        updateExecutionStep('Evaluator による検証完了');
    }
    
    if (agentElement) {
        // Set agent to active state
        setAgentState(agentElement, 'active');
        
        // Add response to agent card
        const responsesContainer = agentElement.querySelector('.agent-responses');
        const responseElement = document.createElement('div');
        responseElement.className = 'agent-response';
        
        responseElement.innerHTML = `
            <div class="response-content">${message.content}</div>
            <div class="response-answer">回答: ${message.answer}</div>
        `;
        
        responsesContainer.appendChild(responseElement);
        
        // After a delay, set agent to completed state
        setTimeout(() => {
            setAgentState(agentElement, 'completed');
        }, 2000);
    }
}

// Handle expert assignment
function handleExpertAssignment(message) {
    // Update status to show expert assignment
    updateStatus('running', `専門家を割り当て中: ${message.assigned_experts.join(', ')}`);
    updateExecutionStep('専門家への タスク割り当て完了');
    
    // Highlight assigned experts
    const allAgents = ['GeometryExpert', 'AlgebraExpert', 'Evaluator'];
    allAgents.forEach(agentName => {
        const element = document.getElementById(`agent${agentName}`);
        if (element) {
            if (message.assigned_experts.includes(agentName)) {
                element.classList.add('assigned');
                element.classList.add('expert-receiving');
                setTimeout(() => element.classList.remove('expert-receiving'), 3000);
            } else {
                element.classList.remove('assigned');
            }
        }
    });
}

// Handle task delegation (new function for visual flow)
function handleTaskDelegation(message) {
    console.log('Task delegation:', message);
    
    // Show Orchestrator is delegating
    const orchestratorElement = document.getElementById('agentOrchestrator');
    if (orchestratorElement) {
        orchestratorElement.classList.add('orchestrator-flow', 'delegating');
        setTimeout(() => {
            orchestratorElement.classList.remove('delegating');
        }, 3000);
    }
    
    // Show visual arrows to assigned experts
    message.to_agents.forEach((agentName, index) => {
        setTimeout(() => {
            showDelegationArrow(agentName);
            
            // Highlight receiving expert
            const expertElement = document.getElementById(`agent${agentName}`);
            if (expertElement) {
                expertElement.classList.add('expert-receiving');
                setTimeout(() => expertElement.classList.remove('expert-receiving'), 2000);
            }
        }, index * 500); // Stagger the arrows
    });
    
    updateExecutionStep(`タスク指示: ${message.to_agents.join(', ')}`);
}

// Show delegation arrow animation
function showDelegationArrow(targetAgent) {
    // This is a simplified version - in a real implementation you'd calculate positions
    const connectionLines = document.querySelectorAll('.connection-line');
    connectionLines.forEach((line, index) => {
        if (index < 3) { // We have 3 connection lines
            line.classList.add('active');
            setTimeout(() => line.classList.remove('active'), 2000);
        }
    });
}

// Handle evaluation start
function handleEvaluationStart(message) {
    updateStatus('running', '評価者が解答を検証中...');
    updateExecutionStep('Evaluator による検証開始');
    
    // Set Evaluator to thinking state
    const evaluatorElement = document.getElementById('agentEvaluator');
    if (evaluatorElement) {
        setAgentState(evaluatorElement, 'thinking');
    }
}

// Handle debate end
function handleDebateEnd(message) {
    updateStatus('completed', '協調推論完了！');
    updateExecutionStep('実行完了');
    executionInProgress = false;
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

// Handle Task Ledger updates
function handleTaskLedgerUpdate(message) {
    const taskLedger = message.task_ledger;
    
    // Animate ledger section
    const taskLedgerSection = document.querySelector('.ledger-section:first-child');
    taskLedgerSection.classList.add('updated');
    setTimeout(() => taskLedgerSection.classList.remove('updated'), 1000);
    
    // Update given facts
    updateLedgerList('givenFacts', taskLedger.given_facts);
    
    // Update facts to lookup
    updateLedgerList('factsToLookup', taskLedger.facts_to_lookup);
    
    // Update facts to derive
    updateLedgerList('factsToDerive', taskLedger.facts_to_derive);
    
    // Update educated guesses
    updateLedgerList('educatedGuesses', taskLedger.educated_guesses);
    
    // Update task plan (ordered list)
    updateLedgerList('taskPlan', taskLedger.task_plan);
}

// Handle Progress Ledger updates
function handleProgressLedgerUpdate(message) {
    const progressLedger = message.progress_ledger;
    
    // Animate ledger section
    const progressLedgerSection = document.querySelector('.ledger-section:last-child');
    progressLedgerSection.classList.add('updated');
    setTimeout(() => progressLedgerSection.classList.remove('updated'), 1000);
    
    // Update task completion status
    const taskCompleteElement = document.getElementById('taskComplete');
    taskCompleteElement.textContent = progressLedger.task_complete ? '完了' : '未完了';
    taskCompleteElement.className = progressLedger.task_complete ? 'status-indicator complete' : 'status-indicator';
    
    // Update progress being made
    const progressBeingMadeElement = document.getElementById('progressBeingMade');
    progressBeingMadeElement.textContent = progressLedger.progress_being_made ? '進行中' : '停滞中';
    progressBeingMadeElement.className = progressLedger.progress_being_made ? 'status-indicator progress' : 'status-indicator stalled';
    
    // Update stall count
    const stallCountElement = document.getElementById('stallCount');
    stallCountElement.textContent = progressLedger.stall_count;
    
    // Update next speaker
    const nextSpeakerElement = document.getElementById('nextSpeaker');
    nextSpeakerElement.textContent = progressLedger.next_speaker || '-';
    
    // Update next speaker instruction
    const instructionElement = document.getElementById('nextSpeakerInstruction');
    instructionElement.textContent = progressLedger.next_speaker_instruction || '-';
    
    // Update completed steps
    updateLedgerList('completedSteps', progressLedger.completed_steps);
}

// Helper function to update ledger lists
function updateLedgerList(elementId, items) {
    const listElement = document.getElementById(elementId);
    const currentItems = Array.from(listElement.children).map(li => li.textContent);
    
    // Clear existing items
    listElement.innerHTML = '';
    
    // Add all items
    items.forEach((item, index) => {
        const listItem = document.createElement('li');
        listItem.textContent = item;
        
        // Highlight new items
        if (!currentItems.includes(item)) {
            listItem.classList.add('new-item');
            setTimeout(() => listItem.classList.remove('new-item'), 2000);
        }
        
        listElement.appendChild(listItem);
    });
}

// Clear ledger displays
function clearLedgers() {
    // Clear Task Ledger
    document.getElementById('givenFacts').innerHTML = '';
    document.getElementById('factsToLookup').innerHTML = '';
    document.getElementById('factsToDerive').innerHTML = '';
    document.getElementById('educatedGuesses').innerHTML = '';
    document.getElementById('taskPlan').innerHTML = '';
    
    // Clear Progress Ledger
    document.getElementById('taskComplete').textContent = '未完了';
    document.getElementById('taskComplete').className = 'status-indicator';
    document.getElementById('progressBeingMade').textContent = '-';
    document.getElementById('progressBeingMade').className = 'status-indicator';
    document.getElementById('stallCount').textContent = '0';
    document.getElementById('nextSpeaker').textContent = '-';
    document.getElementById('nextSpeakerInstruction').textContent = '-';
    document.getElementById('completedSteps').innerHTML = '';
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

// Update execution step
function updateExecutionStep(step) {
    if (currentStep) {
        currentStep.textContent = step;
    }
    
    if (executionState) {
        if (executionInProgress) {
            executionState.textContent = '実行中';
            executionState.className = 'state-indicator running';
        } else {
            executionState.textContent = '完了';
            executionState.className = 'state-indicator completed';
        }
    }
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
            content = `${getFriendlyAgentName(message.agent_id)} が分析中...`;
            break;
        case 'agent_response':
            content = `${getFriendlyAgentName(message.agent_id)}: ${message.answer}`;
            break;
        case 'expert_assignment':
            content = `Orchestratorが専門家を割り当て: ${message.assigned_experts.join(', ')} - 理由: ${message.reasoning}`;
            break;
        case 'task_delegation':
            content = `Orchestratorが ${message.to_agents.join(', ')} にタスクを指示: ${message.instruction}`;
            break;
        case 'task_ledger_update':
            content = `Task Ledger更新: ${message.task_ledger.given_facts.length} 個の事実, ${message.task_ledger.task_plan.length} 個の計画ステップ`;
            break;
        case 'progress_ledger_update':
            content = `Progress Ledger更新: 完了=${message.progress_ledger.task_complete}, 次の担当者=${message.progress_ledger.next_speaker || 'なし'}`;
            break;
        case 'evaluation_start':
            content = 'Evaluatorが解答の検証を開始';
            break;
        case 'debate_end':
            content = `協調推論完了 - 最終回答: ${message.final_answer}`;
            break;
        case 'error':
            content = `エラー: ${message.message}`;
            break;
        default:
            content = JSON.stringify(message);
    }
    
    logEntry.innerHTML = `
        <div class="log-timestamp">${timestamp}</div>
        <div class="log-content">${content}</div>
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