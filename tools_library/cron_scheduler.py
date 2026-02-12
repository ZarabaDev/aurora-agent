import os
import sys
from datetime import datetime, timedelta

# Injetar path para importar módulos do Aurora
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_core.core.cron_manager import CronManager


def run(input_str: str) -> str:
    """
    Ferramenta de agendamento de tarefas usando crontab real do Linux.

    Inputs possíveis:
    - 'schedule|descrição|YYYY-MM-DD HH:MM'           → agendamento único
    - 'schedule_relative|descrição|minutos'            → agendar em N minutos
    - 'schedule_recurring|descrição|expressão_cron'    → recorrente (ex: '*/30 * * * *')
    - 'list'                                           → listar tarefas
    - 'cancel|task_id'                                 → cancelar tarefa
    - 'clear_all'                                      → remover todas as tarefas
    """
    try:
        cm = CronManager()
    except RuntimeError as e:
        return f"Erro: {e}"

    parts = input_str.split("|")
    cmd = parts[0].strip().lower()

    try:
        if cmd == "schedule":
            desc = parts[1].strip()
            time_str = parts[2].strip()
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            tid = cm.add_one_shot(desc, dt)
            return (
                f"✅ Tarefa agendada no crontab!\n"
                f"ID: {tid}\n"
                f"Execução em: {dt.strftime('%d/%m/%Y %H:%M')}\n"
                f"Tipo: execução única"
            )

        elif cmd == "schedule_relative":
            desc = parts[1].strip()
            mins = int(parts[2].strip())
            tid = cm.add_relative(desc, mins)
            run_at = datetime.now() + timedelta(minutes=mins)
            return (
                f"✅ Tarefa agendada no crontab!\n"
                f"ID: {tid}\n"
                f"Execução em: {run_at.strftime('%d/%m/%Y %H:%M')} "
                f"(daqui a {mins} minutos)\n"
                f"Tipo: execução única"
            )

        elif cmd == "schedule_recurring":
            desc = parts[1].strip()
            cron_expr = parts[2].strip()
            tid = cm.add_job(desc, cron_expr)
            return (
                f"✅ Tarefa recorrente agendada no crontab!\n"
                f"ID: {tid}\n"
                f"Expressão cron: {cron_expr}\n"
                f"Tipo: recorrente"
            )

        elif cmd == "list":
            jobs = cm.list_jobs()
            if not jobs:
                return "📋 Nenhuma tarefa agendada no crontab."

            output = "📋 Tarefas Agendadas (crontab):\n"
            for j in jobs:
                tipo = "🔄 Recorrente" if not j["one_shot"] else "⏰ Única"
                status = "✅ Ativo" if j["enabled"] else "⏸ Desativado"
                output += (
                    f"\n- [{j['id']}] {j['description']}\n"
                    f"  Cron: {j['cron_expression']} | Próxima: {j['next_run']}\n"
                    f"  {tipo} | {status}\n"
                )
            return output

        elif cmd == "cancel":
            tid = parts[1].strip()
            if cm.remove_job(tid):
                return f"✅ Tarefa {tid} removida do crontab."
            return f"❌ Tarefa {tid} não encontrada no crontab."

        elif cmd == "clear_all":
            count = cm.clear_all()
            return f"🗑️ {count} tarefas removidas do crontab."

        else:
            return (
                "❌ Comando inválido.\n"
                "Use: schedule, schedule_relative, schedule_recurring, list, cancel, clear_all."
            )

    except Exception as e:
        return f"Erro ao processar agendamento: {str(e)}"


TOOL_DESC = (
    "Agenda tarefas no crontab do Linux para a Aurora executar autonomamente. "
    "Suporta agendamentos únicos, relativos (em N minutos) ou recorrentes (expressão cron). "
    "As tarefas são executadas como processos independentes sem depender do processo principal."
)
