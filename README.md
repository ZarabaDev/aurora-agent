# Aurora Agent

**Aurora** is a self-building, autonomous personal assistant designed to evolve and adapt. Inspired by projects like **AutoGPT**, **OpenClaw**, and **BabyAGI**, Aurora possesses the unique capability to not only decide which tools to use but also to *create* new tools on the fly when it encounters a problem it cannot solve with its existing capabilities.

## 🚀 Features

*   **Self-Building Capability**: Aurora can write its own Python tools to extend its functionality, effectively programming itself to solve new tasks.
*   **Dynamic Thinking Modes**: Switches between "Fast" (Groq/Llama) for quick tasks and "Deep" (OpenRouter/DeepSeek/Gemini) for complex reasoning.
*   **Autonomous Decision Making**: Determines the best approach to a problem, plans its actions, and executes them with minimal human intervention.
*   **Memory System**: Utilizes a vector database (ChromaDB) for long-term memory, allowing it to recall past interactions and learn from experience.
*   **Multi-Modal**: Capable of interacting via Terminal, and optionally integrated with Telegram.

## 🛠️ Installation

### Prerequisites

*   Python 3.10+
*   [Docker](https://www.docker.com/) (Optional, for containerized deployment)

### Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ZarabaDev/aurora-agent.git
    cd aurora-agent
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration:**
    Copy the example environment file and configure your API keys.
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and add your API keys (OpenAI, OpenRouter, Groq, etc.).

5.  **Run Aurora:**
    ```bash
    python main.py
    ```

### 🐳 Docker Setup

1.  **Build and Run with Docker Compose:**
    ```bash
    docker-compose up --build -d
    ```

2.  **View Logs:**
    ```bash
    docker-compose logs -f aurora_agent
    ```

## 🧠 How It Works

Aurora operates on a loop of **Perceive -> Think -> Act**.
1.  **Planner**: Breaks down user requests into actionable steps.
2.  **Critic**: Reviews the plan and selects the appropriate "Thinking Mode" (Fast vs. Deep).
3.  **Executor**: Runs the tools or writes new code.
4.  **Learner**: Stores successful outcomes in its vector memory for future reference.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
