from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


# ============================================================
# CONFIGURAÇÃO
# ============================================================

RAW_DIR = Path(
    "/Users/claudiojacomassi/Library/CloudStorage/"
    "GoogleDrive-claudio.jacomassi@gmail.com/"
    ".shortcut-targets-by-id/"
    "1KAgdHCMybmn_N4ImZ9y8Jk_T_YdxXUDLk/"
    "PUC SP/Suicidio_adolescentes_Brasil/"
    "01_RAW/SIM"
)

OUTPUT_DIR = Path(
    "/Users/claudiojacomassi/Library/CloudStorage/"
    "GoogleDrive-claudio.jacomassi@gmail.com/"
    ".shortcut-targets-by-id/"
    "1KAgdHCMybmn_N4ImZ9y8Jk_T_YdxXUDLk/"
    "PUC SP/Suicidio_adolescentes_Brasil/"
    "02_PROCESSED/SIM"
)

DICTIONARY_FILE = RAW_DIR / (
    "dicionario_variaveis_SIM_oficial_projeto_suicidio_adolescentes.csv"
)


# ============================================================
# INÍCIO
# ============================================================

print("=" * 70)
print("SIM — CONVERSÃO CSV → PARQUET")
print("=" * 70)

print()
print("Diretório RAW:")
print(RAW_DIR)

print()
print("Diretório PROCESSED:")
print(OUTPUT_DIR)

print()


# ============================================================
# VERIFICAÇÕES
# ============================================================

if not RAW_DIR.exists():
    print("ERRO: diretório RAW não encontrado.")
    raise SystemExit(1)

if not DICTIONARY_FILE.exists():
    print("ERRO: dicionário não encontrado:")
    print(DICTIONARY_FILE)
    raise SystemExit(1)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LER DICIONÁRIO
# ============================================================

print("Lendo dicionário...")

dictionary = pd.read_csv(
    DICTIONARY_FILE,
    encoding="utf-8-sig",
    dtype=str
)

dictionary.columns = dictionary.columns.str.strip()

required = [
    "VARIAVEL",
    "DESCRICAO_OFICIAL"
]

for column in required:
    if column not in dictionary.columns:
        print(
            f"ERRO: coluna '{column}' "
            "não encontrada no dicionário."
        )
        raise SystemExit(1)

dictionary["VARIAVEL"] = (
    dictionary["VARIAVEL"]
    .fillna("")
    .str.strip()
)

dictionary["DESCRICAO_OFICIAL"] = (
    dictionary["DESCRICAO_OFICIAL"]
    .fillna("")
    .str.strip()
)


# ============================================================
# MAPA VARIÁVEL → DESCRIÇÃO
# ============================================================

variable_to_description = {}

for _, row in dictionary.iterrows():

    variable = row["VARIAVEL"]
    description = row["DESCRICAO_OFICIAL"]

    if not variable:
        continue

    if not description or description == "—":
        description = variable

    variable_to_description[variable] = description


print(
    f"Variáveis no dicionário: "
    f"{len(variable_to_description)}"
)

print()


# ============================================================
# LOCALIZAR CSVs
# ============================================================

csv_files = sorted(
    file
    for file in RAW_DIR.glob("*.csv")
    if file.name != DICTIONARY_FILE.name
)

print(
    f"Arquivos CSV encontrados: "
    f"{len(csv_files)}"
)

print()

if not csv_files:
    print("Nenhum CSV encontrado.")
    raise SystemExit(0)


# ============================================================
# PROCESSAR CADA CSV
# ============================================================

for csv_file in csv_files:

    print("=" * 70)
    print(f"ARQUIVO: {csv_file.name}")
    print("=" * 70)

    parquet_file = OUTPUT_DIR / (
        csv_file.stem + ".parquet"
    )

    print()
    print("Lendo CSV...")

    # --------------------------------------------------------
    # Ler CSV
    # --------------------------------------------------------

    df = pd.read_csv(
        csv_file,
        encoding="utf-8",
        dtype=str,
        low_memory=False
    )

    print(
        f"Linhas: {len(df):,}"
    )

    print(
        f"Colunas: {len(df.columns)}"
    )

    # --------------------------------------------------------
    # Limpar nomes das colunas
    # --------------------------------------------------------

    original_columns = [
        str(column).strip()
        for column in df.columns
    ]

    # --------------------------------------------------------
    # Construir novos nomes
    # --------------------------------------------------------

    new_columns = []

    not_found = []

    for column in original_columns:

        description = variable_to_description.get(
            column
        )

        if description is None:

            description = column
            not_found.append(column)

        new_columns.append(description)

    # --------------------------------------------------------
    # Garantir nomes únicos
    # --------------------------------------------------------

    used = {}

    unique_columns = []

    for column in new_columns:

        if column not in used:

            used[column] = 1
            unique_columns.append(column)

        else:

            used[column] += 1

            unique_columns.append(
                f"{column} [{used[column]}]"
            )

    df.columns = unique_columns

    # --------------------------------------------------------
    # Mostrar mapeamento
    # --------------------------------------------------------

    print()
    print("Mapeamento:")

    for old, new in zip(
        original_columns,
        unique_columns
    ):

        print(
            f"  {old} -> {new}"
        )

    # --------------------------------------------------------
    # Variáveis não encontradas
    # --------------------------------------------------------

    if not_found:

        print()
        print(
            "ATENÇÃO — variáveis não encontradas "
            "no dicionário:"
        )

        for variable in not_found:
            print(
                f"  {variable}"
            )

    # --------------------------------------------------------
    # Converter para Parquet
    # --------------------------------------------------------

    print()
    print("Gravando Parquet...")

    table = pa.Table.from_pandas(
        df,
        preserve_index=False
    )

    # Metadata para manter a rastreabilidade
    metadata = dict(
        table.schema.metadata or {}
    )

    metadata[
        b"arquivo_origem"
    ] = csv_file.name.encode("utf-8")

    metadata[
        b"dicionario_origem"
    ] = DICTIONARY_FILE.name.encode("utf-8")

    metadata[
        b"descricao"
    ] = (
        b"SIM — variaveis renomeadas conforme "
        b"dicionario oficial"
    )

    table = table.replace_schema_metadata(
        metadata
    )

    pq.write_table(
        table,
        parquet_file,
        compression="snappy"
    )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    csv_size = csv_file.stat().st_size
    parquet_size = parquet_file.stat().st_size

    print()
    print("CONCLUÍDO")
    print()
    print("Parquet:")
    print(parquet_file)

    print()
    print(
        f"CSV:     "
        f"{csv_size / 1024 / 1024:.2f} MB"
    )

    print(
        f"Parquet: "
        f"{parquet_size / 1024 / 1024:.2f} MB"
    )

    print()


# ============================================================
# FINAL
# ============================================================

print("=" * 70)
print("TODOS OS ARQUIVOS FORAM CONVERTIDOS")
print("=" * 70)

print()
print("Arquivos Parquet:")
print(OUTPUT_DIR)đ

print()
print("Os arquivos RAW não foram modificados.")