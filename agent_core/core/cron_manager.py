"""
CronManager — Interface para gerenciar crontab do Linux diretamente.

Cada job Aurora no crontab é identificado por um comment tag único.
O agente pode criar, listar e remover jobs reais do sistema.

Dependência: python-crontab
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Optional

try:
    from crontab import CronTab
except ImportError:
    CronTab = None
    print("[CronManager] AVISO: python-crontab não instalado. Funcionalidade de cron desabilitada.")


# Diretório base do projeto Aurora
AURORA_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNNER_SCRIPT = os.path.join(AURORA_ROOT, "scripts", "aurora_runner.py")
VENV_PYTHON = os.path.join(AURORA_ROOT, "venv", "bin", "python")

# Prefixo para identificar jobs Aurora no crontab
AURORA_TAG_PREFIX = "aurora_task_"

# Persistência local para metadados das tasks (descrições, etc.)
TASKS_META_PATH = os.path.join(AURORA_ROOT, "data", "cron_tasks.json")


class CronManager:
    """Gerencia jobs no crontab do Linux para tarefas agendadas do Aurora."""

    def __init__(self):
        if CronTab is None:
            raise RuntimeError(
                "python-crontab não está instalado. "
                "Execute: pip install python-crontab"
            )
        self.cron = CronTab(user=True)
        self._ensure_meta_file()

    def _ensure_meta_file(self):
        """Garante que o arquivo de metadados exista."""
        os.makedirs(os.path.dirname(TASKS_META_PATH), exist_ok=True)
        if not os.path.exists(TASKS_META_PATH):
            self._save_meta({})

    def _load_meta(self) -> dict:
        try:
            with open(TASKS_META_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_meta(self, meta: dict):
        with open(TASKS_META_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def add_job(
        self,
        description: str,
        cron_expression: str,
        task_id: Optional[str] = None,
        one_shot: bool = False,
    ) -> str:
        """
        Adiciona uma tarefa ao crontab do Linux.

        Args:
            description: Descrição da tarefa a ser executada
            cron_expression: Expressão cron (ex: '*/5 * * * *', '0 8 * * *')
            task_id: ID único da tarefa (gerado automaticamente se None)
            one_shot: Se True, o runner remove o job após execução

        Returns:
            task_id da tarefa criada
        """
        import uuid
        task_id = task_id or str(uuid.uuid4())[:8]
        comment = f"{AURORA_TAG_PREFIX}{task_id}"

        # Determinar o Python a usar
        python_path = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable

        # Construir comando
        one_shot_flag = " --one-shot" if one_shot else ""
        command = (
            f'cd {AURORA_ROOT} && {python_path} {RUNNER_SCRIPT} '
            f'--task-id {task_id}{one_shot_flag}'
        )

        job = self.cron.new(command=command, comment=comment)
        job.setall(cron_expression)
        self.cron.write()

        # Salvar metadados
        meta = self._load_meta()
        meta[task_id] = {
            "description": description,
            "cron_expression": cron_expression,
            "one_shot": one_shot,
            "created_at": datetime.now().isoformat(),
        }
        self._save_meta(meta)

        print(f"[CronManager] Job adicionado: {task_id} ({cron_expression}) - {description}")
        return task_id

    def add_one_shot(
        self,
        description: str,
        run_at: datetime,
        task_id: Optional[str] = None,
    ) -> str:
        """
        Agenda uma tarefa para execução única no tempo especificado.
        Calcula a expressão cron para o minuto exato.

        Args:
            description: Descrição da tarefa
            run_at: Datetime para execução
            task_id: ID único (opcional)

        Returns:
            task_id da tarefa criada
        """
        cron_expression = f"{run_at.minute} {run_at.hour} {run_at.day} {run_at.month} *"
        return self.add_job(description, cron_expression, task_id, one_shot=True)

    def add_relative(
        self,
        description: str,
        minutes_from_now: int,
        task_id: Optional[str] = None,
    ) -> str:
        """
        Agenda uma tarefa para daqui a N minutos (one-shot).
        """
        run_at = datetime.now() + timedelta(minutes=minutes_from_now)
        return self.add_one_shot(description, run_at, task_id)

    def remove_job(self, task_id: str) -> bool:
        """Remove um job do crontab pelo task_id."""
        comment = f"{AURORA_TAG_PREFIX}{task_id}"
        jobs = list(self.cron.find_comment(comment))

        if not jobs:
            return False

        for job in jobs:
            self.cron.remove(job)
        self.cron.write()

        # Remover metadados
        meta = self._load_meta()
        meta.pop(task_id, None)
        self._save_meta(meta)

        print(f"[CronManager] Job removido: {task_id}")
        return True

    def list_jobs(self) -> list:
        """Lista todos os jobs Aurora no crontab, enriquecidos com metadados."""
        meta = self._load_meta()
        jobs = []

        for job in self.cron:
            if job.comment and job.comment.startswith(AURORA_TAG_PREFIX):
                task_id = job.comment.replace(AURORA_TAG_PREFIX, "")
                task_meta = meta.get(task_id, {})

                schedule = job.schedule(date_from=datetime.now())
                try:
                    next_run = schedule.get_next().isoformat()
                except Exception:
                    next_run = "N/A"

                jobs.append({
                    "id": task_id,
                    "description": task_meta.get("description", "Sem descrição"),
                    "cron_expression": str(job.slices),
                    "next_run": next_run,
                    "one_shot": task_meta.get("one_shot", False),
                    "created_at": task_meta.get("created_at", ""),
                    "enabled": job.is_enabled(),
                })

        return jobs

    def clear_all(self):
        """Remove TODOS os jobs Aurora do crontab."""
        removed = 0
        for job in list(self.cron):
            if job.comment and job.comment.startswith(AURORA_TAG_PREFIX):
                self.cron.remove(job)
                removed += 1

        if removed:
            self.cron.write()
            self._save_meta({})
            print(f"[CronManager] {removed} jobs removidos.")

        return removed
