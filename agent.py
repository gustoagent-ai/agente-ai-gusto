import os
from dotenv import load_dotenv
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from prompt import SYSTEM_PROMPT
from observability import setup_observability

load_dotenv()
setup_observability()

model_settings = ModelSettings(
    max_tokens=5000
)


model = OpenAIChatModel(
    model_name=os.getenv("MODEL", "anthropic/claude-haiku-4.5"),
    provider="openrouter"
)

agent = Agent(
    model,
    system_prompt=SYSTEM_PROMPT,
    instrument=True,
    model_settings=model_settings
)


@agent.tool_plain
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together and return the result."""
    return a + b


async def main():
    print("AI Assistant - Type 'exit' to quit\n")

    conversation_history = []

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if not user_input:
            continue

        result = await agent.run(user_input,message_history=conversation_history[:-10])

        conversation_history = result.all_messages()

        print(f"Assistant: {result.output}\n")

async def run_agent(prompt: str) -> str:
    """
    Ejecuta el agente IA con un prompt y retorna solo el texto de salida.
    """
    result = await agent.run(prompt)
    return result.output

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

