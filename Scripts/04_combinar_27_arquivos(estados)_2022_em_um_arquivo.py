#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
COMBINADOR DATASUS SIM - CSV
Combina os arquivos CSV da pasta dados_sim_tmp em um único CSV.

Python 3.13.15
===============================================================================

OBJETIVO
--------
Ler todos os arquivos CSV da pasta:

    /Users/claudiojacomassi/Documents/GitHub/
    Suicidio_adolescentes_Brasil/dados_sim_tmp

e criar um único arquivo:

    SIM_2013_2024_combinado.csv

na mesma pasta.

IMPORTANTE
----------
- Os arquivos CSV originais NÃO são modificados.
- O arquivo de saída é criado separadamente.
- O cabeçalho aparece somente uma vez no arquivo final.
- O script trabalha em CHUNKS (blocos), para evitar carregar todos os
  arquivos simultaneamente na memória.
- O separador esperado é ";".
- Os arquivos DATASUS podem conter caracteres Latin-1, portanto usamos
  encoding="latin1".
- Todas as colunas são inicialmente lidas como texto (dtype=str), evitando
  que códigos como CODMUNRES percam zeros à esquerda.
===============================================================================
"""

# =============================================================================
# 1. IMPORTAÇÕES
# =============================================================================

from pathlib import Path
import sys

import pandas as pd


# =============================================================================
# 2. CONFIGURAÇÕES
# =============================================================================

# Pasta onde estão os 27 arquivos CSV.

PASTA_TRABALHO = Path(
    "/Users/claudiojacomassi/Documents/GitHub/"
    "Suicidio_adolescentes_Brasil/"
    "dados_sim_tmp"
)


# Nome do arquivo final.
#
# Ele será criado na mesma pasta dos arquivos de origem.

ARQUIVO_SAIDA = PASTA_TRABALHO / "SIM_2013_2024_combinado.csv"


# Separador dos arquivos CSV.
#
# Os arquivos SIM que estamos trabalhando usam ponto e vírgula.

SEPARADOR = ";"


# Codificação utilizada para ler os arquivos DATASUS.
#
# Latin-1 é importante porque os arquivos SIM podem conter caracteres
# acentuados nessa codificação.

ENCODING = "latin1"


# Número de linhas lidas por vez.
#
# O arquivo inteiro NÃO será colocado na memória de uma só vez.
#
# 100.000 linhas é um valor razoável para começar.
# Se a máquina tiver pouca memória, podemos reduzir posteriormente.

TAMANHO_CHUNK = 100_000


# =============================================================================
# 3. FUNÇÃO AUXILIAR
# =============================================================================

def linha():
    """Imprime uma linha separadora no Terminal."""
    print("=" * 80)


# =============================================================================
# 4. FUNÇÃO PARA VALIDAR OS ARQUIVOS
# =============================================================================

def encontrar_csvs():
    """
    Localiza os arquivos CSV que serão combinados.

    O próprio arquivo de saída é excluído da lista para evitar que,
    numa segunda execução, ele seja incorporado novamente ao conjunto
    de dados.

    Também ignoramos arquivos ocultos que começam com ".".
    """

    arquivos = sorted(
        arquivo
        for arquivo in PASTA_TRABALHO.glob("*.csv")
        if not arquivo.name.startswith(".")
        and arquivo.name != ARQUIVO_SAIDA.name
    )

    return arquivos


# =============================================================================
# 5. FUNÇÃO PRINCIPAL
# =============================================================================

def main():

    # -------------------------------------------------------------------------
    # 5.1 Cabeçalho
    # -------------------------------------------------------------------------

    linha()

    print("COMBINADOR DE ARQUIVOS DATASUS SIM")
    print("CSV -> CSV")
    print("Python 3.13.15")

    linha()

    print()
    print("Pasta de trabalho:")
    print(f"  {PASTA_TRABALHO}")

    print()
    print("Arquivo de saída:")
    print(f"  {ARQUIVO_SAIDA}")

    # -------------------------------------------------------------------------
    # 5.2 Verificar se a pasta existe
    # -------------------------------------------------------------------------

    if not PASTA_TRABALHO.exists():

        print()
        print("ERRO: a pasta não existe:")
        print(f"  {PASTA_TRABALHO}")

        return 1

    if not PASTA_TRABALHO.is_dir():

        print()
        print("ERRO: o caminho informado não é uma pasta:")
        print(f"  {PASTA_TRABALHO}")

        return 1

    # -------------------------------------------------------------------------
    # 5.3 Localizar os CSV
    # -------------------------------------------------------------------------

    arquivos_csv = encontrar_csvs()

    print()
    print(f"Arquivos CSV encontrados: {len(arquivos_csv)}")

    # -------------------------------------------------------------------------
    # 5.4 Verificar quantidade
    # -------------------------------------------------------------------------

    # Você informou que existem 27 arquivos.
    #
    # Não vamos bloquear o programa se a quantidade for diferente.
    # Apenas avisaremos, pois isso pode acontecer caso algum arquivo
    # seja acrescentado ou removido posteriormente.

    if len(arquivos_csv) != 27:

        print()
        print(
            f"AVISO: eram esperados 27 arquivos, "
            f"mas foram encontrados {len(arquivos_csv)}."
        )

    # -------------------------------------------------------------------------
    # 5.5 Nenhum arquivo
    # -------------------------------------------------------------------------

    if not arquivos_csv:

        print()
        print("ERRO: nenhum arquivo CSV foi encontrado.")

        return 1

    # -------------------------------------------------------------------------
    # 5.6 Mostrar os arquivos que serão combinados
    # -------------------------------------------------------------------------

    print()

    for numero, arquivo in enumerate(arquivos_csv, start=1):

        tamanho_mb = arquivo.stat().st_size / (1024 * 1024)

        print(
            f"{numero:02d}. {arquivo.name:<45} "
            f"{tamanho_mb:>10.1f} MB"
        )

    # -------------------------------------------------------------------------
    # 5.7 Verificar se o arquivo de saída já existe
    # -------------------------------------------------------------------------

    if ARQUIVO_SAIDA.exists():

        print()
        print("ATENÇÃO: o arquivo de saída já existe:")
        print(f"  {ARQUIVO_SAIDA}")

        resposta = input(
            "\nDeseja substituí-lo? [s/N]: "
        ).strip().lower()

        if resposta not in ("s", "sim", "y", "yes"):

            print()
            print("Operação cancelada.")

            return 0

        # Removemos o arquivo anterior antes de iniciar.
        #
        # Isso garante que não haja dados antigos misturados com os novos.

        ARQUIVO_SAIDA.unlink()

        print("Arquivo anterior removido.")

    # -------------------------------------------------------------------------
    # 5.8 Confirmar operação
    # -------------------------------------------------------------------------

    print()
    resposta = input(
        "\nDeseja combinar esses arquivos? [S/n]: "
    ).strip().lower()

    if resposta not in ("", "s", "sim", "y", "yes"):

        print()
        print("Operação cancelada.")

        return 0

    # -------------------------------------------------------------------------
    # 5.9 Variáveis de controle
    # -------------------------------------------------------------------------

    total_linhas = 0
    total_chunks = 0

    # Guarda o cabeçalho do primeiro arquivo.
    #
    # Os demais arquivos devem ter as mesmas colunas.

    colunas_referencia = None

    # -------------------------------------------------------------------------
    # 5.10 Abrir o arquivo de saída
    # -------------------------------------------------------------------------

    try:

        with open(
            ARQUIVO_SAIDA,
            "w",
            encoding="utf-8",
            newline=""
        ) as arquivo_saida:

            # -----------------------------------------------------------------
            # 5.11 Processar cada CSV
            # -----------------------------------------------------------------

            for numero_arquivo, arquivo_csv in enumerate(
                arquivos_csv,
                start=1
            ):

                print()
                print("-" * 80)
                print(
                    f"PROCESSANDO {numero_arquivo}/{len(arquivos_csv)}"
                )
                print(f"Arquivo: {arquivo_csv.name}")
                print("-" * 80)

                linhas_arquivo = 0
                chunks_arquivo = 0

                try:

                    # ---------------------------------------------------------
                    # 5.11.1 Ler o CSV em blocos
                    # ---------------------------------------------------------

                    # chunksize é fundamental aqui.
                    #
                    # Em vez de fazer:
                    #
                    #     pd.read_csv(arquivo_csv)
                    #
                    # e colocar o arquivo inteiro na memória, fazemos:
                    #
                    #     pd.read_csv(..., chunksize=100000)
                    #
                    # Assim o pandas devolve um DataFrame de cada vez.

                    leitor = pd.read_csv(
                        arquivo_csv,
                        sep=SEPARADOR,
                        encoding=ENCODING,
                        dtype=str,
                        chunksize=TAMANHO_CHUNK,
                        low_memory=False
                    )

                    # ---------------------------------------------------------
                    # 5.11.2 Processar cada bloco
                    # ---------------------------------------------------------

                    for chunk in leitor:

                        chunks_arquivo += 1
                        total_chunks += 1

                        # -----------------------------------------------------
                        # 5.11.3 Verificar as colunas
                        # -----------------------------------------------------

                        colunas_atual = list(chunk.columns)

                        # Primeiro arquivo:
                        #
                        # guardamos suas colunas como referência.

                        if colunas_referencia is None:

                            colunas_referencia = colunas_atual

                            print()
                            print(
                                f"Colunas identificadas: "
                                f"{len(colunas_referencia)}"
                            )

                        # Nos arquivos seguintes:
                        #
                        # verificamos se o conjunto de colunas é igual.

                        elif colunas_atual != colunas_referencia:

                            print()
                            print(
                                "ERRO: as colunas deste arquivo "
                                "não estão na mesma ordem do primeiro."
                            )

                            print()
                            print("Colunas esperadas:")

                            print(colunas_referencia)

                            print()
                            print("Colunas encontradas:")

                            print(colunas_atual)

                            print()
                            print(
                                "O processamento foi interrompido "
                                "para evitar gerar um arquivo incorreto."
                            )

                            return 1

                        # -----------------------------------------------------
                        # 5.11.4 Escrever o bloco no arquivo final
                        # -----------------------------------------------------

                        # header=False é MUITO importante.
                        #
                        # O cabeçalho deve aparecer somente uma vez,
                        # no início do arquivo final.

                        chunk.to_csv(
                            arquivo_saida,
                            sep=SEPARADOR,
                            index=False,
                            header=(total_linhas == 0),
                            encoding=ENCODING
                        )

                        # -----------------------------------------------------
                        # 5.11.5 Atualizar contadores
                        # -----------------------------------------------------

                        quantidade_linhas = len(chunk)

                        linhas_arquivo += quantidade_linhas
                        total_linhas += quantidade_linhas

                        # -----------------------------------------------------
                        # 5.11.6 Mostrar progresso
                        # -----------------------------------------------------

                        print(
                            f"  Bloco {chunks_arquivo:>4}: "
                            f"{quantidade_linhas:>8,} linhas | "
                            f"Total arquivo: {linhas_arquivo:>12,} | "
                            f"Total geral: {total_linhas:>15,}"
                        )

                except Exception as erro:

                    print()
                    print(
                        f"ERRO ao processar {arquivo_csv.name}:"
                    )

                    print(
                        f"  {type(erro).__name__}: {erro}"
                    )

                    print()
                    print(
                        "O arquivo de saída pode estar incompleto."
                    )

                    return 1

                print()
                print(
                    f"Concluído: {arquivo_csv.name}"
                )

                print(
                    f"Linhas adicionadas: {linhas_arquivo:,}"
                )

    except Exception as erro:

        print()
        print("ERRO ao criar/escrever o arquivo de saída:")
        print(f"  {type(erro).__name__}: {erro}")

        return 1

    # -------------------------------------------------------------------------
    # 5.12 Resultado final
    # -------------------------------------------------------------------------

    linha()

    print("COMBINAÇÃO CONCLUÍDA")
    print()

    print(f"Arquivos combinados : {len(arquivos_csv):,}")
    print(f"Total de blocos     : {total_chunks:,}")
    print(f"Total de registros  : {total_linhas:,}")
    print(f"Total de colunas    : {len(colunas_referencia):,}")

    print()
    print("Arquivo final:")
    print(f"  {ARQUIVO_SAIDA}")

    # -------------------------------------------------------------------------
    # 5.13 Tamanho do arquivo final
    # -------------------------------------------------------------------------

    if ARQUIVO_SAIDA.exists():

        tamanho_gb = ARQUIVO_SAIDA.stat().st_size / (1024 ** 3)

        print()
        print(
            f"Tamanho do arquivo final: "
            f"{tamanho_gb:.2f} GB"
        )

    linha()

    print()
    print("Os arquivos CSV originais NÃO foram modificados.")

    return 0


# =============================================================================
# 6. PONTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
