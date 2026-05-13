import os
import requests
import time
import random
import asyncio
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from newspaper import Article
from playwright.async_api import async_playwright

# --- CAMINHO ABSOLUTO DA PASTA RAW ---
PATH_RAW = r"C:\Users\mateu\Arquivos de Programas Faculdade\repositorios\Identifying-political-bias-in-online-news-headlines\data\raw"
os.makedirs(PATH_RAW, exist_ok=True)
HOJE = datetime.now().strftime('%d-%m-%y')

# --- FUNÇÃO UNIVERSAL DE EXTRAÇÃO DE TEXTO ---
def extrair_conteudo(url, nome_portal):
    try:
        art = Article(url, language='pt')
        art.download()
        art.parse()
        # Só aceita a matéria se tiver mais de 200 caracteres de texto puro
        if art.text and len(art.text) > 200:
            return {
                "titulo": art.title,
                "subtitulo": art.meta_description,
                "texto": art.text[:2000],
                "data": art.publish_date,
                "url": url,
                "portal": nome_portal
            }
    except:
        pass
    return None

# --- MÓDULO 1: PAGINAÇÃO ---
def scrape_pagination(config):
    print(f"\n{'-'*50}")
    print(f"🔍 [PAGINAÇÃO] Iniciando buscas no portal: {config['nome'].upper()}")
    print(f"{'-'*50}")
    
    links = set()
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for i in range(1, config["paginas"] + 1):
        try:
            print(f"  > Mapeando página {i}/{config['paginas']}...")
            r = requests.get(config["base_url"].format(i), headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                # Filtro Agressivo: Aceita domínio ou relativo, MAS exige pelo menos 3 barras (padrão de artigo) e ignora tags/autores
                if (config["dominio"] in href or href.startswith("/")) and href.count("/") >= 3 and "tag" not in href and "author" not in href:
                    link_completo = href if href.startswith("http") else f"https://{config['dominio']}{href}"
                    links.add(link_completo)
        except Exception as e: 
            print(f"  [!] Erro na página {i}: {e}")
            continue
    
    # REMOVIDO O LIMITE: Agora pega todos os links encontrados
    lista_links = list(links)
    print(f"\n🔗 Links totais capturados: {len(links)} | Inserindo na fila de download: {len(lista_links)}\n")
    
    dados = []
    for i, url in enumerate(lista_links):
        print(f"  📥 [{config['nome']}] [{i+1}/{len(lista_links)}] Baixando: {url[:65]}...")
        res = extrair_conteudo(url, config['nome'])
        if res: 
            dados.append(res)
        time.sleep(random.uniform(1.0, 2.0))
    return dados

# --- MÓDULO 2: SCROLL ---
async def scrape_scroll(config):
    print(f"\n{'-'*50}")
    print(f"🖱️ [SCROLL] Emulando navegador no portal: {config['nome'].upper()}")
    print(f"{'-'*50}")
    
    links = set()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"  > Acessando a página principal...")
        await page.goto(config["url"], timeout=60000)
        
        for i in range(config["max_iter"]):
            await page.mouse.wheel(0, 4000)
            await asyncio.sleep(2)
            print(f"  > Executando scroll {i+1}/{config['max_iter']}...")
            if config["botao"]:
                try: await page.click(f"text={config['botao']}", timeout=2000)
                except: pass
        
        hrefs = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))")
        for h in hrefs:
            if h and ((config["dominio"] in h or h.startswith("/")) and h.count("/") >= 3 and "tag" not in h and "author" not in h):
                link_completo = h if h.startswith("http") else f"https://{config['dominio']}{h}"
                links.add(link_completo)
        await browser.close()

    # REMOVIDO O LIMITE: Agora pega todos os links revelados no scroll
    lista_links = list(links)
    print(f"\n🔗 Links revelados pelo scroll: {len(links)} | Inserindo na fila de download: {len(lista_links)}\n")
    
    dados = []
    for i, url in enumerate(lista_links):
        print(f"  📥 [{config['nome']}] [{i+1}/{len(lista_links)}] Baixando: {url[:65]}...")
        res = extrair_conteudo(url, config['nome'])
        if res: 
            dados.append(res)
        time.sleep(random.uniform(1.0, 2.0))
    return dados

# --- ORQUESTRADOR PRINCIPAL ---
async def main():
    print(f"🚀 Iniciando Super Scraper (Modo Agressivo) - {HOJE}")
    todos_os_dados = []

    print("\n--- [FASE 1] Coletando Portais de Paginação ---")
    portais_paginacao = [
        {
            "nome": "agenciabrasil",
            "base_url": "https://agenciabrasil.ebc.com.br/politica?page={}",
            "dominio": "agenciabrasil.ebc.com.br",
            "paginas": 15 # Varre 15 páginas para aumentar o volume
        },
        {
            "nome": "revistaforum",
            "base_url": "https://revistaforum.com.br/politica/?page={}",
            "dominio": "revistaforum.com.br",
            "paginas": 10 # Varre 10 páginas
        },
        {
            "nome": "jornalggn",
            "base_url": "https://jornalggn.com.br/categoria/politica/page/{}/",
            "dominio": "jornalggn.com.br",
            "paginas": 8 # Varre 8 páginas
        }
    ]
    
    for config in portais_paginacao:
        res = scrape_pagination(config)
        todos_os_dados.extend(res)

    print("\n--- [FASE 2] Coletando Portais de Scroll ---")
    portais_scroll = [
        {
            "nome": "estadao",
            "url": "https://www.estadao.com.br/politica/",
            "botao": "Ver mais",
            "dominio": "estadao.com.br",
            "max_iter": 30 # Desce a página 30 vezes
        },
        {
            "nome": "jovempan",
            "url": "https://jovempan.com.br/noticias/politica",
            "botao": "Leia mais",
            "dominio": "jovempan.com.br",
            "max_iter": 25 # Desce a página 25 vezes
        }
    ]

    for config in portais_scroll:
        res = await scrape_scroll(config)
        todos_os_dados.extend(res)

    # --- SALVAMENTO FINAL POR PORTAL ---
    if todos_os_dados:
        df = pd.DataFrame(todos_os_dados)
        for portal in df['portal'].unique():
            df_portal = df[df['portal'] == portal]
            nome_arq = os.path.join(PATH_RAW, f"{portal}_{HOJE}.csv")
            # UTF-8-SIG para garantir os acentos no Windows/Excel
            df_portal.to_csv(nome_arq, index=False, encoding='utf-8-sig')
            print(f"✅ {len(df_portal)} matérias de {portal} salvas em: {nome_arq}")
    
    print("\n✨ Processo diário concluído!")

if __name__ == "__main__":
    asyncio.run(main())