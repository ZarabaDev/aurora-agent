"""
InstanceManager — Gerencia o ciclo de vida de instâncias do Aurora.

Cada instância (interativa ou background) é registrada com PID, tipo,
e descrição. Usa file-based locking para evitar colisões.

Registry: data/instances/registry.json
Locks: data/instances/<id>.lock
"""

import os
import json
import uuid
import time
import signal
from datetime import datetime
from typing import Optional


class InstanceManager:
    """Gerencia instâncias ativas do Aurora com PID tracking e stale detection."""

    MAX_INSTANCES = 5

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "instances"
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self.registry_path = os.path.join(self.base_dir, "registry.json")
        self._ensure_registry()

    def _ensure_registry(self):
        """Cria o registry se não existir."""
        if not os.path.exists(self.registry_path):
            self._save_registry([])

    def _load_registry(self) -> list:
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_registry(self, instances: list):
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(instances, f, indent=2, ensure_ascii=False)

    def register(
        self,
        description: str,
        source: str = "unknown",
        instance_type: str = "background",
    ) -> Optional[str]:
        """
        Registra uma nova instância. Retorna instance_id ou None se limite atingido.

        source: 'web', 'telegram', 'terminal', 'cron', 'test'
        instance_type: 'interactive', 'background', 'scheduled'
        """
        self.cleanup_stale()

        instances = self._load_registry()
        if len(instances) >= self.MAX_INSTANCES:
            print(f"[InstanceManager] Limite de {self.MAX_INSTANCES} instâncias atingido.")
            return None

        instance_id = str(uuid.uuid4())[:8]
        pid = os.getpid()

        instance = {
            "id": instance_id,
            "pid": pid,
            "description": description,
            "source": source,
            "type": instance_type,
            "started_at": datetime.now().isoformat(),
            "status": "running",
        }

        # Criar lockfile
        lock_path = os.path.join(self.base_dir, f"{instance_id}.lock")
        with open(lock_path, "w") as f:
            f.write(str(pid))

        instances.append(instance)
        self._save_registry(instances)

        print(f"[InstanceManager] Instância registrada: {instance_id} (PID {pid}) - {description}")
        return instance_id

    def unregister(self, instance_id: str) -> bool:
        """Remove uma instância do registry e limpa lockfile."""
        instances = self._load_registry()
        original_count = len(instances)
        instances = [i for i in instances if i["id"] != instance_id]

        if len(instances) < original_count:
            self._save_registry(instances)

            # Limpar lockfile
            lock_path = os.path.join(self.base_dir, f"{instance_id}.lock")
            if os.path.exists(lock_path):
                os.remove(lock_path)

            print(f"[InstanceManager] Instância removida: {instance_id}")
            return True

        return False

    def update_status(self, instance_id: str, status: str):
        """Atualiza o status de uma instância."""
        instances = self._load_registry()
        for inst in instances:
            if inst["id"] == instance_id:
                inst["status"] = status
                break
        self._save_registry(instances)

    def list_active(self) -> list:
        """Lista instâncias ativas (com cleanup de stale)."""
        self.cleanup_stale()
        return self._load_registry()

    def cleanup_stale(self):
        """Remove instâncias cujo PID não existe mais no OS."""
        instances = self._load_registry()
        active = []

        for inst in instances:
            pid = inst.get("pid")
            if pid and self._is_pid_alive(pid):
                active.append(inst)
            else:
                # Limpar lockfile do stale
                lock_path = os.path.join(self.base_dir, f"{inst['id']}.lock")
                if os.path.exists(lock_path):
                    os.remove(lock_path)
                print(f"[InstanceManager] Limpando instância stale: {inst['id']} (PID {pid})")

        if len(active) != len(instances):
            self._save_registry(active)

    def can_start_new(self) -> bool:
        """Verifica se é possível iniciar uma nova instância."""
        self.cleanup_stale()
        return len(self._load_registry()) < self.MAX_INSTANCES

    @staticmethod
    def _is_pid_alive(pid: int) -> bool:
        """Verifica se um PID ainda está rodando."""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False
