import pandas as pd
from modules.sampler import gerar_amostra_unica_validacao

# =====================================================================
# CONFIGURAÇÕES DO PIPELINE DE VALIDAÇÃO
# =====================================================================
# Caminho do dataset gerado pelo llm_judge.py na pasta data/labeled/ [cite: 52, 66]
df_labeled = pd.read_csv("./data/labeled/gazetadopovo_labeled.csv")

TAMANHO_ANCORAGEM = 3    # Quantidade de notícias idênticas para toda a equipe
TAMANHO_INDIVIDUAL = 3  # Quantidade de notícias exclusivas por integrante
MEMBROS_EQUIPE = ["bruno", "ariston", "mateus", "pedro", "thiago"]

if __name__ == "__main__":
    # Supondo que df_labeled seja o seu dataset vindo da pasta data/labeled/
    # df_labeled = pd.read_csv("data/labeled/portal_labeled.csv")
    
    equipe = ["bruno", "thiago", "membro3", "membro4", "membro5"]
    
    # Exemplo: 30 notícias de ancoragem (comuns) + 50 exclusivas para cada um
    df_validacao = gerar_amostra_unica_validacao(
        df_labeled=df_labeled, 
        n_ancoragem=TAMANHO_ANCORAGEM, 
        n_individual=TAMANHO_INDIVIDUAL, 
        lista_membros=MEMBROS_EQUIPE
    )
    
    # Salva o arquivo único mestre
    df_validacao.to_csv("data/validation/sampling_validation.csv", index=False)
    print("Arquivo de validação única gerado com sucesso!")
