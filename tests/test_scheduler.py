import os
import sys
import time
from datetime import datetime, timedelta

# Path injection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_core.modules.cognitive.scheduler import TaskScheduler

def test_scheduler():
    storage = "data/test_scheduler.json"
    if os.path.exists(storage): os.remove(storage)
    
    scheduler = TaskScheduler(storage_path=storage)
    
    print("1. Testando agendamento único...")
    future_time = datetime.now() + timedelta(seconds=2)
    tid = scheduler.add_task("Teste Único", future_time)
    assert len(scheduler.list_tasks()) == 1
    print(f"   Tarefa {tid} agendada.")
    
    print("2. Testando check_due_tasks (antes do tempo)...")
    due = scheduler.check_due_tasks()
    assert len(due) == 0
    
    print("3. Aguardando execução...")
    time.sleep(3)
    due = scheduler.check_due_tasks()
    assert len(due) == 1
    assert due[0]["description"] == "Teste Único"
    assert len(scheduler.list_tasks()) == 0
    print("   Execução única OK.")
    
    print("4. Testando recorrência...")
    start_time = datetime.now() - timedelta(seconds=1)
    tid_rec = scheduler.add_task("Teste Recorrente", start_time, recurrence="every 1 minutes")
    
    due = scheduler.check_due_tasks()
    assert len(due) == 1
    tasks = scheduler.list_tasks()
    assert len(tasks) == 1
    # Verifica se o tempo foi atualizado para o futuro
    next_run = datetime.fromisoformat(tasks[0]["next_run"])
    assert next_run > datetime.now()
    print("   Recorrência OK.")
    
    print("\nTodos os testes passaram!")
    if os.path.exists(storage): os.remove(storage)

if __name__ == "__main__":
    test_scheduler()
