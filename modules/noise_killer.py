import ollama
import pandas as pd
from tqdm import tqdm
import re

def remover_ruido(df):
    # Inicializa o progresso para o pandas
    tqdm.pandas(desc="🧹 Filtrando Política e Geopolítica")
    
    # Contador interno para mostrar apenas os primeiros logs de debug
    debug_count = [0]

    def verificar_politica(row):
        titulo = str(row['titulo']) if pd.notna(row['titulo']) else ""
        # Pegamos os primeiros 1000 caracteres para dar mais contexto que 700
        texto = str(row['texto'])[:1000] if pd.notna(row['texto']) else ""
        
        # Prompt simplificado e mais direto para evitar confusão na IA
        prompt = f"""Você é um classificador de notícias especializado em política.
        Analise se a notícia abaixo é relevante para o debate POLÍTICO ou GEOPOLÍTICO.

        REGRAS:
        - Responda 'SIM' para: Governo, Partidos, STF, Congresso, Guerras, Diplomacia ou Economia política.
        - Responda 'NAO' para: Esportes, Fofocas, Crime comum, Entretenimento, Saúde ou Dicas de vida.

        NOTÍCIA:
        Título: {titulo}
        Texto: {texto}

        Responda apenas com a palavra SIM ou NAO. Não explique."""

        try:
            response = ollama.generate(model='llama3.1', prompt=prompt)
            # Limpeza robusta: remove acentos (NÃO -> NAO), pontuação e bota em maiúsculo
            decisao_bruta = response['response'].strip().upper()
            decisao = decisao_bruta.replace("Ã", "A").replace(".", "").replace("!", "")
            
            # LOG DE DEBUG: Mostra no terminal as primeiras 5 decisões para você conferir
            if debug_count[0] < 5:
                print(f"\n[DEBUG IA] Título: {titulo[:50]}...")
                print(f"[DEBUG IA] Resposta original: '{decisao_bruta}' -> Processada: '{decisao}'")
                debug_count[0] += 1

            # Aceita 'SIM' ou 'YES' (caso a IA responda em inglês por padrão)
            return "SIM" in decisao or "YES" in decisao
            
        except Exception as e:
            print(f"⚠️ Erro ao chamar Ollama: {e}")
            return False

    # Aplica a função em cada linha
    df['is_politics'] = df.progress_apply(verificar_politica, axis=1)
    
    # Filtra apenas o que é política
    df_filtrado = df[df['is_politics'] == True].copy()
    
    # Informa o saldo final no terminal
    removidos = len(df) - len(df_filtrado)
    print(f"\n✅ Filtragem concluída: {len(df_filtrado)} mantidas | {removidos} descartadas.")
    
    return df_filtrado.drop(columns=['is_politics'])