
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

# --------------------------------------------------
# 2. Selecionar arquivo Parquet no Finder
# --------------------------------------------------

arquivo_parquet = filedialog.askopenfilename(
    title="Selecione o arquivo Parquet para converter",
    filetypes=[
        ("Arquivos Parquet", "*.parquet"),
        ("Todos os arquivos", "*.*")
    ]
)

# Verificar se o usuário selecionou um arquivo
if not arquivo_parquet:
    print("Operação cancelada pelo usuário.")
    root.destroy()
    raise SystemExit

print(f"\nArquivo selecionado:\n{arquivo_parquet}")

# --------------------------------------------------
# 3. Definir nome inicial do arquivo CSV
# --------------------------------------------------

caminho_parquet = Path(arquivo_parquet)

nome_csv = caminho_parquet.stem + ".csv"

# --------------------------------------------------
# 4. Escolher onde salvar o CSV
# --------------------------------------------------

arquivo_csv = filedialog.asksaveasfilename(
    title="Escolha onde salvar o arquivo CSV",
    initialdir=str(caminho_parquet.parent),
    initialfile=nome_csv,
    defaultextension=".csv",
    filetypes=[
        ("Arquivo CSV", "*.csv")
    ]
)

if not arquivo_csv:
    print("Salvamento cancelado pelo usuário.")
    root.destroy()
    raise SystemExit

# --------------------------------------------------
# 5. Ler o arquivo Parquet
# --------------------------------------------------

print("\nLendo arquivo Parquet...")

df = pd.read_parquet(
    arquivo_parquet,
    engine="pyarrow"
)

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

root.destroy()
