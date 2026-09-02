"""
================================================================================
CONVERSOR SIM: CSV -> PARQUET
Projeto: Suicídio em adolescentes no Brasil
Curso: Inteligência Artificial - PUC-SP

OBJETIVO
--------
Converter os arquivos anuais do SIM (Sistema de Informação sobre Mortalidade)
de CSV para Parquet, mantendo os nomes OFICIAIS das variáveis.

Exemplos:
    CODMUNRES
    IDADE
    CAUSABAS
    SEXO
    RACACOR

As descrições oficiais das variáveis NÃO serão colocadas como nomes das
colunas. Elas serão armazenadas nos METADADOS do arquivo Parquet.

Por que fazemos isso?
---------------------
1. Os nomes oficiais são estáveis e facilitam a programação.
2. Podemos usar diretamente nomes como CODMUNRES, IDADE e CAUSABAS no código.
3. As descrições oficiais continuam disponíveis para documentação.
4. Evitamos criar colunas com nomes muito longos ou caracteres especiais.
5. Mantemos uma separação clara entre:
       - DADO: nome oficial da variável
       - DOCUMENTAÇÃO: descrição oficial da variável

ATENÇÃO
-------
Este programa NÃO altera os arquivos CSV originais da pasta RAW.

Fluxo:

    01_RAW/SIM/*.csv
            |
            | leitura
            v
    02_PROCESSED/SIM/*.parquet
            |
            +--> nomes oficiais das colunas preservados
            |
            +--> descrições oficiais armazenadas nos metadados
            |
            +--> arquivo de origem registrado nos metadados

================================================================================
"""

# ==============================================================================
# BLOCO 1 — IMPORTAÇÃO DAS BIBLIOTECAS
# ==============================================================================

# Path facilita a criação e manipulação de caminhos de arquivos e pastas.
from pathlib import Path

# json será usado para guardar o dicionário de descrições dentro dos
# metadados do Parquet.
import json

# pandas é utilizado para ler os arquivos CSV e criar DataFrames.
import pandas as pd

# pyarrow permite trabalhar diretamente com o formato Parquet.
import pyarrow as pa
import pyarrow.parquet as pq


# ==============================================================================
# BLOCO 2 — DEFINIÇÃO DA PASTA RAW
# ==============================================================================

# RAW_DIR aponta para os arquivos CSV originais do SIM.
#
# RAW significa "dados brutos/originais".
#
# Uma regra importante do nosso projeto é:
#
#       RAW não deve ser alterado.
#
# Assim, podemos sempre voltar aos dados originais se encontrarmos algum
# problema durante o processamento.
RAW_DIR = Path(
    "/Users/claudiojacomassi/Library/CloudStorage/"
    "GoogleDrive-claudio.jacomassi@gmail.com/"
    ".shortcut-targets-by-id/"
    "1KAgdHCMybmn_N4ImZ9y8JkT_YdxXUDLk/"
    "PUC SP/Suicidio_adolescentes_Brasil/"
    "01_RAW/SIM"
)


# ==============================================================================
# BLOCO 3 — DEFINIÇÃO DA PASTA DE SAÍDA
# ==============================================================================

# OUTPUT_DIR é a pasta onde serão gravados os arquivos Parquet.
#
# Estamos seguindo a organização:
#
#       01_RAW
#       02_PROCESSED
#
# O RAW contém os arquivos originais.
# O PROCESSED contém arquivos transformados para facilitar a análise.
OUTPUT_DIR = Path(
    "/Users/claudiojacomassi/Library/CloudStorage/"
    "GoogleDrive-claudio.jacomassi@gmail.com/"
    ".shortcut-targets-by-id/"
    "1KAgdHCMybmn_N4ImZ9y8JkT_YdxXUDLk/"
    "PUC SP/Suicidio_adolescentes_Brasil/"
    "02_PROCESSED/SIM"
)


# ==============================================================================
# BLOCO 4 — LOCALIZAÇÃO DO DICIONÁRIO OFICIAL
# ==============================================================================

# O dicionário contém, entre outras informações:
#
#       VARIAVEL
#       DESCRICAO_OFICIAL
#
# Por exemplo, conceitualmente:
#
#       CODMUNRES -> Código do município de residência
#
# O programa usa esse arquivo somente para documentação.
DICTIONARY_FILE = RAW_DIR / (
    "dicionario_variaveis_SIM_oficial_projeto_suicidio_adolescentes.csv"
)


# ==============================================================================
# BLOCO 5 — CONFIGURAÇÕES DOS ARQUIVOS
# ==============================================================================

# Os arquivos SIM do nosso projeto estão em formato CSV separado por ponto e
# vírgula.
#
# Exemplo:
#
#       CODMUNRES;IDADE;CAUSABAS;SEXO
#
# Por isso usamos:
SEP = ";"

# Os arquivos do SIM que estamos trabalhando utilizam a codificação Latin-1.
#
# Essa codificação é importante porque os dados podem conter caracteres
# acentuados.
ENCODING_CSV = "latin1"

# O dicionário fornecido para o projeto foi salvo em UTF-8 com BOM.
# utf-8-sig consegue ler tanto UTF-8 comum quanto UTF-8 com BOM.
ENCODING_DICTIONARY = "utf-8-sig"


# ==============================================================================
# BLOCO 6 — VERIFICAÇÃO DAS PASTAS E DO DICIONÁRIO
# ==============================================================================

# Antes de começar, verificamos se a pasta RAW realmente existe.
#
# Isso evita que o programa avance e apresente um erro pouco claro mais tarde.
if not RAW_DIR.exists():
    raise FileNotFoundError(
        "A pasta RAW do SIM não foi encontrada:\n"
        f"{RAW_DIR}\n\n"
        "Verifique o caminho do Google Drive."
    )


# Verificamos se o dicionário oficial está presente.
if not DICTIONARY_FILE.exists():
    raise FileNotFoundError(
        "O dicionário oficial do SIM não foi encontrado:\n"
        f"{DICTIONARY_FILE}"
    )


# Criamos a pasta de saída se ela ainda não existir.
#
# parents=True:
#   cria também pastas intermediárias, se necessário.
#
# exist_ok=True:
#   não gera erro se a pasta já existir.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# BLOCO 7 — LEITURA DO DICIONÁRIO OFICIAL
# ==============================================================================

print("=" * 80)
print("CONVERSOR SIM — CSV PARA PARQUET")
print("=" * 80)

print("\nLendo o dicionário oficial...")
print(f"Dicionário: {DICTIONARY_FILE}")


# Lemos o dicionário como texto.
#
# dtype=str é importante porque códigos e valores do SIM não devem ser
# convertidos automaticamente para números.
dictionary = pd.read_csv(
    DICTIONARY_FILE,
    sep=";",
    encoding=ENCODING_DICTIONARY,
    dtype=str,
)


# Retiramos espaços desnecessários dos nomes das colunas do próprio dicionário.
dictionary.columns = dictionary.columns.str.strip()


# ==============================================================================
# BLOCO 8 — VERIFICAÇÃO DAS COLUNAS DO DICIONÁRIO
# ==============================================================================

# Para o nosso processo, precisamos obrigatoriamente destas duas colunas.
required_dictionary_columns = [
    "VARIAVEL",
    "DESCRICAO_OFICIAL",
]


for column in required_dictionary_columns:
    if column not in dictionary.columns:
        raise ValueError(
            f"A coluna obrigatória '{column}' não existe no dicionário."
        )


# ==============================================================================
# BLOCO 9 — LIMPEZA DO DICIONÁRIO
# ==============================================================================

# fillna("") transforma valores ausentes em texto vazio.
#
# Depois usamos strip() para remover espaços no início e no fim.
dictionary["VARIAVEL"] = (
    dictionary["VARIAVEL"]
    .fillna("")
    .astype(str)
    .str.strip()
)

dictionary["DESCRICAO_OFICIAL"] = (
    dictionary["DESCRICAO_OFICIAL"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# ==============================================================================
# BLOCO 10 — CRIAÇÃO DO MAPA VARIÁVEL -> DESCRIÇÃO
# ==============================================================================

# Vamos transformar o DataFrame do dicionário em um dicionário Python.
#
# Exemplo conceitual:
#
# {
#     "CODMUNRES": "Código do município de residência",
#     "IDADE": "Idade",
#     "CAUSABAS": "Causa básica da morte"
# }
#
# Esse mapa será utilizado para criar os metadados do Parquet.
variable_to_description = {}


for _, row in dictionary.iterrows():

    # Nome oficial da variável.
    variable = row["VARIAVEL"]

    # Descrição oficial correspondente.
    description = row["DESCRICAO_OFICIAL"]

    # Se a linha não tiver nome de variável, ignoramos.
    if not variable:
        continue

    # Se não houver descrição, usamos o próprio nome da variável como
    # fallback. Assim nunca ficamos com uma entrada sem valor.
    if not description or description == "—":
        description = variable

    # Guarda a relação:
    #       nome oficial -> descrição oficial
    variable_to_description[variable] = description


print(f"\nVariáveis encontradas no dicionário: {len(variable_to_description)}")


# ==============================================================================
# BLOCO 11 — LOCALIZAÇÃO DOS CSVs DO SIM
# ==============================================================================

# Procuramos somente arquivos CSV diretamente dentro da pasta RAW/SIM.
#
# O dicionário também é um CSV, portanto ele será explicitamente excluído.
#
# O backup de 2022 chamado:
#
#   Mortalidade_Geral_2022_colon_separator.csv
#
# está em uma subpasta ("zip and dbf files") e, portanto, não será encontrado
# por glob("*.csv") nesta pasta principal.
csv_files = sorted(
    file
    for file in RAW_DIR.glob("*.csv")
    if file.name != DICTIONARY_FILE.name
)


# Se nenhum CSV for encontrado, não há trabalho a executar.
if not csv_files:
    raise FileNotFoundError(
        "Nenhum arquivo CSV do SIM foi encontrado em:\n"
        f"{RAW_DIR}"
    )


print(f"Arquivos CSV encontrados: {len(csv_files)}")


# ==============================================================================
# BLOCO 12 — PROCESSAMENTO DE CADA ANO
# ==============================================================================

# Cada CSV será convertido individualmente.
#
# Exemplo:
#
#       Mortalidade_Geral_2013.csv
#                  |
#                  v
#       Mortalidade_Geral_2013.parquet
#
#       Mortalidade_Geral_2014.csv
#                  |
#                  v
#       Mortalidade_Geral_2014.parquet
#
# e assim por diante.
for csv_file in csv_files:

    print("\n" + "-" * 80)
    print(f"Processando: {csv_file.name}")
    print("-" * 80)

    # O nome do Parquet será igual ao nome do CSV, apenas trocando a extensão.
    #
    # stem:
    #       Mortalidade_Geral_2022
    #
    # resultará em:
    #       Mortalidade_Geral_2022.parquet
    parquet_file = OUTPUT_DIR / (csv_file.stem + ".parquet")

    print(f"Saída: {parquet_file}")


    # ==========================================================================
    # BLOCO 12.1 — LEITURA DO CSV
    # ==========================================================================

    # Lemos todas as colunas como texto.
    #
    # Isso é deliberado.
    #
    # No SIM existem códigos que podem parecer números, mas são categorias ou
    # códigos. Se o pandas fizer inferência automática de tipos, podemos perder
    # zeros à esquerda ou misturar tipos.
    #
    # Exemplo:
    #
    #       "01001"
    #
    # poderia virar:
    #
    #       1001
    #
    # e perder a informação original.
    df = pd.read_csv(
        csv_file,
        sep=SEP,
        encoding=ENCODING_CSV,
        dtype=str,
        low_memory=False,
    )


    # ==========================================================================
    # BLOCO 12.2 — PRESERVAÇÃO DOS NOMES OFICIAIS
    # ==========================================================================

    # Guardamos os nomes das colunas exatamente como vieram do CSV,
    # removendo apenas espaços acidentais no começo/fim.
    #
    # IMPORTANTE:
    #
    # NÃO usamos aqui as descrições do dicionário para renomear as colunas.
    #
    # Portanto:
    #
    #       CODMUNRES
    #
    # continua sendo:
    #
    #       CODMUNRES
    #
    # e não:
    #
    #       Código do município de residência
    #
    # Essa é uma decisão importante da arquitetura do projeto.
    original_columns = [
        str(column).strip()
        for column in df.columns
    ]


    # Aplicamos os nomes oficiais limpos ao DataFrame.
    df.columns = original_columns


    # ==========================================================================
    # BLOCO 12.3 — VERIFICAÇÃO DE NOMES DUPLICADOS
    # ==========================================================================

    # Em condições normais, cada variável deve aparecer apenas uma vez.
    #
    # Entretanto, fazemos uma verificação explícita para evitar gerar um
    # Parquet ambíguo.
    duplicated_columns = [
        column
        for column in pd.Series(original_columns)
        .loc[lambda s: s.duplicated(keep=False)]
        .unique()
    ]


    if duplicated_columns:
        raise ValueError(
            "Foram encontradas colunas duplicadas no arquivo:\n"
            f"{duplicated_columns}\n"
            f"Arquivo: {csv_file.name}"
        )


    # ==========================================================================
    # BLOCO 12.4 — IDENTIFICAÇÃO DAS VARIÁVEIS SEM DESCRIÇÃO
    # ==========================================================================

    # Verificamos quais colunas do CSV não aparecem no dicionário.
    #
    # Isso pode acontecer porque:
    #
    # - o layout do SIM mudou ao longo dos anos;
    # - uma variável nova foi acrescentada;
    # - o dicionário do projeto não contém determinada variável.
    #
    # IMPORTANTE:
    #
    # Mesmo que uma variável não esteja no dicionário, ela NÃO será removida.
    #
    # O dado original é preservado.
    not_found = [
        column
        for column in original_columns
        if column not in variable_to_description
    ]


    # ==========================================================================
    # BLOCO 12.5 — CRIAÇÃO DOS METADADOS DAS DESCRIÇÕES
    # ==========================================================================

    # Criamos somente as descrições das variáveis que realmente existem
    # naquele arquivo.
    #
    # Isso é particularmente importante porque os arquivos do SIM não possuem
    # exatamente o mesmo número de colunas em todos os anos.
    descriptions_for_file = {
        column: variable_to_description[column]
        for column in original_columns
        if column in variable_to_description
    }


    # ==========================================================================
    # BLOCO 12.6 — CONVERSÃO PARA ARROW TABLE
    # ==========================================================================

    # O pandas DataFrame é convertido para uma tabela Arrow.
    #
    # preserve_index=False significa que o índice do pandas não será gravado
    # como uma coluna adicional no Parquet.
    table = pa.Table.from_pandas(
        df,
        preserve_index=False,
    )


    # ==========================================================================
    # BLOCO 12.7 — PREPARAÇÃO DOS METADADOS
    # ==========================================================================

    # Um Parquet pode armazenar metadados junto com o schema.
    #
    # Recuperamos os metadados existentes, caso existam.
    metadata = dict(table.schema.metadata or {})


    # --------------------------------------------------------------------------
    # METADADO 1 — ARQUIVO DE ORIGEM
    # --------------------------------------------------------------------------

    # Registramos de qual CSV veio o Parquet.
    #
    # Isso é útil para rastreabilidade.
    metadata[b"arquivo_origem"] = csv_file.name.encode("utf-8")


    # --------------------------------------------------------------------------
    # METADADO 2 — DICIONÁRIO UTILIZADO
    # --------------------------------------------------------------------------

    # Registramos qual dicionário foi usado para documentar as variáveis.
    metadata[b"dicionario_origem"] = DICTIONARY_FILE.name.encode("utf-8")


    # --------------------------------------------------------------------------
    # METADADO 3 — DESCRIÇÕES OFICIAIS
    # --------------------------------------------------------------------------

    # O JSON permite guardar a relação:
    #
    #       nome oficial -> descrição oficial
    #
    # sem alterar os nomes das colunas.
    #
    # ensure_ascii=False mantém caracteres acentuados no JSON.
    descriptions_json = json.dumps(
        descriptions_for_file,
        ensure_ascii=False,
        sort_keys=True,
    )

    metadata[b"sim_descriptions"] = descriptions_json.encode("utf-8")


    # --------------------------------------------------------------------------
    # METADADO 4 — INFORMAÇÃO SOBRE A ESTRATÉGIA
    # --------------------------------------------------------------------------

    metadata[b"descricao"] = (
        "SIM — nomes oficiais das variáveis preservados; "
        "descricoes oficiais armazenadas nos metadados."
    ).encode("utf-8")


    # ==========================================================================
    # BLOCO 12.8 — SUBSTITUIÇÃO DO SCHEMA COM OS METADADOS
    # ==========================================================================

    # O schema continua contendo os nomes oficiais das colunas.
    #
    # Apenas acrescentamos os metadados definidos acima.
    table = table.replace_schema_metadata(metadata)


    # ==========================================================================
    # BLOCO 12.9 — GRAVAÇÃO DO PARQUET
    # ==========================================================================

    # compression="snappy":
    #
    # Snappy é uma compressão muito usada com Parquet porque oferece boa
    # velocidade de leitura/escrita e redução significativa do tamanho.
    pq.write_table(
        table,
        parquet_file,
        compression="snappy",
    )


    # ==========================================================================
    # BLOCO 12.10 — RELATÓRIO DO PROCESSAMENTO
    # ==========================================================================

    print(f"Linhas: {len(df):,}".replace(",", "."))
    print(f"Colunas: {len(df.columns)}")

    print("\nNomes oficiais das colunas preservados.")
    print(f"Descrições encontradas no dicionário: {len(descriptions_for_file)}")

    # Se houver variáveis não encontradas no dicionário, mostramos quais são.
    if not_found:
        print(
            "\nAVISO — variáveis presentes no CSV mas ausentes no dicionário:"
        )

        for column in not_found:
            print(f"  - {column}")

    else:
        print("Todas as colunas deste arquivo possuem descrição no dicionário.")

    print("\nParquet criado com sucesso.")


# ==============================================================================
# BLOCO 13 — FINALIZAÇÃO
# ==============================================================================

print("\n" + "=" * 80)
print("PROCESSAMENTO CONCLUÍDO")
print("=" * 80)

print(f"\nArquivos Parquet gravados em:")
print(OUTPUT_DIR)

print("\nIMPORTANTE:")
print("- Os CSVs originais NÃO foram modificados.")
print("- Os nomes oficiais das variáveis foram preservados.")
print("- As descrições oficiais foram armazenadas nos metadados.")
print("- Os arquivos foram gravados com compressão Snappy.")

print("\nExemplo de utilização futura:")
print("    CODMUNRES")
print("    IDADE")
print("    CAUSABAS")
print("    SEXO")
print("    RACACOR")

print("\nEsses nomes poderão ser usados diretamente nos próximos scripts")
print("de limpeza, seleção de suicídios e criação do dataset analítico.")
