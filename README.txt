Variável-alvo do projeto Taxa de suicídio entre adolescentes de 10 a 19 anos (?), por 100.000 habitantes, para cada município brasileiro com população superior a 50.000 habitantes (municipios com menos que 50.000 habitantes podem ter um indice also em relacao aos outros mesmo com poucos suicidios devido a baixa populacao - ainda verificar se 50.000 e o numero correto (?)).

Proposta Bases de dados do projeto:

                    ┌── SIM
                    │   suicídios - ano
                    │
                    ├── SINAN
                    │   violência/autolesão
                    │
                    ├── SIH
                    │   internações/tentativas
                    │
                    ├── CNES
                    │   CAPS/profissionais
                    │
                    └── IBGE
                        população
                        renda
                        educação
                        domicílios
                        saneamento
                        internet
                              ↓
                     BASE MUNICÍPIO-ANO
                              ↓
                       MACHINE LEARNING
                              ↓
                risco de suicídio adolescente

Os scripts criados contem referencia as pastas de arquivo no google drive mas via um link criado no computador de Claudio Jacomassi, ou seja, se tentar rodar em outro computador tera que mudar os diretorios que os scripts apontam.

