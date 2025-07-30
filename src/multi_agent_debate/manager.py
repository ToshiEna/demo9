import asyncio
from typing import List, Optional
from autogen_core import SingleThreadedAgentRuntime, TypeSubscription, DefaultTopicId
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from .core import Orchestrator, GeometryExpert, AlgebraExpert, Evaluator, MathAggregator, Question, DebateCallback


class DebateManager:
    def __init__(self, azure_api_key: str, azure_endpoint: str, azure_deployment: str, model_name: str = "gpt-4o-mini", api_version: str = "2024-06-01"):
        self.azure_api_key = azure_api_key
        self.azure_endpoint = azure_endpoint
        self.azure_deployment = azure_deployment
        self.model_name = model_name
        self.api_version = api_version
        self.runtime = None
        self.model_client = None
        self.callback: Optional[DebateCallback] = None
        
    def set_callback(self, callback: DebateCallback):
        """Set callback for real-time updates"""
        self.callback = callback
        
    async def initialize(self):
        """Initialize the runtime and agents"""
        self.runtime = SingleThreadedAgentRuntime()
        self.model_client = AzureOpenAIChatCompletionClient(
            model=self.model_name,
            azure_endpoint=self.azure_endpoint,
            azure_deployment=self.azure_deployment,
            api_version=self.api_version,
            api_key=self.azure_api_key
        )
        
        # Register the new specialized agents
        await Orchestrator.register(
            self.runtime,
            "Orchestrator",
            lambda: Orchestrator(
                model_client=self.model_client,
                callback=self.callback
            ),
        )
        
        await GeometryExpert.register(
            self.runtime,
            "GeometryExpert", 
            lambda: GeometryExpert(
                model_client=self.model_client,
                callback=self.callback
            ),
        )
        
        await AlgebraExpert.register(
            self.runtime,
            "AlgebraExpert",
            lambda: AlgebraExpert(
                model_client=self.model_client,
                callback=self.callback
            ),
        )
        
        await Evaluator.register(
            self.runtime,
            "Evaluator",
            lambda: Evaluator(
                model_client=self.model_client,
                callback=self.callback
            ),
        )
        
        # Register aggregator
        await MathAggregator.register(
            self.runtime, 
            "MathAggregator", 
            lambda: MathAggregator(callback=self.callback)
        )
        
        # Set up communication topology for sequential workflow
        # MathAggregator -> Orchestrator -> GeometryExpert/AlgebraExpert -> Evaluator -> MathAggregator
        
        # All agents can receive messages from default topic
        await self.runtime.add_subscription(TypeSubscription("Question", "Orchestrator"))
        await self.runtime.add_subscription(TypeSubscription("ExpertAssignment", "GeometryExpert"))
        await self.runtime.add_subscription(TypeSubscription("ExpertAssignment", "AlgebraExpert"))
        await self.runtime.add_subscription(TypeSubscription("ExpertAssignment", "Evaluator"))
        await self.runtime.add_subscription(TypeSubscription("ExpertSolution", "Evaluator"))
        await self.runtime.add_subscription(TypeSubscription("ExpertSolution", "Orchestrator"))
        await self.runtime.add_subscription(TypeSubscription("Answer", "MathAggregator"))
    
    async def solve_problem(self, question: str) -> str:
        """Solve a math problem using multi-agent debate"""
        if not self.runtime:
            await self.initialize()
            
        # Start the runtime
        self.runtime.start()
        
        # Publish the question
        await self.runtime.publish_message(Question(content=question), DefaultTopicId())
        
        # Wait for completion
        await self.runtime.stop_when_idle()
        
        return "Debate completed"  # The actual answer is handled by callbacks
    
    async def cleanup(self):
        """Clean up resources"""
        if self.model_client:
            await self.model_client.close()
            
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()