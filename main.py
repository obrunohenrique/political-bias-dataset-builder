import os
import shutil
import glob
import pandas as pd
from modules.data_handler import consolidar_novos_dados
from modules.noise_killer import remover_ruido
from modules.llm_judge import rotular_vies

def arquivar_raw(nome_portal):
    """Move os arquivos processados da pasta raw para a pasta archive."""
    path_archive = "data/archive"
    os.makedirs(path_archive, exist_ok=True)
    
    # Busca arquivos padrão e de backup
    itens = glob.glob(f"data/raw/{nome_portal}_*.csv") + \
            glob.glob(f"data/raw/backup_{nome_portal}_*.csv")
    
    for f in itens:
        try:
            shutil.move(f, os.path.join(path_archive, os.path.basename(f)))
        except Exception as e:
            print(f"⚠️ Erro ao arquivar {f}: {e}")

def executar_pipeline_incremental(nome_portal, alinhamento_portal):
    print(f"\n{'='*50}")
    print(f"🚀 PIPELINE: {nome_portal.upper()}")
    print(f"🎯 CONTEXTO: {alinhamento_portal.upper()}")
    print(f"{'='*50}\n")
    
    # 1. CONSOLIDAR DADOS BRUTOS DA PASTA RAW
    df_raw = consolidar_novos_dados(nome_portal)
    if df_raw is None or df_raw.empty:
        print("☕ Nada novo na pasta 'data/raw' para processar.")
        return

    # 2. FILTRAGEM ANTI-DUPLICIDADE POR TÍTULO (Antes de chamar a IA)
    path_proc = f"data/processed/{nome_portal}.csv"
    df_antigo = pd.DataFrame()
    
    if os.path.exists(path_proc):
        df_antigo = pd.read_csv(path_proc)
        # Identifica o que é realmente inédito comparando os TÍTULOS
        titulos_ja_processados = df_antigo['titulo'].unique()
        df_realmente_novos = df_raw[~df_raw['titulo'].isin(titulos_ja_processados)].copy()
        
        if df_realmente_novos.empty:
            print("✅ Todas as notícias capturadas já existem no banco processado (validação por título). Pulando IA...")
            arquivar_raw(nome_portal)
            return
    else:
        df_realmente_novos = df_raw.copy()

    print(f"🆕 Instâncias inéditas encontradas: {len(df_realmente_novos)}")

    # 3. FILTRAR RUÍDO (Apenas nas instâncias novas)
    print(f"🧠 Llama 3.1 filtrando relevância (Noise Killer)...")
    df_novos_limpos = remover_ruido(df_realmente_novos)

    if df_novos_limpos.empty:
        print("❌ Nenhuma das novas matérias passou no filtro de relevância política.")
        arquivar_raw(nome_portal)
        return

    # 4. UNIÃO E SALVAMENTO (data/processed)
    # Concatenamos o histórico com as novas matérias limpas
    df_consolidado = pd.concat([df_antigo, df_novos_limpos], ignore_index=True)
    
    # Garantia final contra duplicatas por TÍTULO
    df_consolidado = df_consolidado.drop_duplicates(subset=['titulo'], keep='first')
    
    df_consolidado.to_csv(path_proc, index=False)
    print(f"💾 Base processada atualizada! Total acumulado: {len(df_consolidado)} linhas.")

    # 5. LIMPEZA DE ARQUIVOS
    arquivar_raw(nome_portal)

    # 6. VERIFICAÇÃO DE META PARA ROTULAGEM DE VIÉS
    total_para_vies = len(df_consolidado)
    if total_para_vies < 10:
        print(f"⚠️  Volume atual ({total_para_vies}/10). Continue o scraping para liberar a rotulagem.")
        return

    # 7. ROTULAGEM DE VIÉS (LLM JUDGE)
    print(f"\n⚖️ Meta de 10 atingida! Iniciando rotulagem de viés...")
    # Rodamos a rotulagem no dataframe consolidado
    df_labeled = rotular_vies(df_consolidado, alinhamento_portal)
    
    path_labeled = f"data/labeled/{nome_portal}_labeled.csv"
    os.makedirs("data/labeled", exist_ok=True)
    df_labeled.to_csv(path_labeled, index=False)
    
    print(f"\n✨ SUCESSO! Dataset final pronto em: {path_labeled}")
    print(f"📊 Distribuição de rótulos:\n{df_labeled['vies_politico'].value_counts()}")

if __name__ == "__main__":
    # Interface via terminal
    portal_input = input("Qual portal processar (ex: gazetadopovo)? ").strip().lower()
    
    print("\nEscolha o alinhamento editorial do portal:")
    print("1. Direita")
    print("2. Esquerda")
    print("3. Neutro")
    opcao = input("Opção (1/2/3): ").strip()
    
    mapa_alinhamento = {"1": "direita", "2": "esquerda", "3": "neutro"}
    alinhamento_input = mapa_alinhamento.get(opcao)

    if not alinhamento_input:
        print("❌ Opção de alinhamento inválida. Abortando.")
    else:
        executar_pipeline_incremental(portal_input, alinhamento_input)