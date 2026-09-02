"""
VALIDAÇÃO DOS ARQUIVOS SIM — 2013 A 2024

Objetivo:
    Ler os arquivos CSV do SIM e verificar:
      1. separador utilizado em cada ano;
      2. número de colunas;
      3. especificamente, 87 colunas em 2022;
      4. especificamente, 354.056 registros em 2022;
      5. nomes das colunas.

IMPORTANTE:
    Este programa é somente de LEITURA.
    Nenhum arquivo CSV é alterado, convertido, renomeado ou apagado.

As explicações abaixo foram acrescentadas para facilitar o estudo
do Python durante o desenvolvimento do projeto.
"""

import csv
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================
#
# Neste bloco definimos onde estão os arquivos do SIM e quais
# anos queremos analisar.
#
# Não existe processamento dos dados ainda: estamos apenas
# preparando as informações que o programa vai utilizar.
# ============================================================

PASTA_SIM = Path(
    "/Users/claudiojacomassi/Library/CloudStorage/"
    "GoogleDrive-claudio.jacomassi@gmail.com/"
    ".shortcut-targets-by-id/"
    "1KAgdHCMybmn_N4ImZ9y8JkT_YdxXUDLk/"
    "PUC SP/Suicidio_adolescentes_Brasil/"
    "01_RAW/SIM"
)

# range(2013, 2025) gera os anos de 2013 até 2024.
# O segundo limite (2025) não é incluído.
ANOS = range(2013, 2025)


# ============================================================
# FUNÇÃO PARA ANALISAR UM ARQUIVO
# ============================================================
#
# Esta função recebe o caminho de um CSV e retorna um dicionário
# com as informações que precisamos para a auditoria.
#
# Usamos uma função porque a mesma análise será repetida para
# cada um dos 12 arquivos.
# ============================================================

def analisar_arquivo(caminho):

    # open() abre o arquivo. "r" significa leitura (read).
    # latin1 é usado para lidar com a codificação dos CSVs do SIM.
    with open(
        caminho,
        "r",
        encoding="latin1",
        newline=""
    ) as f:

        primeira_linha = f.readline().rstrip("\r\n")

        # A primeira linha é o cabeçalho do CSV.
        # Contamos ";" e "," para descobrir qual deles está sendo
        # usado como separador das colunas.
        #
        # Esta é uma heurística simples, adequada aos arquivos
        # que estamos validando.
        qtd_ponto_virgula = primeira_linha.count(";")
        qtd_virgula = primeira_linha.count(",")

        if qtd_ponto_virgula > qtd_virgula:
            separador = ";"
        else:
            separador = ","

        # readline() já consumiu a primeira linha.
        # seek(0) volta o ponteiro para o início para que o
        # csv.reader possa ler novamente o cabeçalho e os dados.
        f.seek(0)

        # csv.reader interpreta cada linha respeitando o
        # separador que acabamos de detectar.
        leitor = csv.reader(
            f,
            delimiter=separador
        )

        # next() obtém a próxima linha. Aqui é o cabeçalho.
        # O resultado é uma lista com os nomes das colunas.
        cabecalho = next(leitor)

        # Como o cabeçalho já foi consumido, contamos somente
        # as linhas restantes: cada linha corresponde a um registro.
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

# Lista vazia que receberá um dicionário com os resultados
# de cada arquivo analisado.
resultados = []


# ============================================================
# ANALISAR CADA ANO
# ============================================================
#
# Percorremos 2013–2024, montamos o nome do respectivo arquivo,
# verificamos se ele existe e chamamos analisar_arquivo().
#
# Os resultados são acumulados na lista "resultados".
# ============================================================

for ano in ANOS:

    # f-string monta o nome do arquivo usando o ano atual.
    # O operador "/" de Path junta pasta + nome do arquivo.
    arquivo = PASTA_SIM / f"Mortalidade_Geral_{ano}.csv"

    if not arquivo.exists():

        print(f"⚠️  {ano}: ARQUIVO NÃO ENCONTRADO")

        continue

    print(f"Analisando {ano}...")

    # Executa a análise do arquivo e recebe o dicionário
    # com separador, colunas, registros e cabeçalho.
    resultado = analisar_arquivo(arquivo)

    # append() acrescenta esse resultado à lista geral.
    resultados.append(resultado)


# ============================================================
# TABELA RESUMO
# ============================================================
#
# Aqui mostramos em uma visão única as quatro primeiras
# verificações: ano, separador, número de colunas e registros.
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
#
# Além da tabela geral, fazemos três testes explícitos para 2022:
#   - separador deve ser ";"
#   - deve haver 87 colunas
#   - deve haver 354.056 registros
#
# O objetivo é confirmar que a conversão do arquivo de 2022
# preservou exatamente a quantidade de dados.
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
#
# Quantidade de colunas, sozinha, não garante que os arquivos
# tenham a mesma estrutura. Por isso mostramos os nomes.
#
# Isto é importante porque uma coluna pode ser acrescentada,
# removida ou ter seu nome alterado entre versões do SIM.
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
#
# Agora comparamos os nomes das variáveis de cada ano com 2018.
#
# Usamos SET (conjunto) porque ele permite fazer operações como
# A - B, que significa "elementos que estão em A mas não em B".
#
# Assim conseguimos identificar:
#   - colunas ausentes em determinado ano;
#   - colunas que aparecem somente naquele ano.
#
# Essa comparação NÃO altera os arquivos.
# ============================================================

print()
print("=" * 80)
print("COMPARAÇÃO DOS NOMES DAS COLUNAS")
print("=" * 80)

# Usamos 2018 como referência porque ele possui o layout
# completo de 87 colunas que adotamos para esta comparação.
# Isso não significa que 2018 seja necessariamente "o padrão
# oficial" para todos os anos; significa apenas que ele é nossa
# referência de comparação nesta etapa do projeto.
referencia = next(
    (
        r for r in resultados
        if r["arquivo"] == "Mortalidade_Geral_2018.csv"
    ),
    None
)

if referencia:

    # set() transforma a lista de nomes em um conjunto,
    # permitindo comparar estruturas por operações de conjuntos.
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

        # Colunas que existem no ano atual, mas não em 2018.
        # sorted() apenas organiza o resultado alfabeticamente.
        somente_no_ano = sorted(
            colunas_ano - colunas_referencia
        )

        # Colunas que existem em 2018, mas não no ano atual.
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
#
# Esta mensagem confirma que a leitura terminou.
# Nenhum arquivo foi modificado pelo programa.
# ============================================================

print()
print("=" * 80)
print("VALIDAÇÃO CONCLUÍDA — NENHUM ARQUIVO FOI ALTERADO")
print("=" * 80)
print()