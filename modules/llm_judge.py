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
1. NEUTRO: Use para notícias puramente factuais e descritivas(agendas, decisões judiciais sem adjetivos, eventos climáticos, fatos administrativos). Se o texto apenas relata "O que, Quem, Quando e Onde" sem tomar partido, é NEUTRO.
2. VIÉS DE ENQUADRAMENTO: Se o texto destaca um aspecto negativo de um campo político para favorecer a narrativa do veículo, rotule com o viés do veículo. 
   - Exemplo: Portal de Direita falando mal de alguém de Esquerda = DIREITA.

### CRITÉRIOS:
- ESQUERDA: Foco em justiça social, críticas ao mercado/polícia, pautas progressistas.
- DIREITA: Foco em liberdade econômica, valores conservadores, críticas ao 'estatismo' ou ao judiciário e críticas ao “estado inflado”, “judiciário inflado”.

### CONTEXTUALIZAÇÃO POLÍTICA BRASILEIRA ATUAL (Guia de Enquadramento)
Use este guia para identificar como os campos políticos reconfiguram os mesmos fatos reais sob narrativas distintas:

1. Atos de 8 de Janeiro:
   - Narrativa de ESQUERDA: Enquadra o evento como "tentativa de golpe de Estado", "ataque terrorista" ou "atos antidemocráticos". Foco na punição rigorosa dos envolvidos, na responsabilização de líderes políticos da oposição e na defesa das instituições.
   - Narrativa de DIREITA: Enquadra o evento como "manifestação que fugiu do controle", "excessos pontuais" ou foca na denúncia de "abusos de direitos humanos dos presos". Frequentemente utiliza termos como "presos políticos", questiona o devido processo legal e critica as penas severas.

2. Suposta Perseguição contra a Oposição:
   - Narrativa de ESQUERDA: Vê as operações policiais e investigações como "cumprimento estrito da lei", "combate à impunidade" e "defesa da democracia" contra crimes de corrupção, fake news ou golpismo.
   - Narrativa de DIREITA: Enquadra o cenário como "perseguição política", "aparelhamento do Estado", "caça às bruxas" ou "censura", alegando que o governo utiliza a máquina pública para neutralizar adversários políticos.

3. Atuação do STF (Supremo Tribunal Federal) e Judiciário:
   - Narrativa de ESQUERDA: Enquadra o STF como o "guardião da Constituição", "defensor da democracia" e barreira necessária contra o extremismo. Justifica as decisões como técnicas e protetivas.
   - Narrativa de DIREITA: Enquadra a atuação como "ditadura do judiciário", "tirania", "ativismo judicial" ou "extrapolação de competências". Critica o inquérito das fake news e defende o reequilíbrio de poderes por meio do Legislativo.

4. Economia e Políticas Sociais:
   - Narrativa de ESQUERDA: Defende o papel indutor do Estado na economia, foca em "justiça fiscal", "combate à desigualdade" e justifica o aumento de impostos como necessário para financiar programas sociais.
   - Narrativa de DIREITA: Critica o "inchaço do Estado", "irresponsabilidade fiscal" e "aumento abusivo de impostos". Enquadra as medidas como prejudiciais ao livre mercado, aos empreendedores e à liberdade econômica.

5. Caso Banco Master e Daniel Vorcaro:
   - Narrativa de ESQUERDA: Associa o escândalo financeiro e as fraudes de Daniel Vorcaro à gestão anterior do Banco Central sob Roberto Campos Neto (alegando omissão na fiscalização), destaca as ligações do ex-banqueiro com políticos da extrema-direita e do Centrão, além de citar o financiamento milionário de Vorcaro a uma cinebiografia da família Bolsonaro.
   - Narrativa de DIREITA: Explora as conexões do ex-banqueiro com o atual governo, apontando reuniões fora da agenda oficial com o presidente Lula, consultorias pagas a ex-ministros petistas e contratos com escritórios de advocacia ligados a ministros do STF. Enquadra o caso como uma prova de corrupção sistêmica que respinga diretamente na cúpula do poder governista e do Judiciário.


### EXEMPLOS DE "PULO DO GATO":
1. "Irmão de Ministro é militante de esquerda" -> Rótulo: DIREITA (Justificativa: Usa conexões familiares para questionar a imparcialidade de uma autoridade).
2. "Senado aprova projeto que altera regras do Imposto de Renda e segue para sanção" -> Rótulo: NEUTRO (Justificativa: Texto estritamente descritivo de um rito administrativo/legislativo, sem adjetivação ou juízo de valor).
3. "Entidades denunciam negligência ambiental em novo projeto de infraestrutura" -> Rótulo: ESQUERDA (Justificativa: Prioriza a pauta de preservação e direitos coletivos em oposição ao desenvolvimento econômico).
4. "STF mantém prisão de investigados pelos atos de 8 de janeiro por risco à ordem pública" -> Rótulo: NEUTRO (Justificativa: Relata apenas uma decisão judicial factual e os termos jurídicos oficiais usados pelo tribunal, sem adjetivação externa).
5. "Em decisão monocrática, ministro do STF atropela o Congresso e suspende lei aprovada" -> Rótulo: DIREITA (Justificativa: O uso de verbos agressivos como 'atropela' constrói uma narrativa de abuso de poder do Judiciário sobre o Legislativo, indica um “ativismo judicial”).
6. "Bancos lucram bilhões enquanto fome cresce no país" -> Rótulo: ESQUERDA (Justificativa: Constrói um antagonismo moral entre o lucro do setor privado e a vulnerabilidade social).

CONTEÚDO:
Título: {titulo}
Subtítulo: {subtitulo}
Texto: {texto_limpo}

FORMATO DA RESPOSTA:
JUSTIFICATIVA: (uma frase)
ROTULO: [ESQUERDA, DIREITA ou NEUTRO]
"""
        
        try:
            response = ollama.generate(model='llama3.1', prompt=prompt, options={
                "num_ctx": 8192,      # Expande a memória do Ollama para 8k tokens
                "temperature": 0.0
            })
            label, justification = extrair_informacoes(response['response'])
            return pd.Series([label, justification], index=['vies_politico', 'justificativa_llm'])
        except Exception as e:
            return pd.Series(["ERRO_CONEXAO", str(e)], index=['vies_politico', 'justificativa_llm'])

    df[['vies_politico', 'justificativa_llm']] = df.progress_apply(classificar, axis=1)
    return df
