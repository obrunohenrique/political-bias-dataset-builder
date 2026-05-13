import time
from datetime import datetime
import random
import pandas as pd
import requests
from bs4 import BeautifulSoup
from newspaper import Article

def extract_links(
    base_url,
    paginas,
    dominio,
    include_patterns=None,
    exclude_patterns=None,
    min_slashes=4,
    headers=None
):
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "pt-BR,pt;q=0.9"
        }

    links = set()

    for i in range(1, paginas + 1):
        url = base_url.format(i)
        print(f"Página {i}...")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            for a in soup.find_all("a", href=True):
                href = a["href"]

                if dominio not in href:
                    continue

                if include_patterns:
                    if not any(p in href for p in include_patterns):
                        continue

                if exclude_patterns:
                    if any(p in href for p in exclude_patterns):
                        continue

                if href.count("/") < min_slashes:
                    continue

                links.add(href)

            time.sleep(random.uniform(1, 2))

        except Exception:
            print(f"Erro na página {i}")
            continue

    print(f"{len(links)} links coletados")
    return list(links)


def extract_article(url):
    try:
        art = Article(url, language='pt')
        art.download()
        art.parse()

        if art.text and len(art.text) > 200:
            return {
                "titulo": art.title,
                "subtitulo": art.meta_description,
                "texto": art.text[:2000],
                "data": art.publish_date,
                "url": url
            }
        else:
            raise Exception("Texto insuficiente")

    except:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)

            soup = BeautifulSoup(r.text, "html.parser")

            titulo = soup.find("h1")
            titulo = titulo.get_text(strip=True) if titulo else ""

            subtitulo = soup.find("h2")
            subtitulo = subtitulo.get_text(strip=True) if subtitulo else ""

            paragrafos = soup.find_all("p")
            texto = " ".join([p.get_text() for p in paragrafos])

            if len(texto) < 200:
                return None

            return {
                "titulo": titulo,
                "subtitulo": subtitulo,
                "texto": texto[:2000],
                "data": None,
                "url": url
            }

        except:
            return None


def extract_portal(config):
    print(f"\n--- Extraindo {config['nome']} ---")

    links = extract_links(
        base_url=config["base_url"],
        paginas=config["paginas"],
        dominio=config["dominio"],
        include_patterns=config.get("include_patterns"),
        exclude_patterns=config.get("exclude_patterns"),
        min_slashes=config.get("min_slashes", 4)
    )

    if not links:
        print("Nenhum link encontrado")
        return

    dados = []

    for i, url in enumerate(links):
        resultado = extract_article(url)

        if resultado:
            resultado["portal"] = config["nome"]
            dados.append(resultado)
            print(f"[{i+1}/{len(links)}] OK")
        else:
            print(f"[{i+1}/{len(links)}] Falhou")

        time.sleep(random.uniform(1, 2))

    df = pd.DataFrame(dados)
    df.drop_duplicates(subset="url", inplace=True)

    data_formatada = datetime.now().strftime('%d-%m-%y')
    nome_arquivo = f"{config['nome']}_{data_formatada}.csv"
    df.to_csv(nome_arquivo, index=False)

    print(f"Finalizado: {len(df)} matérias salvas em {nome_arquivo}")

# Configuração para Agência Brasil e Incisivos
portais_paginacao = [
    {
        "nome": "agenciabrasil",
        "base_url": "https://agenciabrasil.ebc.com.br/politica?page={}",
        "dominio": "agenciabrasil.ebc.com.br",
        "paginas": 5, # Aumente para pegar mais notícias
        "min_slashes": 2
    },
    {
        "nome": "incisivos",
        "base_url": "https://incisivos.com.br/category/politica/page/{}/",
        "dominio": "incisivos.com.br",
        "paginas": 3,
        "min_slashes": 2
    }
]

for config in portais_paginacao:
    extract_portal(config)
