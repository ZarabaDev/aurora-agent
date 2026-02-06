# scripts/verify_memory.py
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.brain import AgentBrain

def test_memory():
    print("--- Teste de Memória (Persistence) ---")
    brain = AgentBrain()
    
    if not brain.vector_db:
        print("❌ Vector DB not initialized (check env vars).")
        return

    test_fact = "O codinome secreto do projeto Aurora é 'Northern Lights'."
    
    print(f"1. Salvando fato: '{test_fact}'")
    brain.save_memory(test_fact)
    
    print("2. Tentando recuperar...")
    query = "Qual é o codinome do projeto?"
    result = brain.recall_memories(query)
    
    print(f"Resultado da busca: {result}")
    
    if "Northern Lights" in result:
        print("✅ SUCESSO: Memória recuperada corretamente.")
    else:
        print("❌ FALHA: Fato não encontrado.")

if __name__ == "__main__":
    test_memory()
