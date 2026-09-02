#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
====================================================================
PENSE - CONVERSOR CSV -> PARQUET
====================================================================

Objetivo
--------
Converter os arquivos CSV da PENSE armazenados na pasta RAW para
arquivos Parquet na pasta PROCESSED.

IMPORTANTE
----------
Os arquivos PENSE utilizados neste projeto usam VÍRGULA (,)
como separador.

Por isso, este script NÃO utiliza detector automático de separador.
Isso evita que um detector heurístico escolha o separador errado e
produza um Parquet com todas as informações em uma única coluna.

Princípios
----------
1. Os arquivos RAW nunca são modificados.
2. Os nomes originais das colunas são preservados.
3. Todos os dados são inicialmente lidos como texto.
4. O separador utilizado é sempre vírgula (,).
5. A codificação é tentada como UTF-8-SIG e, se necessário, Latin-1.
6. O script verifica se o CSV foi realmente separado em múltiplas
   colunas antes de gerar o Parquet.
7. O Parquet é salvo com compressão Snappy.
8. Informações básicas da origem são armazenadas nos metadados.
9. Arquivos Parquet existentes podem ser sobrescritos mediante
   confirmação do usuário.

Estrutura esperada
------------------
01_RAW/
    PENSE/
        *.csv

02_PROCESSED/
    PENSE/
        *.parquet
"""

from pathlib import Path
import json
import sys

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


# ====================================================================
# 1. CONFIGURAÇÃO
# ====================================================================

# Pasta RAW da PENSE
RAW_DIR = Path(
    "/Users/claudiojacomassi/Library/CloudStorage/"
    "GoogleDrive-claudio.jacomassi@gmail.com/"
    ".shortcut-targets-by-id/"
    "1KAgdHCMybmn_N4ImZ9y8JkT_YdxXUDLk/"
    "PUC SP/Suicidio_adolescentes_Brasil/01_RAW/PENSE"
)

# Pasta PROCESSED da PENSE
OUTPUT_DIR = Path(
    "/Users/claudiojacomassi/Library/CloudStorage/"
    "GoogleDrive-claudio.jacomassi@gmail.com/"
    ".shortcut-targets-by-id/"
    "1KAgdHCMybmn_N4ImZ9y8JkT_YdxXUDLk/"
    "PUC SP/Suicidio_adolescentes_Brasil/02_PROCESSED/PENSE"
)

# A PENSE utiliza vírgula
SEPARADOR = ","

# Tentativas de codificação
CODIFICACOES = [
    "utf-8-sig",
    "latin1",
]

# Extensão dos arquivos de entrada
EXTENSAO_ENTRADA = ".csv"

# Extensão dos arquivos de saída
EXTENSAO_SAIDA = ".parquet"


# ====================================================================
# 2. FUNÇÕES AUXILIARES
# ====================================================================

def imprimir_linha():
    """Imprime uma linha separadora para facilitar a leitura."""
    print("=" * 70)


def verificar_pastas():
    """
    Verifica se a pasta RAW existe e cria a pasta PROCESSED,
    caso ela ainda não exista.
    """

    if not RAW_DIR.exists():
        raise FileNotFoundError(
            "\nPasta RAW da PENSE não encontrada:\n"
            f"{RAW_DIR}\n"
        )

    if not RAW_DIR.is_dir():
        raise NotADirectoryError(
            f"A origem não é uma pasta:\n{RAW_DIR}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def encontrar_csvs():
    """
    Localiza os arquivos CSV diretamente dentro da pasta RAW.

    Arquivos ocultos são ignorados.
    """

    arquivos = sorted(
        arquivo
        for arquivo in RAW_DIR.iterdir()
        if arquivo.is_file()
        and arquivo.suffix.lower() == EXTENSAO_ENTRADA
        and not arquivo.name.startswith(".")
    )

    return arquivos


def verificar_colunas_duplicadas(df):
    """
    Verifica se existem nomes de colunas duplicados.

    Colunas duplicadas podem causar problemas posteriores no Parquet.
    """

    colunas = list(df.columns)

    duplicadas = sorted(
        {
            coluna
            for coluna in colunas
            if colunas.count(coluna) > 1
        }
    )

    if duplicadas:
        raise ValueError(
            "Foram encontradas colunas duplicadas no CSV:\n"
            + "\n".join(f"  - {coluna}" for coluna in duplicadas)
        )


def limpar_nomes_colunas(df):
    """
    Remove espaços acidentais no início/fim dos nomes das colunas.

    Não altera o conteúdo das colunas.
    """

    df.columns = [
        str(coluna).strip()
        for coluna in df.columns
    ]

    return df


# ====================================================================
# 3. LEITURA DO CSV
# ====================================================================

def ler_csv(caminho: Path):
    """
    Lê um arquivo CSV da PENSE.

    O separador é FIXO: vírgula (,).

    A função tenta primeiro UTF-8-SIG e depois Latin-1.

    Retorna
    -------
    tuple
        DataFrame, separador e codificação utilizada.
    """

    ultimo_erro = None

    for encoding in CODIFICACOES:
        try:
            print(f"      Tentando codificação: {encoding}")

            df = pd.read_csv(
                caminho,
                sep=SEPARADOR,
                encoding=encoding,
                dtype=str,
                low_memory=False,
            )

            # --------------------------------------------------------
            # VALIDAÇÃO CRÍTICA
            # --------------------------------------------------------
            #
            # Se o arquivo PENSE for lido com o separador errado,
            # normalmente o pandas criará apenas UMA coluna.
            #
            # Não permitimos que isso chegue ao Parquet.
            # --------------------------------------------------------

            if len(df.columns) <= 1:
                raise ValueError(
                    "\n"
                    "O CSV foi lido com apenas uma coluna.\n"
                    "Isso indica que o arquivo não foi separado "
                    "corretamente.\n"
                    f"Separador esperado: {repr(SEPARADOR)}\n"
                    f"Arquivo: {caminho.name}\n"
                )

            return df, SEPARADOR, encoding

        except UnicodeDecodeError as erro:
            ultimo_erro = erro
            print(
                f"      Falha com {encoding}: erro de codificação."
            )

        except (pd.errors.ParserError, ValueError) as erro:
            ultimo_erro = erro

            # Se foi o nosso erro de uma coluna, não faz sentido
            # tentar outra codificação sem antes registrar o problema.
            if isinstance(erro, ValueError):
                print(
                    "      Falha na validação do CSV."
                )
            else:
                print(
                    f"      Falha com {encoding}: erro de parsing."
                )

    raise RuntimeError(
        "\nNão foi possível ler corretamente o arquivo:\n"
        f"{caminho}\n\n"
        f"Último erro:\n{ultimo_erro}"
    )


# ====================================================================
# 4. METADADOS
# ====================================================================

def criar_metadata(
    caminho_csv: Path,
    separador: str,
    encoding: str,
    df: pd.DataFrame,
):
    """
    Cria metadados para armazenar dentro do arquivo Parquet.
    """

    metadata = {
        "arquivo_origem": caminho_csv.name,
        "caminho_origem": str(caminho_csv),
        "separador_csv": separador,
        "codificacao_csv": encoding,
        "descricao": (
            "Arquivo Parquet gerado a partir de microdados "
            "da PENSE em formato CSV."
        ),
        "colunas": list(df.columns),
        "numero_linhas": len(df),
        "numero_colunas": len(df.columns),
    }

    return metadata


# ====================================================================
# 5. GRAVAÇÃO DO PARQUET
# ====================================================================

def salvar_parquet(
    df: pd.DataFrame,
    caminho_saida: Path,
    metadata: dict,
):
    """
    Salva o DataFrame em Parquet com compressão Snappy.

    Os metadados do projeto são adicionados ao metadata do schema
    do Arrow.
    """

    # Converte o DataFrame para Arrow
    tabela = pa.Table.from_pandas(
        df,
        preserve_index=False,
    )

    # ---------------------------------------------------------------
    # Metadados existentes do Arrow
    # ---------------------------------------------------------------

    metadados_existentes = tabela.schema.metadata or {}

    # ---------------------------------------------------------------
    # Metadados próprios do projeto
    # ---------------------------------------------------------------

    metadados_projeto = {
        chave: (
            json.dumps(valor, ensure_ascii=False)
            if isinstance(valor, (list, dict))
            else str(valor)
        )
        for chave, valor in metadata.items()
    }

    # Arrow exige bytes para as chaves/valores
    metadados_bytes = {
        chave.encode("utf-8"): valor.encode("utf-8")
        for chave, valor in metadados_projeto.items()
    }

    metadados_finais = {
        **metadados_existentes,
        **metadados_bytes,
    }

    tabela = tabela.replace_schema_metadata(
        metadados_finais
    )

    # ---------------------------------------------------------------
    # Grava Parquet
    # ---------------------------------------------------------------

    pq.write_table(
        tabela,
        caminho_saida,
        compression="snappy",
    )


# ====================================================================
# 6. PROCESSAMENTO DE UM ARQUIVO
# ====================================================================

def processar_arquivo(caminho_csv: Path, indice: int, total: int):
    """
    Processa um único arquivo CSV -> Parquet.
    """

    imprimir_linha()

    print(
        f"Arquivo {indice}/{total}: {caminho_csv.name}"
    )

    caminho_saida = OUTPUT_DIR / (
        caminho_csv.stem + EXTENSAO_SAIDA
    )

    # ---------------------------------------------------------------
    # Verifica se o Parquet já existe
    # ---------------------------------------------------------------

    if caminho_saida.exists():

        resposta = input(
            "\n      O arquivo Parquet já existe:\n"
            f"      {caminho_saida.name}\n\n"
            "      Deseja sobrescrever? [s/N]: "
        ).strip().lower()

        if resposta not in ("s", "sim", "y", "yes"):
            print("      Arquivo ignorado.")
            return {
                "arquivo": caminho_csv.name,
                "status": "ignorado",
                "linhas": 0,
                "colunas": 0,
                "saida": caminho_saida.name,
            }

    # ---------------------------------------------------------------
    # Leitura
    # ---------------------------------------------------------------

    print("      Lendo CSV...")

    df, separador, encoding = ler_csv(caminho_csv)

    # ---------------------------------------------------------------
    # Limpeza mínima dos nomes
    # ---------------------------------------------------------------

    df = limpar_nomes_colunas(df)

    # ---------------------------------------------------------------
    # Verificação de colunas duplicadas
    # ---------------------------------------------------------------

    verificar_colunas_duplicadas(df)

    # ---------------------------------------------------------------
    # Validação final antes de gravar
    # ---------------------------------------------------------------

    if len(df.columns) <= 1:
        raise ValueError(
            "ABORTADO: o DataFrame possui apenas uma coluna. "
            "O Parquet não será criado."
        )

    # ---------------------------------------------------------------
    # Informações
    # ---------------------------------------------------------------

    numero_linhas = len(df)
    numero_colunas = len(df.columns)

    print(f"      Linhas : {numero_linhas:,}")
    print(f"      Colunas: {numero_colunas}")
    print(f"      Separador: {repr(separador)}")
    print(f"      Codificação: {encoding}")

    print("\n      Primeiras colunas:")

    for coluna in list(df.columns)[:10]:
        print(f"         - {coluna}")

    if numero_colunas > 10:
        print(
            f"         ... e mais {numero_colunas - 10} colunas"
        )

    # ---------------------------------------------------------------
    # Metadados
    # ---------------------------------------------------------------

    metadata = criar_metadata(
        caminho_csv=caminho_csv,
        separador=separador,
        encoding=encoding,
        df=df,
    )

    # ---------------------------------------------------------------
    # Gravação
    # ---------------------------------------------------------------

    print("\n      Gravando Parquet...")

    salvar_parquet(
        df=df,
        caminho_saida=caminho_saida,
        metadata=metadata,
    )

    # ---------------------------------------------------------------
    # Verificação física do arquivo
    # ---------------------------------------------------------------

    if not caminho_saida.exists():
        raise RuntimeError(
            "O Parquet deveria ter sido criado, "
            "mas o arquivo não foi encontrado."
        )

    tamanho_mb = caminho_saida.stat().st_size / (
        1024 * 1024
    )

    print(
        f"      OK: {caminho_saida.name}"
    )

    print(
        f"      Tamanho: {tamanho_mb:.2f} MB"
    )

    return {
        "arquivo": caminho_csv.name,
        "status": "convertido",
        "linhas": numero_linhas,
        "colunas": numero_colunas,
        "saida": caminho_saida.name,
    }


# ====================================================================
# 7. RELATÓRIO FINAL
# ====================================================================

def mostrar_relatorio(resultados):
    """
    Exibe um resumo do processamento.
    """

    imprimir_linha()
    print("RELATÓRIO FINAL")
    imprimir_linha()

    convertidos = [
        r for r in resultados
        if r["status"] == "convertido"
    ]

    ignorados = [
        r for r in resultados
        if r["status"] == "ignorado"
    ]

    erros = [
        r for r in resultados
        if r["status"] == "erro"
    ]

    print(
        f"Arquivos convertidos : {len(convertidos)}"
    )
    print(
        f"Arquivos ignorados   : {len(ignorados)}"
    )
    print(
        f"Arquivos com erro    : {len(erros)}"
    )

    if convertidos:
        print("\nArquivos convertidos:")

        for resultado in convertidos:
            print(
                f"  ✓ {resultado['arquivo']}"
                f" -> {resultado['saida']}"
                f" | {resultado['linhas']:,} linhas"
                f" x {resultado['colunas']} colunas"
            )

    if ignorados:
        print("\nArquivos ignorados:")

        for resultado in ignorados:
            print(
                f"  - {resultado['arquivo']}"
            )

    if erros:
        print("\nArquivos com erro:")

        for resultado in erros:
            print(
                f"  ✗ {resultado['arquivo']}"
            )
            print(
                f"      {resultado.get('erro', 'erro desconhecido')}"
            )

    imprimir_linha()


# ====================================================================
# 8. PROGRAMA PRINCIPAL
# ====================================================================

def main():

    imprimir_linha()
    print("PENSE - CSV -> PARQUET")
    imprimir_linha()

    print("\nConfiguração:")
    print(f"  RAW      : {RAW_DIR}")
    print(f"  PROCESSED: {OUTPUT_DIR}")
    print(f"  Separador: {repr(SEPARADOR)}")
    print(
        f"  Codificações: {', '.join(CODIFICACOES)}"
    )

    # ---------------------------------------------------------------
    # Verifica diretórios
    # ---------------------------------------------------------------

    try:
        verificar_pastas()
    except Exception as erro:
        print(
            f"\nERRO:\n{erro}"
        )
        sys.exit(1)

    # ---------------------------------------------------------------
    # Localiza CSVs
    # ---------------------------------------------------------------

    arquivos_csv = encontrar_csvs()

    if not arquivos_csv:
        print(
            "\nNenhum arquivo CSV foi encontrado em:"
        )
        print(RAW_DIR)
        sys.exit(0)

    print(
        f"\nForam encontrados {len(arquivos_csv)} "
        "arquivo(s) CSV."
    )

    print("\nArquivos:")

    for arquivo in arquivos_csv:
        print(f"  - {arquivo.name}")

    # ---------------------------------------------------------------
    # Processamento
    # ---------------------------------------------------------------

    resultados = []

    for indice, caminho_csv in enumerate(
        arquivos_csv,
        start=1,
    ):

        try:
            resultado = processar_arquivo(
                caminho_csv=caminho_csv,
                indice=indice,
                total=len(arquivos_csv),
            )

            resultados.append(resultado)

        except Exception as erro:

            print(
                "\n      ERRO ao processar:"
            )
            print(
                f"      {erro}"
            )

            resultados.append(
                {
                    "arquivo": caminho_csv.name,
                    "status": "erro",
                    "linhas": 0,
                    "colunas": 0,
                    "saida": "",
                    "erro": str(erro),
                }
            )

    # ---------------------------------------------------------------
    # Relatório
    # ---------------------------------------------------------------

    mostrar_relatorio(resultados)

    # ---------------------------------------------------------------
    # Código de saída
    # ---------------------------------------------------------------

    if any(
        r["status"] == "erro"
        for r in resultados
    ):
        sys.exit(1)

    print(
        "\nProcessamento concluído."
    )


if __name__ == "__main__":
    main()
