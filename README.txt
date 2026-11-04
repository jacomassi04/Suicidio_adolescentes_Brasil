Arquivos necessarios para iniciar o processo:
    00_Dicionário_Microdados_PENSE2024.xlsx
    01_Colunas_recomendadas_pense_2024_final.xlsx
    01_PENSE2024_MICRODADOS.CSV
Esses arquivos devem ser carregados na pasta "02_Tratamento_dados_database_PENSE_2024" do repositorio do GitHub "Suicidio_adolescentes_Brasil"

No final de todos os scripts da pasta acima, tres arquivos sao gerados (nesta mesma pasta):
    07_PENSE2024_IDADE_13_A_17_CATEGORY.Feather
    07_PENSE2024_IDADE_13_A_17_V_CRAMER_MAIORES_CORRELACOES (e um arquivo feather - necessita mudar nos scripts)
    08_PENSE2024_MCA_COORDENADAS.Feather

Estes 3 arquivos vao alimentar os scripts nas pastas seguintes:
    03_Analise_estatistica
    04_K-MODE_(Nao_Supervisionado)
    05_K-Means_HAC_GMM_DBScan_pos_MCA
    06_Regressao_logistica_(Supervisionado)
    07_Random_Forest

E portanto, nestas pastas, os scripts precisam ser adaptados para que o "path" dos 3 arquivos acima seja atualizado.

Iniciamos o trabalho com arquivos com formato parquet (pela rapidez de carregar e trabalhar em comparacao com csv e xlsx), mas depois tivemos que mudar para feather pois o parquet nao suporta tipo de dados "category" do pandas.
