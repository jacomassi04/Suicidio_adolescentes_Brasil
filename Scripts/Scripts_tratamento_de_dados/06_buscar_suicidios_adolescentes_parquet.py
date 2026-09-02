#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
06 - BUSCAR SUICÍDIOS DE ADOLESCENTES NO SIM
===============================================================================

OBJETIVO
--------
Ler os arquivos Parquet do SIM (Sistema de Informação sobre Mortalidade),
identificar os óbitos por suicídio entre adolescentes de 10 a 19 anos
e gerar um arquivo CSV consolidado para as etapas seguintes do projeto.

CRITÉRIOS DO PROJETO
--------------------
- Causa básica: CID-10 X60 até X84
- Idade: 10 até 19 anos
- Município: CODMUNRES (município de residência)
- Período: 2013 até 2024

ARQUITETURA DOS DADOS
---------------------
GitHub
    -> scripts e documentação

Google Drive
    -> 01_RAW       : dados originais
    -> 02_PROCESSED : dados tratados, incluindo Parquet
    -> 03_FINAL     : bases finais para análise/modelagem

IMPORTANTE
----------
Este script NÃO altera os arquivos Parquet originais.
Ele apenas lê os arquivos e grava o resultado final em 03_FINAL/SIM.
===============================================================================
"""

# =============================================================================
# 1. IMPORTAÇÃO DAS BIBLIOTECAS
# =============================================================================
# Path       : permite trabalhar com caminhos de arquivos de forma segura.
# pandas     : leitura, filtragem e manipulação dos dados.
# pyarrow    : leitura eficiente da estrutura dos arquivos Parquet.
# re         : expressões regulares para interpretar a variável IDADE.
# csv        : escrita do arquivo CSV final.
# sys        : encerramento do programa em caso de erro.
# =============================================================================

from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import re
import csv
import sys


# =============================================================================
# 2. CONFIGURAÇÃO GERAL DO PROJETO
# =============================================================================

ANO_INICIAL = 2013
ANO_FINAL = 2024

IDADE_MINIMA = 10
IDADE_MAXIMA = 19

# Prefixos de causa básica de morte classificados como suicídio.
CID_INICIAL = "X60"
CID_FINAL = "X84"


# =============================================================================
# 3. CAMINHOS DOS DADOS
# =============================================================================
# Os scripts ficam no GitHub, mas os dados ficam no Google Drive.
#
# Por isso NÃO usamos:
#
# PROJECT_ROOT / "02_PROCESSED" / "SIM"
#
# porque PROJECT_ROOT seria o diretório do GitHub.
#
# Aqui apontamos explicitamente para a pasta do projeto no Google Drive.
# =============================================================================

GOOGLE_DRIVE_PROJECT = Path(
    "/Users/claudiojacomassi/Library/CloudStorage/"
    "GoogleDrive-claudio.jacomassi@gmail.com/"
    ".shortcut-targets-by-id/1KAgdHCMybmn_N4ImZ9y8JkT_YdxXUDLk/"
    "PUC SP/Suicidio_adolescentes_Brasil"
)

# Pasta contendo os Parquets tratados do SIM.
PROCESSED_DIR = GOOGLE_DRIVE_PROJECT / "02_PROCESSED" / "SIM"

# Pasta onde será salvo o resultado final.
FINAL_DIR = GOOGLE_DRIVE_PROJECT / "03_FINAL" / "SIM"

# Nome do arquivo final.
OUTPUT_FILE = FINAL_DIR / "suicidios_adolescentes_2013_2024.csv"


# =============================================================================
# 4. VARIÁVEIS DO SIM QUE QUEREMOS PRESERVAR
# =============================================================================
# Algumas variáveis são fundamentais para o projeto.
#
# CAUSABAS : causa básica da morte
# CODMUNRES : município de residência
# DTOBITO : data do óbito
# IDADE : idade codificada no SIM
#
# As demais variáveis abaixo podem ser úteis posteriormente para análise
# descritiva e/ou modelagem.
# =============================================================================

VARIAVEIS_PRINCIPAIS = [
    "CAUSABAS",
    "CODMUNRES",
    "DTOBITO",
    "IDADE",
]

VARIAVEIS_EXTRAS = [
    "SEXO",
    "RACACOR",
    "ESC2010",
    "ESTCIV",
    "SERIESCFAL",
    "OCUP",
    "LOCOCOR",
    "CODMUNOCOR",
    "ESCMAE",
    "ESCMAE2010",
    "SERIESCMAE",
    "OCUPMAE",
    "GRAVIDEZ",
    "PESO",
    "ASSISTMED",
    "NECROPSIA",
    "TPPOS",
    "CAUSABAS_O",
    "FONTEINV",
    "CIRCOBITO",
]

# Variáveis que serão procuradas nos arquivos.
TODAS_VARIAVEIS = VARIAVEIS_PRINCIPAIS + VARIAVEIS_EXTRAS


# =============================================================================
# 5. FUNÇÃO PARA VERIFICAR AS PASTAS
# =============================================================================
# Antes de começar a ler arquivos, verificamos se:
#
# 1. O projeto existe no Google Drive.
# 2. A pasta 02_PROCESSED/SIM existe.
# 3. A pasta 03_FINAL/SIM pode ser criada.
#
# Isso evita erros pouco claros mais adiante.
# =============================================================================

def verificar_pastas():
    """Verifica se as pastas de entrada e saída existem."""

    print("\nVerificando estrutura de pastas...")

    if not GOOGLE_DRIVE_PROJECT.exists():
        raise FileNotFoundError(
            "\nPasta do projeto no Google Drive não encontrada:\n"
            f"{GOOGLE_DRIVE_PROJECT}"
        )

    if not PROCESSED_DIR.exists():
        raise FileNotFoundError(
            "\nPasta 02_PROCESSED/SIM não encontrada:\n"
            f"{PROCESSED_DIR}"
        )

    # Cria a pasta final caso ainda não exista.
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    print("  [OK] Pasta do projeto encontrada")
    print(f"  [OK] Entrada : {PROCESSED_DIR}")
    print(f"  [OK] Saída   : {FINAL_DIR}")


# =============================================================================
# 6. LOCALIZAR OS ARQUIVOS PARQUET DE MORTALIDADE
# =============================================================================
# IMPORTANTE:
#
# A pasta também contém o dicionário de variáveis em formato Parquet.
#
# Portanto NÃO podemos simplesmente usar:
#
#     *.parquet
#
# porque isso faria o programa tentar processar o dicionário como se fosse
# uma base de mortalidade.
#
# Os arquivos que queremos possuem o padrão:
#
#     Mortalidade_Geral_YYYY.parquet
#
# Por isso usamos:
#
#     Mortalidade_Geral_*.parquet
#
# Dessa forma o dicionário fica automaticamente fora do processamento.
# =============================================================================

def localizar_parquets():
    """Localiza somente os Parquets de mortalidade do SIM."""

    arquivos = sorted(
        PROCESSED_DIR.glob("Mortalidade_Geral_*.parquet")
    )

    if not arquivos:
        raise FileNotFoundError(
            "\nNenhum arquivo Parquet de mortalidade foi encontrado em:\n"
            f"{PROCESSED_DIR}"
        )

    print(
        f"\nArquivos Parquet de mortalidade encontrados: "
        f"{len(arquivos)}"
    )

    for arquivo in arquivos:
        print(f"  - {arquivo.name}")

    return arquivos


# =============================================================================
# 7. IDENTIFICAR O ANO DO ARQUIVO
# =============================================================================
# O nome dos Parquets normalmente contém o ano.
#
# Exemplo:
#     Mortalidade_Geral_2019.parquet
#
# Usamos uma expressão regular para procurar um ano entre 2013 e 2024.
#
# Se o ano não estiver no nome, retornamos None e posteriormente tentaremos
# obter o ano através de DTOBITO.
# =============================================================================

def obter_ano_do_nome(caminho):
    """Tenta identificar o ano no nome do arquivo."""

    encontrados = re.findall(r"(20\d{2})", caminho.name)

    for texto in encontrados:
        ano = int(texto)

        if ANO_INICIAL <= ano <= ANO_FINAL:
            return ano

    return None


# =============================================================================
# 8. DECODIFICAR A VARIÁVEL IDADE
# =============================================================================
# A variável IDADE do SIM utiliza códigos.
#
# Para idade em anos, os códigos 410 a 419 representam aproximadamente:
#
#     410 -> 10 anos
#     411 -> 11 anos
#     ...
#     419 -> 19 anos
#
# Como os dados são lidos como texto, primeiro limpamos o valor.
#
# A função retorna a idade em anos ou NA quando não consegue interpretar.
# =============================================================================

def decodificar_idade(valor):
    """Converte o código IDADE do SIM para idade em anos."""

    if pd.isna(valor):
        return pd.NA

    texto = str(valor).strip()

    if not texto:
        return pd.NA

    # Aceita valores que eventualmente tenham sido lidos como 410.0.
    texto = texto.split(".")[0]

    if not texto.isdigit():
        return pd.NA

    codigo = int(texto)

    # Códigos 410 a 419 correspondem a 10 a 19 anos.
    if 410 <= codigo <= 419:
        return codigo - 400

    # Alguns arquivos/processamentos podem eventualmente trazer
    # a idade já em anos. Mantemos essa possibilidade como fallback.
    if 10 <= codigo <= 19:
        return codigo

    return pd.NA


# =============================================================================
# 9. VERIFICAR SE A CAUSA É SUICÍDIO
# =============================================================================
# O critério principal do projeto é a CAUSABAS.
#
# Suicídio:
#     X60 até X84
#
# Não usamos CIRCOBITO como critério principal.
#
# CIRCOBITO pode ser utilizado como variável de apoio/validação,
# mas a classificação principal vem de CAUSABAS.
# =============================================================================

def mascara_suicidio(serie):
    """Retorna uma máscara booleana para causas X60-X84."""

    texto = (
        serie
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # Extrai somente os três primeiros caracteres da CID.
    cid = texto.str[:3]

    # Verifica se começa com X e possui número entre 60 e 84.
    numero = pd.to_numeric(
        cid.str.extract(r"X(\d{2})", expand=False),
        errors="coerce",
    )

    return (
        numero.ge(60)
        & numero.le(84)
    )


# =============================================================================
# 10. IDENTIFICAR O ANO DO ÓBITO
# =============================================================================
# DTOBITO é a data de óbito.
#
# Tentamos primeiro interpretar a data.
# O parâmetro dayfirst=True é importante para dados brasileiros no formato
# dia/mês/ano.
#
# Se a data não puder ser interpretada, utilizamos o ano encontrado no
# nome do arquivo como fallback.
# =============================================================================

def obter_ano_obito(df, ano_arquivo):
    """Cria uma série com o ano do óbito."""

    if "DTOBITO" not in df.columns:
        if ano_arquivo is not None:
            return pd.Series(
                ano_arquivo,
                index=df.index,
                dtype="Int64",
            )

        return pd.Series(
            pd.NA,
            index=df.index,
            dtype="Int64",
        )

    datas = pd.to_datetime(
        df["DTOBITO"],
        errors="coerce",
        dayfirst=True,
    )

    anos = datas.dt.year.astype("Int64")

    # Onde não foi possível obter o ano pela data, usamos o ano do arquivo.
    if ano_arquivo is not None:
        anos = anos.fillna(ano_arquivo)

    return anos


# =============================================================================
# 11. LER UM ARQUIVO PARQUET
# =============================================================================
# Primeiro verificamos quais colunas existem no Parquet.
#
# Isso é feito através do schema do Parquet, sem carregar o arquivo inteiro
# apenas para descobrir os nomes das colunas.
#
# Depois carregamos somente as colunas necessárias.
#
# Isso reduz memória e tempo de processamento.
# =============================================================================

def ler_parquet(caminho):
    """Lê somente as colunas necessárias de um Parquet."""

    print(f"\nLendo: {caminho.name}")

    parquet_file = pq.ParquetFile(caminho)

    colunas_disponiveis = parquet_file.schema_arrow.names

    # Descobre quais das nossas variáveis existem neste arquivo.
    colunas_para_ler = [
        coluna
        for coluna in TODAS_VARIAVEIS
        if coluna in colunas_disponiveis
    ]

    # CAUSABAS e IDADE são obrigatórias para este processo.
    obrigatorias = ["CAUSABAS", "IDADE"]

    faltantes = [
        coluna
        for coluna in obrigatorias
        if coluna not in colunas_disponiveis
    ]

    if faltantes:
        raise ValueError(
            f"\nO arquivo {caminho.name} não possui "
            f"as variáveis obrigatórias: {faltantes}"
        )

    df = pd.read_parquet(
        caminho,
        columns=colunas_para_ler,
    )

    print(f"  Registros lidos: {len(df):,}")
    print(f"  Colunas lidas  : {len(df.columns)}")

    return df


# =============================================================================
# 12. PROCESSAR UM ARQUIVO
# =============================================================================
# Aqui acontece o núcleo da seleção:
#
# 1. Identificar suicídios X60-X84.
# 2. Decodificar idade.
# 3. Manter 10-19 anos.
# 4. Determinar ano.
# 5. Manter 2013-2024.
# 6. Adicionar ano e arquivo de origem.
#
# O resultado contém somente os óbitos que atendem aos critérios.
# =============================================================================

def processar_arquivo(caminho):
    """Processa um arquivo Parquet e retorna somente suicídios 10-19."""

    ano_arquivo = obter_ano_do_nome(caminho)

    df = ler_parquet(caminho)

    # -------------------------------------------------------------------------
    # ETAPA A - selecionar causa básica X60-X84
    # -------------------------------------------------------------------------

    mascara_cid = mascara_suicidio(df["CAUSABAS"])

    df = df.loc[mascara_cid].copy()

    print(f"  Após filtro X60-X84: {len(df):,}")

    if df.empty:
        return df

    # -------------------------------------------------------------------------
    # ETAPA B - transformar IDADE codificada em idade em anos
    # -------------------------------------------------------------------------

    df["IDADE_ANOS"] = df["IDADE"].apply(decodificar_idade)

    # Mantém somente 10 a 19 anos.
    df = df[
        df["IDADE_ANOS"].between(
            IDADE_MINIMA,
            IDADE_MAXIMA,
            inclusive="both",
        )
    ].copy()

    print(f"  Após filtro 10-19 anos: {len(df):,}")

    if df.empty:
        return df

    # -------------------------------------------------------------------------
    # ETAPA C - determinar o ano do óbito
    # -------------------------------------------------------------------------

    df["ANO"] = obter_ano_obito(
        df,
        ano_arquivo,
    )

    # Mantém somente 2013-2024.
    df = df[
        df["ANO"].between(
            ANO_INICIAL,
            ANO_FINAL,
            inclusive="both",
        )
    ].copy()

    # -------------------------------------------------------------------------
    # ETAPA D - registrar a origem
    # -------------------------------------------------------------------------

    df["ARQUIVO_ORIGEM"] = caminho.name

    print(f"  Registros selecionados: {len(df):,}")

    return df


# =============================================================================
# 13. PADRONIZAR AS COLUNAS
# =============================================================================
# Arquivos de anos diferentes podem não possuir exatamente as mesmas colunas.
#
# Para poder concatenar tudo, criamos as colunas ausentes com NA.
#
# Assim, 2013, por exemplo, não quebra o processamento caso alguma variável
# tenha surgido somente em anos posteriores.
# =============================================================================

def padronizar_colunas(df):
    """Garante que o DataFrame tenha todas as colunas esperadas."""

    colunas_finais = (
        VARIAVEIS_PRINCIPAIS
        + VARIAVEIS_EXTRAS
        + ["IDADE_ANOS", "ANO", "ARQUIVO_ORIGEM"]
    )

    for coluna in colunas_finais:
        if coluna not in df.columns:
            df[coluna] = pd.NA

    return df[colunas_finais]


# =============================================================================
# 14. GERAR RESUMO DA BASE
# =============================================================================
# Depois de juntar todos os anos, mostramos algumas estatísticas simples.
#
# Isso é uma etapa de CONTROLE DE QUALIDADE.
# Não é ainda a análise estatística final.
# =============================================================================

def mostrar_resumo(df):
    """Mostra estatísticas básicas da base selecionada."""

    print("\n")
    print("=" * 72)
    print("RESUMO DA BASE")
    print("=" * 72)

    print(f"Total de suicídios adolescentes: {len(df):,}")

    if df.empty:
        return

    print("\nÓbitos por ano:")
    por_ano = (
        df["ANO"]
        .value_counts()
        .sort_index()
    )

    for ano, quantidade in por_ano.items():
        print(f"  {int(ano)}: {quantidade:,}")

    print("\nÓbitos por idade:")
    por_idade = (
        df["IDADE_ANOS"]
        .value_counts()
        .sort_index()
    )

    for idade, quantidade in por_idade.items():
        print(f"  {int(idade)} anos: {quantidade:,}")

    if "SEXO" in df.columns:
        print("\nÓbitos por SEXO:")
        print(df["SEXO"].value_counts(dropna=False).to_string())

    print("\nMunicípios distintos:")
    if "CODMUNRES" in df.columns:
        municipios = (
            df["CODMUNRES"]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )

        print(f"  {municipios:,}")


# =============================================================================
# 15. SALVAR O RESULTADO FINAL
# =============================================================================
# O arquivo é salvo em 03_FINAL/SIM.
#
# sep=";" é usado porque é o padrão que estamos adotando para os CSVs
# do projeto.
#
# UTF-8-SIG facilita a abertura no Excel em ambientes Windows.
#
# index=False impede que o índice do pandas vire uma coluna extra.
# =============================================================================

def salvar_resultado(df):
    """Salva a base final em CSV."""

    FINAL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\nSalvando resultado...")
    print(f"Arquivo: {OUTPUT_FILE}")

    df.to_csv(
        OUTPUT_FILE,
        sep=";",
        encoding="utf-8-sig",
        index=False,
        quoting=csv.QUOTE_MINIMAL,
    )

    print("\n[OK] Arquivo salvo com sucesso.")
    print(f"     {OUTPUT_FILE}")
    print(f"     Registros: {len(df):,}")
    print(f"     Colunas  : {len(df.columns)}")


# =============================================================================
# 16. FUNÇÃO PRINCIPAL
# =============================================================================
# main() organiza a sequência completa:
#
# verificar -> localizar -> processar -> juntar -> padronizar -> resumir
# -> salvar.
#
# Manter essa sequência organizada torna o script mais fácil de entender
# e de modificar posteriormente.
# =============================================================================

def main():

    print("=" * 72)
    print("SIM - SUICÍDIOS DE ADOLESCENTES 10-19 ANOS")
    print("=" * 72)

    print("\nCritérios:")
    print("  CID-10      : X60-X84")
    print("  Idade       : 10-19 anos")
    print("  Município   : CODMUNRES")
    print("  Período     : 2013-2024")

    # -------------------------------------------------------------------------
    # Verificação da estrutura de diretórios.
    # -------------------------------------------------------------------------

    verificar_pastas()

    # -------------------------------------------------------------------------
    # Localização dos Parquets.
    # -------------------------------------------------------------------------

    arquivos = localizar_parquets()

    resultados = []

    # -------------------------------------------------------------------------
    # Processamento de cada ano.
    # -------------------------------------------------------------------------

    for numero, arquivo in enumerate(arquivos, start=1):

        print("\n" + "-" * 72)
        print(f"ARQUIVO {numero}/{len(arquivos)}")
        print("-" * 72)

        try:
            resultado = processar_arquivo(arquivo)

            if not resultado.empty:
                resultado = padronizar_colunas(resultado)
                resultados.append(resultado)

        except Exception as erro:
            print(f"\n[ERRO] Falha ao processar {arquivo.name}")
            print(f"       {erro}")

            # Interrompe o processamento porque um erro em um ano
            # pode comprometer a base consolidada.
            raise

    # -------------------------------------------------------------------------
    # Verificar se encontramos algum registro.
    # -------------------------------------------------------------------------

    if not resultados:
        print("\nNenhum suicídio de adolescente foi encontrado.")
        return

    # -------------------------------------------------------------------------
    # Concatenar todos os anos.
    # -------------------------------------------------------------------------

    print("\n")
    print("=" * 72)
    print("CONSOLIDANDO OS ANOS")
    print("=" * 72)

    df_final = pd.concat(
        resultados,
        ignore_index=True,
    )

    # Ordenação para facilitar inspeção e análises posteriores.
    colunas_ordenacao = [
        coluna
        for coluna in ["ANO", "CODMUNRES", "IDADE_ANOS"]
        if coluna in df_final.columns
    ]

    if colunas_ordenacao:
        df_final = df_final.sort_values(
            by=colunas_ordenacao,
            kind="stable",
        ).reset_index(drop=True)

    print(f"Total consolidado: {len(df_final):,}")

    # -------------------------------------------------------------------------
    # Resumo de controle de qualidade.
    # -------------------------------------------------------------------------

    mostrar_resumo(df_final)

    # -------------------------------------------------------------------------
    # Salvar arquivo final.
    # -------------------------------------------------------------------------

    salvar_resultado(df_final)

    print("\n")
    print("=" * 72)
    print("PROCESSAMENTO CONCLUÍDO")
    print("=" * 72)


# =============================================================================
# 17. EXECUÇÃO DO SCRIPT
# =============================================================================
# Esta condição garante que main() seja executada quando o arquivo for
# chamado diretamente pelo Python:
#
#     python 06_buscar_suicidios_adolescentes_parquet.py
#
# mas não seja executada automaticamente se o arquivo for importado por
# outro script.
# =============================================================================

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\n\nProcessamento interrompido pelo usuário.")
        sys.exit(1)

    except Exception as erro:
        print("\n")
        print("=" * 72)
        print("ERRO DURANTE O PROCESSAMENTO")
        print("=" * 72)
        print(erro)
        sys.exit(1)
