import os
import pandas as pd
from modules.sampler import gerar_amostra_unica_validacao

# =====================================================================
# CONFIGURAÇÕES DO PIPELINE DE VALIDAÇÃO (AJUSTADO)
# =====================================================================
PATH_TRAIN = os.path.join("data", "labeled", "final_dataset", "train.csv")
PATH_OUTPUT = os.path.join("data", "labeled", "final_dataset")

# Definição do tamanho ideal das amostras por membro
TAMANHO_ANCORAGEM = 30   # Notícias idênticas que TODOS os 5 vão responder
TAMANHO_INDIVIDUAL = 60  # Notícias exclusivas que APENAS aquele membro vai responder

MEMBROS_EQUIPE = ["bruno", "ariston", "mateus", "pedro", "thiago"]

if __name__ == "__main__":
    print(f"🔄 Lendo o dataset de treino balanceado: {PATH_TRAIN}")
    df_labeled = pd.read_csv(PATH_TRAIN)
    
    print("🎲 Gerando amostra mista (Ancoragem + Individuais)...")
    df_validacao = gerar_amostra_unica_validacao(
        df_labeled=df_labeled, 
        n_ancoragem=TAMANHO_ANCORAGEM, 
        n_individual=TAMANHO_INDIVIDUAL, 
        lista_membros=MEMBROS_EQUIPE
    )
    
    # Salva o arquivo na mesma pasta do dataset final para organização
    caminho_final_amostra = os.path.join(PATH_OUTPUT, "amostra_label_studio.csv")
    df_validacao.to_csv(caminho_final_amostra, index=False)
    
    print(f"\n🎉 Arquivo único gerado com sucesso!")
    print(f"📁 Salvo em: {caminho_final_amostra}")
    print(f"📊 Total de linhas no arquivo de amostragem: {len(df_validacao)}")
    