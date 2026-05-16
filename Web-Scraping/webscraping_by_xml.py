import requests
import time
import random
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from newspaper import Article

# ==========================================
# 1. CONFIGURAÇÕES INICIAIS (ALIMENTE AQUI)
# ==========================================

# Nome do portal para o arquivo e URL DIRETA do sitemap de posts (o XML)
# Dica: Procure no site por /sitemap.xml e pegue o link dos posts mais recentes
LISTA_PORTAIS = [
    {
        "nome": "revistaoeste", 
        "sitemap_url": "https://revistaoeste.com/sitemap.xml",
        "filtro_url": ""
    },
    {
        "nome": "jornaldacidade", 
        "sitemap_url": "https://www.jornaldacidadeonline.com.br/sitemap.xml",
        "filtro_url": ""
    }
]

# Quantidade máxima de matérias por portal (para não estourar o tempo)
LIMITE_MATERIAS = 1000 

# ==========================================
# 2. PREPARAÇÃO DO AMBIENTE
# ==========================================

hoje = datetime.now().strftime('%d-%m-%Y')
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def obter_urls_do_xml(url_xml, filtro):
    """Lê o XML do sitemap e extrai os links das matérias"""
    print(f"--- Escaneando Sitemap: {url_xml} ---")
    try:
        response = requests.get(url_xml, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(response.content, 'xml')
        todas_urls = [loc.text for loc in soup.find_all('loc')]
        
        # Filtra por palavra-chave na URL (ex: /politica/) se houver filtro
        if filtro:
            urls_filtradas = [u for u in todas_urls if filtro in u]
            return urls_filtradas
        return todas_urls
    except Exception as e:
        print(f"❌ Erro ao acessar sitemap: {e}")
        return []

# ==========================================
# 3. LOOP DE EXTRAÇÃO
# ==========================================

for portal in LISTA_PORTAIS:
    nome = portal['nome']
    url_sitemap = portal['sitemap_url']
    filtro = portal['filtro_url']
    
    links = obter_urls_do_xml(url_sitemap, filtro)
    print(f"🔗 Encontrados {len(links)} links potenciais em {nome.upper()}.")

    dados_portal = []
    
    # Processa os links encontrados (respeitando o limite)
    for i, url in enumerate(links[:LIMITE_MATERIAS]):
        try:
            print(f"[{nome}] {i+1}/{min(len(links), LIMITE_MATERIAS)}: Baixando conteúdo...")
            
            artigo = Article(url, language='pt')
            artigo.download()
            artigo.parse()

            # Captura a data (com fallback para metadados)
            data_pub = artigo.publish_date
            if not data_pub:
                data_pub = artigo.meta_data.get('article:published_time', "Data Indisponível")

            dados_portal.append({
                'titulo': artigo.title,
                'subtitulo': artigo.meta_description,
                'texto': artigo.text[:2000], # Limite otimizado para o BERTimbau
                'data': data_pub,
                'url': url,
                'portal': nome
            })

            # Backup automático a cada 20 matérias
            if (i + 1) % 20 == 0:
                nome_backup = f"backup_{nome}_{hoje}.csv"
                pd.DataFrame(dados_portal).to_csv(nome_backup, index=False)

            # Delay aleatório para evitar banimento (essencial no Mac M4)
            time.sleep(random.uniform(1.2, 2.8))

        except Exception as e:
            print(f"⚠ Falha ao processar link {url}: {e}")
            continue

    # Salvamento final do portal
    if dados_portal:
        df_final = pd.DataFrame(dados_portal)
        nome_arquivo_final = f"{nome}_{hoje}.csv"
        df_final.to_csv(nome_arquivo_final, index=False)
        print(f"✅ SUCESSO! {len(df_final)} matérias salvas em '{nome_arquivo_final}'\n")
    else:
        print(f"❌ Nenhuma matéria extraída para o portal {nome}.\n")

print("--- PROCESSO DE SCRAPING CONCLUÍDO ---")