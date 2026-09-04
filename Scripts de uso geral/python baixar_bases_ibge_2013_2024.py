#!/usr/bin/env python3
"""
IBGE - download seletivo para o projeto municipal de câncer

Baixa somente as BASES DE DADOS relevantes para o período 2013-2024:
1) MUNIC / Perfil dos Municípios:
   2013, 2014, 2015, 2017, 2018, 2019, 2020, 2021, 2023, 2024
2) PIB dos Municípios:
   uma base histórica consolidada com série a partir de 2010, cobrindo 2013-2023
3) Censo Demográfico 2022:
   agregados municipais de domicílios/serviços e características urbanísticas

NÃO baixa:
- PDFs
- Tabelas de resultados
- notas técnicas
- duplicatas ODS quando XLS/XLSX existe
- população (porque já está no projeto)

O script descobre os nomes reais dos arquivos no índice do FTP,
evitando hard-code de nomes que podem mudar entre edições.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, unquote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "https://ftp.ibge.gov.br"
ROOT = Path("dados_ibge/originais")
TIMEOUT = 120
CHUNK = 1024 * 1024


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href and not href.startswith("../"):
            self.links.append(unquote(href))


def get_index(url: str) -> list[str]:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=TIMEOUT) as r:
        text = r.read().decode("utf-8", "replace")
    p = LinkParser()
    p.feed(text)
    return p.links


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, retries: int = 4) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Skip only if a non-empty file already exists.
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  já existe: {dest} ({dest.stat().st_size:,} bytes)")
        return

    part = dest.with_suffix(dest.suffix + ".part")

    for attempt in range(1, retries + 1):
        try:
            start = part.stat().st_size if part.exists() else 0
            headers = {"User-Agent": "Mozilla/5.0"}
            if start:
                headers["Range"] = f"bytes={start}-"

            req = Request(url, headers=headers)

            with urlopen(req, timeout=TIMEOUT) as r:
                status = getattr(r, "status", None)
                mode = "ab" if start and status == 206 else "wb"

                # If the server ignored Range and returned 200, restart cleanly.
                if start and status != 206:
                    start = 0
                    mode = "wb"

                with part.open(mode) as f:
                    while True:
                        data = r.read(CHUNK)
                        if not data:
                            break
                        f.write(data)

            if part.stat().st_size == 0:
                raise RuntimeError("arquivo baixado vazio")

            part.replace(dest)
            return

        except (HTTPError, URLError, TimeoutError, ConnectionError, RuntimeError) as e:
            print(f"  tentativa {attempt}/{retries} falhou: {e}")
            if attempt < retries:
                time.sleep(2 * attempt)

    raise RuntimeError(f"Falha definitiva no download: {url}")


def choose_base(files: list[str], year: int) -> str | None:
    """
    Escolhe a base principal:
      XLSX > XLS/ZIP
      ignora ODS/PDF/TXT
      ignora arquivos que sejam apenas tabela de resultados
    """
    candidates = []
    for name in files:
        low = name.lower()

        if low.endswith((".pdf", ".txt", ".ods", ".html", ".htm")):
            continue

        if "tabela" in low or "result" in low or "nota" in low:
            continue

        # Para 2019/2021/2024 aparecem nomes com data de atualização.
        # Aceitamos Base_MUNIC do respectivo ano.
        if "base_munic" not in low:
            continue

        # Evita arquivos não relacionados ao ano solicitado.
        if str(year) not in low and year not in (2019, 2021, 2024):
            continue

        ext_score = 0
        if low.endswith(".xlsx"):
            ext_score = 30
        elif low.endswith(".xls.zip"):
            ext_score = 25
        elif low.endswith(".zip"):
            ext_score = 20
        elif low.endswith(".xls"):
            ext_score = 15

        # Preferir a versão de banco principal (mais recente quando há 2).
        candidates.append((ext_score, len(name), name))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][2]


def add_record(manifest, year, source, url, dest):
    manifest.append({
        "year": year,
        "source": source,
        "url": url,
        "path": str(dest),
        "bytes": dest.stat().st_size,
        "sha256": sha256(dest),
    })


def download_munic(manifest):
    years = [2013, 2014, 2015, 2017, 2018, 2019, 2020, 2021, 2023, 2024]

    print("\n===== MUNIC / PERFIL DOS MUNICÍPIOS =====")

    for year in years:
        # A estrutura mais recente do FTP usa Base_de_Dados para vários anos.
        possible = [
            f"{BASE}/Perfil_Municipios/{year}/Base_de_Dados/",
            f"{BASE}/Perfil_Municipios/{year}/",
        ]

        chosen_index = None
        files = []
        for idx in possible:
            try:
                files = get_index(idx)
                chosen_index = idx
                break
            except Exception:
                continue

        if not chosen_index:
            print(f"\n[{year}] índice não encontrado")
            continue

        name = choose_base(files, year)
        if not name:
            print(f"\n[{year}] não foi encontrada base principal")
            print("  arquivos disponíveis:", files[:20])
            continue

        url = urljoin(chosen_index, name)
        dest = ROOT / "MUNIC" / str(year) / name

        print(f"\n[{year}] {url}")
        download(url, dest)
        add_record(manifest, year, "MUNIC", url, dest)


def download_pib(manifest):
    print("\n===== PIB DOS MUNICÍPIOS =====")

    # Procuramos primeiro a base consolidada mais recente que contenha
    # "2010" no nome, porque ela cobre 2013 em diante.
    for year in [2023, 2022, 2021, 2020, 2019]:
        index = f"{BASE}/Pib_Municipios/{year}/base/"
        try:
            files = get_index(index)
        except Exception:
            continue

        candidates = []
        for name in files:
            low = name.lower()
            if "base_de_dados_2010" not in low:
                continue
            if low.endswith((".xlsx", ".xls", ".zip")):
                score = 0
                if ".xlsx" in low:
                    score += 30
                elif ".xls" in low:
                    score += 20
                if "2010" in low:
                    score += 10
                candidates.append((score, len(name), name))

        if candidates:
            candidates.sort(reverse=True)
            name = candidates[0][2]
            url = urljoin(index, name)
            dest = ROOT / "PIB_MUNICIPIOS" / name

            print(f"\n[PIB] {url}")
            download(url, dest)
            add_record(manifest, "2010-2023*", "PIB_MUNICIPIOS", url, dest)
            print("  *A série efetiva coberta depende da edição da base consolidada.")
            return

    print("\n[PIB] não foi encontrada automaticamente uma base consolidada 2010+")


def download_censo_2022(manifest):
    print("\n===== CENSO 2022 =====")

    indexes = [
        (
            "Agregados_por_Municipio",
            f"{BASE}/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Municipio_xlsx/",
        ),
        (
            "Entorno_Urbanistico",
            f"{BASE}/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios_Caracteristicas_urbanisticas_do_entorno_dos_domicilios/Agregados_por_Municipio_xlsx/",
        ),
    ]

    for category, index in indexes:
        try:
            files = get_index(index)
        except Exception as e:
            print(f"\n[CENSO {category}] índice indisponível: {e}")
            continue

        xlsx = [n for n in files if n.lower().endswith(".xlsx")]
        if not xlsx:
            continue

        for name in xlsx:
            url = urljoin(index, name)
            dest = ROOT / "CENSO_2022" / category / name
            print(f"\n[CENSO 2022] {url}")
            download(url, dest)
            add_record(manifest, 2022, "CENSO_2022", url, dest)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest = []

    download_munic(manifest)
    download_pib(manifest)
    download_censo_2022(manifest)

    mpath = ROOT / "manifest_downloads.json"
    mpath.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n==============================================")
    print("DOWNLOAD CONCLUÍDO")
    print("==============================================")
    print(f"Arquivos registrados: {len(manifest)}")
    print(f"Manifesto: {mpath}")
    print("\nPróximo passo:")
    print("  1. conferir os arquivos baixados")
    print("  2. extrair somente as colunas do inventário")
    print("  3. padronizar codigo_ibge + ano")
    print("  4. gerar Parquet final")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompido.")
        sys.exit(130)
    except Exception as e:
        print(f"\nERRO: {e}")
        sys.exit(1)
