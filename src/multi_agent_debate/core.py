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
    def __init__(self, model_client: ChatCompletionClient, topic_type: str, num_neighbors: int, max_round: int, callback: DebateCallback = None) -> None:
        super().__init__("A debator.")
        self._topic_type = topic_type
        self._model_client = model_client
        self._num_neighbors = num_neighbors
        self._history: List[LLMMessage] = []
        self._buffer: Dict[int, List[IntermediateSolverResponse]] = {}
        # Create diverse system messages for different agents
        agent_personalities = [
            "You are a methodical assistant who loves to break down problems step by step. You approach math problems systematically and show all your work clearly.",
            "You are a creative assistant who likes to find alternative approaches to math problems. You often think outside the box and consider multiple solution paths.",
            "You are a detail-oriented assistant who focuses on precision and accuracy. You double-check your work and explain your reasoning thoroughly.",
            "You are an intuitive assistant who can quickly identify patterns and shortcuts. You balance speed with accuracy in your mathematical reasoning."
        ]
        
        personality = agent_personalities[ord(topic_type[-1]) - ord('A')] if topic_type.endswith(('A', 'B', 'C', 'D')) else agent_personalities[0]
        
        self._system_messages = [
            SystemMessage(
                content=(
                    f"{personality} "
                    "Your task is to assist in solving a math reasoning problem by providing "
                    "a clear and detailed solution. Limit your output within 100 words, "
                    "and your final answer should be a single numerical number, "
                    "in the form of {{answer}}, at the end of your response. "
                    "For example, 'The answer is {{42}}.'"
                )
            )
        ]
        self._round = 0
        self._max_round = max_round
        self._callback = callback

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
        
        print(f"{'-'*80}\nSolver {self.id} round {self._round}:\n{model_result.content}")
        
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
                f"{'-'*80}\nSolver {self.id} round {message.round}:\nReceived all responses from {self._num_neighbors} neighbors."
            )
            
            # Notify callback about round completion
            if self._callback:
                self._callback.on_round_complete(message.round)
            
            # Add delay to simulate deliberation between rounds
            await asyncio.sleep(1)
            
            # Prepare the prompt for the next question.
            prompt = "These are the solutions to the problem from other agents:\n"
            for i, resp in enumerate(self._buffer[message.round]):
                prompt += f"Agent {i+1} solution: {resp.content}\n"
            prompt += (
                "Using the solutions from other agents as additional information, "
                "can you provide your answer to the math problem? "
                f"The original math problem is {message.question}. "
                "Consider if there are different approaches shown by other agents and explain your reasoning. "
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