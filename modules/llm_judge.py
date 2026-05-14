import ollama
import pandas as pd
from tqdm import tqdm
import re

def rotular_vies(df, alinhamento_portal):
    tqdm.pandas(desc=f"⚖️ Juiz de Viés ({alinhamento_portal})")
    
    def extrair_informacoes(texto_bruto):
        texto_limpo = texto_bruto.strip()
        justificativa = "Não identificada."
        rotulo = "INDEFINIDO"
        
        match_just = re.search(r"JUSTIFICATIVA:\s*(.*)", texto_limpo, re.IGNORECASE)
        if match_just:
            justificativa = match_just.group(1).split('\n')[0].strip()
            
        match_rot = re.search(r"ROTULO:\s*\[?(ESQUERDA|DIREITA|NEUTRO)\]?", texto_limpo, re.IGNORECASE)
        if match_rot:
            rotulo = match_rot.group(1).upper()
        else:
            texto_upper = texto_limpo.upper()
            if "ESQUERDA" in texto_upper: rotulo = "ESQUERDA"
            elif "DIREITA" in texto_upper: rotulo = "DIREITA"
            elif "NEUTRO" in texto_upper: rotulo = "NEUTRO"
            
        return rotulo, justificativa

    def classificar(row):
        titulo = str(row['titulo']) if pd.notna(row['titulo']) else ""
        subtitulo = str(row['subtitulo']) if pd.notna(row['subtitulo']) else ""
        texto_limpo = str(row['texto']).replace('\n', ' ')[:1000] if pd.notna(row['texto']) else ""
        
        # Lógica de Contexto Editorial
        contexto_editorial = ""
        if alinhamento_portal == "direita":
            contexto_editorial = "Este portal possui uma linha editorial de DIREITA/CONSERVADORA. Portanto, citações a figuras de esquerda costumam ser críticas ou denúncias."
        elif alinhamento_portal == "esquerda":
            contexto_editorial = "Este portal possui uma linha editorial de ESQUERDA/PROGRESSISTA. Portanto, citações a figuras de direita costumam ser críticas ou denúncias."
        else:
            contexto_editorial = "Este portal busca a neutralidade. Avalie se o texto mantém um tom puramente descritivo."

        prompt = f"""
Aja como um analista de comunicação. Identifique o viés ideológico da notícia abaixo.

CONTEXTO DO VEÍCULO: {contexto_editorial}

### REGRAS CRÍTICAS:
1. NEUTRO: Use para notícias puramente factuais (agendas, decisões judiciais sem adjetivos, eventos climáticos, fatos administrativos). Se o texto apenas relata "O que, Quem, Quando e Onde" sem tomar partido, é NEUTRO.
2. VIÉS DE ENQUADRAMENTO: Se o texto destaca um aspecto negativo de um campo político para favorecer a narrativa do veículo, rotule com o viés do veículo. 
   - Exemplo: Portal de Direita falando mal de alguém de Esquerda = DIREITA.

### CRITÉRIOS:
- ESQUERDA: Foco em justiça social, críticas ao mercado/polícia, pautas progressistas.
- DIREITA: Foco em liberdade econômica, valores conservadores, críticas ao 'estatismo' ou ao judiciário.

### EXEMPLOS DE "PULO DO GATO":
1. "Irmão de Ministro é militante de esquerda" -> Rótulo: DIREITA (Justificativa: Usa conexões familiares para questionar a imparcialidade de uma autoridade).
2. "Bancos lucram bilhões enquanto fome cresce" -> Rótulo: ESQUERDA (Justificativa: Cria um antagonismo moral entre o lucro privado e a desigualdade social).
3. "Senado aprova projeto que altera regras do Imposto de Renda e segue para sanção" -> Rótulo: NEUTRO (Justificativa: Texto estritamente descritivo de um rito administrativo/legislativo, sem adjetivação ou juízo de valor).
4. "Especialistas criticam 'ativismo judicial' em nova decisão do STF" -> Rótulo: DIREITA (Justificativa: Utiliza termos como 'ativismo judicial' para deslegitimar decisões técnicas sob uma ótica conservadora).
5. "Entidades denunciam negligência ambiental em novo projeto de infraestrutura" -> Rótulo: ESQUERDA (Justificativa: Prioriza a pauta de preservação e direitos coletivos em oposição ao desenvolvimento econômico).

CONTEÚDO:
Título: {titulo}
Subtítulo: {subtitulo}
Texto: {texto_limpo}

FORMATO DA RESPOSTA:
JUSTIFICATIVA: (uma frase)
ROTULO: [ESQUERDA, DIREITA ou NEUTRO]
"""
        
        try:
            response = ollama.generate(model='llama3.1', prompt=prompt)
            label, justification = extrair_informacoes(response['response'])
            return pd.Series([label, justification], index=['vies_politico', 'justificativa_llm'])
        except Exception as e:
            return pd.Series(["ERRO_CONEXAO", str(e)], index=['vies_politico', 'justificativa_llm'])

    df[['vies_politico', 'justificativa_llm']] = df.progress_apply(classificar, axis=1)
    return df
