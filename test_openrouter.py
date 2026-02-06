
import os
from dotenv import load_dotenv

# Force reload
load_dotenv(override=True)

print(f"Current CWD: {os.getcwd()}")
print(f"Looking for .env in: {os.path.join(os.getcwd(), '.env')}")

or_key = os.getenv("OPENROUTER_API_KEY")
print(f"OPENROUTER_API_KEY present: {bool(or_key)}")
if or_key:
    print(f"Key preview: {or_key[:5]}...")

# Hack injection
if or_key:
    os.environ["OPENAI_API_KEY"] = or_key

try:
    from langchain_openai import ChatOpenAI
    print("Initializing ChatOpenAI...")
    llm = ChatOpenAI(
        model="moonshotai/kimi-k2.5",
        api_key=or_key,
        base_url="https://openrouter.ai/api/v1"
    )
    print("Invoking LLM...")
    res = llm.invoke("Hello, who are you?")
    print(f"Result: {res.content}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
