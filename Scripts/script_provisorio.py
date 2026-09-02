import os
import subprocess
import pandas as pd
from dbfread import DBF

# 1. Configurações de caminhos
pasta_temporaria = './dados_sim_tmp'
ano = '2022'

unidades_federativas = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

print("\nProcessando e unificando os arquivos brutos locais...")
lista_dataframes = []

# Encontra o caminho real do executável blast-dbf dentro do seu ambiente virtual
import sys
blast_bin = os.path.join(sys.prefix, 'bin', 'blast-dbf')

# Caso não encontre no venv, tenta o caminho padrão onde o pip instala no Mac Intel
if not os.path.exists(blast_bin):
    blast_bin = '/Users/claudiojacomassi/Documents/GitHub/Suicidio_adolescentes_Brasil/.venv/bin/blast-dbf'

# 2. Descomprimir arquivos .dbc para .dbf e ler com o dbfread
for uf in unidades_federativas:
    nome_arquivo = f"DO{uf}{ano}.dbc"
    caminho_dbc = os.path.join(pasta_temporaria, nome_arquivo)
    caminho_dbf = os.path.join(pasta_temporaria, f"DO{uf}{ano}.dbf")
    
    if os.path.exists(caminho_dbc):
        print(f"Convertendo dados de: {uf}")
        try:
            # Descomprime o formato .dbc do DATASUS usando o binário do venv mapeado para Intel
            subprocess.run([blast_bin, caminho_dbc, caminho_dbf], check=True, stdout=subprocess.DEVNULL)
            
            # Lê o arquivo intermediário .dbf mantendo a codificação dos textos em português
            table = DBF(caminho_dbf, encoding='iso-8859-1')
            df_uf = pd.DataFrame(iter(table))
            
            # Força o nome das colunas a ficarem em letras MAIÚSCULAS puros (ORIGEM, DTOBITO, etc.)
            df_uf.columns = [col.upper() for col in df_uf.columns]
            lista_dataframes.append(df_uf)
            
            # Remove o arquivo .dbf temporário para poupar espaço no Mac
            if os.path.exists(caminho_dbf):
                os.remove(caminho_dbf)
                
        except Exception as e:
            print(f"Erro ao processar dados de {uf}: {e}")
    else:
        print(f"Arquivo não encontrado: {caminho_dbc}")

# 3. Consolidar o arquivo para o Brasil inteiro
if lista_dataframes:
    print("\nConsolidando o arquivo para o Brasil inteiro...")
    brasil_2022_df = pd.concat(lista_dataframes, ignore_index=True)
    
    # 4. Definir o caminho de destino exato no seu Google Drive
    caminho_destino = (
        '/Users/claudiojacomassi/Library/CloudStorage/GoogleDrive-claudio.jacomassi@://gmail.com'
        '.shortcut-targets-by-id/1KAgdHCMybmn_N4ImZ9y8JkT_YdxXUDLk/PUC SP/'
        'Suicidio_adolescentes_Brasil/01_RAW/SIM/Mortalidade_Geral_2022.csv'
    )
    
    os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)
    
    # Salvar em CSV mantendo a integridade das 87 colunas puras que você precisa
    brasil_2022_df.to_csv(caminho_destino, index=False, encoding='utf-8')
    print(f"\nSucesso total! Arquivo de 2022 gerado com {len(brasil_2022_df.columns)} colunas.")
    print(f"Salvo em: {caminho_destino}")
else:
    print("\nNenhum arquivo pôde ser processado. Verifique a pasta temporária.")
