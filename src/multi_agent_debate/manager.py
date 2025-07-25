import asyncio
from typing import List, Optional
from autogen_core import SingleThreadedAgentRuntime, TypeSubscription, DefaultTopicId
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from .core import MathSolver, MathAggregator, Question, DebateCallback


class DebateManager:
    def __init__(self, azure_api_key: str, azure_endpoint: str, azure_deployment: str, model_name: str = "gpt-4o-mini", api_version: str = "2024-06-01", num_solvers: int = 4, max_rounds: int = 3):
        self.azure_api_key = azure_api_key
        self.azure_endpoint = azure_endpoint
        self.azure_deployment = azure_deployment
        self.model_name = model_name
        self.api_version = api_version
        self.num_solvers = num_solvers
        self.max_rounds = max_rounds
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
        
        # Register solver agents
        solver_names = [f"MathSolver{chr(65+i)}" for i in range(self.num_solvers)]  # A, B, C, D
        
        for solver_name in solver_names:
            await MathSolver.register(
                self.runtime,
                solver_name,
                lambda name=solver_name: MathSolver(
                    model_client=self.model_client,
                    topic_type=name,
                    num_neighbors=2,  # Each solver has 2 neighbors in ring topology
                    max_round=self.max_rounds,
                    callback=self.callback
                ),
            )
        
        # Register aggregator
        await MathAggregator.register(
            self.runtime, 
            "MathAggregator", 
            lambda: MathAggregator(num_solvers=self.num_solvers, callback=self.callback)
        )
        
        # Set up communication topology (ring structure)
        # A -> B -> C -> D -> A (each agent connects to 2 neighbors)
        for i in range(self.num_solvers):
            current_solver = solver_names[i]
            # Connect to next solver (circular)
            next_solver = solver_names[(i + 1) % self.num_solvers]
            # Connect to previous solver (circular)
            prev_solver = solver_names[(i - 1) % self.num_solvers]
            
            await self.runtime.add_subscription(TypeSubscription(current_solver, next_solver))
            await self.runtime.add_subscription(TypeSubscription(current_solver, prev_solver))
    
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