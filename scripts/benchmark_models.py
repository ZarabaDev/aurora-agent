
import os
import yaml
import glob
import argparse
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Load env variables
load_dotenv(override=True)

# Configuration
USER_MODELS = [
    "google/gemini-3-flash-preview",
    "deepseek/deepseek-v3.2"
]

SCENARIOS = {
    "DB Request": "Preciso da lista de users que não logaram na última semana. Consegue gerar a query pra mim?",
    "CSS Help": "Mano, tô apanhando pro CSS desse modal. Ele não centraliza nem a pau. Alguma dica rápida?",
    "Opinion": "O que você acha de eu reescrever isso tudo em Go? Tô meio de saco cheio de Python."
}

def load_system_prompt(soul_path):
    if not os.path.exists(soul_path):
        # Fallback to default path if not found directly
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_path = os.path.join(base_dir, "agent_core", "config", "soul.yaml")
        if os.path.exists(default_path) and soul_path == "default":
             soul_path = default_path
        else:
             # Try looking in agent_core/config/souls/
             potential_path = os.path.join(base_dir, "agent_core", "config", "souls", soul_path)
             if os.path.exists(potential_path):
                 soul_path = potential_path
             elif os.path.exists(potential_path + ".yaml"):
                 soul_path = potential_path + ".yaml"

    print(f"Loading soul from: {soul_path}")
    
    with open(soul_path, "r") as f:
        soul_config = yaml.safe_load(f)
    
    directives = "\n".join([f"- {d}" for d in soul_config['core_directives']])
    
    return f"""
    Você é {soul_config['name']}.
    Role: {soul_config['role']}
    Tom de voz: {soul_config['voice']['tone']}
    
    DIRETRIZES PRIMÁRIAS:
    {directives}
    """

def get_next_version_filename(base_name="benchmark_results_v"):
    # Find existing files matching the pattern
    files = glob.glob(f"{base_name}*.md")
    if not files:
        return f"{base_name}1.md"
    
    max_v = 0
    for f in files:
        try:
            # Extract number between 'v' and '.md'
            part = f.replace(base_name, "").replace(".md", "")
            num = int(part)
            if num > max_v:
                max_v = num
        except ValueError:
            continue
            
    return f"{base_name}{max_v + 1}.md"

def run_benchmark(soul_arg):
    try:
        system_prompt = load_system_prompt(soul_arg)
    except Exception as e:
        print(f"Error loading soul: {e}")
        return

    results = {}
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found.")
        return

    # Set env var for langchain compatibility
    os.environ["OPENAI_API_KEY"] = api_key

    print(f"Starting benchmark for {len(USER_MODELS)} models...")
    
    output_file = get_next_version_filename()
    print(f"Writing results to: {output_file}")

    with open(output_file, "w") as f:
        f.write("# Aurora Model Benchmark Results\n\n")
        f.write(f"**Soul Config**: `{soul_arg}`\n")
        f.write(f"**System Prompt Tone**: {system_prompt.split('Tom de voz: ')[1].splitlines()[0]}\n\n")

    for model in USER_MODELS:
        print(f"\nTesting model: {model}")
        try:
            llm = ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                openai_api_base="https://openrouter.ai/api/v1"
            )
            
            with open(output_file, "a") as f:
                f.write(f"## Model: `{model}`\n\n")
            
            for scenario_name, prompt in SCENARIOS.items():
                print(f"  - Scenario: {scenario_name}")
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=prompt)
                ]
                
                try:
                    response = llm.invoke(messages)
                    content = response.content.strip()
                except Exception as e:
                    content = f"**ERROR**: {str(e)}"
                    print(f"    Error in invocation: {e}")
                
                with open(output_file, "a") as f:
                    f.write(f"### {scenario_name}\n")
                    f.write(f"**Input**: {prompt}\n\n")
                    f.write(f"**Aurora**: {content}\n\n")
                    f.write("---\n")
                    
        except Exception as e:
            print(f"Failed to initialize {model}: {e}")
            with open(output_file, "a") as f:
                f.write(f"## Model: `{model}`\n\n")
                f.write(f"**Initialization Error**: {str(e)}\n\n")

    print(f"\nBenchmark completed. Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Aurora Benchmarks')
    parser.add_argument('--soul', type=str, default='default', help='Path or name of the soul config to use')
    args = parser.parse_args()
    
    run_benchmark(args.soul)
