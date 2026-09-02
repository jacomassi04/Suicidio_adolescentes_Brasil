import csv
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA_SIM = Path(
    "/Users/claudiojacomassi/Library/CloudStorage/"
    "GoogleDrive-claudio.jacomassi@gmail.com/"
    ".shortcut-targets-by-id/"
    "1KAgdHCMybmn_N4ImZ9y8JkT_YdxXUDLk/"
    "PUC SP/Suicidio_adolescentes_Brasil/"
    "01_RAW/SIM"
)

ANOS = range(2013, 2025)


# ============================================================
# FUNÇÃO PARA ANALISAR UM ARQUIVO
# ============================================================

def analisar_arquivo(caminho):

    with open(
        caminho,
        "r",
        encoding="latin1",
        newline=""
    ) as f:

        primeira_linha = f.readline().rstrip("\r\n")

        # Detectar separador pelo cabeçalho
        qtd_ponto_virgula = primeira_linha.count(";")
        qtd_virgula = primeira_linha.count(",")

        if qtd_ponto_virgula > qtd_virgula:
            separador = ";"
        else:
            separador = ","

        # Voltar ao início
        f.seek(0)

        leitor = csv.reader(
            f,
            delimiter=separador
        )

        cabecalho = next(leitor)

        registros = sum(
            1 for _ in leitor
        )

    return {
        "arquivo": caminho.name,
        "separador": separador,
        "colunas": len(cabecalho),
        "registros": registros,
        "cabecalho": cabecalho,
    }


# ============================================================
# INÍCIO
# ============================================================

print()
print("=" * 80)
print("VALIDAÇÃO DOS ARQUIVOS SIM — 2013 A 2024")
print("=" * 80)
print()

resultados = []


# ============================================================
# ANALISAR CADA ANO
# ============================================================

for ano in ANOS:

    arquivo = PASTA_SIM / f"Mortalidade_Geral_{ano}.csv"

    if not arquivo.exists():

        print(f"⚠️  {ano}: ARQUIVO NÃO ENCONTRADO")

        continue

    print(f"Analisando {ano}...")

    resultado = analisar_arquivo(arquivo)

    resultados.append(resultado)


# ============================================================
# TABELA RESUMO
# ============================================================

print()
print("=" * 80)
print("1–4. RESUMO DOS ARQUIVOS")
print("=" * 80)

print(
    f"{'ANO':<8}"
    f"{'SEPARADOR':<12}"
    f"{'COLUNAS':<10}"
    f"{'REGISTROS':>15}"
)

print("-" * 80)

for r in resultados:

    ano = r["arquivo"].replace(
        "Mortalidade_Geral_", ""
    ).replace(
        ".csv", ""
    )

    print(
        f"{ano:<8}"
        f"{repr(r['separador']):<12}"
        f"{r['colunas']:<10}"
        f"{r['registros']:>15,}".replace(",", ".")
    )


# ============================================================
# VALIDAÇÃO ESPECÍFICA DE 2022
# ============================================================

print()
print("=" * 80)
print("VALIDAÇÃO ESPECÍFICA DE 2022")
print("=" * 80)

resultado_2022 = next(
    (
        r for r in resultados
        if r["arquivo"] == "Mortalidade_Geral_2022.csv"
    ),
    None
)

if resultado_2022 is None:

    print("❌ Arquivo de 2022 não encontrado.")

else:

    separador_ok = resultado_2022["separador"] == ";"
    colunas_ok = resultado_2022["colunas"] == 87
    registros_ok = resultado_2022["registros"] == 354056

    print(
        f"Separador ';' ............ "
        f"{'✓ SIM' if separador_ok else '❌ NÃO'}"
    )

    print(
        f"87 colunas ............... "
        f"{'✓ SIM' if colunas_ok else '❌ NÃO'}"
    )

    print(
        f"354.056 registros ........ "
        f"{'✓ SIM' if registros_ok else '❌ NÃO'}"
    )


# ============================================================
# NOMES DAS COLUNAS
# ============================================================

print()
print("=" * 80)
print("5. NOMES DAS COLUNAS")
print("=" * 80)

for r in resultados:

    ano = r["arquivo"].replace(
        "Mortalidade_Geral_", ""
    ).replace(
        ".csv", ""
    )

    print()
    print(f"ANO {ano} — {len(r['cabecalho'])} colunas")
    print("-" * 80)

    print(
        " | ".join(r["cabecalho"])
    )


# ============================================================
# COMPARAÇÃO DOS NOMES DAS COLUNAS
# ============================================================

print()
print("=" * 80)
print("COMPARAÇÃO DOS NOMES DAS COLUNAS")
print("=" * 80)

# Usar 2018 como referência porque possui o layout de 87 colunas
referencia = next(
    (
        r for r in resultados
        if r["arquivo"] == "Mortalidade_Geral_2018.csv"
    ),
    None
)

if referencia:

    colunas_referencia = set(
        referencia["cabecalho"]
    )

    print()
    print("2018 será utilizado como referência.")
    print()

    for r in resultados:

        if r is referencia:
            continue

        colunas_ano = set(
            r["cabecalho"]
        )

        somente_no_ano = sorted(
            colunas_ano - colunas_referencia
        )

        ausentes_no_ano = sorted(
            colunas_referencia - colunas_ano
        )

        print()
        print(
            f"ANO {r['arquivo'].replace('Mortalidade_Geral_', '').replace('.csv', '')}"
        )
        print("-" * 80)

        if not somente_no_ano and not ausentes_no_ano:

            print("✓ Mesmos nomes de colunas de 2018.")

        else:

            if ausentes_no_ano:

                print(
                    "Ausentes em relação a 2018:"
                )

                for coluna in ausentes_no_ano:
                    print(f"  - {coluna}")

            if somente_no_ano:

                print(
                    "Existem somente neste ano:"
                )

                for coluna in somente_no_ano:
                    print(f"  + {coluna}")


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 80)
print("VALIDAÇÃO CONCLUÍDA — NENHUM ARQUIVO FOI ALTERADO")
print("=" * 80)
print()