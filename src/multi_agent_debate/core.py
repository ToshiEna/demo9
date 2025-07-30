import asyncio
import re
import urllib.parse
import urllib.request
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from autogen_core import (
    DefaultTopicId,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    TypeSubscription,
    default_subscription,
    message_handler,
)
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient


@dataclass
class Question:
    content: str


@dataclass
class Answer:
    content: str


@dataclass
class SolverRequest:
    content: str
    question: str


@dataclass
class IntermediateSolverResponse:
    content: str
    question: str
    answer: str
    round: int


@dataclass
class FinalSolverResponse:
    answer: str


@dataclass
class ExpertAssignment:
    """Message from Expert Recruiter to assign problem to specific experts"""
    question: str
    assigned_experts: List[str]  # List of expert names to solve the problem
    reasoning: str


@dataclass 
class ExpertSolution:
    """Solution from an assigned expert"""
    expert_name: str
    question: str
    solution: str
    answer: str


@dataclass
class EvaluationRequest:
    """Request for Evaluator to validate solutions"""
    question: str
    solutions: List[ExpertSolution]


@dataclass
class TaskLedger:
    """Task Ledger to track problem-solving state"""
    question: str
    given_facts: List[str] = field(default_factory=list)
    facts_to_lookup: List[str] = field(default_factory=list)
    facts_to_derive: List[str] = field(default_factory=list)
    educated_guesses: List[str] = field(default_factory=list)
    task_plan: List[str] = field(default_factory=list)
    
    def update_from_analysis(self, analysis_content: str):
        """Update ledger from orchestrator analysis"""
        # Extract information from analysis
        lines = analysis_content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("GIVEN_FACTS:"):
                current_section = "given_facts"
                fact = line.replace("GIVEN_FACTS:", "").strip()
                if fact:
                    self.given_facts.append(fact)
            elif line.startswith("FACTS_TO_LOOKUP:"):
                current_section = "facts_to_lookup"
                fact = line.replace("FACTS_TO_LOOKUP:", "").strip()
                if fact:
                    self.facts_to_lookup.append(fact)
            elif line.startswith("FACTS_TO_DERIVE:"):
                current_section = "facts_to_derive"
                fact = line.replace("FACTS_TO_DERIVE:", "").strip()
                if fact:
                    self.facts_to_derive.append(fact)
            elif line.startswith("EDUCATED_GUESSES:"):
                current_section = "educated_guesses"
                guess = line.replace("EDUCATED_GUESSES:", "").strip()
                if guess:
                    self.educated_guesses.append(guess)
            elif line.startswith("TASK_PLAN:"):
                current_section = "task_plan"
                plan = line.replace("TASK_PLAN:", "").strip()
                if plan:
                    self.task_plan.append(plan)
            elif line.startswith("- ") and current_section:
                item = line[2:].strip()
                if current_section == "given_facts":
                    self.given_facts.append(item)
                elif current_section == "facts_to_lookup":
                    self.facts_to_lookup.append(item)
                elif current_section == "facts_to_derive":
                    self.facts_to_derive.append(item)
                elif current_section == "educated_guesses":
                    self.educated_guesses.append(item)
                elif current_section == "task_plan":
                    self.task_plan.append(item)


@dataclass
class ProgressLedger:
    """Progress Ledger to monitor task execution"""
    task_complete: bool = False
    unproductive_loops: int = 0
    progress_being_made: bool = True
    next_speaker: Optional[str] = None
    next_speaker_instruction: str = ""
    stall_count: int = 0
    completed_steps: List[str] = field(default_factory=list)
    
    def update_progress(self, step_completed: str = None, progress_made: bool = True):
        """Update progress tracking"""
        if step_completed:
            self.completed_steps.append(step_completed)
        
        self.progress_being_made = progress_made
        
        if not progress_made:
            self.stall_count += 1
        else:
            self.stall_count = 0
    
    def check_stall(self) -> bool:
        """Check if we're in a stall condition"""
        return self.stall_count > 2 or not self.progress_being_made
    
    def set_next_action(self, speaker: str, instruction: str):
        """Set the next speaker and instruction"""
        self.next_speaker = speaker
        self.next_speaker_instruction = instruction


class DebateCallback:
    def on_agent_response(self, agent_id: str, round_num: int, content: str, answer: str):
        """Called when an agent provides a response"""
        pass
    
    def on_agent_thinking(self, agent_id: str, round_num: int):
        """Called when an agent starts thinking"""
        pass
    
    def on_debate_start(self, question: str):
        """Called when debate starts"""
        pass
    
    def on_debate_end(self, final_answer: str):
        """Called when debate ends"""
        pass
    
    def on_round_complete(self, round_num: int):
        """Called when a round is complete"""
        pass

    def on_expert_assignment(self, assigned_experts: List[str], reasoning: str):
        """Called when Expert Recruiter assigns experts"""
        pass
    
    def on_evaluation_start(self):
        """Called when Evaluator starts validation"""
        pass
    
    def on_task_ledger_update(self, task_ledger: TaskLedger):
        """Called when Task Ledger is updated"""
        pass
    
    def on_progress_ledger_update(self, progress_ledger: ProgressLedger):
        """Called when Progress Ledger is updated"""
        pass


async def simple_search(query: str, max_results: int = 3) -> str:
    """
    Simple web search function (mock implementation for now)
    In a real implementation, you would use a search API like Google Custom Search
    """
    # For now, return a mock search result that helps with mathematical problem categorization
    mock_results = {
        "geometry": [
            "Geometry problems often involve shapes, areas, perimeters, angles, and spatial relationships",
            "Key concepts: area calculation, volume, coordinate geometry, trigonometry",
            "Common types: area and perimeter problems, 3D geometry, coordinate plane problems"
        ],
        "algebra": [
            "Algebra problems involve equations, variables, mathematical relationships and patterns",
            "Key concepts: linear equations, systems of equations, polynomial operations, functions",
            "Common types: word problems with unknowns, equation solving, pattern recognition"
        ],
        "arithmetic": [
            "Arithmetic problems involve basic operations, fractions, percentages, and number relationships",
            "Key concepts: addition, subtraction, multiplication, division, ratios, proportions",
            "Common types: word problems with basic math, percentage calculations, ratio problems"
        ]
    }
    
    # Simple keyword matching to return relevant information
    query_lower = query.lower()
    results = []
    
    for category, info_list in mock_results.items():
        if any(keyword in query_lower for keyword in [category, "面積", "周囲", "図形", "正方形", "円", "三角形", "angle", "area", "perimeter", "shape"]):
            if category == "geometry":
                results.extend(info_list)
        elif any(keyword in query_lower for keyword in ["方程式", "未知数", "変数", "equation", "variable", "unknown", "solve for"]):
            if category == "algebra":
                results.extend(info_list)
        elif any(keyword in query_lower for keyword in ["計算", "合計", "total", "sum", "multiply", "divide", "percent"]):
            if category == "arithmetic":
                results.extend(info_list)
    
    if not results:
        results = ["This appears to be a general mathematical problem that may require multiple mathematical domains."]
    
    return "Search results:\n" + "\n".join(f"- {result}" for result in results[:max_results])


@default_subscription
class Orchestrator(RoutedAgent):
    """Orchestrator that manages Task Ledger and Progress Ledger to coordinate problem-solving"""
    
    def __init__(self, model_client: ChatCompletionClient, callback: DebateCallback = None) -> None:
        super().__init__("Orchestrator")
        self._model_client = model_client
        self._callback = callback
        self._task_ledger: Optional[TaskLedger] = None
        self._progress_ledger: Optional[ProgressLedger] = None
        
        self._system_messages = [
            SystemMessage(
                content=(
                    "You are an Orchestrator (指揮者) who manages the problem-solving process using Task Ledger and Progress Ledger. "
                    "Your job is to:\n"
                    "1. Create and update the Task Ledger with:\n"
                    "   - Given or verified facts from the problem\n"
                    "   - Facts that need to be looked up\n"
                    "   - Facts that need to be derived through computation or logic\n"
                    "   - Educated guesses for missing information\n"
                    "   - A clear task plan for solving the problem\n"
                    "2. Update the Progress Ledger to monitor:\n"
                    "   - Whether the task is complete\n"
                    "   - Detection of unproductive loops\n"
                    "   - Whether progress is being made\n"
                    "   - What the next speaker should be\n"
                    "   - Instructions for the next speaker\n"
                    "3. Analyze mathematical problems and decide which expert(s) should solve them\n"
                    "4. Coordinate the overall problem-solving workflow\n\n"
                    "Expert assignment guidelines:\n"
                    "- For problems involving shapes, areas, perimeters, angles, spatial relationships: assign GeometryExpert\n"
                    "- For problems involving equations, unknowns, variables, algebraic relationships: assign AlgebraExpert\n"
                    "- For complex problems requiring multiple domains: assign both experts\n"
                    "- For simple arithmetic: assign AlgebraExpert as default\n\n"
                    "Format your response with clear sections:\n"
                    "TASK_LEDGER_UPDATE:\n"
                    "GIVEN_FACTS: [list facts from the problem]\n"
                    "FACTS_TO_LOOKUP: [list facts that need research]\n"
                    "FACTS_TO_DERIVE: [list facts that need calculation/logic]\n"
                    "EDUCATED_GUESSES: [list reasonable assumptions]\n"
                    "TASK_PLAN: [list steps to solve the problem]\n\n"
                    "PROGRESS_ANALYSIS:\n"
                    "PROGRESS_MADE: [true/false]\n"
                    "NEXT_SPEAKER: [GeometryExpert|AlgebraExpert|both]\n"
                    "SPEAKER_INSTRUCTION: [specific instruction for the expert(s)]\n\n"
                    "ANALYSIS: [your analysis of the problem]\n"
                    "ASSIGNED_EXPERTS: [GeometryExpert|AlgebraExpert|both]\n"
                    "REASONING: [why you chose these experts]"
                )
            )
        ]

    @message_handler
    async def handle_question(self, message: Question, ctx: MessageContext) -> None:
        print(f"{'-'*80}\nOrchestrator analyzing problem and creating ledgers:\n{message.content}")
        
        # Initialize ledgers
        self._task_ledger = TaskLedger(question=message.content)
        self._progress_ledger = ProgressLedger()
        
        # Notify callback that agent is thinking
        if self._callback:
            self._callback.on_agent_thinking("Orchestrator", 0)
        
        # Perform web search to help with analysis
        search_results = await simple_search(message.content)
        
        # Prepare comprehensive prompt for ledger creation and expert assignment
        prompt = (
            f"Analyze this mathematical problem and create/update the Task Ledger and Progress Ledger:\n"
            f"Problem: {message.content}\n\n"
            f"Additional context from research:\n{search_results}\n\n"
            f"Create a comprehensive task ledger breakdown and determine which expert(s) should handle this problem."
        )
        
        # Get AI analysis with ledger updates
        history = [UserMessage(content=prompt, source="user")]
        model_result = await self._model_client.create(self._system_messages + history)
        assert isinstance(model_result.content, str)
        
        print(f"Orchestrator analysis:\n{model_result.content}")
        
        # Update Task Ledger from analysis
        self._task_ledger.update_from_analysis(model_result.content)
        
        # Parse progress analysis
        progress_made = True
        next_speaker = ""
        speaker_instruction = ""
        
        lines = model_result.content.split('\n')
        for line in lines:
            if line.startswith("PROGRESS_MADE:"):
                progress_made = "true" in line.lower()
            elif line.startswith("NEXT_SPEAKER:"):
                next_speaker = line.replace("NEXT_SPEAKER:", "").strip()
            elif line.startswith("SPEAKER_INSTRUCTION:"):
                speaker_instruction = line.replace("SPEAKER_INSTRUCTION:", "").strip()
        
        # Update Progress Ledger
        self._progress_ledger.update_progress("Problem analyzed and ledgers created", progress_made)
        self._progress_ledger.set_next_action(next_speaker, speaker_instruction)
        
        # Parse the expert assignment
        assigned_experts = []
        reasoning = ""
        
        for line in lines:
            if line.startswith("ASSIGNED_EXPERTS:"):
                expert_text = line.replace("ASSIGNED_EXPERTS:", "").strip()
                if "both" in expert_text.lower():
                    assigned_experts = ["GeometryExpert", "AlgebraExpert"]
                elif "GeometryExpert" in expert_text:
                    assigned_experts = ["GeometryExpert"]
                elif "AlgebraExpert" in expert_text:
                    assigned_experts = ["AlgebraExpert"] 
                else:
                    assigned_experts = ["AlgebraExpert"]  # Default
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
        
        if not assigned_experts:
            assigned_experts = ["AlgebraExpert"]  # Safe default
        
        if not reasoning:
            reasoning = "General mathematical problem requiring expert analysis."

        # Notify callback about ledger updates
        if self._callback:
            self._callback.on_task_ledger_update(self._task_ledger)
            self._callback.on_progress_ledger_update(self._progress_ledger)
            self._callback.on_expert_assignment(assigned_experts, reasoning)
            self._callback.on_agent_response("Orchestrator", 0, model_result.content, f"Assigned: {', '.join(assigned_experts)}")
        
        # Send assignment to experts
        assignment = ExpertAssignment(
            question=message.content,
            assigned_experts=assigned_experts,
            reasoning=reasoning
        )
        
        await self.publish_message(assignment, topic_id=DefaultTopicId())

    @message_handler
    async def handle_expert_solution(self, message: ExpertSolution, ctx: MessageContext) -> None:
        """Monitor expert solutions and update progress ledger"""
        if self._progress_ledger:
            step_completed = f"{message.expert_name} provided solution"
            self._progress_ledger.update_progress(step_completed, True)
            
            # Check if we should continue or wrap up
            if self._progress_ledger.check_stall():
                self._progress_ledger.set_next_action("Evaluator", "Validate available solutions due to stall detection")
            else:
                self._progress_ledger.set_next_action("Evaluator", "Validate expert solutions")
            
            # Notify callback of progress update
            if self._callback:
                self._callback.on_progress_ledger_update(self._progress_ledger)


@default_subscription  
class GeometryExpert(RoutedAgent):
    """Geometry Expert specialized in spatial reasoning and geometric problems"""
    
    def __init__(self, model_client: ChatCompletionClient, callback: DebateCallback = None) -> None:
        super().__init__("Geometry Expert")
        self._model_client = model_client
        self._callback = callback
        
        self._system_messages = [
            SystemMessage(
                content=(
                    "You are a Geometry Expert (幾何学専門家) specialized in spatial reasoning, geometric shapes, measurements, and geometric problem solving. "
                    "You excel at visualizing geometric relationships and applying geometric principles. "
                    "Focus on geometric aspects of problems: shapes, areas, perimeters, volumes, angles, coordinates, and spatial relationships. "
                    "Apply geometric principles, spatial reasoning, and measurement concepts to provide clear solutions. "
                    "Your final answer should be a single numerical number in the form of {{answer}}, at the end of your response."
                )
            )
        ]

    @message_handler
    async def handle_assignment(self, message: ExpertAssignment, ctx: MessageContext) -> None:
        if "GeometryExpert" not in message.assigned_experts:
            return  # Not assigned to this problem
            
        print(f"{'-'*80}\nGeometry Expert solving problem:\n{message.question}")
        
        # Notify callback that agent is thinking
        if self._callback:
            self._callback.on_agent_thinking("GeometryExpert", 1)
        
        prompt = (
            f"As a Geometry Expert, solve this mathematical problem using geometric principles:\n"
            f"Problem: {message.question}\n"
            f"Assignment reasoning: {message.reasoning}\n\n"
            f"Focus on the geometric aspects and provide a clear solution with geometric reasoning."
        )
        
        history = [UserMessage(content=prompt, source="user")]
        model_result = await self._model_client.create(self._system_messages + history)
        assert isinstance(model_result.content, str)
        
        print(f"Geometry Expert solution:\n{model_result.content}")
        
        # Extract answer
        match = re.search(r"\{\{(\-?\d+(\.\d+)?)\}\}", model_result.content)
        answer = match.group(1) if match else "No answer found"
        
        # Notify callback
        if self._callback:
            self._callback.on_agent_response("GeometryExpert", 1, model_result.content, answer)
        
        # Send solution
        solution = ExpertSolution(
            expert_name="GeometryExpert",
            question=message.question,
            solution=model_result.content,
            answer=answer
        )
        
        await self.publish_message(solution, topic_id=DefaultTopicId())


@default_subscription
class AlgebraExpert(RoutedAgent):
    """Algebra Expert specialized in algebraic thinking and problem solving"""
    
    def __init__(self, model_client: ChatCompletionClient, callback: DebateCallback = None) -> None:
        super().__init__("Algebra Expert")
        self._model_client = model_client
        self._callback = callback
        
        self._system_messages = [
            SystemMessage(
                content=(
                    "You are an Algebra Expert (代数学専門家) specialized in algebraic thinking, equations, variables, and mathematical relationships. "
                    "You excel at pattern recognition, algebraic manipulation, and solving equations. "
                    "Focus on algebraic aspects of problems: equations, unknowns, variables, mathematical relationships, patterns, and systematic problem solving. "
                    "Apply algebraic thinking, equation solving, and mathematical relationship analysis to provide clear solutions. "
                    "Your final answer should be a single numerical number in the form of {{answer}}, at the end of your response."
                )
            )
        ]

    @message_handler  
    async def handle_assignment(self, message: ExpertAssignment, ctx: MessageContext) -> None:
        if "AlgebraExpert" not in message.assigned_experts:
            return  # Not assigned to this problem
            
        print(f"{'-'*80}\nAlgebra Expert solving problem:\n{message.question}")
        
        # Notify callback that agent is thinking  
        if self._callback:
            self._callback.on_agent_thinking("AlgebraExpert", 1)
        
        prompt = (
            f"As an Algebra Expert, solve this mathematical problem using algebraic methods:\n"
            f"Problem: {message.question}\n"
            f"Assignment reasoning: {message.reasoning}\n\n"
            f"Focus on the algebraic aspects and provide a clear solution with algebraic reasoning."
        )
        
        history = [UserMessage(content=prompt, source="user")]
        model_result = await self._model_client.create(self._system_messages + history)
        assert isinstance(model_result.content, str)
        
        print(f"Algebra Expert solution:\n{model_result.content}")
        
        # Extract answer
        match = re.search(r"\{\{(\-?\d+(\.\d+)?)\}\}", model_result.content)
        answer = match.group(1) if match else "No answer found"
        
        # Notify callback
        if self._callback:
            self._callback.on_agent_response("AlgebraExpert", 1, model_result.content, answer)
        
        # Send solution
        solution = ExpertSolution(
            expert_name="AlgebraExpert", 
            question=message.question,
            solution=model_result.content,
            answer=answer
        )
        
        await self.publish_message(solution, topic_id=DefaultTopicId())


@default_subscription
class Evaluator(RoutedAgent):
    """Evaluator that validates solutions from experts and determines task completion"""
    
    def __init__(self, model_client: ChatCompletionClient, callback: DebateCallback = None) -> None:
        super().__init__("Evaluator")
        self._model_client = model_client
        self._callback = callback
        self._solutions_buffer: List[ExpertSolution] = []
        self._expected_experts: List[str] = []
        self._current_question = ""
        self._progress_ledger: Optional[ProgressLedger] = None
        
        self._system_messages = [
            SystemMessage(
                content=(
                    "You are an Evaluator (評価者) who verifies mathematical solutions and determines task completion. "
                    "Your job is to check the accuracy and reasoning of solutions provided by expert agents. "
                    "Evaluate each solution for:\n"
                    "1. Mathematical accuracy - are the calculations correct?\n"
                    "2. Logical reasoning - does the approach make sense?\n"
                    "3. Completeness - is the solution thorough?\n"
                    "4. Consistency - do multiple solutions agree?\n\n"
                    "You also help determine if the task is complete by checking:\n"
                    "- Are all required solutions provided?\n"
                    "- Are the solutions accurate and consistent?\n"
                    "- Can a final answer be confidently provided?\n\n"
                    "Provide a final validated answer and explain your evaluation process. "
                    "Your final answer should be a single numerical number in the form of {{answer}}, at the end of your response."
                )
            )
        ]

    @message_handler
    async def handle_assignment(self, message: ExpertAssignment, ctx: MessageContext) -> None:
        # Track which experts are expected to respond
        self._expected_experts = message.assigned_experts.copy()
        self._current_question = message.question
        self._solutions_buffer.clear()
        
        # Initialize progress tracking for evaluation phase
        self._progress_ledger = ProgressLedger()
        self._progress_ledger.set_next_action("Experts", f"Waiting for solutions from: {', '.join(self._expected_experts)}")
        
        print(f"{'-'*80}\nEvaluator waiting for solutions from: {', '.join(self._expected_experts)}")

    @message_handler
    async def handle_solution(self, message: ExpertSolution, ctx: MessageContext) -> None:
        if message.expert_name in self._expected_experts:
            self._solutions_buffer.append(message)
            print(f"Evaluator received solution from {message.expert_name}")
            
            # Update progress
            if self._progress_ledger:
                step = f"Received solution from {message.expert_name}"
                self._progress_ledger.update_progress(step, True)
            
            # Check if all expected solutions received
            received_experts = [sol.expert_name for sol in self._solutions_buffer]
            if set(received_experts) == set(self._expected_experts):
                await self._evaluate_solutions()

    async def _evaluate_solutions(self):
        print(f"{'-'*80}\nEvaluator evaluating {len(self._solutions_buffer)} solutions")
        
        # Notify callback that evaluation is starting
        if self._callback:
            self._callback.on_evaluation_start()
            self._callback.on_agent_thinking("Evaluator", 2)
        
        # Update progress ledger for evaluation start
        if self._progress_ledger:
            self._progress_ledger.update_progress("Starting solution evaluation", True)
            self._progress_ledger.set_next_action("Evaluator", "Validating expert solutions")
            if self._callback:
                self._callback.on_progress_ledger_update(self._progress_ledger)
        
        # Prepare evaluation prompt
        solutions_text = ""
        for i, solution in enumerate(self._solutions_buffer, 1):
            solutions_text += f"\nSolution {i} from {solution.expert_name}:\n{solution.solution}\nAnswer: {solution.answer}\n"
        
        prompt = (
            f"Evaluate these expert solutions for the problem:\n"
            f"Problem: {self._current_question}\n"
            f"Expert Solutions:{solutions_text}\n\n"
            f"Provide your evaluation of each solution and determine the final validated answer. "
            f"Check mathematical accuracy, reasoning quality, and consistency between solutions. "
            f"Also determine if the task is now complete based on the quality and consistency of solutions."
        )
        
        history = [UserMessage(content=prompt, source="user")]
        model_result = await self._model_client.create(self._system_messages + history)
        assert isinstance(model_result.content, str)
        
        print(f"Evaluator validation:\n{model_result.content}")
        
        # Extract final validated answer
        match = re.search(r"\{\{(\-?\d+(\.\d+)?)\}\}", model_result.content)
        final_answer = match.group(1) if match else "Evaluation incomplete"
        
        # Update progress ledger - task completion
        if self._progress_ledger:
            self._progress_ledger.task_complete = True
            self._progress_ledger.update_progress("Task completed with validated answer", True)
            self._progress_ledger.set_next_action("Complete", "Final answer provided")
            if self._callback:
                self._callback.on_progress_ledger_update(self._progress_ledger)
        
        # Notify callback
        if self._callback:
            self._callback.on_agent_response("Evaluator", 2, model_result.content, final_answer)
            self._callback.on_debate_end(final_answer)
        
        # Publish final answer
        await self.publish_message(Answer(content=final_answer), topic_id=DefaultTopicId())


@default_subscription
class MathAggregator(RoutedAgent):
    def __init__(self, callback: DebateCallback = None) -> None:
        super().__init__("Math Aggregator")
        self._callback = callback

    @message_handler
    async def handle_question(self, message: Question, ctx: MessageContext) -> None:
        print(f"{'-'*80}\nAggregator {self.id} received question:\n{message.content}")
        
        # Notify callback about debate start
        if self._callback:
            self._callback.on_debate_start(message.content)
        
        print(f"{'-'*80}\nAggregator {self.id} forwards question to Orchestrator.")
        # Forward question directly to Orchestrator instead of broadcasting
        await self.publish_message(message, topic_id=DefaultTopicId())

    @message_handler
    async def handle_final_answer(self, message: Answer, ctx: MessageContext) -> None:
        print(f"{'-'*80}\nAggregator {self.id} received final validated answer: {message.content}")
        # The final answer is already handled by the Evaluator's callback
        # No additional processing needed here