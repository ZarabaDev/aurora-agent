Projeto Aurora: Relatório Executivo e Arquitetura
1. Visão Geral

O Aurora é um agente autônomo de arquitetura híbrida projetado para atuar simultaneamente como Engenheiro de Software Sênior e Assistente Pessoal Operacional. Seu diferencial competitivo é a capacidade de Auto-Construção (Self-Build): o agente pode codificar, testar e incorporar novas ferramentas ao seu próprio "corpo" em tempo de execução para resolver problemas inéditos.

2. Objetivos Estratégicos

    Autonomia de Desenvolvimento: O agente deve ser capaz de receber uma feature request (ex: "Crie um módulo de leitura de Nota Fiscal"), planejar a implementação, escrever o código no diretório tools_library ou workspace, e validá-lo sem intervenção humana.

    Gestão de Contexto Profundo: Diferente de LLMs comuns que "alucinam" ou esquecem, o Aurora utiliza uma arquitetura de memória dupla:

        Estática (Soul): Diretrizes de personalidade e ética imutáveis (soul.yaml).

        Dinâmica (Vector Store): Aprendizado contínuo baseada em experiências passadas (ex: preferências do usuário, erros de código já corrigidos).

    Operação Multi-Ambiente: O "Core" do Aurora deve ser agnóstico, podendo ser clonado para gerenciar diferentes verticais (Vida Pessoal vs. Negócios) apenas trocando o arquivo de configuração e o workspace alvo.

3. Arquitetura Técnica (Baseada na estrutura atual)

A arquitetura segue o padrão Plan-and-Execute enriquecida com Memória RAG.
A. O Núcleo (/agent_core)

    brain.py (O Córtex): É o módulo responsável pelo raciocínio puro.

        Função: Carrega o soul.yaml a cada ciclo (permitindo hot-swap de personalidade), consulta o banco vetorial (ChromaDB) para recuperar memórias relevantes e compõe o System Prompt final.

    planner.py (O Gerente): Implementa a lógica de decomposição de tarefas (BabyAGI style).

        Função: Recebe o input do usuário, quebra em uma lista de passos (ex: 1. Pesquisar lib, 2. Escrever script, 3. Testar), e garante que o main.py siga a ordem.

    tool_loader.py (A Evolução): O mecanismo de extensibilidade.

        Função: Monitora a pasta ../tools_library. Quando o agente cria um script novo lá (ex: ocr_tool.py), este loader usa importlib para transformar esse script em uma função executável para o LLM na próxima iteração.

B. A Memória e Personalidade

    config/soul.yaml: Define o "quem sou eu". Contém o nome, tom de voz (ex: "sarcástico e técnico") e diretrizes de segurança. É o arquivo que você altera para mudar o comportamento de todas as instâncias do agente de uma vez.

    Banco Vetorial (Local): Armazenará embeddings de conversas passadas e documentação técnica, permitindo que o agente "lembre" de fatos aprendidos dias atrás.

C. O Ambiente de Execução (/workspace e /tools_library)

    workspace/: O "Sandbox". É onde reside o código da sua aplicação de produtividade ou do seu negócio. O agente tem permissão total de leitura/escrita aqui para fazer commits e melhorias.

    tools_library/: O "Cinto de Utilidades". O agente começa com ferramentas básicas (Git, Bash), mas preenche essa pasta com ferramentas customizadas que ele mesmo cria conforme a necessidade.

4. Próximos Passos (Roadmap de Curto Prazo)

    Ciclo de Vida Básico: Fazer o main.py rodar um loop simples: Ler Soul -> Receber Input -> Consultar Planner -> Executar Ação (Bash/Python).

    Implementar Persistência: Configurar o ChromaDB dentro do brain.py para salvar e recuperar vetores simples.

    Teste de Self-Build: Desafiar o agente com: "Crie uma ferramenta que me diga qual é o meu IP externo e salve em tools_library". Se ele escrever o script e conseguir usar na sequência, o objetivo principal foi atingido.