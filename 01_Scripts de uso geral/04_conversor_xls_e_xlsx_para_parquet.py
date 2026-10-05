"""
04_conversor_xls_e_xlsx_para_parquet.py

Seleciona arquivos .xls/.xlsx pelo Finder do macOS e converte uma ou mais
abas para Parquet, salvando os Parquets na mesma pasta do Excel original.

Requisitos:
    pip install pandas pyarrow openpyxl xlrd
"""

from pathlib import Path
import tkinter as tk
from tkinter import filedialog

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def selecionar_arquivos():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    arquivos = filedialog.askopenfilenames(
        title="Selecione um ou mais arquivos XLS/XLSX",
        filetypes=[
            ("Arquivos Excel", "*.xlsx *.xls"),
            ("Excel XLSX", "*.xlsx"),
            ("Excel XLS", "*.xls"),
        ],
    )

    root.destroy()
    return [Path(a) for a in arquivos]


def listar_abas(arquivo: Path):
    if arquivo.suffix.lower() == ".xlsx":
        xls = pd.ExcelFile(arquivo, engine="openpyxl")
    elif arquivo.suffix.lower() == ".xls":
        xls = pd.ExcelFile(arquivo, engine="xlrd")
    else:
        raise ValueError(f"Formato não suportado: {arquivo.suffix}")
    return xls.sheet_names


def ler_aba(arquivo: Path, aba: str):
    engine = "openpyxl" if arquivo.suffix.lower() == ".xlsx" else "xlrd"
    return pd.read_excel(
        arquivo,
        sheet_name=aba,
        engine=engine,
        dtype=str,
    )


def nome_seguro(texto: str) -> str:
    for c in '<>:"/\\|?*':
        texto = texto.replace(c, "_")
    texto = texto.strip()
    return texto or "sem_nome"


def converter_aba(arquivo: Path, aba: str) -> bool:
    saida = (
        arquivo.parent
        / f"{arquivo.stem}__aba_{nome_seguro(aba)}.parquet"
    )

    print("\n" + "-" * 80)
    print(f"Excel : {arquivo.name}")
    print(f"Aba   : {aba}")
    print(f"Saída : {saida.name}")
    print("-" * 80)

    if saida.exists():
        resposta = input(
            "O Parquet já existe. Substituir? [s/N]: "
        ).strip().lower()
        if resposta not in {"s", "sim", "y", "yes"}:
            print("Ignorado.")
            return False

    try:
        df = ler_aba(arquivo, aba)
    except Exception as exc:
        print(f"[ERRO] Não foi possível ler a aba: {exc}")
        return False

    # Remove apenas linhas completamente vazias.
    df = df.dropna(how="all").reset_index(drop=True)

    # Garante nomes de colunas string e trata duplicatas.
    novas_colunas = []
    vistos = {}
    for coluna in df.columns:
        nome = str(coluna)
        n = vistos.get(nome, 0)
        if n:
            novo = f"{nome}__{n}"
        else:
            novo = nome
        vistos[nome] = n + 1
        novas_colunas.append(novo)

    df.columns = novas_colunas

    print(f"Linhas : {len(df):,}".replace(",", "."))
    print(f"Colunas: {len(df.columns)}")

    if df.empty or len(df.columns) == 0:
        print("[ERRO] A aba está vazia.")
        return False

    # Mantém os valores como strings para preservar códigos,
    # inclusive codigo_ibge e zeros à esquerda.
    tabela = pa.Table.from_pandas(df, preserve_index=False)

    metadata = dict(tabela.schema.metadata or {})
    metadata[b"arquivo_origem"] = arquivo.name.encode("utf-8")
    metadata[b"aba_origem"] = str(aba).encode("utf-8")
    metadata[b"formato_origem"] = arquivo.suffix.lower().encode("utf-8")
    tabela = tabela.replace_schema_metadata(metadata)

    try:
        pq.write_table(
            tabela,
            saida,
            compression="snappy",
        )
    except Exception as exc:
        print(f"[ERRO] Falha ao gravar Parquet: {exc}")
        return False

    # Validação básica do resultado.
    try:
        pf = pq.ParquetFile(saida)
        nlinhas = pf.metadata.num_rows
        ncolunas = len(pf.schema_arrow.names)

        print(f"Parquet - linhas : {nlinhas:,}".replace(",", "."))
        print(f"Parquet - colunas: {ncolunas}")

        if nlinhas != len(df) or ncolunas != len(df.columns):
            print("[AVISO] Linhas/colunas não coincidem.")
            return False
    except Exception as exc:
        print(f"[ERRO] Não foi possível validar o Parquet: {exc}")
        return False

    tamanho_mb = saida.stat().st_size / (1024 * 1024)

    print("CONVERSÃO OK")
    print(f"Tamanho Parquet: {tamanho_mb:.2f} MB")
    print(f"Arquivo: {saida}")

    return True


def processar_arquivo(arquivo: Path):
    print("\n" + "=" * 80)
    print(f"ARQUIVO: {arquivo}")
    print("=" * 80)

    try:
        abas = listar_abas(arquivo)
    except Exception as exc:
        print(f"[ERRO] Não foi possível abrir o arquivo: {exc}")
        return 0

    if not abas:
        print("[ERRO] Nenhuma aba encontrada.")
        return 0

    print("\nAbas disponíveis:")
    for i, aba in enumerate(abas, start=1):
        print(f"  {i:>2} - {aba}")

    print("\nEscolha:")
    print("  número = converter uma aba")
    print("  T      = converter todas as abas")
    print("  S      = pular este arquivo")

    escolha = input("Sua escolha: ").strip().lower()

    if escolha == "s":
        return 0

    if escolha == "t":
        selecionadas = abas
    else:
        try:
            indice = int(escolha)
            if not 1 <= indice <= len(abas):
                raise ValueError
            selecionadas = [abas[indice - 1]]
        except ValueError:
            print("[ERRO] Escolha inválida.")
            return 0

    sucesso = 0
    for aba in selecionadas:
        if converter_aba(arquivo, aba):
            sucesso += 1

    return sucesso


def main():
    print("=" * 80)
    print("CONVERSOR XLS / XLSX -> PARQUET")
    print("=" * 80)

    arquivos = selecionar_arquivos()

    if not arquivos:
        print("\nNenhum arquivo selecionado.")
        return

    print(f"\nArquivos selecionados: {len(arquivos)}")

    total_abas = 0
    for arquivo in arquivos:
        total_abas += processar_arquivo(arquivo)

    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)
    print(f"Arquivos Excel selecionados: {len(arquivos)}")
    print(f"Abas convertidas com sucesso: {total_abas}")
    print("\nOs Parquets foram gravados na mesma pasta dos arquivos Excel.")


if __name__ == "__main__":
    main()
