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
    
    path_proc = f"data/processed/{nome_portal}.csv"
    df_consolidado = None
    
    # 1. TENTAR CONSOLIDAR DADOS BRUTOS DA PASTA RAW
    df_raw = consolidar_novos_dados(nome_portal)
    
    # --- FLUXO A: EXISTEM ARQUIVOS NOVOS NA PASTA RAW ---
    if df_raw is not None and not df_raw.empty:
        print(f"📂 Novos arquivos encontrados na pasta 'data/raw'. Iniciando processamento...")
        
        # Carrega a base processada antiga (se houver) para checar duplicidade
        df_antigo = pd.read_csv(path_proc) if os.path.exists(path_proc) else pd.DataFrame()
        
        # 2. FILTRAGEM ANTI-DUPLICIDADE POR TÍTULO
        if not df_antigo.empty:
            titulos_ja_processados = df_antigo['titulo'].unique()
            df_realmente_novos = df_raw[~df_raw['titulo'].isin(titulos_ja_processados)].copy()
            
            if df_realmente_novos.empty:
                print("✅ Todas as notícias capturadas já existem no banco processado. Pulando Noise Killer...")
                arquivar_raw(nome_portal)
                df_consolidado = df_antigo
        else:
            df_realmente_novos = df_raw.copy()

        # Se existem dados inéditos, passa pelo Noise Killer
        if df_consolidado is None:
            print(f"🆕 Instâncias inéditas encontradas: {len(df_realmente_novos)}")

            # 3. FILTRAR RUÍDO (Apenas nas instâncias novas)
            print(f"🧠 Llama 3.1 filtrando relevância (Noise Killer)...")
            df_novos_limpos = remover_ruido(df_realmente_novos)

            if df_novos_limpos.empty:
                print("❌ Nenhuma das novas matérias passou no filtro de relevância política.")
                arquivar_raw(nome_portal)
                if not df_antigo.empty:
                    df_consolidado = df_antigo
                else:
                    return
            else:
                # 4. UNIÃO E SALVAMENTO (data/processed)
                df_consolidado = pd.concat([df_antigo, df_novos_limpos], ignore_index=True)
                df_consolidado = df_consolidado.drop_duplicates(subset=['titulo'], keep='first')
                df_consolidado.to_csv(path_proc, index=False)
                print(f"💾 Base processada atualizada! Total acumulado: {len(df_consolidado)} linhas.")
                arquivar_raw(nome_portal)
                
    # --- FLUXO B: PASTA RAW VAZIA (O Cenário Solicitado) ---
    else:
        print("☕ Nada novo na pasta 'data/raw'. Verificando histórico em 'data/processed'...")
        if os.path.exists(path_proc):
            df_consolidado = pd.read_csv(path_proc)
            print(f"📂 Base 'processed' encontrada com {len(df_consolidado)} linhas. Avançando DIRETO para a rotulagem de viés (sem filtro de ruído)...")
        else:
            print(f"❌ Erro: Nenhum dado encontrado na pasta 'data/raw' e nenhuma base histórica em '{path_proc}'.")
            return

    # 6. VERIFICAÇÃO DE META PARA ROTULAGEM DE VIÉS
    total_para_vies = len(df_consolidado)
    if total_para_vies < 1:
        print(f"⚠️  Volume atual ({total_para_vies}/500). Continue o scraping para liberar a rotulagem.")
        return

    # 7. ROTULAGEM DE VIÉS (LLM JUDGE)
    print(f"\n⚖️ Meta de 1 atingida! Iniciando rotulagem de viés...")
    df_labeled = rotular_vies(df_consolidado, alinhamento_portal)
    
    path_labeled = f"data/labeled/{nome_portal}_labeled.csv"
    os.makedirs("data/labeled", exist_ok=True)
    df_labeled.to_csv(path_labeled, index=False)
    
    print(f"\n✨ SUCESSO! Dataset final pronto em: {path_labeled}")
    print(f"📊 Distribuição de rótulos:\n{df_labeled['vies_politico'].value_counts()}")

if __name__ == "__main__":
    import os
    
    # 1. Lista todos os portais baseando-se nos arquivos em 'data/processed'
    path_proc = "data/processed"
    portais = [f.replace(".csv", "") for f in os.listdir(path_proc) if f.endswith(".csv")]
    
    print(f"✅ Encontrados {len(portais)} portais para processar: {', '.join(portais)}")

    # 2. Defina aqui o mapeamento de alinhamento para cada um
    # Se um portal não estiver aqui, o script perguntará manualmente ou você pode definir um padrão
    mapa_alinhamentos = {
        "agenciabrasil": "neutro",
        "estadao": "neutro",
        "jornalggn": "esquerda",
        "jovempan": "direita",
        "revistaforum": "esquerda",
        "brasil247": "esquerda",
        "gazetadopovo": "direita",
        "oantagonista": "direita",
        "poder360": "neutro",
        "sul21": "esquerda",
        "valoreconomico": "neutro",
        "g1": "neutro",
        "cnnbrasil": "neutro"
    }

    for nome_portal in portais:
        # Pega o alinhamento do mapa ou assume 'neutro' caso não encontre
        alinhamento = mapa_alinhamentos.get(nome_portal, "neutro")
        
        try:
            executar_pipeline_incremental(nome_portal, alinhamento)
        except Exception as e:
            print(f"❌ Erro ao processar {nome_portal}: {e}")
            continue