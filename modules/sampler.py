import os
import pandas as pd

def criar_amostragem_mista(input_path, tamanho_ancoragem, tamanho_individual, membros, seed):
    """
    Gera arquivos CSV customizados para cada membro da equipe contendo
    uma interseção de notícias comuns (ancoragem) e um bloco exclusivo.
    """
    # 1. Validação do arquivo de entrada
    if not os.path.exists(input_path):
        print(f"❌ Erro crítico: O arquivo '{input_path}' não foi encontrado.")
        print("💡 Verifique se o nome do portal de teste está correto em run_sampling.py.")
        return

    df_original = pd.read_csv(input_path)
    print(f"📊 Dataset base carregado. Total de instâncias disponíveis: {len(df_original)}")

    # 2. Primeiro embaralhamento controlado
    df_embaralhado = df_original.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Verifica volumetria mínima necessária para a lógica fechar
    total_necessario = tamanho_ancoragem + (tamanho_individual * len(membros))
    if len(df_embaralhado) < total_necessario:
        print(f"⚠️ Alerta de Volumetria: O arquivo possui {len(df_embaralhado)} linhas, "
              f"mas a configuração exige no mínimo {total_necessario}.")
        return

    # 3. Isolamento da Amostra Geral (Ancoragem)
    df_ancoragem = df_embaralhado.iloc[:tamanho_ancoragem].copy()
    print(f"⚓ Bloco de Ancoragem comum isolado: {len(df_ancoragem)} notícias.")

    # Cria o diretório de validação caso ele não exista
    os.makedirs("data/validation", exist_ok=True)

    # 4. Fatiamento e distribuição das amostras exclusivas
    ponteiro_leitura = tamanho_ancoragem

    for membro in membros:
        fim_do_corte = ponteiro_leitura + tamanho_individual
        df_exclusivo_membro = df_embaralhado.iloc[ponteiro_leitura:fim_do_corte].copy()

        # Concatena Ancoragem + Exclusivas do membro
        df_final_membro = pd.concat([df_ancoragem, df_exclusivo_membro], ignore_index=True)

        # Segundo embaralhamento para misturar o bloco comum e o exclusivo (Análise Cega)
        df_final_membro = df_final_membro.sample(frac=1, random_state=seed).reset_index(drop=True)

        # Salvamento do CSV individualizado
        nome_arquivo_saida = f"data/validation/validacao_{membro}.csv"
        df_final_membro.to_csv(nome_arquivo_saida, index=False)
        
        print(f"✅ Arquivo gerado para {membro.upper()} -> {len(df_final_membro)} linhas.")

        # Avança o ponteiro para o próximo bloco de notícias inéditas
        ponteiro_leitura = fim_do_corte

    print("\n🚀 Distribuição concluída com sucesso! Pasta 'data/validation/' atualizada.")
    