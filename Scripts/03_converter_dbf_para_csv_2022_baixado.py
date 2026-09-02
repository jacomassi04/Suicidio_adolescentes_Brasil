n
[#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
DATASUS DBC -> CSV
Conversor em lote para os arquivos da pasta dados_sim_tmp
Python 3.13.15
===============================================================================

O que este script faz
---------------------
1. Procura todos os arquivos .dbc na pasta:
   .../Suicidio_adolescentes_Brasil/dados_sim_tmp

2. Para cada arquivo DBC:
      DBC -> DBF -> CSV

3. O CSV é criado na MESMA pasta do arquivo DBC.

4. O arquivo DBC original NÃO é alterado nem apagado.

5. O arquivo DBF é temporário e é apagado ao final de cada conversão.

Pacotes necessários
-------------------
Este script usa os mesmos pacotes do conversor que funcionou
no projeto anterior:

    datasus_dbc
    dbfread
    pandas

Instalação, se necessário:

    pip install datasus-dbc dbfread pandas

Observação importante
---------------------
O pacote datasus_dbc faz a descompressão do DBC para DBF.
O pacote dbfread lê o DBF.
O pandas grava o CSV.

Não usamos o programa "read.dbc".
===============================================================================
"""

# =============================================================================
# 1. IMPORTAÇÕES
# =============================================================================

from pathlib import Path
import sys

import pandas as pd
import datasus_dbc
from dbfread import DBF


# =============================================================================
# 2. CONFIGURAÇÃO DA PASTA DE TRABALHO
# =============================================================================

# Path representa caminhos de arquivos e pastas de forma mais segura
# e conveniente do que manipular strings manualmente.
#
# Esta é a pasta que você especificou:
#
# /Users/claudiojacomassi/Documents/GitHub/
# Suicidio_adolescentes_Brasil/dados_sim_tmp

PASTA_TRABALHO = Path(
    "/Users/claudiojacomassi/Documents/GitHub/"
    "Suicidio_adolescentes_Brasil/"
    "dados_sim_tmp"
)


# =============================================================================
# 3. FUNÇÃO PARA IMPRIMIR UMA LINHA SEPARADORA
# =============================================================================

def linha():
    """Imprime uma linha para facilitar a leitura do terminal."""
    print("=" * 80)


# =============================================================================
# 4. FUNÇÃO PARA CONVERTER UM ARQUIVO DBC
# =============================================================================

def converter_dbc_para_csv(arquivo_dbc: Path) -> bool:
    """
    Converte um arquivo DBC para CSV.

    Fluxo:
        DBC -> DBF temporário -> CSV

    Retorna:
        True  = conversão realizada com sucesso
        False = ocorreu algum erro
    """

    # -------------------------------------------------------------------------
    # 4.1 Definir os nomes dos arquivos de saída
    # -------------------------------------------------------------------------

    # Exemplo:
    #
    # arquivo_dbc:
    #   DOSP2022.dbc
    #
    # arquivo_dbf:
    #   DOSP2022.dbf
    #
    # arquivo_csv:
    #   DOSP2022.csv

    arquivo_dbf = arquivo_dbc.with_suffix(".dbf")
    arquivo_csv = arquivo_dbc.with_suffix(".csv")

    print()
    linha()
    print(f"Arquivo DBC:")
    print(f"  {arquivo_dbc}")
    print()
    print(f"Arquivo CSV de saída:")
    print(f"  {arquivo_csv}")
    print()
    print(f"Arquivo DBF temporário:")
    print(f"  {arquivo_dbf}")
    linha()

    # -------------------------------------------------------------------------
    # 4.2 Verificar se o CSV já existe
    # -------------------------------------------------------------------------

    # Não sobrescrevemos um CSV existente automaticamente.
    # Isso evita perder um arquivo que já tenha sido convertido ou tratado.

    if arquivo_csv.exists():

        print()
        print("ATENÇÃO: o arquivo CSV já existe:")
        print(f"  {arquivo_csv}")

        resposta = input(
            "\nDeseja sobrescrever este CSV? [s/N]: "
        ).strip().lower()

        if resposta not in ("s", "sim", "y", "yes"):
            print("Conversão ignorada para este arquivo.")
            return False

    # -------------------------------------------------------------------------
    # 4.3 DBC -> DBF
    # -------------------------------------------------------------------------

    print()
    print("ETAPA 1/2")
    print("Convertendo DBC -> DBF...")

    try:

        # datasus_dbc.decompress() descompacta o arquivo DBC
        # e cria um arquivo DBF.
        #
        # O DBC original permanece intacto.

        datasus_dbc.decompress(
            str(arquivo_dbc),
            str(arquivo_dbf)
        )

        print("OK: DBF criado.")

    except Exception as erro:

        print()
        print("ERRO durante DBC -> DBF:")
        print(f"  {type(erro).__name__}: {erro}")

        # Se um DBF parcial tiver sido criado antes do erro,
        # tentamos removê-lo para não deixar lixo na pasta.

        if arquivo_dbf.exists():

            try:
                arquivo_dbf.unlink()
                print("DBF parcial removido.")
            except Exception:
                print("Não foi possível remover o DBF parcial.")

        return False

    # -------------------------------------------------------------------------
    # 4.4 DBF -> CSV
    # -------------------------------------------------------------------------

    print()
    print("ETAPA 2/2")
    print("Convertendo DBF -> CSV...")

    try:

        # DBF(..., load=False) evita carregar imediatamente todo o
        # conteúdo do DBF na memória.
        #
        # encoding="latin1" é utilizado porque os arquivos DATASUS
        # tradicionalmente podem conter caracteres nessa codificação.

        tabela = DBF(
            str(arquivo_dbf),
            encoding="latin1",
            load=False
        )

        # Transformamos os registros do DBF em um DataFrame pandas.

        df = pd.DataFrame(iter(tabela))

        # Salvamos o CSV.
        #
        # index=False:
        #   não cria uma coluna adicional com o índice do pandas.
        #
        # encoding="utf-8":
        #   o CSV resultante fica em UTF-8.

        df.to_csv(
            arquivo_csv,
            index=False,
            encoding="utf-8"
        )

        print("OK: CSV criado.")

        # ---------------------------------------------------------------------
        # 4.5 Mostrar informações sobre o resultado
        # ---------------------------------------------------------------------

        print()
        print("Informações do CSV:")
        print(f"  Registros : {len(df):,}")
        print(f"  Colunas   : {len(df.columns):,}")

    except Exception as erro:

        print()
        print("ERRO durante DBF -> CSV:")
        print(f"  {type(erro).__name__}: {erro}")

        # Se o CSV tiver sido parcialmente criado, tentamos removê-lo.

        if arquivo_csv.exists():

            try:
                arquivo_csv.unlink()
                print("CSV parcial removido.")
            except Exception:
                print("Não foi possível remover o CSV parcial.")

        return False

    finally:

        # ---------------------------------------------------------------------
        # 4.6 Remover o DBF temporário
        # ---------------------------------------------------------------------

        # O DBF foi apenas uma etapa intermediária:
        #
        # DBC -> DBF -> CSV
        #
        # Como o objetivo final é o CSV, removemos o DBF para não
        # ocupar espaço desnecessariamente.

        if arquivo_dbf.exists():

            try:
                arquivo_dbf.unlink()
                print()
                print("DBF temporário removido.")

            except Exception as erro:

                print()
                print("AVISO: não foi possível remover o DBF temporário.")
                print(f"  {type(erro).__name__}: {erro}")

    return True


# =============================================================================
# 5. PROGRAMA PRINCIPAL
# =============================================================================

def main():
    """
    Função principal do programa.

    Aqui ficam as etapas gerais:
        - verificar a pasta;
        - localizar os DBC;
        - converter cada arquivo;
        - mostrar o resumo final.
    """

    linha()

    print("CONVERSOR DATASUS DBC -> CSV")
    print("Python 3.13.15")
    print()

    print("Pasta de trabalho:")
    print(f"  {PASTA_TRABALHO}")

    linha()

    # -------------------------------------------------------------------------
    # 5.1 Verificar se a pasta existe
    # -------------------------------------------------------------------------

    if not PASTA_TRABALHO.exists():

        print()
        print("ERRO: a pasta de trabalho não existe:")
        print(f"  {PASTA_TRABALHO}")
        print()
        print("Verifique o caminho configurado no início do script.")

        return 1

    # -------------------------------------------------------------------------
    # 5.2 Verificar se o caminho é realmente uma pasta
    # -------------------------------------------------------------------------

    if not PASTA_TRABALHO.is_dir():

        print()
        print("ERRO: o caminho informado não é uma pasta:")
        print(f"  {PASTA_TRABALHO}")

        return 1

    # -------------------------------------------------------------------------
    # 5.3 Procurar arquivos DBC
    # -------------------------------------------------------------------------

    # Procuramos tanto .dbc quanto .DBC.
    #
    # Isso torna o script mais robusto caso alguns arquivos tenham
    # extensão em maiúsculas.

    arquivos_dbc = sorted(
        list(PASTA_TRABALHO.glob("*.dbc"))
        + list(PASTA_TRABALHO.glob("*.DBC"))
    )

    # Remove eventuais duplicidades.
    arquivos_dbc = sorted(set(arquivos_dbc))

    print()
    print(f"Arquivos DBC encontrados: {len(arquivos_dbc)}")

    # -------------------------------------------------------------------------
    # 5.4 Nenhum arquivo encontrado
    # -------------------------------------------------------------------------

    if not arquivos_dbc:

        print()
        print("Nenhum arquivo .dbc foi encontrado.")
        print()
        print("Conteúdo atual da pasta:")

        for item in sorted(PASTA_TRABALHO.iterdir()):
            print(f"  - {item.name}")

        return 0

    # -------------------------------------------------------------------------
    # 5.5 Mostrar a lista de arquivos
    # -------------------------------------------------------------------------

    print()

    for numero, arquivo in enumerate(arquivos_dbc, start=1):
        print(f"  {numero:02d}. {arquivo.name}")

    # -------------------------------------------------------------------------
    # 5.6 Confirmar antes de iniciar o processamento
    # -------------------------------------------------------------------------

    print()
    resposta = input(
        "Deseja iniciar a conversão desses arquivos? [S/n]: "
    ).strip().lower()

    if resposta not in ("", "s", "sim", "y", "yes"):

        print()
        print("Conversão cancelada pelo usuário.")

        return 0

    # -------------------------------------------------------------------------
    # 5.7 Processar os arquivos
    # -------------------------------------------------------------------------

    total = len(arquivos_dbc)
    sucessos = 0
    falhas = 0

    for numero, arquivo_dbc in enumerate(arquivos_dbc, start=1):

        print()
        print()
        print(f"PROCESSANDO ARQUIVO {numero} DE {total}")

        sucesso = converter_dbc_para_csv(arquivo_dbc)

        if sucesso:
            sucessos += 1
        else:
            falhas += 1

    # -------------------------------------------------------------------------
    # 5.8 Resumo final
    # -------------------------------------------------------------------------

    print()
    print()
    linha()

    print("CONVERSÃO FINALIZADA")
    print()

    print(f"Total de DBC encontrados : {total}")
    print(f"Conversões com sucesso   : {sucessos}")
    print(f"Conversões com erro      : {falhas}")

    print()
    print("Pasta dos resultados:")
    print(f"  {PASTA_TRABALHO}")

    linha()

    # -------------------------------------------------------------------------
    # 5.9 Mostrar os CSV encontrados após o processamento
    # -------------------------------------------------------------------------

    print()
    print("Arquivos CSV na pasta:")

    arquivos_csv = sorted(PASTA_TRABALHO.glob("*.csv"))

    if arquivos_csv:

        for arquivo_csv in arquivos_csv:

            # stat().st_size retorna o tamanho do arquivo em bytes.
            tamanho_mb = arquivo_csv.stat().st_size / (1024 * 1024)

            print(
                f"  - {arquivo_csv.name} "
                f"({tamanho_mb:,.1f} MB)"
            )

    else:

        print("  Nenhum CSV encontrado.")

    print()

    # Código de retorno do programa:
    #
    # 0 = execução concluída
    # 1 = houve pelo menos uma falha.

    if falhas > 0:
        return 1

    return 0


# =============================================================================
# 6. PONTO DE ENTRADA
# =============================================================================

# Este bloco faz com que main() seja executada quando o arquivo é chamado
# diretamente pelo Python:
#
#     python converter_dbc_para_csv.py
#
# Se este arquivo for importado por outro programa, main() não será
# executada automaticamente.

if __name__ == "__main__":

    sys.exit(main())
