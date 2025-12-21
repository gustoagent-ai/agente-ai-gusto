import os
from dotenv import load_dotenv
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from prompt import SYSTEM_PROMPT
from observability import setup_observability
from knowledge_base import MENU_INFO

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
def needs_menu_info(user_input: str) -> bool:
    keywords = [
        "menu", "menú", "informacion", "información", "precio", "plan", "semana",
        "mensual", "comidas", "despacho", "zona", "pagar", "transferencia"
    ]
    user_input = user_input.lower()
    return any(word in user_input for word in keywords)


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


