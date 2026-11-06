# Pesquisa — Sequências de Acordes Customizadas

## Perguntas que você precisa responder

1. **Algoritmo de matching**: hoje, as 6 sequências hardcoded em `main.py` (linhas
   40-45) são comparadas contra músicas via uma tag pré-computada
   (`SEQ_FAMOSA`/`seqs_famosas`, vinda do CSV). Sequências cadastradas pelo usuário
   não têm essa tag — o matching precisa ser calculado em tempo real a partir da
   lista de acordes de cada música (`musica.acordes`/`musica.cifra`). O que vai
   definir "a sequência X aparece na música Y"? A ordem dos acordes importa?
   Repetições de acorde dentro da música importam? É preciso normalizar (ex.:
   maiúsculas/minúsculas, variações de escrita do mesmo acorde)?
2. **Validação da hipótese**: rode o algoritmo que você está considerando contra os
   dados reais em `data/top/dataset_final.csv`, para as 6 sequências hoje
   hardcoded, e confirme (ou refute) que ele reproduz os mesmos matches que o
   código atual produz via `seqs_famosas`. Esse é o bar mínimo de correção que
   você vai usar na fase de testes.
3. **Banco de dados**: quais bancos embarcados (sem serviço externo adicional) são
   viáveis dentro do container Docker único e local-only já documentado em
   `docs/adr/0001-local-only-docker-deploy.md`? O que cada opção implica para o
   `Dockerfile` atual e para a persistência dos dados entre reinícios do
   container?
4. **Frontend existente**: o que a página `#/porsequencia`
   (`static/templates/sequencia.html` +
   `static/assets/js/controllers/sequencia.js`) já faz? Repare que ela tem hoje uma
   lista *hardcoded no JavaScript* de 4 sequências (`sequencia1`..`sequencia4`),
   diferente das 6 que existem no backend — um detalhe real e pré-existente do
   código, não um erro seu, que vale entender antes de decidir o que precisa
   mudar.

## Registro das descobertas

### Resumo

O backend carrega `data/top/dataset_final.csv` em memória e usa a tag
pré-computada `SEQ_FAMOSA` para as 6 sequências de `main.py:40-45`; não existe
matching em tempo real. A tag foi gerada por `get_famosas` em
`scripts/generate_data_set.py:7-24`, e a regra que reproduz exatamente a coluna
é: após **lowercasing** dos dois lados, ocorrência **contígua e ordenada** da
sequência na lista de acordes da música **e** todos os acordes da música
pertencentes ao conjunto de acordes da sequência. `Musica.acordes` é
`list(set(cifra))` e perde ordem/repetição (`musica.py:17`); a regra só é
reproduzível com `Musica.cifra` ordenada (`musica.py:16`). A tela
`#/porsequencia` tem 4 sequências hardcoded, um subconjunto das 6 do backend, e
envia `GET /similares?sequencia=...` sem paginação. Hoje não há banco: o CSV é a
única fonte, e o container único do ADR 0001 não tem serviço externo. Um banco
embutido em arquivo (SQLite é o caso mais direto) cabe nesse container;
sobreviver à recriação do container depende de volume, que o deploy atual não
declara.

Correspondência com as perguntas do template:

| Pergunta | Seções |
| --- | --- |
| 1. Algoritmo de matching | 1, 2 |
| 2. Validação da hipótese | 1 |
| 3. Banco de dados | 5 |
| 4. Frontend existente | 3, 4 |
| (custo da busca, apoio às decisões) | 6 |

### 1. SEQ_FAMOSA e regra de matching

- A coluna `SEQ_FAMOSA` é o índice 7 e `CIFRA` o índice 8 (`main.py:33-34`);
  são lidas em `main.py:52-63` e a tag é usada em `main.py:209`.
- Geração: `scripts/generate_data_set.py:7-24`. As 6 sequências estão em `:8`
  (`bm;g;d;a`, `c;g;am;f`, `em;g`, `c;a7;dm;g7`, `gm;f`, `c;c7;f;fm`). A função
  lowercasa a cifra inteira (`:12`), testa a sequência como substring da string
  separada por `;` (`:13`) e exige que todo token da música (`acorde.split(';')`,
  `:16`) esteja na lista de tokens da sequência (`:17-20`). Ao passar, grava o
  índice (`:21-23`); o CSV escreve o resultado em `:88-89`.
- Regra equivalente no nível de tokens, que foi a testada: com
  `cifra_lower = [t.lower() for t in musica.cifra]` e `seq = sequencia.split(';')`,
  a música recebe a tag se `contigua(cifra_lower, seq)` **e**
  `set(cifra_lower) ⊆ set(seq)`. O teste de substring do gerador é um pré-filtro;
  com a checagem de subconjunto, equivale a exigir a sequência como bloco
  contíguo na lista ordenada.
- Validação independente (script Python temporário importando `main`, 67.585
  músicas): para cada uma das 6, comparei `str(id) in musica.seqs_famosas` com
  essa regra e obtive **0 divergências** (199, 296, 4, 5, 7 e 3 tags; 514 músicas
  no total). Sem o lowercasing, a mesma regra diverge em 514 músicas: `m.cifra`
  preserva a caixa (`Bm` ≠ `bm`).
- Sem filtro de gênero, `GET /similares?sequencia=...` (test client) retorna o
  conjunto marcado pela tag, paginado em 100: página 1 de `Bm,G,D,A` → 100,
  `C,G,Am,F` → 100, `Em,G` → 4, `C,A7,Dm,G7` → 5, `Gm,F` → 7, `C,C7,F,Fm` → 3.
  A regra acima reproduz exatamente esse conjunto; o 100 é só o corte de
  `TAM_PAGINA` (`main.py:35,226-228`).
- A coluna bruta só contém `0`..`5` ou `NA` (7 valores distintos; nenhum id
  múltiplo). O mapeamento id → nome está em
  `data/mapeamento_sequencias_famosas.txt:1-6`.
- Repetições (dedução a partir da regra; **a confirmar com script na proposta**):
  como a sequência precisa aparecer como bloco contíguo, um acorde repetido
  **dentro** do bloco (ex.: `Bm, Bm, G, D, A` buscando `Bm,G,D,A`) não impede o
  match se o bloco exato aparecer a partir da segunda ocorrência, mas uma
  repetição no meio (ex.: `Bm, G, G, D, A`) impede. Repetições **fora** do bloco
  são permitidas, desde que todos os acordes da música pertençam à sequência.

Contagens por definição, sobre as 67.585 músicas carregadas (tudo comparado em
minúsculas):

| id  | sequência  | tag | contígua | conjunto | contígua + conjunto | divergências |
| --- | ---------- | --- | -------- | -------- | ------------------- | ------------ |
| 0   | Bm,G,D,A   | 199 | 866      | 9.014    | 199                 | 0            |
| 1   | C,G,Am,F   | 296 | 1.216    | 9.099    | 296                 | 0            |
| 2   | Em,G       | 4   | 3.110    | 8.165    | 4                   | 0            |
| 3   | C,A7,Dm,G7 | 5   | 96       | 8.194    | 5                   | 0            |
| 4   | Gm,F       | 7   | 1.039    | 8.159    | 7                   | 0            |
| 5   | C,C7,F,Fm  | 3   | 132      | 8.198    | 3                   | 0            |

A tabela mostra que nem “contígua” nem “conjunto” isolados reproduzem a tag; a
conjunção reproduz. Os totais de “conjunto” incluem as 8.141 músicas sem cifra
(conjunto vazio é subconjunto de qualquer sequência). O campo `acordes`
(`musica.py:17`) não preserva a ordem necessária para a parte contígua.

### 2. Formato dos acordes no CSV

- O CSV é separado por vírgula, tem 9 colunas e **não tem cabeçalho**: `csv.reader`
  vê 67.586 linhas de dados, todas com 9 colunas. `main.py:49-50` lê e descarta a
  primeira linha — que é a música real `14-bis,a-qualquer-tempo` —, e `main.py:55`
  usa `line.split(',')`.
- Dentro de `CIFRA` o separador é ponto e vírgula (`main.py:59`;
  `scripts/generate_data_set.py:73,89`). No arquivo, 59.246 das 67.586 linhas usam
  `;`; 8.141 têm `NA` e viram `m.cifra = []`; 6 linhas contêm `|` (tablatura) e 5
  contêm tab.
- `limpa_cifra` (`main.py:11-23`) divide a cifra por `;`, descarta pedaços vazios
  e, para cada pedaço, se houver `|` pega o texto antes do primeiro `|` e o
  primeiro token; senão divide por espaços/tabs. Por isso pedaços com mais de um
  acorde separado por espaço também funcionam. Evidência no CSV: 51 linhas com
  token vazio (ex.: `;` no fim), 26 com espaço interno em algum pedaço, 3 com
  espaço nas pontas e 16 com dois espaços seguidos. Não há vírgula literal dentro
  de `CIFRA` (o `,` é o delimitador de campo).
- `SEQ_FAMOSA` também usa `;` entre ids (`main.py:63`), mas na prática só tem um id
  ou `NA`.
- A API/frontend usam vírgula entre acordes. O JS monta
  `similares?sequencia=Bm,G,D,A` (`sequencia.js:55-61,73`); o backend remove as
  vírgulas e usa a string concatenada como chave (`main.py:191`), daí as chaves
  `BmGDA`, `CGAmF` etc. (`main.py:40-45`). A entrada não é comparada acorde a
  acorde com o CSV; ela é reduzida à chave concatenada.
- Caixa: `7M` e `7m` são tokens distintos e ambos existem em `m.cifra`: 38.991
  ocorrências em 431 tokens distintos com `7M`; 639 ocorrências em 38 tokens
  distintos com `7m` (sobre 3.505.331 ocorrências e 6.653 tokens únicos).
  Exemplos: `E7M`, `C7M`, `A7M(9)` vs `A7m`, `D7m`, `F#m7m`. A tag foi gerada
  com lowercasing (`scripts/generate_data_set.py:12`), o que colapsa `7M` e `7m`;
  o endpoint não normaliza caixa (`main.py:191-195`), e testei que `Bm,G,D,A`
  retorna resultados enquanto `bm,g,d,a` e `BM,G,D,A` retornam `[]`.
- Enarmonia: não há normalização em nenhuma etapa; `C#` e `Db` são tokens
  diferentes. Contando a fundamental (parte antes de `/`) sobre as 3.505.331
  ocorrências de `m.cifra`: `C#` 107.315 vs `Db` 7.461; `D#` 28.324 vs `Eb`
  43.178; `F#` 165.741 vs `Gb` 2.977; `G#` 62.263 vs `Ab` 23.704; `A#` 19.134 vs
  `Bb` 98.235. Há 3.808 tokens distintos com baixo invertido (`/`), que não
  entram nessa contagem de fundamental.
- Comparando o `CIFRA` bruto do CSV com `m.cifra` pelo mesmo `limpa_cifra`, a
  diferença é 0 — as diferenças textuais são só espaços/tabs, `;` vazios e
  tablatura, já absorvidos pelo parser.

### 3. Fluxo de `GET /similares` até `#/porsequencia`

- Rota `#/porsequencia` em `routes.js:17-21`, template
  `static/templates/sequencia.html` e controller
  `static/assets/js/controllers/sequencia.js`.
- Clique em uma sequência: `sequencia.html:6-7` chama
  `pesquisarPorSequencia` (`sequencia.js:63-90`). `createChordsString`
  (`sequencia.js:55-61`) monta `similares?sequencia=Bm,G,D,A`; se houver gênero,
  acrescenta `&generos=<gênero>` (`sequencia.js:74-76`). A URL é relativa
  (`apiUrl = ""`, `sequencia.js:72,77`); a constante `RESTAPI` de `app.js:3-5`
  não é usada nesse controller.
- Backend: `get_similares` (`main.py:170-201`). O branch de sequência
  (`main.py:190-197`) remove as vírgulas (`:191`), procura a chave no dict
  `sequencias` (`main.py:40-45`) e chama `get_similares_por_sequencia`
  (`main.py:203-223`), que filtra por gênero (`:205`), percorre a coleção e testa
  `str(id_seq) in musica.seqs_famosas` (`:209`), monta o dicionário (`:210-220`)
  e retorna a lista. `get_pagina` fatia 100 itens (`main.py:226-228`;
  `TAM_PAGINA = 100` em `main.py:35`).
- Paginação: o default é `pagina=1` (`main.py:176`);
  `get_similares_por_sequencia` monta a lista completa e só depois `get_pagina`
  fatia 100 (`main.py:196,203-228`). O frontend não envia `pagina`
  (`sequencia.js:73-77`), o template não tem controle de próxima/anterior
  (`sequencia.html`) e a resposta não inclui total: a UI mostra no máximo 100
  resultados. O gerador de baseline contorna isso percorrendo páginas 1..200 até
  uma página vazia (`tests/baseline/gerar_baseline.py:5-14`).
- Gênero: `apply_filtro` (`main.py:266-272`) ignora o argumento `musicas` e
  concatena `genero_musicas[genero]` para cada gênero válido. Sem filtro, usa a
  lista global `generos` (`main.py:179-182`). A ordem da coleção é por gênero, não
  por popularidade global; o template ordena só a página atual por
  `-popularidade` (`sequencia.html:42`).
- A lista de gêneros do frontend é hardcoded em `app.js:6-58` (51 itens) e difere
  do backend `/generos` (52): o backend tem `R&B;` com 303 músicas, ausente no
  JS. Testes: `Bm,G,D,A&generos=MPB` → 1 na página 1; `...&generos=Rock` → 5;
  gênero inexistente → `[]`.
- As respostas continuam `json.dumps` e vêm como
  `Content-Type: text/html; charset=utf-8` (`main.py:197,201`; testado).

### 4. As 4 sequências do JS versus as 6 do backend

- JS (`sequencia.js:2-31`): Bm-G-D-A, C-G-Am-F, Gm-F, C-C7-F-Fm.
- Backend (`main.py:40-45`): `BmGDA` (0), `CGAmF` (1), `EmG` (2), `CA7DmG7` (3),
  `GmF` (4), `CC7FFm` (5).
- As 4 do JS são os ids 0, 1, 4 e 5; faltam Em-G (2) e C-A7-Dm-G7 (3).

| lista      | sequência  | chave sem `,` | id  |
| ---------- | ---------- | ------------- | --- |
| JS         | Bm,G,D,A   | `BmGDA`       | 0   |
| JS         | C,G,Am,F   | `CGAmF`       | 1   |
| JS         | Gm,F       | `GmF`         | 4   |
| JS         | C,C7,F,Fm  | `CC7FFm`      | 5   |
| só backend | Em,G       | `EmG`         | 2   |
| só backend | C,A7,Dm,G7 | `CA7DmG7`     | 3   |

- Sequência desconhecida: o branch `elif sequencia_tag` inicializa
  `similares = []` e só preenche se `acordes in sequencias`
  (`main.py:190-197`). Retorna `[]` com HTTP 200 e `Content-Type: text/html`.
  Testei `C,D,E`, `ZZZ`, `Em,G,Am`, `BM,G,D,A` e `bm,g,d,a`: todos retornam `[]`.
- O template não tem formulário/input para sequência customizada; a lista é só
  `Sequencia.sequenciasFamosas` (`sequencia.html:6-8`). Como as 4 do JS batem com
  chaves conhecidas do backend, o caminho “desconhecida” não é alcançável pela UI
  atual; só por chamada direta à API.

### 5. Banco no container único e persistência

- Hoje não há banco. `main.py:49-98` lê o CSV no import; `requirements.txt:4-5`
  só lista Flask e gunicorn; `Dockerfile:1-12` é um único estágio
  `python:3.9-slim` com `COPY . .` e gunicorn. O ADR 0001 fixa container único
  local-only e mantém a busca em CSV em memória
  (`docs/adr/0001-local-only-docker-deploy.md:9-12`).
- Opções embutidas observadas, sem serviço externo:
  - SQLite: `sqlite3` já vem na imagem `python:3.9-slim` (verificado com
    `docker run --rm python:3.9-slim python -c "import sqlite3, sys; ..."`:
    Python 3.9.25 e SQLite 3.46.1); armazena em arquivo único e não adiciona
    dependência ao `requirements.txt`.
  - DuckDB, TinyDB, `shelve`/`dbm`: também embutidos/file-based. DuckDB e TinyDB
    não estão em `requirements.txt`; `shelve`/`dbm` são da biblioteca padrão.
  - Postgres/MySQL/Mongo: exigem processo/serviço além do container único; não
    existem no Dockerfile nem no ADR 0001.
- Concorrência: o `CMD` do `Dockerfile:12` não passa `--workers`, então o gunicorn
  usa 1 worker síncrono. Se o número de workers subir, o arquivo SQLite passa a
  ter escritores concorrentes entre processos (WAL/`busy_timeout` viram
  requisito); DuckDB também não é pensado para múltiplos processos escrevendo no
  mesmo arquivo.
- Persistência: o filesystem gravável do container sobrevive a `docker restart`
  do mesmo container (teste executado: arquivo criado em `/tmp` continuou
  legível após `docker restart`), mas não a `docker rm`/novo container. Para
  sobreviver à recriação, o arquivo precisa estar em volume nomeado ou bind
  mount. O container da app em execução (`deciframe`) tem `Mounts=[]`, ou seja,
  hoje só usa a camada gravável efêmera. O `Dockerfile` não declara `VOLUME`
  (`Dockerfile:1-12`); montar um volume em `/app` esconderia o código copiado,
  então o ponto de montagem deve ser um subdiretório dedicado (ex.:
  `/app/instance`). `.dockerignore` não exclui arquivo de banco
  (`.dockerignore:1-4`), então `COPY . .` copiaria um arquivo presente no
  contexto para a imagem; `.gitignore` também não ignora banco
  (`.gitignore:1-4`). O app atual não escreve nenhum arquivo.

### 6. Quantidade de músicas e custo de percorrer todas

- O CSV tem 67.586 linhas de dados e nenhum cabeçalho. `main.py:49-50` descarta a
  primeira linha, então `len(main.musicas) = 67.585`: a música
  `14-bis / a-qualquer-tempo` existe no CSV mas não é carregada. Há 8.141 músicas
  com `CIFRA` bruta `NA`, que ficam com `m.cifra = []`; 52 gêneros; 6.653 acordes
  únicos; 3.505.331 ocorrências de acordes.
- Medições locais (Python 3.10.12, `.venv`, após import): import ~1,90 s, RSS
  ~272 MB; `get_similares_por_sequencia(0, generos)` ~0,026 s; HTTP
  `/similares?sequencia=Bm,G,D,A` página 1 ~0,025 s; varredura completa de
  ocorrência contígua em `m.cifra` ~0,28 s; continência de conjunto em `m.cifra`
  ~0,10 s; sequência desconhecida ~0,0002 s.
- Cada página de uma sequência conhecida refaz a varredura completa antes de
  fatiar (`main.py:196,203-228`); o frontend pede só a página 1.

## Trade-offs identificados

Opções levantadas a partir das descobertas acima. A escolha fica para
`02-proposal.md`.

### Algoritmo de matching

| Opção | Prós | Contras |
| --- | --- | --- |
| Contígua + conjunto (regra da tag) | Reproduz as 6 com 0 divergências; mesmo comportamento de hoje | Muito restritiva: exclui músicas com qualquer acorde fora da sequência (ex.: Em,G casa com 4 de 67.585 músicas); sequências novas tendem a retornar poucos resultados |
| Só contígua | Mais intuitiva ("a sequência aparece na música"); mais resultados (ex.: 866 vs 199 para Bm,G,D,A) | Quebra a regressão das 6 |
| Conjunto sem ordem | Simples; não depende da ordem | Quebra a regressão; inclui as 8.141 músicas sem cifra como falso positivo |
| Híbrida (6 pela tag, novas por outra regra) | Passa na regressão sem limitar as novas | Comportamento inconsistente entre sequências; as 6 deixam de validar o algoritmo novo |

### Normalização de caixa

| Opção | Prós | Contras |
| --- | --- | --- |
| Minúsculas (como o gerador da tag) | Reproduz as 6 (verificado) | Colapsa `7M` e `7m`, que são acordes diferentes |
| Caixa preservada | Mantém o significado musical | Ainda não verificado se reproduz as 6 |

### Momento do cálculo

| Opção | Prós | Contras |
| --- | --- | --- |
| Em tempo real a cada busca | Simples | ~0,28 s por varredura, repetida a cada página |
| Pré-cálculo no cadastro, resultado salvo | Busca vira leitura; o catálogo de músicas é fixo (CSV), então o resultado não fica desatualizado | Cadastro mais lento; mais dados persistidos |
| Cache em memória | Rápido após a primeira busca | Perdido ao reiniciar; primeira busca continua lenta |

### Banco de dados

| Opção | Prós | Contras |
| --- | --- | --- |
| SQLite | Biblioteca padrão; sem dependência nova; SQL e transações | Um escritor por vez (relevante só com mais workers) |
| TinyDB | Simples, JSON legível | Dependência nova; sem transações fortes |
| `shelve`/`dbm` | Biblioteca padrão | Sem consultas; formato dependente da plataforma |
| DuckDB | Bom para análise | Dependência nova; não pensado para escrita concorrente |
| Postgres/MySQL/Mongo | Robustos | Exigem serviço externo; conflitam com o ADR 0001 |

### Persistência

| Opção | Prós | Contras |
| --- | --- | --- |
| Camada gravável do container | Nada a configurar | Perde os dados com `docker rm`/recriação |
| Volume nomeado em subdiretório (ex.: `/app/instance`) | Sobrevive à recriação; não esconde o código | Exige mudar o comando de execução e documentar |
| Bind mount | Arquivo visível no host | Depende de caminho do host |

### Frontend

| Opção | Prós | Contras |
| --- | --- | --- |
| Lista vinda de `GET` no backend | Atende ao requisito; resolve as 2 sequências ausentes da UI | Mais uma chamada ao carregar a página |
| Cadastro na mesma página `#/porsequencia` | Fluxo direto: cadastrar e buscar | Página fica mais carregada |
| Cadastro em página separada | Separa responsabilidades | Mais navegação; mais código |
| Entrada como texto livre (`Bm,G,D,A`) | Simples de implementar | Erros de digitação; exige validação |
| Seleção acorde a acorde | Menos erro de entrada | Mais complexa; muitos acordes possíveis |

## Decisões em aberto (resolvidas na proposta)

Não houve consulta com o professor. As questões abaixo foram triadas com base no
enunciado (`00-enunciado.md`) e no teste de regressão das 6 sequências originais
(`tests/baseline/`). A decisão final e a justificativa de cada item ficam em
`02-proposal.md`.

### Já restringidas pelo enunciado ou pela regressão

- **Regra de match.** As 6 originais precisam produzir os mesmos resultados de
  hoje, e a única regra que reproduz a tag com 0 divergências é "contígua e
  ordenada + todos os acordes da música pertencem à sequência" (seção 1). Usar a
  mesma regra para sequências novas mantém o comportamento "do mesmo jeito que já
  funciona hoje".
- **Fonte da ordem.** `m.cifra`, pois `m.acordes` é `list(set(...))` e perde a
  ordem (`musica.py:16-17`).
- **Repetições.** Seguir o mesmo tratamento da regra que reproduz a tag.
- **Ordenação e paginação.** Iguais às de hoje (por gênero, páginas de 100).
- **Catálogo.** As 6 originais entram no banco como dados iniciais; a tela
  `#/porsequencia` passa a listar o catálogo vindo do backend (requisito do
  enunciado), o que também resolve a ausência de Em-G e C-A7-Dm-G7 na UI.
- **Banco.** Precisa caber no container único (ADR 0001); persistir entre
  recriações do container exige volume em subdiretório dedicado (seção 5).

### A verificar na proposta

- **Caixa (`7M` ≠ `7m`).** A tag foi gerada com lowercasing, o que colapsa `7M` e
  `7m`. A validação da seção 1 comparou sequência em minúsculas com `m.cifra`
  original, e não testou comparação com a caixa preservada nos dois lados. Antes
  de decidir, verificar se a comparação case-sensitive também reproduz as 6 com 0
  divergências; se sim, preservar a caixa; se não, a regressão prevalece e o
  conflito é registrado.
- **Repetições.** Confirmar com script o comportamento deduzido na seção 1.
- **Formato da chave.** A API concatena os acordes sem separador (`BmGDA`), o que
  pode ser ambíguo para sequências novas. Avaliar identificar a sequência pela
  lista de acordes, não pela string concatenada.

### Decisões do implementador (enunciado: "é decisão sua")

- Tecnologia de banco e esquema.
- Formato da API nova.
- Duplicatas: candidata a retornar a sequência existente sem recadastrar.
- Validação de entrada e separadores aceitos (vírgula e ponto e vírgula).
- Abuso: sem login, catálogo aberto; definir limites mínimos (tamanho da
  sequência, quantidade de acordes).
- Edição/exclusão: não previstas no enunciado; candidatas a ficar fora, já que
  sem login qualquer visitante poderia apagar sequências.
- Rótulo/descrição da sequência: opcional.

### Fora do escopo

- **Enarmonia e transposição/tom.** O matching atual não usa nenhum dos dois
  (`TOM` existe em `main.py:32`, mas não participa); o enunciado pede o mesmo
  comportamento de hoje.
- **Métrica/compasso.** O dado não existe no CSV.

### Achados fora da feature (incluídos no escopo por decisão minha)

Não fazem parte dos requisitos do enunciado, mas foram incluídos no escopo por
decisão do implementador. Cada correção será um passo separado no plano, com
commit próprio e verificação da regressão das 6 sequências.

- `main.py:49-50` descarta a primeira linha do CSV como se fosse cabeçalho, mas
  ela é a música `14-bis / a-qualquer-tempo`. A verificar: se essa música tem
  tag `SEQ_FAMOSA`; se tiver, a correção altera o baseline e ele será regerado
  com justificativa.
- A lista de gêneros do frontend (`app.js:6-58`, 51 itens) não tem `R&B;`,
  presente no backend (52 itens, 303 músicas). O `;` no nome sugere erro na
  geração do dado; a decidir se a correção é no JS ou na limpeza do nome.
- A UI mostra no máximo 100 resultados, sem paginação, e a resposta da API não
  informa o total. Maior das três correções; prioridade baixa.
