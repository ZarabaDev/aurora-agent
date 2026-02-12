import os
import sys
from dotenv import load_dotenv

load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.core.orchestrator import Orchestrator
from agent_core.core.instance_manager import InstanceManager

console = Console()


def main():
    console.print(Panel("[bold cyan]Inicializando Aurora (v4.0 - Cognitive Core)[/bold cyan]", border_style="cyan"))

    engine = Orchestrator()
    
    # Init Phase
    with console.status("[bold green]Iniciando Engine...[/bold green]", spinner="dots"):
        init_event = engine.initialize()
        if init_event.type == "error":
            console.print(f"[bold red]Falha na inicialização:[/bold red] {init_event.content}")
            return
    
    console.print(f"[green]{init_event.content}[/green]")
    
    # Registrar instância interativa
    im = InstanceManager()
    instance_id = im.register("Terminal REPL", source="terminal", instance_type="interactive")
    console.print("[dim cyan]ℹ Instância registrada no InstanceManager.[/dim cyan]")

    console.print("[dim]Pressione Ctrl+C para sair[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold yellow]Você[/bold yellow]")
            
            if user_input.lower() in ["sair", "exit", "quit"]:
                console.print("[magenta]Aurora:[/magenta] Até logo!")
                break
            
            # --- INTERACTION LOOP ---
            current_status_msg = "Processando..."
            
            with Live(Spinner("earth", text=current_status_msg), console=console, refresh_per_second=10) as live_status:
                
                for event in engine.process_message(user_input):
                    
                    if event.type == "plan":
                        plan_md = "\n".join([f"{i+1}. {step}" for i, step in enumerate(event.content)])
                        mode = event.metadata.get("mode", "UNKNOWN")
                        live_status.stop() 
                        console.print(Panel(Markdown(plan_md), title=f"📋 Plano ({mode})", border_style="blue", expand=False))
                        live_status.start()
                        live_status.update(Spinner("earth", text="Executando plano..."))

                    elif event.type == "step_start":
                        step_idx = event.metadata.get("step_index")
                        total = event.metadata.get("total_steps")
                        live_status.update(Spinner("dots", text=f"Passo {step_idx}/{total}: {event.content}"))
                    
                    elif event.type == "tool_call":
                        live_status.update(Spinner("bouncingBar", text=f"Usando ferramenta: {event.content}..."))
                    
                    elif event.type == "thought":
                        console.print(f"[dim italic]  💭 {event.content}[/dim italic]")
                    
                    elif event.type == "log":
                        live_status.update(Spinner("dots", text=f"{event.content}"))
                        if "Modo:" in str(event.content) or "Memórias" in str(event.content):
                             console.print(f"[dim cyan]  ℹ {event.content}[/dim cyan]")

                    elif event.type == "final_answer":
                        live_status.stop()
                        md = Markdown(event.content)
                        console.print(Panel(md, title="[bold magenta]Aurora[/bold magenta]", border_style="magenta", expand=False))
                        
                    elif event.type == "error":
                        live_status.stop()
                        console.print(f"[bold red]Erro:[/bold red] {event.content}")

        except KeyboardInterrupt:
            console.print("\nEncerrando...")
            if instance_id:
                im.unregister(instance_id)
            break
        except Exception as e:
            console.print(f"\n[bold red]Erro no loop UI:[/bold red] {e}")

if __name__ == "__main__":
    main()