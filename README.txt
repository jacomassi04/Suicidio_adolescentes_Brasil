# Suicídio e Saúde dos Adolescentes no Brasil — PeNSE 2024

## 1. Apresentação

Este projeto utiliza os microdados da Pesquisa Nacional de Saúde do Escolar (PeNSE 2024), disponibilizados pelo Instituto Brasileiro de Geografia e Estatística (IBGE), para desenvolver uma análise exploratória e estatística de características e comportamentos relacionados à saúde de adolescentes brasileiros.

O repositório reúne procedimentos de preparação dos dados, análise estatística, identificação de agrupamentos por aprendizado não supervisionado e modelagem por regressão logística.

A investigação utiliza uma base selecionada de estudantes de 13 a 17 anos, conforme os critérios de processamento documentados nos scripts.

## 2. Objetivos

- Preparar e documentar os microdados para análise.
- Identificar e tratar códigos especiais, valores ausentes e registros duplicados.
- Padronizar variáveis e categorias conforme o dicionário da pesquisa.
- Descrever a distribuição das respostas por meio de frequências e gráficos.
- Investigar associações entre variáveis categóricas.
- Explorar perfis de estudantes por meio do algoritmo K-Modes.
- Investigar relações entre variáveis explicativas e um desfecho por meio de regressão logística, conforme a definição da variável-alvo e os procedimentos de validação adotados.

## 3. Organização do projeto

### 02_T ratamento_dados_database_PENSE_2024

Etapa de preparação e transformação dos microdados.

Os arquivos e notebooks incluem:

- Dicionário dos microdados e análise de respostas especiais.
- Seleção e organização das colunas recomendadas.
- Remoção de colunas não utilizadas.
- Recodificação e conversão de respostas em categorias descritivas.
- Remoção de registros com valores ausentes e de duplicados.
- Conversão de variáveis para representações categóricas e numéricas.
- Geração de bases intermediárias em CSV, Parquet e Feather.
- Relatórios de diagnóstico e recodificação.

### 03_Analise_estatistica

Etapa de análise descritiva e de associação entre variáveis.

Notebooks identificados:

- `01_Frequencias.ipynb`
- `02_mapa_de_calor.ipynb`
- `03_Qui_quadrado_e_V_de_Cramer.ipynb`

### 04_K-MODE_(Nao_Supervisionado)

Etapa de agrupamento de registros por similaridade de categorias.

Notebooks identificados:

- `01_KMODE_diagnostico_custo_por_numero_K.ipynb`
- `02_Kmode_definir_hyperparametros.ipynb`

O objetivo é avaliar soluções com diferentes números de agrupamentos e configurações do algoritmo. A escolha final deverá considerar, além do custo, a estabilidade, o tamanho dos grupos e sua interpretabilidade.

### 05_Regressao_logistica_(Supervisionado)

Etapa de modelagem estatística supervisionada.

Notebook identificado:

- `01_Regressao_logistica.ipynb`

A documentação definitiva desta etapa deverá especificar o desfecho analisado, as variáveis explicativas, o tratamento de dados ausentes, a estratégia de validação e as métricas de desempenho.

## 4. Fluxo de processamento

A sequência geral identificada é:

1. Inspeção dos microdados e do dicionário.
2. Seleção das colunas de interesse.
3. Recodificação das respostas e tratamento de valores especiais.
4. Remoção de registros e duplicados conforme os critérios dos notebooks.
5. Conversão e exportação das bases analíticas.
6. Análise exploratória e estatística.
7. Aplicação e avaliação do K-Modes.
8. Modelagem por regressão logística.

A ordem exata de dependência entre os arquivos de saída deve ser confirmada nos caminhos de leitura e gravação dos notebooks.

## 5. Tecnologias

A estrutura observada indica o uso de Python e Jupyter Notebooks, com arquivos de dados em CSV, Parquet e Feather, além de planilhas Excel para dicionários, diagnósticos e relatórios.

As bibliotecas e suas versões deverão ser documentadas após a inspeção dos imports dos notebooks e do ambiente utilizado.

## 6. Dados e reprodutibilidade

A fonte original dos dados é a PeNSE 2024, do IBGE.

Para permitir a reprodução das análises, devem ser documentados:

- Origem e versão dos arquivos de entrada.
- Dicionário de variáveis utilizado.
- Critérios de seleção, exclusão e recodificação.
- Ordem de execução dos notebooks.
- Dependências de software.
- Parâmetros dos modelos e sementes aleatórias, quando aplicáveis.
- Arquivos de saída produzidos por cada etapa.

## 7. Considerações metodológicas

A exclusão de registros com valores ausentes pode alterar a composição da amostra e introduzir viés. Esse efeito deverá ser avaliado e documentado.

A remoção de duplicados deverá ser baseada em critérios explícitos, considerando que registros semelhantes não são necessariamente duplicados.

A interpretação dos resultados deverá considerar o desenho amostral da PeNSE, incluindo pesos, estratos e unidades primárias de amostragem quando pertinentes.

O K-Modes identifica agrupamentos com base nas categorias utilizadas; não demonstra causalidade nem estabelece categorias clínicas.

Os resultados da regressão logística dependem da definição do desfecho, dos pressupostos do modelo e do protocolo de validação.

## 8. Ética, privacidade e licença

A publicação do repositório deverá respeitar as condições de uso e atribuição dos microdados originais. Antes de tornar o código público, devem ser revisados os dados derivados, os notebooks, as saídas, os logs e o histórico de versões.

A licença do código deverá ser definida separadamente das condições aplicáveis aos dados.

## 9. Status do projeto

Projeto em desenvolvimento. A documentação de resultados, parâmetros, métricas e conclusões será ampliada conforme a validação dos notebooks e das análises.