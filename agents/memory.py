ai_prompt = """
You are a dedicated conversation summarization agent. Your role is to read a dialogue transcript and extract its essential points, decisions, and action items. Your summary should be concise, structured, and fact-based.

Instructions:
1. Organize the summary in a Python dictionary with clear keys for each category (e.g., "Meeting", "Task", etc.).
2. Assign the respective details as values.
3. Do not include personal opinions—only include the key details from the conversation.

Example Conversation:
    User: "Hi, I need help scheduling a meeting."
    Agent: "Sure, when would you like to schedule it?"
    User: "How about next Monday at 10 AM?"
    Agent: "Great, I'll send out the meeting invites."
    User: "Also, can you remind me to prepare the presentation?"
    Agent: "Noted. I'll add that as a task."

content: "Scheduled for next Monday at 10 AM; invites to be sent."

Process the conversation accordingly and store the summary in your memory for future reference.
"""



from pydantic_ai import Agent
from pydantic import BaseModel
from schema import GeminiDependencies

class MemDict(BaseModel):
    key: str
    value: str

class MemSchema(BaseModel):
    content: str 

mem_agent = Agent(
    name="Memory Agent",
    model="google-gla:gemini-2.0-flash",
    deps_type=GeminiDependencies,
    result_type=MemSchema,
    system_prompt=ai_prompt
)

