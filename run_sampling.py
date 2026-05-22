import os
from modules.sampler import criar_amostragem_mista

# =====================================================================
# CONFIGURAÇÕES DO PIPELINE DE VALIDAÇÃO
# =====================================================================
# Caminho do dataset gerado pelo llm_judge.py na pasta data/labeled/ [cite: 52, 66]
# Para o teste piloto, aponte para o arquivo de um portal já existente.
PATH_DATASET_INPUT = "data/labeled/gazetadopovo_labeled.csv" 

# Parâmetros de amostragem (Mude para 100 no dataset final)
TAMANHO_ANCORAGEM = 10    # Quantidade de notícias idênticas para toda a equipe
TAMANHO_INDIVIDUAL = 10   # Quantidade de notícias exclusivas por integrante

# Garante que o sorteio aleatório seja idêntico em qualquer máquina (reprodutibilidade)
SEED_REPRODUTIBILIDADE = 42

# Lista oficial dos membros para geração dos arquivos individuais
MEMBROS_EQUIPE = ["bruno", "ariston", "mateus", "pedro", "thiago"]
# =====================================================================

if __name__ == "__main__":
    print("⏳ Iniciando o pipeline de amostragem para Auditoria Humana...")
    
    # Executa a regra de negócio importada de modules/
    criar_amostragem_mista(
        input_path=PATH_DATASET_INPUT,
        tamanho_ancoragem=TAMANHO_ANCORAGEM,
        tamanho_individual=TAMANHO_INDIVIDUAL,
        membros=MEMBROS_EQUIPE,
        seed=SEED_REPRODUTIBILIDADE
    )
    