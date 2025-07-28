import asyncio
import re
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


# Callback interface for real-time updates
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


@default_subscription
class MathSolver(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient, topic_type: str, role_type: str, num_neighbors: int, max_round: int, callback: DebateCallback = None) -> None:
        super().__init__(f"A {role_type} agent.")
        self._topic_type = topic_type
        self._role_type = role_type
        self._model_client = model_client
        self._num_neighbors = num_neighbors
        self._history: List[LLMMessage] = []
        self._buffer: Dict[int, List[IntermediateSolverResponse]] = {}
        
        # Define specialized roles based on M500 research framework
        role_definitions = {
            "ExpertRecruiter": {
                "name": "Expert Recruiter (専門家採用担当者)",
                "personality": "You are an Expert Recruiter who analyzes mathematical problems and coordinates the problem-solving process. You identify what types of mathematical expertise are needed and guide the collaborative reasoning process.",
                "task": "Analyze the given problem, identify the mathematical domains involved (geometry, algebra, arithmetic, etc.), and provide an initial solution approach while coordinating with domain experts."
            },
            "GeometryExpert": {
                "name": "Geometry Expert (幾何学専門家)", 
                "personality": "You are a Geometry Expert specialized in spatial reasoning, geometric shapes, measurements, and geometric problem solving. You excel at visualizing geometric relationships and applying geometric principles.",
                "task": "Focus on geometric aspects of the problem. Apply geometric principles, spatial reasoning, and measurement concepts to provide solutions."
            },
            "AlgebraExpert": {
                "name": "Algebra Expert (代数学専門家)",
                "personality": "You are an Algebra Expert specialized in algebraic thinking, equations, variables, and mathematical relationships. You excel at pattern recognition and algebraic manipulation.",
                "task": "Focus on algebraic aspects of the problem. Apply algebraic thinking, equation solving, and mathematical relationship analysis to provide solutions."
            },
            "Evaluator": {
                "name": "Evaluator (評価者)",
                "personality": "You are an Evaluator who verifies mathematical solutions and provides critical feedback. You check the accuracy and reasoning of solutions provided by other experts.",
                "task": "Evaluate the solutions provided by other experts, check for mathematical accuracy, identify potential errors, and provide constructive feedback to improve the solution quality."
            }
        }
        
        role_config = role_definitions.get(role_type, role_definitions["ExpertRecruiter"])
        personality = role_config["personality"]
        self._role_name = role_config["name"]
        self._role_task = role_config["task"]
        
        self._system_messages = [
            SystemMessage(
                content=(
                    f"{personality} "
                    f"{self._role_task} "
                    "Provide a clear and detailed solution within 150 words. "
                    "Your final answer should be a single numerical number, "
                    "in the form of {{answer}}, at the end of your response. "
                    "For example, 'The answer is {{42}}.' "
                    "When working with other experts, consider their domain expertise and build upon their insights."
                )
            )
        ]
        self._round = 0
        self._max_round = max_round
        self._callback = callback

    @property
    def role_name(self) -> str:
        """Get the human-readable role name"""
        return self._role_name

    @message_handler
    async def handle_request(self, message: SolverRequest, ctx: MessageContext) -> None:
        # Notify callback that agent is thinking
        if self._callback:
            self._callback.on_agent_thinking(self.id, self._round)
        
        # Simulate thinking time
        await asyncio.sleep(2)
        
        # Add the question to the memory.
        self._history.append(UserMessage(content=message.content, source="user"))
        # Make an inference using the model.
        model_result = await self._model_client.create(self._system_messages + self._history)
        assert isinstance(model_result.content, str)
        # Add the response to the memory.
        self._history.append(AssistantMessage(content=model_result.content, source=self.metadata["type"]))
        
        print(f"{'-'*80}\n{self._role_name} ({self.id}) round {self._round}:\n{model_result.content}")
        
        # Extract the answer from the response.
        match = re.search(r"\{\{(\-?\d+(\.\d+)?)\}\}", model_result.content)
        if match is None:
            raise ValueError("The model response does not contain the answer.")
        answer = match.group(1)
        
        # Notify callback
        if self._callback:
            self._callback.on_agent_response(self.id, self._round, model_result.content, answer)
        
        # Increment the counter.
        self._round += 1
        if self._round == self._max_round:
            # If the counter reaches the maximum round, publishes a final response.
            await self.publish_message(FinalSolverResponse(answer=answer), topic_id=DefaultTopicId())
        else:
            # Publish intermediate response to the topic associated with this solver.
            await self.publish_message(
                IntermediateSolverResponse(
                    content=model_result.content,
                    question=message.question,
                    answer=answer,
                    round=self._round,
                ),
                topic_id=DefaultTopicId(type=self._topic_type),
            )

    @message_handler
    async def handle_response(self, message: IntermediateSolverResponse, ctx: MessageContext) -> None:
        # Add neighbor's response to the buffer.
        self._buffer.setdefault(message.round, []).append(message)
        # Check if all neighbors have responded.
        if len(self._buffer[message.round]) == self._num_neighbors:
            print(
                f"{'-'*80}\n{self._role_name} ({self.id}) round {message.round}:\nReceived all responses from {self._num_neighbors} neighbors."
            )
            
            # Notify callback about round completion
            if self._callback:
                self._callback.on_round_complete(message.round)
            
            # Add delay to simulate deliberation between rounds
            await asyncio.sleep(1)
            
            # Prepare the prompt for the next question.
            prompt = f"As a {self._role_name}, review these solutions from other experts:\n"
            for i, resp in enumerate(self._buffer[message.round]):
                prompt += f"Expert {i+1} solution: {resp.content}\n"
            prompt += (
                f"Based on your expertise as a {self._role_name} and the solutions from other experts, "
                f"provide your analysis and solution to the problem. {self._role_task} "
                f"The original problem is: {message.question}. "
                "Consider the approaches shown by other experts and explain your reasoning from your specialized perspective. "
                "Your final answer should be a single numerical number, "
                "in the form of {{answer}}, at the end of your response."
            )
            # Send the question to the agent itself to solve.
            await self.send_message(SolverRequest(content=prompt, question=message.question), self.id)
            # Clear the buffer.
            self._buffer.pop(message.round)


@default_subscription
class MathAggregator(RoutedAgent):
    def __init__(self, num_solvers: int, callback: DebateCallback = None) -> None:
        super().__init__("Math Aggregator")
        self._num_solvers = num_solvers
        self._buffer: List[FinalSolverResponse] = []
        self._callback = callback

    @message_handler
    async def handle_question(self, message: Question, ctx: MessageContext) -> None:
        print(f"{'-'*80}\nAggregator {self.id} received question:\n{message.content}")
        
        # Notify callback about debate start
        if self._callback:
            self._callback.on_debate_start(message.content)
        
        prompt = (
            f"Can you solve the following math problem?\n{message.content}\n"
            "Explain your reasoning. Your final answer should be a single numerical number, "
            "in the form of {{answer}}, at the end of your response."
        )
        print(f"{'-'*80}\nAggregator {self.id} publishes initial solver request.")
        await self.publish_message(SolverRequest(content=prompt, question=message.content), topic_id=DefaultTopicId())

    @message_handler
    async def handle_final_solver_response(self, message: FinalSolverResponse, ctx: MessageContext) -> None:
        self._buffer.append(message)
        if len(self._buffer) == self._num_solvers:
            print(f"{'-'*80}\nAggregator {self.id} received all final answers from {self._num_solvers} solvers.")
            # Find the majority answer.
            answers = [resp.answer for resp in self._buffer]
            majority_answer = max(set(answers), key=answers.count)
            # Publish the aggregated response.
            await self.publish_message(Answer(content=majority_answer), topic_id=DefaultTopicId())
            # Clear the responses.
            self._buffer.clear()
            print(f"{'-'*80}\nAggregator {self.id} publishes final answer:\n{majority_answer}")
            
            # Notify callback about debate end
            if self._callback:
                self._callback.on_debate_end(majority_answer)