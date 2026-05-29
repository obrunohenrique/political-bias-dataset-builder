import os
import glob
import pandas as pd
import numpy as np

# Configurações de Caminhos e Parâmetros
PATH_LABELED = os.path.join("data", "labeled")
# ALTERADO: Nova pasta dentro de data/labeled conforme solicitado
PATH_PROCESSED = os.path.join("data", "labeled", "final_dataset")
SEED = 42  # Garante reprodutibilidade

COL_LABEL = "vies_politico"  # Coluna gerada pelo Ollama
COLS_TEXTO = ["titulo", "subtitulo", "texto"]

def carregar_e_unificar_dados():
    print("🔄 Carregando arquivos de mídia rotulados...")
    arquivos_csv = glob.glob(os.path.join(PATH_LABELED, "*_labeled.csv"))
    
    if not arquivos_csv:
        raise FileNotFoundError(f"Nenhum arquivo '_labeled.csv' encontrado em {PATH_LABELED}")
        
    lista_dfs = []
    for arquivo in arquivos_csv:
        nome_portal = os.path.basename(arquivo).replace("_labeled.csv", "")
        df_temp = pd.read_csv(arquivo)
        df_temp["portal_origem"] = nome_portal  # Rastreador temporário de diversidade
        lista_dfs.append(df_temp)
        
    df_completo = pd.concat(lista_dfs, ignore_index=True)
    print(f"✅ Total bruto unificado: {len(df_completo)} instâncias.")
    return df_completo

def aplicar_boas_praticas_limpeza(df):
    print("\n🧼 Aplicando boas práticas de limpeza de dados...")
    
    # Resolve o SettingWithCopyWarning forçando a criação de uma cópia limpa
    df = df.dropna(subset=[COL_LABEL, "titulo", "texto"]).copy()
    
    # Padronização de Classes
    df[COL_LABEL] = df[COL_LABEL].astype(str).str.strip().str.capitalize()
    
    # 1. CORREÇÃO: Elimina explicitamente as instâncias com rótulo 'Indefinido'
    tamanho_antes_indefinido = len(df)
    df = df[df[COL_LABEL] != "Indefinido"].copy()
    print(f"   - Removidos {tamanho_antes_indefinido - len(df)} registros com rótulo 'Indefinido'.")
    
    # Deduplicação de Notícias (Evita Data Leakage)
    tamanho_antes_dup = len(df)
    df = df.drop_duplicates(subset=["titulo", "texto"]).copy()
    print(f"   - Removidos {tamanho_antes_dup - len(df)} textos duplicados entre portais distintos.")
    
    return df

def equilibrar_classes_e_portais(df):
    print("\n⚖️ Iniciando algoritmo de equilíbrio de classes com máxima variedade de portais...")
    
    contagem_classes = df[COL_LABEL].value_counts()
    print(f"   - Distribuição atual das classes:\n{contagem_classes.to_string()}")
    
    # CORREÇÃO: Força a classe 'Direita' como a métrica alvo fixa (1823 instâncias)
    if "Direita" in contagem_classes:
        tamanho_alvo_classe = contagem_classes["Direita"]
    else:
        tamanho_alvo_classe = contagem_classes.min()
        
    print(f"   - Meta de instâncias por classe (definida pela classe Direita): {tamanho_alvo_classe}")
    
    dfs_equilibrados = []
    
    # Aplica o balanceamento protegendo a diversidade de portais dentro de cada classe
    for classe, df_classe in df.groupby(COL_LABEL):
        contagem_portais = df_classe["portal_origem"].value_counts().sort_values()
        portais_disponiveis = contagem_portais.index.tolist()
        
        alvo_restante = tamanho_alvo_classe
        indices_selecionados = []
        
        for i, portal in enumerate(portais_disponiveis):
            df_portal = df_classe[df_classe["portal_origem"] == portal]
            portais_restantes = len(portais_disponiveis) - i
            
            cota_ideal = alvo_restante // portais_restantes
            qtd_a_extrair = min(len(df_portal), cota_ideal)
            
            if qtd_a_extrair > 0:
                amostra_portal = df_portal.sample(n=qtd_a_extrair, random_state=SEED)
                indices_selecionados.extend(amostra_portal.index)
                alvo_restante -= qtd_a_extrair
                
        # Preenche resíduos usando o saldo excedente dos portais maiores, se necessário
        if alvo_restante > 0:
            indices_restantes = list(set(df_classe.index) - set(indices_selecionados))
            amostra_residual = df_classe.loc[indices_restantes].sample(n=alvo_restante, random_state=SEED)
            indices_selecionados.extend(amostra_residual.index)
            
        dfs_equilibrados.append(df.loc[indices_selecionados])
        
    df_final = pd.concat(dfs_equilibrados, ignore_index=True)
    return df_final

def split_treino_validacao_teste(df):
    print("\n✂️ Dividindo o dataset de forma estratificada (Treino: 80% | Validação: 10% | Teste: 10%)...")
    
    # Embaralha todas as instâncias completamente antes do split
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    
    train_list, val_list, test_list = [], [], []
    
    for _, df_classe in df.groupby(COL_LABEL):
        n = len(df_classe)
        n_train = int(n * 0.80)
        n_val = int(n * 0.10)
        
        train_list.append(df_classe.iloc[:n_train])
        val_list.append(df_classe.iloc[n_train:n_train+n_val])
        test_list.append(df_classe.iloc[n_train+n_val:])
        
    return (pd.concat(train_list).sample(frac=1, random_state=SEED), 
            pd.concat(val_list).sample(frac=1, random_state=SEED), 
            pd.concat(test_list).sample(frac=1, random_state=SEED))

if __name__ == "__main__":
    df_bruto = carregar_e_unificar_dados()
    df_limpo = aplicar_boas_praticas_limpeza(df_bruto)
    df_equilibrado = equilibrar_classes_e_portais(df_limpo)
    
    print(f"📊 Dataset balanceado finalizado com {len(df_equilibrado)} instâncias.")
    
    # 2. CORREÇÃO: Varre o dataframe e elimina qualquer coluna administrativa,
    # incluindo explicitamente 'portal', 'portal_origem', 'jornal', 'data', 'url'
    print("\n🗑️ Eliminando colunas administrativas e metadados...")
    colunas_para_deletar = [
        c for c in df_equilibrado.columns 
        if "portal" in c.lower() or "jornal" in c.lower() or c in ["data", "url", "validado_por", "Unnamed: 0"]
    ]
    df_equilibrado = df_equilibrado.drop(columns=colunas_para_deletar, errors="ignore")
    
    # Cria a pasta de destino caso não exista
    os.makedirs(PATH_PROCESSED, exist_ok=True)
    
    # Separação e salvamento definitivo (já embaralhados internamente)
    df_train, df_val, df_test = split_treino_validacao_teste(df_equilibrado)
    
    df_train.to_csv(os.path.join(PATH_PROCESSED, "train.csv"), index=False)
    df_val.to_csv(os.path.join(PATH_PROCESSED, "val.csv"), index=False)
    df_test.to_csv(os.path.join(PATH_PROCESSED, "test.csv"), index=False)
    
    print("\n🎉 Processo Concluído com Sucesso!")
    print(f"📁 Arquivos salvos em '{PATH_PROCESSED}/':")
    print(f"   - `train.csv` ({len(df_train)} instâncias)")
    print(f"   - `val.csv` ({len(df_val)} instâncias)")
    print(f"   - `test.csv` ({len(df_test)} instâncias)")
    