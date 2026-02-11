# Aurora Agent v5.0 🌌

**Aurora** is a self-building, autonomous personal assistant designed to evolve and adapt. In version **v5.0**, Aurora introduces a revolutionary **"Brain + Voice" cognitive architecture**, separating high-level reasoning from natural language generation.

## 🚀 New in v5.0

### 🧠 Brain + Voice Separation
Aurora now thinks like a human but speaks like a persona.
- **The Brain (Gemini 3)**: Analyzes complex problems, plans execution, and generates precise technical instructions.
- **The Voice (Groq/Llama)**: Translates those instructions into natural, empathetic, and persona-aligned speech. No more robotic "Task completed" messages.

### 🛡️ Resilient Memory System
Never loses context.
- **Primary**: Uses `OpenAI Embeddings` for high-quality semantic search.
- **Fallback**: Automatically switches to local `HuggingFace Embeddings` (CPU-optimized) if the API fails.
- **Vector Store**: Powered by ChromaDB (local).

### 🌙 Sleep & Consolidation Routine
Aurora learns while you sleep.
- **Interaction Logging**: Every thought, action, and result is logged to `data/logs/` (JSONL format).
- **Sleep Mode**: A nightly routine (`scripts/run_sleep.py`) analyzes the day's logs, extracts insights, and saves them to long-term memory.

---

## 🖥️ Aurora HUD // Neural Interface

Aurora features a **Sci-Fi / Retro-Futurism Web Interface** that visualizes the v5.0 cognitive process in real-time.

![Aurora HUD](aurora_hud_final_check.png)

The HUD displays:
*   🧠 **Neural Planner**: System 2 reasoning (Deep Thinking).
*   💭 **Thought Stream**: Internal monologue and critique.
*   ⚙️ **Tool Matrix**: Live tool execution status.
*   📡 **Output Terminal**: The synthesized voice response.

### Accessing the HUD
1.  **Start the Server**:
    ```bash
    python web_server.py
    ```
2.  **Open Browser**: Go to `http://localhost:5001`

---

## 🛠️ Installation

### Prerequisites
*   Python 3.10+
*   [Docker](https://www.docker.com/) (Optional)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ZarabaDev/aurora-agent.git
    cd aurora-agent
    ```

2.  **Install Dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    Copy `.env.example` to `.env` and configure your keys:
    ```bash
    cp .env.example .env
    ```
    Required keys: `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`.

4.  **Run Aurora:**
    ```bash
    python agent_core/main.py
    ```

---

## 🧠 Cognitive Architecture v5.0

Aurora operates on a sophisticated loop:

1.  **Perceive**: Logs user input and retrieves context from robust memory.
2.  **Gatekeeper**: Decides between **Fast Thinking** (Reflex) or **Deep Thinking** (Reasoning).
3.  **Think (System 2)**: Gemini 3 generates a multi-step plan and critiques it.
4.  **Act**: Executes tools (Python, Shell, Search) and validates results.
5.  **Synthesize**: The **Voice Module** transforms the technical outcome into natural speech.
6.  **Consolidate**: Periodically (during "sleep"), successful patterns are stored in long-term memory.

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
