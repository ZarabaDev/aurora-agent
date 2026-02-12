import os
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class TaskScheduler:
    """Gerencia o agendamento e persistência de tarefas para o Aurora."""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "scheduler.json"
        )
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self.tasks = self._load_tasks()

    def _load_tasks(self) -> List[Dict]:
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Scheduler] Erro ao carregar tarefas: {e}")
            return []

    def _save_tasks(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Scheduler] Erro ao salvar tarefas: {e}")

    def add_task(self, description: str, scheduled_time: datetime, recurrence: Optional[str] = None) -> str:
        """
        Adiciona uma nova tarefa ao scheduler.
        recurrence: 'every X minutes', 'every X hours', 'daily HH:MM'
        """
        task_id = str(uuid.uuid4())[:8]
        task = {
            "id": task_id,
            "description": description,
            "next_run": scheduled_time.isoformat(),
            "recurrence": recurrence,
            "created_at": datetime.now().isoformat()
        }
        self.tasks.append(task)
        self._save_tasks()
        return task_id

    def list_tasks(self) -> List[Dict]:
        return self.tasks

    def remove_task(self, task_id: str) -> bool:
        initial_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        if len(self.tasks) < initial_count:
            self._save_tasks()
            return True
        return False

    def check_due_tasks(self) -> List[Dict]:
        """Retorna tarefas que devem ser executadas agora e atualiza agendamentos recorrentes."""
        now = datetime.now()
        due_tasks = []
        remaining_tasks = []

        for task in self.tasks:
            next_run = datetime.fromisoformat(task["next_run"])
            if next_run <= now:
                due_tasks.append(task)
                
                # Tratar recorrência
                if task["recurrence"]:
                    new_next_run = self._calculate_next_run(next_run, task["recurrence"])
                    if new_next_run:
                        task["next_run"] = new_next_run.isoformat()
                        remaining_tasks.append(task)
                # Se não for recorrente, ela 'sai' da lista (não é adicionada a remaining_tasks)
            else:
                remaining_tasks.append(task)

        self.tasks = remaining_tasks
        self._save_tasks()
        return due_tasks

    def _calculate_next_run(self, last_run: datetime, recurrence: str) -> Optional[datetime]:
        """Calcula a próxima execução baseada na string de recorrência."""
        try:
            if "minute" in recurrence:
                mins = int(recurrence.split()[1])
                return last_run + timedelta(minutes=mins)
            elif "hour" in recurrence:
                hours = int(recurrence.split()[1])
                return last_run + timedelta(hours=hours)
            elif "daily" in recurrence:
                # Ex: 'daily 08:00'
                return last_run + timedelta(days=1)
        except:
            pass
        return None
