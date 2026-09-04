"""
======================================================================
CONVERSOR RTF (JSON) -> PARQUET
Atlas Brasil
======================================================================

OBJETIVO
--------
Selecionar um arquivo RTF pelo Finder, extrair o JSON existente
dentro dele e salvar as estruturas encontradas em arquivos Parquet
no mesmo diretório do arquivo original.

O arquivo RTF original NÃO é alterado.

IMPORTANTE
----------
O arquivo Atlas_Brasil_base_de_dados.rtf analisado contém a
CONFIGURAÇÃO/REQUISIÇÃO da consulta do Atlas Brasil.

Ele contém, entre outras informações:

- territorialidades
- estados selecionados
- indicadores selecionados
- anos selecionados
- paginação
- ordenação

Ele NÃO contém as linhas finais dos municípios com seus valores.

Portanto, este programa converte o conteúdo efetivamente existente
no RTF para Parquet. Ele não cria dados municipais que não estão
presentes no arquivo.

======================================================================
"""

import json
import re
import html
from pathlib import Path

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox


# ======================================================================
# 1. SELECIONAR ARQUIVO PELO FINDER
# ======================================================================

def selecionar_arquivo():
    """
    Abre o Finder para o usuário selecionar o arquivo RTF.
    """

    root = tk.Tk()
    root.withdraw()

    arquivo = filedialog.askopenfilename(
        title="Selecione o arquivo RTF",
        filetypes=[
            ("Arquivos RTF", "*.rtf"),
            ("Todos os arquivos", "*.*"),
        ],
    )

    root.destroy()

    if not arquivo:
        return None

    return Path(arquivo)


# ======================================================================
# 2. LER O ARQUIVO RTF
# ======================================================================

def ler_rtf(caminho):
    """
    Lê o conteúdo bruto do arquivo RTF.

    Não tenta converter o RTF inteiro para texto.
    Apenas lê o conteúdo necessário para localizar o JSON.
    """

    return caminho.read_text(
        encoding="utf-8",
        errors="ignore"
    )


# ======================================================================
# 3. EXTRAIR O JSON DO RTF
# ======================================================================

def extrair_json_do_rtf(texto_rtf):
    """
    Localiza o JSON dentro do RTF.

    O JSON começa na região:

        {"territorialidades":

    e termina no fechamento correspondente.

    Esta função também remove os escapes \{ e \} que aparecem
    no RTF copiado/gerado pelo Safari.
    """

    # ------------------------------------------------------------------
    # Localizar o início do JSON.
    #
    # No arquivo sabemos que existe:
    #
    # "territorialidades"
    # ------------------------------------------------------------------

    pos_territorialidades = texto_rtf.find(
        '"territorialidades"'
    )

    if pos_territorialidades == -1:

        raise ValueError(
            "Não foi encontrado o campo "
            "'territorialidades' no arquivo RTF."
        )

    # ------------------------------------------------------------------
    # Procurar a abertura do objeto JSON.
    #
    # Usamos o último '{' antes de "territorialidades".
    # ------------------------------------------------------------------

    inicio = texto_rtf.rfind(
        "{",
        0,
        pos_territorialidades
    )

    if inicio == -1:

        raise ValueError(
            "Não foi encontrada a abertura do objeto JSON."
        )

    # ------------------------------------------------------------------
    # Extrair uma região a partir do início.
    # ------------------------------------------------------------------

    trecho = texto_rtf[inicio:]

    # ------------------------------------------------------------------
    # O RTF pode representar chaves como:
    #
    #     \{
    #     \}
    #
    # Essas barras NÃO fazem parte do JSON.
    #
    # Portanto removemos apenas a barra quando ela precede
    # uma chave.
    # ------------------------------------------------------------------

    trecho = trecho.replace(r"\{", "{")
    trecho = trecho.replace(r"\}", "}")

    # ------------------------------------------------------------------
    # Também podem existir escapes RTF relacionados a aspas.
    # ------------------------------------------------------------------

    trecho = trecho.replace(r"\'22", '"')

    # ------------------------------------------------------------------
    # Converter entidades HTML, caso existam.
    # ------------------------------------------------------------------

    trecho = html.unescape(trecho)

    # ------------------------------------------------------------------
    # Agora localizar o objeto JSON corretamente.
    #
    # Precisamos contar { e }, mas ignorando chaves que estejam
    # dentro de strings.
    # ------------------------------------------------------------------

    nivel = 0
    dentro_string = False
    escape = False

    fim = None

    for i, caractere in enumerate(trecho):

        # --------------------------------------------------------------
        # Se o caractere anterior foi uma barra de escape,
        # este caractere não deve ser interpretado.
        # --------------------------------------------------------------

        if escape:

            escape = False
            continue

        # --------------------------------------------------------------
        # Barra dentro de string
        # --------------------------------------------------------------

        if caractere == "\\" and dentro_string:

            escape = True
            continue

        # --------------------------------------------------------------
        # Aspas
        # --------------------------------------------------------------

        if caractere == '"':

            dentro_string = not dentro_string
            continue

        # --------------------------------------------------------------
        # Se estamos dentro de uma string, ignoramos { e }.
        # --------------------------------------------------------------

        if dentro_string:
            continue

        # --------------------------------------------------------------
        # Abertura de objeto
        # --------------------------------------------------------------

        if caractere == "{":

            nivel += 1

        # --------------------------------------------------------------
        # Fechamento de objeto
        # --------------------------------------------------------------

        elif caractere == "}":

            nivel -= 1

            if nivel == 0:

                fim = i + 1
                break

    if fim is None:

        raise ValueError(
            "Não foi possível encontrar o fechamento "
            "do objeto JSON."
        )

    json_texto = trecho[:fim]

    # ------------------------------------------------------------------
    # Remover caracteres de controle.
    # ------------------------------------------------------------------

    json_texto = "".join(
        caractere
        for caractere in json_texto
        if (
            caractere in "\n\r\t"
            or ord(caractere) >= 32
        )
    )

    # ------------------------------------------------------------------
    # Diagnóstico
    # ------------------------------------------------------------------

    print("\nPrimeiros caracteres do JSON:")
    print("--------------------------------------")
    print(json_texto[:300])
    print("--------------------------------------")

    # ------------------------------------------------------------------
    # Interpretar JSON
    # ------------------------------------------------------------------

    try:

        dados = json.loads(json_texto)

    except json.JSONDecodeError as erro:

        print("\nERRO AO INTERPRETAR O JSON")
        print("--------------------------------------")
        print(erro)

        inicio_erro = max(
            0,
            erro.pos - 200
        )

        fim_erro = min(
            len(json_texto),
            erro.pos + 200
        )

        print("\nTrecho próximo ao erro:")
        print("--------------------------------------")
        print(
            json_texto[
                inicio_erro:fim_erro
            ]
        )
        print("--------------------------------------")

        raise

    return dados


# ======================================================================
# 4. TRANSFORMAR TERRITORIALIDADES
# ======================================================================

def criar_tabela_territorialidades(dados):

    territorialidades = (
        dados
        .get("territorialidades", {})
        .get("entidades", [])
    )

    if not territorialidades:
        return None

    registros = []

    for entidade in territorialidades:

        registros.append({

            "entidade": entidade.get("e"),

            "municipios": json.dumps(
                entidade.get("mun", []),
                ensure_ascii=False
            ),

            "regioes_metropolitanas": json.dumps(
                entidade.get("rm", []),
                ensure_ascii=False
            ),

            "estados": json.dumps(
                entidade.get("est", []),
                ensure_ascii=False
            ),

            "udh": json.dumps(
                entidade.get("udh", []),
                ensure_ascii=False
            ),

            "localidades": json.dumps(
                entidade.get("l", []),
                ensure_ascii=False
            ),
        })

    return pd.DataFrame(registros)


# ======================================================================
# 5. TRANSFORMAR INDICADORES
# ======================================================================

def criar_tabela_indicadores(dados):

    indicadores = (
        dados
        .get("indicadores", {})
        .get("cod_indicadores", [])
    )

    if not indicadores:
        return None

    registros = []

    for indicador in indicadores:

        registros.append(indicador)

    return pd.DataFrame(registros)


# ======================================================================
# 6. TRANSFORMAR PAGINAÇÃO
# ======================================================================

def criar_tabela_paginacao(dados):

    pagination = dados.get("pagination")

    if not pagination:
        return None

    return pd.DataFrame(
        [pagination]
    )


# ======================================================================
# 7. TRANSFORMAR ORDENAÇÃO
# ======================================================================

def criar_tabela_ordenacao(dados):

    ordenation = dados.get("ordenation")

    if not ordenation:
        return None

    if isinstance(ordenation, dict):

        return pd.DataFrame(
            [ordenation]
        )

    if isinstance(ordenation, list):

        return pd.DataFrame(
            ordenation
        )

    return None


# ======================================================================
# 8. SALVAR DATAFRAME COMO PARQUET
# ======================================================================

def salvar_parquet(
    dataframe,
    caminho,
    descricao
):

    dataframe.to_parquet(
        caminho,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )

    print(
        f"\nArquivo criado:"
        f"\n{caminho}"
    )

    print(
        f"Linhas : {len(dataframe):,}"
    )

    print(
        f"Colunas: {len(dataframe.columns)}"
    )

    # Mostrar primeiras colunas
    print("\nColunas:")

    for coluna in dataframe.columns[:15]:

        print(
            f"  - {coluna}"
        )

    if len(dataframe.columns) > 15:

        print(
            f"  ... + "
            f"{len(dataframe.columns) - 15} colunas"
        )


# ======================================================================
# 9. PROGRAMA PRINCIPAL
# ======================================================================

def main():

    print("=" * 70)
    print("CONVERSOR RTF (JSON) -> PARQUET")
    print("Atlas Brasil")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Selecionar arquivo
    # ------------------------------------------------------------------

    caminho_rtf = selecionar_arquivo()

    if caminho_rtf is None:

        print(
            "\nNenhum arquivo foi selecionado."
        )

        return

    print(
        "\nArquivo selecionado:"
    )

    print(caminho_rtf)

    # ------------------------------------------------------------------
    # Ler RTF
    # ------------------------------------------------------------------

    print(
        "\nLendo arquivo RTF..."
    )

    texto_rtf = ler_rtf(
        caminho_rtf
    )

    print(
        f"Arquivo lido: "
        f"{len(texto_rtf):,} caracteres"
    )

    # ------------------------------------------------------------------
    # Extrair JSON
    # ------------------------------------------------------------------

    print(
        "\nExtraindo JSON..."
    )

    dados = extrair_json_do_rtf(
        texto_rtf
    )

    print(
        "\nJSON interpretado "
        "com sucesso!"
    )

    # ------------------------------------------------------------------
    # Mostrar estrutura
    # ------------------------------------------------------------------

    print(
        "\nEstruturas encontradas:"
    )

    for chave in dados.keys():

        print(
            f"  - {chave}"
        )

    # ------------------------------------------------------------------
    # Criar tabelas
    # ------------------------------------------------------------------

    tabelas = {}

    tabela = criar_tabela_territorialidades(
        dados
    )

    if tabela is not None:

        tabelas["territorialidades"] = tabela

    tabela = criar_tabela_indicadores(
        dados
    )

    if tabela is not None:

        tabelas["indicadores"] = tabela

    tabela = criar_tabela_paginacao(
        dados
    )

    if tabela is not None:

        tabelas["pagination"] = tabela

    tabela = criar_tabela_ordenacao(
        dados
    )

    if tabela is not None:

        tabelas["ordenation"] = tabela

    # ------------------------------------------------------------------
    # Verificar tabelas
    # ------------------------------------------------------------------

    print(
        "\nResumo das estruturas:"
    )

    print("-" * 70)

    for nome, dataframe in tabelas.items():

        print(
            f"{nome:25s} "
            f"{len(dataframe):>8,} linhas x "
            f"{len(dataframe.columns):>4} colunas"
        )

    # ------------------------------------------------------------------
    # Diretório de saída
    #
    # Mesmo diretório do RTF.
    # ------------------------------------------------------------------

    diretorio = caminho_rtf.parent

    print(
        "\nDiretório de saída:"
    )

    print(diretorio)

    # ------------------------------------------------------------------
    # Criar Parquets
    # ------------------------------------------------------------------

    arquivos_criados = []

    for nome, dataframe in tabelas.items():

        nome_saida = (
            caminho_rtf.stem
            + "_"
            + nome
            + ".parquet"
        )

        caminho_saida = (
            diretorio
            / nome_saida
        )

        # --------------------------------------------------------------
        # Se já existir, perguntar
        # --------------------------------------------------------------

        if caminho_saida.exists():

            resposta = messagebox.askyesno(
                "Arquivo já existe",
                (
                    f"O arquivo\n\n"
                    f"{nome_saida}\n\n"
                    f"já existe.\n\n"
                    f"Deseja sobrescrever?"
                ),
            )

            if not resposta:

                print(
                    f"\nIgnorado: "
                    f"{nome_saida}"
                )

                continue

        # --------------------------------------------------------------
        # Salvar
        # --------------------------------------------------------------

        salvar_parquet(
            dataframe,
            caminho_saida,
            f"Estrutura {nome}"
        )

        arquivos_criados.append(
            caminho_saida
        )

    # ------------------------------------------------------------------
    # Resultado final
    # ------------------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "CONVERSÃO CONCLUÍDA"
    )

    print(
        "=" * 70
    )

    if arquivos_criados:

        print(
            "\nArquivos Parquet criados:"
        )

        for arquivo in arquivos_criados:

            print(
                f"  {arquivo}"
            )

    else:

        print(
            "\nNenhum arquivo Parquet foi criado."
        )

    print(
        "\nO arquivo RTF original "
        "não foi alterado."
    )


# ======================================================================
# EXECUTAR
# ======================================================================

if __name__ == "__main__":

    main()