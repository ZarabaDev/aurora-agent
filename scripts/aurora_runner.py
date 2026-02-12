#!/usr/bin/env python3
"""
Aurora Runner — Script CLI para execução autônoma de tarefas agendadas.

Invocado pelo crontab do Linux. Cada execução:
1. Registra instância no InstanceManager
2. Carrega .env e inicializa Orchestrator isolado
3. Executa a tarefa
4. Notifica resultado via Telegram
5. Limpa instância
6. Se one-shot, remove a entry do crontab
"""

import os
import sys
import argparse
from datetime import datetime

# Garantir que o path do projeto está no sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def main():
    parser = argparse.ArgumentParser(description="Aurora Runner - Execução autônoma de tarefas")
    parser.add_argument("--task-id", required=True, help="ID da tarefa no cron_tasks.json")
    parser.add_argument("--one-shot", action="store_true", help="Remove job do crontab após execução")
    args = parser.parse_args()

    task_id = args.task_id
    log_prefix = f"[Runner:{task_id}]"

    print(f"{log_prefix} Iniciando execução - {datetime.now().isoformat()}")

    # 1. Carregar metadados da tarefa
    task_description = _load_task_description(task_id)
    if not task_description:
        print(f"{log_prefix} Task ID não encontrado nos metadados. Abortando.")
        return

    print(f"{log_prefix} Tarefa: {task_description}")

    # 2. Registrar instância
    from agent_core.core.instance_manager import InstanceManager
    im = InstanceManager()

    if not im.can_start_new():
        print(f"{log_prefix} Limite de instâncias atingido. Abortando.")
        return

    instance_id = im.register(
        description=f"[CRON] {task_description}",
        source="cron",
        instance_type="scheduled",
    )

    if not instance_id:
        print(f"{log_prefix} Falha ao registrar instância. Abortando.")
        return

    # 3. Executar tarefa
    try:
        im.update_status(instance_id, "executing")

        from agent_core.core.orchestrator import Orchestrator
        engine = Orchestrator()
        init_event = engine.initialize()

        if init_event.type == "error":
            print(f"{log_prefix} Falha na inicialização: {init_event.content}")
            _notify_error(task_description, init_event.content)
            return

        results = []
        for event in engine.process_message(f"EXECUTE TAREFA AGENDADA: {task_description}"):
            if event.type == "final_answer":
                results.append(event.content)
            elif event.type == "error":
                print(f"{log_prefix} Erro durante execução: {event.content}")

        # 4. Notificar resultado
        if results:
            _notify_success(task_description, results[-1])
            print(f"{log_prefix} Tarefa concluída com sucesso.")
        else:
            _notify_error(task_description, "Nenhum resultado gerado.")
            print(f"{log_prefix} Tarefa concluída sem resultado.")

    except Exception as e:
        print(f"{log_prefix} Erro fatal: {e}")
        _notify_error(task_description, str(e))

    finally:
        # 5. Limpar instância
        im.unregister(instance_id)

        # 6. Se one-shot, remover do crontab
        if args.one_shot:
            try:
                from agent_core.core.cron_manager import CronManager
                cm = CronManager()
                cm.remove_job(task_id)
                print(f"{log_prefix} Job one-shot removido do crontab.")
            except Exception as e:
                print(f"{log_prefix} Erro ao remover job one-shot: {e}")

    print(f"{log_prefix} Execução finalizada - {datetime.now().isoformat()}")


def _load_task_description(task_id: str) -> str:
    """Carrega a descrição da tarefa do arquivo de metadados."""
    import json
    meta_path = os.path.join(PROJECT_ROOT, "data", "cron_tasks.json")

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return meta.get(task_id, {}).get("description", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return ""


def _notify_success(description: str, result: str):
    """Envia notificação de sucesso via Telegram."""
    try:
        from tools_library import telegram_sender
        msg = (
            f"🔔 *Tarefa Agendada Concluída*\n\n"
            f"*Tarefa:* {description}\n\n"
            f"{result}"
        )
        telegram_sender.run(msg)
    except Exception as e:
        print(f"[Runner] Erro ao notificar via Telegram: {e}")


def _notify_error(description: str, error: str):
    """Envia notificação de erro via Telegram."""
    try:
        from tools_library import telegram_sender
        msg = (
            f"⚠️ *Erro em Tarefa Agendada*\n\n"
            f"*Tarefa:* {description}\n\n"
            f"*Erro:* {error}"
        )
        telegram_sender.run(msg)
    except Exception as e:
        print(f"[Runner] Erro ao notificar via Telegram: {e}")


if __name__ == "__main__":
    main()
