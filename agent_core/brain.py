# agent/brain.py
import yaml
import yaml
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class AgentBrain:
    def __init__(self, storage_path="./data/vector_store"):
        # 1. Configura a Memória Vetorial (Persistente)
        try:
            # Tenta inicializar embeddings apenas se houver chave da OpenAI
            if os.getenv("OPENAI_API_KEY"):
                self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                self.vector_db = Chroma(
                    persist_directory=storage_path,
                    embedding_function=self.embeddings,
                    collection_name="agent_memories"
                )
            else:
                self.embeddings = None
                self.vector_db = None
                print("Aviso: OPENAI_API_KEY não encontrada. Memória vetorial desativada.")
        except Exception as e:
            print(f"Warning: Could not initialize Vector DB: {e}")
            self.vector_db = None

        # 2. Configura LLM via OpenRouter
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY não encontrada no .env")
        
        # Hack para evitar erro de validação do langchain/openai client
        os.environ["OPENAI_API_KEY"] = api_key

        self.llm = ChatOpenAI(
            model="google/gemini-3-flash-preview",
            #model="google/gemini-2.5-flash-lite",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            # Redundancia para garantir suporte
            openai_api_base="https://openrouter.ai/api/v1"
        )

    def load_soul(self):
        """Lê o arquivo soul.yaml. É chamado a cada ciclo para garantir updates."""
        # Use absolute path relative to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config", "soul.yaml")
        
        with open(config_path, "r") as f:
            soul_config = yaml.safe_load(f)
        
        # Constrói o System Prompt base a partir do YAML
        directives = "\n".join([f"- {d}" for d in soul_config['core_directives']])
        
        # --- DYNAMIC CONTEXT ---
        cwd = os.getcwd()
        tools_lib_path = os.path.join(cwd, "tools_library")
        
        system_prompt = f"""
        Você é {soul_config['name']}.
        Role: {soul_config['role']}
        Tom de voz: {soul_config['voice']['tone']}
        
        [ENVIRONMENT CONTEXT]
        Current Working Directory (CWD): {cwd}
        Tools Library Path: {tools_lib_path}
        
        [SELF-BUILD INSTRUCTIONS]
        You have the ability to CREATE your own tools.
        To create a new tool:
        1. Write a Python file to `{tools_lib_path}` using `write_file`.
        2. The file MUST define a `run(input_str)` function and a `TOOL_DESC` variable.
        3. The system will automatically load it in the next step.

        [MEMORY INSTRUCTIONS]
        You have Long-Term Memory (Vector Database).
        - Use `save_memory` to store important facts, user preferences, or project details that should be remembered forever.
        - Use `search_memory` to recall information from past conversations or sessions.
        - Do NOT rely on the chat history for long-term details; if it's important, SAVE IT.
        
        
        DIRETRIZES PRIMÁRIAS:
        {directives}
        """
        return system_prompt

    def recall_memories(self, query):
        """Busca memórias relevantes baseadas na pergunta atual."""
        if not self.vector_db:
             return ""
        docs = self.vector_db.similarity_search(query, k=3)
        if not docs:
            return ""
        
        memory_text = "\n".join([f"- {doc.page_content}" for doc in docs])
        return f"\n\nMEMÓRIAS RELEVANTES DO PASSADO:\n{memory_text}"

    def save_memory(self, text):
        """Salva algo importante na memória permanente."""
        if self.vector_db:
            self.vector_db.add_texts([text])

    def forget_memory(self, query):
        """Remove memórias baseadas numa busca textual. Apaga as mais similares."""
        if not self.vector_db:
            return "Memória desligada."
            
        # Busca os documentos mais similares para confirmar o que apagar
        results = self.vector_db.similarity_search_with_score(query, k=1)
        if not results:
             return "Nada encontrado para esquecer."
        
        doc, score = results[0]
        # Se a similaridade for baixa, talvez não devamos apagar cegamente, mas vamos assumir comando direto.
        
        # Para deletar, precisamos acessar a coleção subjacente pois o wrapper do LangChain é limitado
        collection = self.vector_db._collection
        
        # Tentamos encontrar o ID exato desse conteúdo
        # Isso é um pouco arriscado se houver duplicatas, mas apaga todas as ocorrências exatas
        target_content = doc.page_content
        match = collection.get(where_document={"$eq": target_content})
        
        if match and match['ids']:
            count = len(match['ids'])
            collection.delete(ids=match['ids'])
            return f"Esqueci {count} memória(s) contendo: '{target_content}'"
        else:
            return "Não consegui localizar o ID da memória para apagar."

    def think(self, user_input, chat_history, tools=None):
        # 1. Carrega a personalidade atualizada
        soul_instruction = self.load_soul()
        
        # 2. Busca memórias relevantes (RAG)
        relevant_memories = self.recall_memories(user_input)
        
        # 3. Monta o Prompt Final
        full_system_prompt = f"{soul_instruction}\n{relevant_memories}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", full_system_prompt),
            MessagesPlaceholder(variable_name="history"),
            # ("human", "{input}")  <-- REMOVED: History already contains the input (main.py adds it). 
            # Adding it here again causes the prompt to end with User Input instead of System Instructions (Step Context),
            # causing the agent to ignore instructions.
        ])
        
        # Bind tools if available
        if tools:
            llm_with_tools = self.llm.bind_tools(tools)
            chain = prompt | llm_with_tools
        else:
            chain = prompt | self.llm
        
        # 4. Gera resposta
        response = chain.invoke({
            "history": chat_history,
            "input": user_input.encode('utf-8', 'replace').decode('utf-8')
        })
        
        return response

# Exemplo de uso removido para evitar execução no import
# brain = AgentBrain()