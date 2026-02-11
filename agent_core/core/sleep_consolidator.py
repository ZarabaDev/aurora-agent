"""
SleepConsolidator — Overnight memory consolidation routine.

Reads the previous day's interaction logs, analyzes them via LLM,
extracts important insights, and saves them to long-term memory.
Like human sleep, this process consolidates daily experiences into
lasting knowledge.
"""

import json
from datetime import datetime, timedelta

from agent_core.core.interaction_logger import InteractionLogger
from agent_core.core.memory import MemoryManager
from agent_core.utils.llm_factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate


CONSOLIDATION_PROMPT = """Você é o módulo de consolidação de memória da Aurora.
Sua tarefa é analisar o dia e decidir o que vale a pena guardar na memória de longo prazo.

Diferente de um simples resumo, você deve focar no "monólogo interno" (pensamentos) da Aurora. 
Os pensamentos revelam a intenção, as dúvidas e as críticas que ela teve durante as tarefas.

[LOGS DO DIA]
{logs}

[TAREFA DE CONSOLIDAÇÃO]
1. Analise o que Aurora estava PENSANDO e o que ela FEZ.
2. Identifique fatos novos sobre o usuário ou projetos.
3. Extraia lições aprendidas (o que funcionou, o que "bugou", o que ela criticou em seu próprio pensamento).
4. Decida o que deve ser adicionado à memória para que ela não esqueça amanhã.

[FORMATO DE SAÍDA - JSON APENAS]
{{
    "insights": [
        {{
            "type": "preference" | "error" | "solution" | "fact" | "self_improvement",
            "content": "Descrição clara e específica do aprendizado",
            "importance": "low" | "medium" | "high" | "critical"
        }}
    ],
    "summary": "Um breve comentário sobre como foi o dia de hoje do ponto de vista da sua evolução."
}}"""


class SleepConsolidator:
    """Analyzes daily logs and consolidates important memories."""

    MIN_IMPORTANCE = "medium"  # Only save medium+ importance
    IMPORTANCE_LEVELS = ["low", "medium", "high", "critical"]

    def __init__(self):
        self.logger = InteractionLogger()
        self.memory = MemoryManager()
        self.llm = LLMFactory.get_default_model()

    def consolidate(self, date_str: str = None) -> dict:
        """
        Run the consolidation for a given date.

        Args:
            date_str: Date in YYYY-MM-DD format.
                      Defaults to yesterday.

        Returns:
            Dict with consolidation results.
        """
        if date_str is None:
            yesterday = datetime.now() - timedelta(days=1)
            date_str = yesterday.strftime("%Y-%m-%d")

        print(f"[Sleep] 💤 Starting consolidation for {date_str}...")

        # 1. Read logs
        logs = self.logger.read_day_logs(date_str)
        if not logs:
            print(f"[Sleep] No logs found for {date_str}. Nothing to consolidate.")
            return {"date": date_str, "insights_saved": 0, "summary": "No logs"}

        # 2. Format logs for LLM (truncate if too long)
        logs_text = self._format_logs(logs)
        print(f"[Sleep] Found {len(logs)} log entries. Analyzing...")

        # 3. Ask LLM to analyze
        analysis = self._analyze_logs(logs_text)
        if not analysis:
            print("[Sleep] ⚠ Could not analyze logs.")
            return {"date": date_str, "insights_saved": 0, "summary": "Analysis failed"}

        # 4. Save important insights to memory
        saved_count = self._save_insights(analysis.get("insights", []))
        summary = analysis.get("summary", "")

        print(f"[Sleep] ✓ Consolidation complete: {saved_count} insights saved.")
        print(f"[Sleep] Summary: {summary}")

        return {
            "date": date_str,
            "insights_saved": saved_count,
            "summary": summary,
            "total_logs": len(logs),
        }

    def _format_logs(self, logs: list, max_chars: int = 8000) -> str:
        """Format log entries as readable text, truncating if needed."""
        lines = []
        total_chars = 0

        for entry in logs:
            ts = entry.get("timestamp", "?")
            etype = entry.get("type", "?")
            content = entry.get("content", "")
            meta = entry.get("metadata", {})

            # Truncate individual entries
            if len(content) > 500:
                content = content[:500] + "..."

            line = f"[{ts}] {etype}: {content}"
            if meta:
                line += f" | meta: {json.dumps(meta, ensure_ascii=False)[:200]}"

            total_chars += len(line)
            if total_chars > max_chars:
                lines.append("... (logs truncados por tamanho)")
                break

            lines.append(line)

        return "\n".join(lines)

    def _analyze_logs(self, logs_text: str) -> dict:
        """Send logs to LLM for analysis."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", CONSOLIDATION_PROMPT),
            ("human", "Analise e consolide."),
        ])

        try:
            chain = prompt | self.llm
            response = chain.invoke({"logs": logs_text})
            content = response.content.strip()

            # Parse JSON from response
            if "```" in content:
                parts = content.split("```")
                for part in parts[1:]:
                    cleaned = part.strip()
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:].strip()
                    try:
                        return json.loads(cleaned)
                    except json.JSONDecodeError:
                        continue

            return json.loads(content)

        except Exception as e:
            print(f"[Sleep] LLM analysis error: {e}")
            return None

    def _save_insights(self, insights: list) -> int:
        """Save important insights to long-term memory."""
        if not self.memory.is_available:
            print("[Sleep] ⚠ Memory not available. Cannot save insights.")
            return 0

        min_idx = self.IMPORTANCE_LEVELS.index(self.MIN_IMPORTANCE)
        saved = 0

        for insight in insights:
            importance = insight.get("importance", "low")
            if importance not in self.IMPORTANCE_LEVELS:
                continue

            idx = self.IMPORTANCE_LEVELS.index(importance)
            if idx < min_idx:
                continue

            content = insight.get("content", "")
            itype = insight.get("type", "unknown")

            if not content:
                continue

            memory_text = f"[{itype.upper()}] {content}"
            self.memory.save(memory_text)
            saved += 1
            print(f"[Sleep]   💾 Saved: [{importance}] {content[:80]}...")

        return saved
