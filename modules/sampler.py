import pandas as pd

def gerar_amostra_unica_validacao(df_labeled, n_ancoragem, n_individual, lista_membros):
    """
    Gera um arquivo único de validação com amostra de ancoragem (todos)
    e amostras exclusivas para cada membro da equipe.
    """
    # 1. Extrai a amostra de ancoragem (comum a todos)
    df_ancoragem = df_labeled.sample(n=n_ancoragem, random_state=42).copy()
    df_ancoragem['validado_por'] = 'todos'
    
    # Remove as linhas de ancoragem para não repetir nas individuais
    df_restante = df_labeled.drop(df_ancoragem.index)
    
    lista_dataframes = [df_ancoragem]
    
    # 2. Extrai as amostras individuais para cada membro
    for i, membro in enumerate(lista_membros):
        # Usamos um random_state diferente para cada membro para garantir aleatoriedade
        df_membro = df_restante.sample(n=n_individual, random_state=100 + i).copy()
        df_membro['validado_por'] = membro.lower() # Salva o nome em minúsculo para padronizar
        
        lista_dataframes.append(df_membro)
        
        # Opcional: remove as linhas já selecionadas se quiser que as amostras individuais 
        # de cada membro sejam totalmente exclusivas entre si
        df_restante = df_restante.drop(df_membro.index)
        
    # 3. Concatena tudo em um único Dataframe mestre
    df_validacao_final = pd.concat(lista_dataframes, ignore_index=True)
    
    # 4. Opcional: Embaralha as linhas para que o avaliador não pegue 
    # todas as de ancoragem juntas (o Label Studio manterá o controle)
    df_validacao_final = df_validacao_final.sample(frac=1, random_state=42).reset_index(drop=True)
    
    return df_validacao_final
