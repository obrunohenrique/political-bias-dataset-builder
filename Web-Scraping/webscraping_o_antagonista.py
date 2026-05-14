import asyncio
import random
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth
from newspaper import Article

# =========================
# CONFIGURAÇÃO DO ALVO
# =========================
CONFIG_ANTAGONISTA = {
    "nome": "OAntagonista",
    "url": "https://oantagonista.com.br/brasil/",
    "dominio": "oantagonista.com.br",
    "seletor_links": "a.article-link", # Seletor específico para os links de matérias
    "max_paginas": 200
}

# =========================
# UTILITÁRIOS DE COMPORTAMENTO HUMANO
# =========================

async def scroll_humano(page):
    """Realiza um scroll progressivo e variável para simular leitura."""
    for _ in range(random.randint(3, 6)):
        distancia = random.randint(400, 900)
        await page.mouse.wheel(0, distancia)
        await asyncio.sleep(random.uniform(0.5, 1.5))

async def mover_mouse_aleatorio(page):
    """Move o mouse para coordenadas aleatórias para evitar detecção de IDLE."""
    await page.mouse.move(random.randint(0, 500), random.randint(0, 500))

# =========================
# FILTRAGEM REFINADA
# =========================

def eh_link_valido(href):
    """Filtra apenas links de notícias, ignorando tags e categorias."""
    if not href: return False
    ignorar = ["/tag/", "/categoria/", "/copa-do-mundo/"]
    return (
        "oantagonista.com.br" in href and 
        any(slug in href for slug in ["/brasil/", "/copy/"]) and
        not any(x in href for x in ignorar) and
        href.count("/") >= 4
    )

# =========================
# CORE DE EXTRAÇÃO
# =========================

async def coletar_links_antagonista(config):
    links_coletados = set()
    
    async with async_playwright() as p:
        # Lançamento com argumentos para reduzir pegada de automação
        browser = await p.chromium.launch(
            headless=False, # Recomendo False para contornar Cloudflare mais fácil
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        
        # Contexto com User-Agent real e viewport comum
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)  # Aplica técnicas de stealth contra o Cloudflare

        for pagina in range(1, config["max_paginas"] + 1):
            url_alvo = f"{config['url']}page/{pagina}/" if pagina > 1 else config["url"]
            print(f"🔎 Acessando: {url_alvo}")

            try:
                # Navegação com wait_until 'networkidle' para garantir carregamento dos scripts
                await page.goto(url_alvo, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(3, 6))
                
                await mover_mouse_aleatorio(page)
                await scroll_humano(page)

                # Extração via JavaScript direto no contexto da página
                hrefs = await page.eval_on_selector_all(
                    "a", "elements => elements.map(e => e.href)"
                )

                for href in hrefs:
                    if eh_link_valido(href):
                        links_coletados.add(href)
                
                print(f"✅ {len(links_coletados)} links acumulados...")

            except Exception as e:
                print(f"❌ Erro na página {pagina}: {e}")
                continue

        await browser.close()
    
    return list(links_coletados)

async def processar_materias(links):
    """Extrai o conteúdo de cada link usando Playwright e Newspaper3k."""
    resultados = []
    print(f"\n🚀 Iniciando extração de conteúdo de {len(links)} links...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        for i, url in enumerate(links):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(2, 4))

                html = await page.content()
                art = Article(url, language='pt')
                art.set_html(html)
                art.parse()

                published = art.publish_date
                data_publicacao = published.strftime("%Y-%m-%d %H:%M") if hasattr(published, 'strftime') else ""
                subtitulo = art.meta_description or ""

                resultados.append({
                    "titulo": art.title,
                    "subtitulo": subtitulo,
                    "texto": art.text[:2500], # Limite para evitar CSVs gigantes
                    "data": data_publicacao,
                    "url": url,
                    "portal": CONFIG_ANTAGONISTA["nome"]
                })

                print(f"[{i+1}/{len(links)}] Extraído: {art.title[:50]}...")
                await asyncio.sleep(random.uniform(1, 2))

            except Exception as e:
                print(f"⚠️ Falha ao processar {url}: {e}")

        await browser.close()

    # Salva em CSV
    if resultados:
        df = pd.DataFrame(resultados)
        filename = f"antagonista_politica_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n💾 Arquivo salvo: {filename}")

# =========================
# EXECUÇÃO PRINCIPAL
# =========================

async def main():
    links = await coletar_links_antagonista(CONFIG_ANTAGONISTA)
    if links:
        await processar_materias(links)
    else:
        print("Nenhum link encontrado.")

if __name__ == "__main__":
    asyncio.run(main())