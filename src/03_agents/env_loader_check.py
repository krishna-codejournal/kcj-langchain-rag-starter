import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

print("CWD:", Path.cwd())
print("File:", Path(__file__).resolve())
print("ENV_PATH:", ENV_PATH, "exists?", ENV_PATH.exists())

loaded = load_dotenv(ENV_PATH, override=True)
print("load_dotenv returned:", loaded)

print(os.getenv("OPENAI_API_KEY"))

def show(name: str):
    v = os.getenv(name)
    print(f"{name}: {'SET' if v else 'MISSING'}")

show("TAVILY_API_KEY")
show("LANGCHAIN_API_KEY")
show("LANGSMITH_API_KEY")
show("OPENAI_API_KEY")
