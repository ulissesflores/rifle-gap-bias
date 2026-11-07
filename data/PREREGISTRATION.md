# PREREGISTRATION do artigo `2026-rifle-lacunas-prefeitos`

> **Cópia pública (2026-11-03):** caminhos locais da máquina do autor e os nomes e notas dos revisores foram retirados desta cópia. Datas, hipóteses e regras de leitura estão inalteradas.

> O estudo empírico já tem pré-registros selados no projeto de origem: v1 (`preregistro/PREREGISTRO.md`, com as Emendas 01 a 04) e v2 (`preregistro/v2/PREREGISTRO-V2.md`, com a Emenda 01); as cadeias de hash desses arquivos estão em `data/origem/preregistro.manifest.jsonl`. Este arquivo registra as hipóteses do **artigo**, isto é, o que a pesquisa de literatura (A5) e o escrutínio (A6) testam antes da redação.

## Hipóteses

- **H0-lit:** a distorção de tamanho da costura de lacuna interior sob correlação serial **já está documentada** na literatura que aplica ou discute o RIFLE.
  - **H1-lit:** não está; a contribuição é nova.
- **H0-apl:** existe aplicação publicada do RIFLE a prefeitos ou governos municipais brasileiros.
  - **H1-apl:** não existe; o caso brasileiro é novo.
- **H-estudo (selada no v2, não reaberta):** a troca de prefeito move o índice além do acaso.
  - Registro: a regra executada deu "não importa".
  - Avaliação pós-hoc: equivalência não demonstrada; conclusão inconclusiva.
  - Rodada corrigida: T1 sem rejeição.

## Emendas

- **2026-10-31:** tese e título escolhidos pelo autor (ver `docs/paper/F1-GENESE.md`, seção "Decisões do autor").
- **2026-10-31 (depois do conselho), H0-lit desdobrada:**
  - (a) a correção (permutar dentro de blocos contíguos) **já está documentada**: opção `nostitch` do pacote Stata, 2018. Confirmada.
  - (b) a ressalva qualitativa ("long gap") está no software, não no artigo. Confirmada.
  - (c) a distorção QUANTITATIVA da costura padrão não está documentada. Segue como H1.
  - (d) **H-alinhamento, nova, testada por simulação registrada antes de rodar:** o perigo da costura vem de a lacuna coincidir com a troca de líder, e não do comprimento dela.
    - Prevê que lacuna alinhada ≫ lacuna aleatória > lacuna no meio da passagem ≈ 5%.
    - Se as três inflarem, o resultado é outro: a costura é insegura sob correlação serial mesmo com lacuna curta e aleatória.
- **2026-10-31, resultado da H-alinhamento** (`diagnostico_alinhamento.py`, cadeia `piloto` da origem, saída sha 5491adba…):
  - **CONFIRMADA:**
    - lacuna vizinha de troca: 99,8%;
    - p9 junto da eleição: 98,2%;
    - período aleatório: 76%;
    - lacuna no meio da passagem: 0%;
    - sem lacuna: 3,8%.
  - A previsão "a lacuna longa não distorce mais que a curta" também se confirmou: dois períodos deram 71%, contra 98% de um período.
  - **Achado não previsto:** a costura não só infla, ela ENVIESA, e o sinal depende de a passagem verdadeira atravessar a lacuna. Dentro da passagem, a costura alonga a passagem real e o teste fica CONSERVADOR sob o nulo (0% no motor; 0,2% no pacote fiel, com poder de 96,8% na alternativa de 10%). A palavra "cego", usada antes, estava errada (laudos de 2026-10-31).
  - O `nostitch` restaura o tamanho: 5,6% e 4,6%.
  - Escala com o número de unidades em teste (`diagnostico_escala.py`, registrado antes).
- **2026-10-31, números de capa:** passam a vir da tradução fiel do `rifle.ado` (`piloto/rifle_ado.py`, origem).
  - Os do motor do projeto (64%, 98%, 76%, 0%) usam rótulo por passagem (Emenda 02 do v1) e ficam como sensibilidade.
  - Os 64% continuam sendo o tamanho correto do teste PRÉ-REGISTRADO do projeto na máscara real. O artigo critica o PACOTE, cujo número é 34,8%.
  - 27,2% (`diagnostico_ado`) e 26% (`diagnostico_ado_escala`) em N = 1.000 vêm de subamostras e sementes diferentes e são compatíveis.
  - A linha sem lacuna dá 2,2% [1,1-3,9] no pacote fiel: é um conservadorismo leve do próprio pacote (valor-p com ">" estrito, média que inclui o real, agrupamento por identidade). Fica relatado.
- **2026-11-01, portão P3 (autor):** título "Dado faltando na troca de prefeito engana o teste de liderança" e tese revisada (ver `docs/paper/F1-GENESE.md`, "Decisões do autor (P3)"). As hipóteses do artigo ficam:
  - **H1-lit:** a distorção QUANTITATIVA da costura padrão não está documentada. Varredura A5 mais o adendo.
  - **H-alinhamento:** confirmada no motor e no pacote fiel.
  - **H-escala:** a distorção cresce com N; confirmada no pacote fiel.
  - **H1-apl:** sem aplicação publicada a prefeitos brasileiros.
- **2026-11-01, emenda da primeira rodada de revisão externa (gravada ANTES de ver qualquer resultado das células novas):**
  - A revisão apontou afirmações do texto sem célula que as sustente. O módulo `piloto/diagnostico_ado_juizes.py` (origem, cadeia `piloto` seq 51, semente 17112026, 500 bases, 1.000 permutações) acrescenta dez células, todas na tradução fiel do pacote e todas para frases que o artigo JÁ faz; nenhuma hipótese nova.
  - **Regras de leitura fixadas agora:**
    - "o `nostitch` restaura o tamanho" só se mantém, para cada célula `nostitch` em 5.468, se o intervalo exato de 95% contiver 5%; se não contiver, o texto diz o número e deixa de afirmar restauração naquele N.
    - "lacuna dentro do mandato deixa conservador" passa a ser lida contra `sem_lacuna_meio867` (mesmos 867 municípios); a frase "muda só onde a lacuna cai" só fica se a comparação for nessa amostra.
    - o custo de poder do `nostitch` é relatado como a diferença entre `p9_nostitch_poder10/05` e `sem_lacuna_poder*` no mesmo painel de 1.000, sem regra de passar ou falhar: é medida, não teste.
    - `sem_lacuna_N5468` é relatado como a linha de base do pacote no painel inteiro, qualquer que seja.
  - **Correções de texto que não dependem das células** (conferidas antes): a regra geral "lacuna dentro do mandato = conservador" está ERRADA (contraexemplo apontado na revisão, conferido por conta exata: A em 1-4, B em 5-6, falta 2, diferença esperada ρ(1-ρ)(1-2ρ)/3 > 0 para ρ < 0,5); passa a valer só para a célula testada. A comparação "dois períodos distorcem menos que um" (71,4% contra 98,2%) muda posição e amostra junto com o comprimento e deixa de ser usada como evidência sobre comprimento.

- **2026-11-07, portão P2 reaberto (autor):** título passa a ser "O prefeito melhora a cidade além do acaso? Dado faltando na troca de prefeito faz o teste dizer que sim" (a pergunta como gancho, o achado como resposta). Tese, hipóteses e regras de leitura inalteradas.
