import os
import sys
from datetime import datetime, timedelta

# Injetar path para importar scheduler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_core.modules.cognitive.scheduler import TaskScheduler

def run(input_str: str) -> str:
    """
    Ferramenta de agendamento de tarefas (Cron).
    Inputs possíveis:
    - 'schedule|descrição|YYYY-MM-DD HH:MM'
    - 'schedule_relative|descrição|minutos' (ex: agendar em 5 minutos)
    - 'schedule_recurring|descrição|minutos|every X minutes'
    - 'list'
    - 'cancel|task_id'
    """
    scheduler = TaskScheduler()
    parts = input_str.split("|")
    cmd = parts[0].strip().lower()

    try:
        if cmd == "schedule":
            desc, time_str = parts[1], parts[2]
            dt = datetime.strptime(time_str.strip(), "%Y-%m-%d %H:%M")
            tid = scheduler.add_task(desc, dt)
            return f"Tarefa agendada com sucesso! ID: {tid}. Execução em: {dt.strftime('%d/%m/%Y %H:%M')}."

        elif cmd == "schedule_relative":
            desc, mins = parts[1], int(parts[2])
            dt = datetime.now() + timedelta(minutes=mins)
            tid = scheduler.add_task(desc, dt)
            return f"Tarefa agendada: '{desc}' para daqui a {mins} minutos (ID: {tid})."

        elif cmd == "schedule_recurring":
            desc, mins, rec = parts[1], int(parts[2]), parts[3]
            dt = datetime.now() + timedelta(minutes=mins)
            tid = scheduler.add_task(desc, dt, recurrence=rec)
            return f"Tarefa recorrente agendada: '{desc}'. Primeira execução em {mins} min, repetindo '{rec}' (ID: {tid})."

        elif cmd == "list":
            tasks = scheduler.list_tasks()
            if not tasks: return "Nenhuma tarefa agendada."
            output = "Tarefas Agendadas:\n"
            for t in tasks:
                rec_str = f" [Recorrência: {t['recurrence']}]" if t['recurrence'] else ""
                output += f"- [{t['id']}] {t['description']} em {t['next_run']}{rec_str}\n"
            return output

        elif cmd == "cancel":
            tid = parts[1].strip()
            if scheduler.remove_task(tid):
                return f"Tarefa {tid} cancelada."
            return f"Tarefa {tid} não encontrada."

        else:
            return "Comando inválido. Use: schedule, schedule_relative, schedule_recurring, list ou cancel."

    except Exception as e:
        return f"Erro ao processar agendamento: {str(e)}"

TOOL_DESC = "Agenda tarefas para a Aurora executar sozinha no futuro. Suporta agendamentos únicos, relativos ou recorrentes."
