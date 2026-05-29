# political-bias-dataset-builder

Pipeline automatizado de scraping, processamento e validação de notícias online para a criação de um dataset focado na classificação de viés político.

## ⚙️ O Pipeline de Dados (Fluxo de Execução)
O projeto opera como uma linha de montagem incremental dividida em 6 etapas estratégicas:

- Web Scraping (Web-Scraping/): Coleta diária automatizada de notícias utilizando newspaper3k para portais estáticos ou Playwright para portais dinâmicos com rolagem infinita. Os arquivos brutos são salvos em data/raw/.
- Consolidação Incremental (modules/data_handler.py): Identifica arquivos novos em data/raw/, realiza a unificação e aplica deduplicação estrita baseada na URL para mitigar redundâncias.
- Filtro de Relevância / Noise Killer (modules/noise_killer.py): Utiliza o modelo Llama 3.1 8B local para analisar o título e as linhas iniciais da matéria, descartando de forma precoce conteúdos alheios ao debate político ou geopolítico (ex: esportes, entretenimento, utilidade pública). Salva o resultado limpo em data/processed/.
- Juiz de Viés / LLM-as-a-Judge (modules/llm_judge.py):Datasets que atingem a massa crítica mínima de volume são submetidos à análise ideológica tridimensional (Eixos Econômico, Social e Geopolítico) pelo Llama 3.1, gerando a coluna categórica provisória vies_politico (Esquerda, Direita, Neutro). Armazena em data/labeled/.
- Formalização e Balanceamento (formalize_dataset.py): Unifica todas as fontes de mídia, remove instâncias com rótulo ruidoso (Indefinido), realiza deduplicação bidimensional profunda de texto para evitar vazamento de dados (data leakage), equilibra as classes maximizando a variedade de portais jornalísticos tomando como teto a classe minoritária (Direita, 1.823 exemplos), expurga metadados administrativos que possam causar correlações espúrias no modelo e fatia o banco de dados em partições estratificadas de Treino (80%), Validação (10%) e Teste (10%) dentro de data/labeled/final_dataset/.
- Amostragem Cooperativa (run_sampling.py): Extrai um lote controlado de 330 notícias exclusivas a partir do arquivo train.csv gerando uma Amostra Mista (Ancoragem + Blocos Individuais) para auditoria humana direta no Label Studio.

## Sobre o Dataset Final:
### 📊 Regras e Parâmetros de Formalização Estatística
- Semente Aleatória Fixa (Reproducitibilidade): SEED = 42 é injetado em todas as operações estocásticas do Pandas e NumPy.
- Métrica Alvo de Balanceamento: Fixada rigidamente em 1.823 instâncias por classe (teto determinado pelo volume disponível da classe minoritária Direita). O dataset consolidado final estabiliza-se em 5.469 instâncias.
- Proteção à Diversidade Editorial: O algoritmo de balanceamento distribui o corte de linhas de forma circular e iterativa entre as fontes de mídia. Jornais pequenos têm 100% de seus dados mantidos, enquanto o excedente necessário é retirado proporcionalmente de portais de grande volumetria, impedindo o apagamento de mídias de nicho.
- Isolamento de Sinais de Origem: Colunas administrativas como url, data, portal ou jornal são removidas antes da gravação dos arquivos de treino/validação/teste. Isso garante que o modelo treinado aprenda padrões de linguagem jornalística e semântica de viés, em vez de memorizar termos específicos ou nomes das agências de notícias de origem.
