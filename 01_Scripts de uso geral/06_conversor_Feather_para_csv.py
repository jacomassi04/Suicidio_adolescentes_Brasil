
# -*- coding: utf-8 -*-

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

# --------------------------------------------------
# 1. Criar janela para seleção de arquivos
# --------------------------------------------------

root = tk.Tk()
root.withdraw()

try:
    # --------------------------------------------------
    # 2. Selecionar arquivo Feather no Finder
    # --------------------------------------------------

    arquivo_feather = filedialog.askopenfilename(
        title="Selecione o arquivo Feather para converter",
        filetypes=[
            ("Arquivos Feather", "*.feather"),
            ("Todos os arquivos", "*.*")
        ]
    )

    if not arquivo_feather:
        print("Operação cancelada pelo usuário.")
        raise SystemExit

    print(f"\nArquivo selecionado:\n{arquivo_feather}")

    # --------------------------------------------------
    # 3. Definir nome inicial do arquivo CSV
    # --------------------------------------------------

    caminho_feather = Path(arquivo_feather)
    nome_csv = caminho_feather.stem + ".csv"

    # --------------------------------------------------
    # 4. Escolher onde salvar o CSV
    # --------------------------------------------------

    arquivo_csv = filedialog.asksaveasfilename(
        title="Escolha onde salvar o arquivo CSV",
        initialdir=str(caminho_feather.parent),
        initialfile=nome_csv,
        defaultextension=".csv",
        filetypes=[
            ("Arquivo CSV", "*.csv")
        ]
    )

    if not arquivo_csv:
        print("Salvamento cancelado pelo usuário.")
        raise SystemExit

    # --------------------------------------------------
    # 5. Ler o arquivo Feather
    # --------------------------------------------------

    print("\nLendo arquivo Feather...")

    df = pd.read_feather(arquivo_feather)

    # --------------------------------------------------
    # 6. Converter para CSV
    # --------------------------------------------------

    print("Convertendo para CSV...")

    df.to_csv(
        arquivo_csv,
        index=False,
        sep=";",
        encoding="utf-8-sig"
    )

    # --------------------------------------------------
    # 7. Exibir resultado
    # --------------------------------------------------

    print("\nConversão concluída!")
    print(f"Arquivo CSV gerado:\n{arquivo_csv}")
    print(f"\nTotal de linhas: {df.shape[0]:,}")
    print(f"Total de colunas: {df.shape[1]}")

    print("\nVariáveis:")
    print(df.columns.tolist())

    messagebox.showinfo(
        "Conversão concluída",
        f"Arquivo CSV criado com sucesso!\n\n"
        f"Linhas: {df.shape[0]:,}\n"
        f"Colunas: {df.shape[1]}\n\n"
        f"Arquivo:\n{arquivo_csv}"
    )

except SystemExit:
    pass

except Exception as erro:
    print(f"\nErro durante a conversão: {erro}")

    messagebox.showerror(
        "Erro na conversão",
        f"Não foi possível converter o arquivo.\n\n{erro}"
    )

finally:
    root.destroy()
