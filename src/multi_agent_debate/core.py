import asyncio
import re
import urllib.parse
import urllib.request
import json
from dataclasses import dataclass
from typing import Dict, List

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
class ExpertRecruiter(RoutedAgent):
    """Expert Recruiter that analyzes problems and assigns them to appropriate experts"""
    
    def __init__(self, model_client: ChatCompletionClient, callback: DebateCallback = None) -> None:
        super().__init__("Expert Recruiter")
        self._model_client = model_client
        self._callback = callback
        
        self._system_messages = [
            SystemMessage(
                content=(
                    "You are an Expert Recruiter (専門家採用担当者) who analyzes mathematical problems and coordinates the problem-solving process. "
                    "Your job is to:\n"
                    "1. Analyze the given mathematical problem\n"
                    "2. Identify what types of mathematical expertise are needed (geometry, algebra, both, or general arithmetic)\n"
                    "3. Decide which expert(s) should solve the problem: GeometryExpert, AlgebraExpert, or both\n"
                    "4. Provide reasoning for your decision\n\n"
                    "Guidelines:\n"
                    "- For problems involving shapes, areas, perimeters, angles, spatial relationships: assign GeometryExpert\n"
                    "- For problems involving equations, unknowns, variables, algebraic relationships: assign AlgebraExpert\n"
                    "- For complex problems requiring multiple domains: assign both experts\n"
                    "- For simple arithmetic: assign AlgebraExpert as default\n\n"
                    "Respond with your analysis and assignment decision. Format your response as:\n"
                    "ANALYSIS: [your analysis of the problem]\n"
                    "ASSIGNED_EXPERTS: [GeometryExpert|AlgebraExpert|both]\n"
                    "REASONING: [why you chose these experts]"
                )
            )
        ]

    @message_handler
    async def handle_question(self, message: Question, ctx: MessageContext) -> None:
        print(f"{'-'*80}\nExpert Recruiter analyzing problem:\n{message.content}")
        
        # Notify callback that agent is thinking
        if self._callback:
            self._callback.on_agent_thinking("ExpertRecruiter", 0)
        
        # Perform web search to help with analysis
        search_results = await simple_search(message.content)
        
        # Prepare prompt with search results
        prompt = (
            f"Analyze this mathematical problem and decide which expert(s) should solve it:\n"
            f"Problem: {message.content}\n\n"
            f"Additional context from research:\n{search_results}\n\n"
            f"Based on your analysis, which expert(s) should handle this problem?"
        )
        
        # Add the question to history and get AI analysis
        history = [UserMessage(content=prompt, source="user")]
        model_result = await self._model_client.create(self._system_messages + history)
        assert isinstance(model_result.content, str)
        
        print(f"Expert Recruiter analysis:\n{model_result.content}")
        
        # Parse the response to extract assigned experts
        assigned_experts = []
        reasoning = ""
        
        lines = model_result.content.split('\n')
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

        # Notify callback about expert assignment
        if self._callback:
            self._callback.on_expert_assignment(assigned_experts, reasoning)
            self._callback.on_agent_response("ExpertRecruiter", 0, model_result.content, f"Assigned: {', '.join(assigned_experts)}")
        
        # Send assignment to experts
        assignment = ExpertAssignment(
            question=message.content,
            assigned_experts=assigned_experts,
            reasoning=reasoning
        )
        
        await self.publish_message(assignment, topic_id=DefaultTopicId())


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
    """Evaluator that validates solutions from experts"""
    
    def __init__(self, model_client: ChatCompletionClient, callback: DebateCallback = None) -> None:
        super().__init__("Evaluator")
        self._model_client = model_client
        self._callback = callback
        self._solutions_buffer: List[ExpertSolution] = []
        self._expected_experts: List[str] = []
        self._current_question = ""
        
        self._system_messages = [
            SystemMessage(
                content=(
                    "You are an Evaluator (評価者) who verifies mathematical solutions and provides critical feedback. "
                    "Your job is to check the accuracy and reasoning of solutions provided by expert agents. "
                    "Evaluate each solution for:\n"
                    "1. Mathematical accuracy - are the calculations correct?\n"
                    "2. Logical reasoning - does the approach make sense?\n"
                    "3. Completeness - is the solution thorough?\n"
                    "4. Consistency - do multiple solutions agree?\n\n"
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
        print(f"{'-'*80}\nEvaluator waiting for solutions from: {', '.join(self._expected_experts)}")

    @message_handler
    async def handle_solution(self, message: ExpertSolution, ctx: MessageContext) -> None:
        if message.expert_name in self._expected_experts:
            self._solutions_buffer.append(message)
            print(f"Evaluator received solution from {message.expert_name}")
            
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
        
        # Prepare evaluation prompt
        solutions_text = ""
        for i, solution in enumerate(self._solutions_buffer, 1):
            solutions_text += f"\nSolution {i} from {solution.expert_name}:\n{solution.solution}\nAnswer: {solution.answer}\n"
        
        prompt = (
            f"Evaluate these expert solutions for the problem:\n"
            f"Problem: {self._current_question}\n"
            f"Expert Solutions:{solutions_text}\n\n"
            f"Provide your evaluation of each solution and determine the final validated answer. "
            f"Check mathematical accuracy, reasoning quality, and consistency between solutions."
        )
        
        history = [UserMessage(content=prompt, source="user")]
        model_result = await self._model_client.create(self._system_messages + history)
        assert isinstance(model_result.content, str)
        
        print(f"Evaluator validation:\n{model_result.content}")
        
        # Extract final validated answer
        match = re.search(r"\{\{(\-?\d+(\.\d+)?)\}\}", model_result.content)
        final_answer = match.group(1) if match else "Evaluation incomplete"
        
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
        
        print(f"{'-'*80}\nAggregator {self.id} forwards question to Expert Recruiter.")
        # Forward question directly to Expert Recruiter instead of broadcasting
        await self.publish_message(message, topic_id=DefaultTopicId())

    @message_handler
    async def handle_final_answer(self, message: Answer, ctx: MessageContext) -> None:
        print(f"{'-'*80}\nAggregator {self.id} received final validated answer: {message.content}")
        # The final answer is already handled by the Evaluator's callback
        # No additional processing needed here