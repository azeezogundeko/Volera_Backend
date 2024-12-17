from typing import Literal

class AgentClass:
    def __init__(self):
        # Initialize the list of agents with their configurations

        # Public attributes for different agent modes and nodes
        self.meta_agent = "comparison_agent"
        self.human_node = "human_node"
        self.policy_agent = "policy_agent"
        self.search_agent = "search_agent"
        self.shop_agent = "shop_agent"
        self.insights_agent = "insights_agent"
        self.reviewier_agent = "reviewer_agent"
        self.comparison_agent = "comparison_agent"


        self.reader_agent = "ReaderAgent"
        self.end = "END"

        # Modes
        self.shop_mode = "shop"
        self.budget_mode = "budget"
        self.review_mode = "reviews"
        self.analytics_mode = "analytics"
        self.scrape_mode = "scrape"
        self.normal_mode = "normal"
        self.insights_mode = "insights"
        self.recommendation_mode = "recommendation"
        self.comparison_mode = "comparison"

KnownModelName = Literal[
    'openai:gpt-4o',
    'openai:gpt-4o-mini',
    'openai:gpt-4-turbo',
    'openai:gpt-4',
    'openai:o1-preview',
    'openai:o1-mini',
    'openai:gpt-3.5-turbo',
    'groq:llama-3.3-70b-versatile',
    'groq:llama-3.1-70b-versatile',
    'groq:llama3-groq-70b-8192-tool-use-preview',
    'groq:llama3-groq-8b-8192-tool-use-preview',
    'groq:llama-3.1-70b-specdec',
    'groq:llama-3.1-8b-instant',
    'groq:llama-3.2-1b-preview',
    'groq:llama-3.2-3b-preview',
    'groq:llama-3.2-11b-vision-preview',
    'groq:llama-3.2-90b-vision-preview',
    'groq:llama3-70b-8192',
    'groq:llama3-8b-8192',
    'groq:mixtral-8x7b-32768',
    'groq:gemma2-9b-it',
    'groq:gemma-7b-it',
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'gemini-2.0-flash-exp',
    'vertexai:gemini-1.5-flash',
    'vertexai:gemini-1.5-pro',
    # since mistral models are supported by other providers (e.g. ollama), and some of their models (e.g. "codestral")
    # don't start with "mistral", we add the "mistral:" prefix to all to be explicit
    'mistral:mistral-small-latest',
    'mistral:mistral-large-latest',
    'mistral:codestral-latest',
    'mistral:mistral-moderation-latest',
    'ollama:codellama',
    'ollama:gemma',
    'ollama:gemma2',
    'ollama:llama3',
    'ollama:llama3.1',
    'ollama:llama3.2',
    'ollama:llama3.2-vision',
    'ollama:llama3.3',
    'ollama:mistral',
    'ollama:mistral-nemo',
    'ollama:mixtral',
    'ollama:phi3',
    'ollama:qwq',
    'ollama:qwen',
    'ollama:qwen2',
    'ollama:qwen2.5',
    'ollama:starcoder2',
    'claude-3-5-haiku-latest',
    'claude-3-5-sonnet-latest',
    'claude-3-opus-latest',
    'test',
]

agent_manager = AgentClass()
