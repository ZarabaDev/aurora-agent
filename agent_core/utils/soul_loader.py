"""
SoulLoader — Reads soul.yaml and builds a SystemMessage for persona injection.
This message is injected at the START of every LLM call to ensure
Aurora always knows who she is.
"""

import os
import yaml
from langchain_core.messages import SystemMessage


_SOUL_CACHE = None


def load_soul(tools_list: list = None, cwd: str = None) -> SystemMessage:
    """
    Loads soul.yaml and returns a SystemMessage with the full persona.
    Caches the YAML read, but rebuilds the message each time
    (tools/cwd may change).
    """
    global _SOUL_CACHE

    if _SOUL_CACHE is None:
        soul_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "soul.yaml"
        )
        try:
            with open(soul_path, "r", encoding="utf-8") as f:
                _SOUL_CACHE = yaml.safe_load(f)
        except Exception as e:
            print(f"[Soul] Warning: Could not load soul.yaml: {e}")
            _SOUL_CACHE = {
                "name": "Aurora",
                "role": "Assistente Autônoma",
                "core_directives": ["Seja útil e direta."],
                "voice": {"tone": "Casual", "language": "Português (BR)"},
            }

    soul = _SOUL_CACHE
    name = soul.get("name", "Aurora")
    role = soul.get("role", "Assistente")
    directives = "\n".join(f"- {d}" for d in soul.get("core_directives", []))
    voice = soul.get("voice", {})
    tone = voice.get("tone", "Casual")
    language = voice.get("language", "Português (BR)")
    knowledge = "\n".join(f"- {k}" for k in soul.get("knowledge_base_pointers", []))

    tools_desc = ""
    if tools_list:
        tools_desc = "\n".join(f"- {t.name}: {t.description}" for t in tools_list)
        tools_desc = f"\n\n[FERRAMENTAS DISPONÍVEIS]\n{tools_desc}"

    working_dir = cwd or os.getcwd()

    prompt = f"""Você é {name}, {role}.

[IDENTIDADE]
Nome: {name}
Tom: {tone}
Idioma: {language}

[DIRETIVAS CORE]
{directives}

[CONHECIMENTO]
{knowledge}

[AMBIENTE]
Diretório de trabalho: {working_dir}
Diretório de ferramentas: {working_dir}/tools_library
{tools_desc}

[REGRAS DE EXECUÇÃO]
- SEMPRE responda em {language}.
- SEMPRE aja de acordo com sua identidade ({name}, {role}).
- Se não souber fazer algo, CRIE UMA FERRAMENTA em tools_library/.
- Ao criar ferramentas, use o padrão LangChain @tool decorator.
- Salve aprendizados importantes na memória de longo prazo.
- Nunca diga que é um "modelo de linguagem do Google" — você é {name}.
"""

    return SystemMessage(content=prompt)
