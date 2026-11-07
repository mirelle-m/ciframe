# Proposta — Sequências de Acordes Customizadas

## Abordagem escolhida

Decisões registradas: regra contígua + conjunto; caixa preservada; pré-cálculo no
cadastro com cache em memória para buscas populares; SQLite; volume nomeado;
API REST por recurso com busca por `sequencia_id` e parâmetro legado preservado;
duplicata devolve a existente; validação com mínimo de 2 acordes e sem máximo de
acordes; cadastro na própria página `#/porsequencia`.

### Algoritmo de matching

Seja `S = [s1, ..., sk]` a lista ordenada de acordes de uma sequência cadastrada
(`k >= 2`, cada token aparado e com a caixa preservada) e `C = musica.cifra` a
lista ordenada de acordes da música (`musica.py:16`). A música casa com `S` se, e
somente se, as duas condições valem:

1. **Bloco contíguo e ordenado:** existe `i` tal que `C[i:i+k] == S`.
2. **Conjunto contido:** `set(C) ⊆ set(S)`.

A comparação é exata, token a token, com a caixa preservada. Não há lowercasing,
normalização enarmônica (`C#` ≠ `Db`), transposição nem remoção de repetições.
`musica.acordes` não é usado porque é `list(set(cifra))` e perde ordem e repetição
(`musica.py:17`).

A condição 2 é o que reproduz a tag `SEQ_FAMOSA` com **0 divergências** nas 6
sequências originais (verificado em `01-research.md:116-136`). A caixa preservada
também foi verificada com 0 divergências; usar minúsculas colapsaria `7M` e `7m`,
que são acordes diferentes. O custo aceito é que a regra é restritiva para
sequências novas: qualquer acorde fora da sequência elimina a música (ex.: `Em,G`
casa com 4 músicas no dataset). Repetições são literais: `Bm,Bm,G,D,A` casa com
`Bm,G,D,A` porque o bloco exato aparece a partir da segunda nota; `Bm,G,G,D,A` não
casa. Repetições fora do bloco são permitidas desde que a condição 2 valha.

### Banco de dados

SQLite via módulo `sqlite3` da biblioteca padrão, já presente na imagem
`python:3.9-slim`; não adiciona dependência ao `requirements.txt`. O arquivo fica
em `DATABASE_PATH` (default `/app/instance/deciframe.db`), um subdiretório
dedicado para não esconder o código quando o volume for montado. Conexão com
`journal_mode=WAL`, `busy_timeout` e `foreign_keys=ON` configurados; hoje o
gunicorn roda com 1 worker (`Dockerfile:12`), então não há escrita concorrente
entre processos.

Só o catálogo de sequências e os matches pré-calculados vão para o banco.
`musicas` e `generos` continuam vindo do CSV em memória (`main.py:47-98`), como
exige o enunciado e o ADR 0001.

### Esquema de dados (alto nível)

```
sequencias(
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  acordes     TEXT NOT NULL,          -- JSON array ordenado e canônico
  criada_em   TEXT NOT NULL,
  UNIQUE(acordes)
)

sequencia_matches(
  sequencia_id     INTEGER NOT NULL REFERENCES sequencias(id) ON DELETE CASCADE,
  id_unico_musica  TEXT NOT NULL,
  PRIMARY KEY (sequencia_id, id_unico_musica)
)
CREATE INDEX idx_sequencia_matches_musica ON sequencia_matches(id_unico_musica);

meta(
  chave  TEXT PRIMARY KEY,
  valor  TEXT NOT NULL
)
```

- A lista canônica é `json.dumps(acordes, ensure_ascii=False, separators=(',', ':'))`;
  ela serve para deduplicação e para a restrição `UNIQUE`, sem depender de um
  separador que possa aparecer dentro de um acorde.
- `sequencia_matches` guarda o resultado do pré-cálculo. A busca não precisa
  reescanear as cifras.
- `meta.dataset_version` guarda uma impressão do CSV (tamanho + `mtime`, ou hash
  do arquivo). Se mudar entre startups, os matches são apagados e recalculados,
  evitando resultado obsoleto após trocar o CSV.
- As 6 originais são semeadas no primeiro startup, na ordem de `main.py:40-45`
  (`Bm,G,D,A`, `C,G,Am,F`, `Em,G`, `C,A7,Dm,G7`, `Gm,F`, `C,C7,F,Fm`), com a mesma
  regra de matching usada para as novas. A semeadura é idempotente: se a lista
  canônica já existir, nada é criado.
- Versão 1 do esquema registrada em `PRAGMA user_version`; não há framework de
  migration nesta fase.

### Momento do cálculo e cache

- **Cadastro:** `POST /sequencias` valida, deduplica, grava a sequência e calcula
  os matches percorrendo `musicas.values()` com a regra acima, tudo na mesma
  transação. O custo é ~0,28 s por varredura completa (medido em
  `01-research.md`), pago uma vez por sequência.
- **Seed:** no startup, as 6 originais ausentes são inseridas e têm os matches
  calculados (o primeiro startup com banco novo paga ~6 × 0,28 s ≈ 1,7 s); se
  `dataset_version` mudou, todos os matches são reconstruídos.
- **Busca:** carrega os IDs de `sequencia_matches` para um `set` (cacheado por
  sequência) e percorre `apply_filtro(musicas.values(), generos_key)`, mantendo os
  que pertencem ao conjunto. Isso preserva exatamente a ordem atual (agrupamento
  por gênero e popularidade dentro do gênero; `main.py:203-228,266-272`).
- **Cache de buscas populares:** o resultado já serializado é guardado em um LRU
  em memória (ex.: `functools.lru_cache(maxsize=256)`), com chave
  `(sequencia_id, generos, pagina)`, em que `generos` é a tupla na ordem da
  requisição (vazia quando não há filtro). O cache é por processo, some no
  restart e é limpo quando os matches são reconstruídos. Com 1 worker ele atende
  as buscas repetidas; não é cache distribuído, o que exigiria serviço externo e
  conflitaria com o ADR 0001.
- **Invalidação:** criar uma sequência nova não altera o resultado das antigas;
  só a reconstrução por `dataset_version` limpa o cache.

### API

Todos os endpoints continuam retornando `json.dumps(...)` como string, sem
`jsonify` e sem alterar o `Content-Type: text/html` — comportamento legado
intencional (`main.py:197,201`).

| Método | Rota | Descrição |
| --- | --- | --- |
| `GET` | `/sequencias` | Lista o catálogo em ordem de cadastro (`id` crescente). |
| `POST` | `/sequencias` | Cadastra uma sequência. |
| `GET` | `/similares?sequencia_id=<id>` | Busca músicas pela sequência do catálogo. |

`GET /sequencias` → `200`:

```json
[
  {"id": 1, "acordes": ["Bm", "G", "D", "A"], "criada_em": "2026-11-06T19:30:00Z"},
  {"id": 2, "acordes": ["C", "G", "Am", "F"], "criada_em": "2026-11-06T19:30:00Z"}
]
```

`POST /sequencias` aceita `{"acordes": "Bm,G,D,A"}` ou
`{"acordes": ["Bm", "G", "D", "A"]}`. Em caso de criação, responde `201`, com o
objeto criado e `Location: /sequencias/<id>`. Se a lista ordenada já existir
(mesma caixa e mesma ordem), responde `200` com o objeto existente, sem criar
outra linha. Entrada inválida responde `400` com `{"erro": "..."}`.

`GET /similares?sequencia_id=<id>` aceita `generos` e `pagina` como hoje e retorna
a mesma lista de músicas (campos de `main.py:210-220`), com `TAM_PAGINA = 100`
(`main.py:35,226-228`). `sequencia_id` inexistente responde `404` com
`{"erro": "..."}`.

O parâmetro legado `GET /similares?sequencia=Bm,G,D,A` continua aceito: o texto é
dividido por `,` ou `;`, cada token é aparado, a lista é comparada com a lista
canônica do catálogo e, se existir, usa-se o `id` correspondente. Se não existir,
retorna `[]` com `200`, como hoje. Isso preserva as 6 sequências e elimina a
ambiguidade da chave concatenada (`BmGDA`).

Não há rotas de edição ou exclusão: sem login, qualquer visitante poderia apagar
o catálogo.

### Frontend

A página `#/porsequencia` deixa de usar as 4 sequências hardcoded
(`sequencia.js:2-37`) e passa a:

- carregar `GET /sequencias` no controller e montar `vm.sequenciasFamosas` a
  partir do catálogo real, ordenado por cadastro;
- exibir as 6 originais e as novas com o mesmo componente `df-hex`
  (`sequencia.html:6-8`), convertendo `acordes` (array de strings) para o formato
  `{acorde, cor}` que o template espera;
- concentrar o cadastro em uma **seção colapsável inline acima do catálogo**,
  separada da lista por um divisor; o cabeçalho “Cadastre uma sequência” é o
  título da seção e o acionador do abrir/fechar, com o campo alinhado a ele;
- abrir a seção com foco no campo e mantê-la aberta após sucesso, duplicata ou
  erro; o colapso é sempre manual, por decisão do usuário;
- enviar `POST /sequencias` com mensagens de carregando, erro de validação e
  sucesso **dentro da seção**; a mensagem nomeia a sequência, e a criada (ou a
  existente, em duplicata) é recarregada, selecionada e destacada na lista;
- selecionar e destacar por `id` da sequência, não por nome de acorde: apenas os
  hexágonos da sequência escolhida mudam de cor, e a linha selecionada recebe
  uma marca visual própria;
- usar texto branco e uma área de sucesso de alto contraste sobre o magenta,
  seguindo os textos dos demais painéis, e alinhar campo/botão ao padrão visual
  do app (sem o cinza padrão do `btn-default`);
- buscar com `GET /similares?sequencia_id=<id>` em vez de montar a string
  concatenada (`sequencia.js:55-77`), mantendo o filtro de gênero e a renderização
  atual.

O padrão visual existente é mantido (AngularJS 1.4.9 + Bootstrap, sem build). As
decisões de layout, estados e contraste estão registradas em `frontend.md`; a
revisão visual pós-implementação está detalhada em `03-plan.md`, na seção
“Revisão após implementação”. Backend, banco e API não mudam nesta revisão.

### Persistência e deploy

O `Dockerfile` cria `/app/instance` (sem declarar `VOLUME`, para não gerar
volumes anônimos); o volume nomeado é montado nesse subdiretório no `docker run`,
sem esconder o código copiado para `/app`:

```
docker run -v deciframe-data:/app/instance -p 8080:8080 ciframe
```

O `README.md` passa a documentar esse comando. `.dockerignore` e `.gitignore`
incluem `instance/` e arquivos `*.db`, `*.db-wal`, `*.db-shm` para não copiar um
banco local para a imagem nem versioná-lo. Sem volume, o arquivo sobrevive a
`docker restart`, mas não a `docker rm`/recriação; com o volume nomeado, sobrevive
aos dois. O ADR 0001 continua válido: container único, local-only, sem serviço
externo.

## Sistemas impactados

| Arquivo | Mudança |
| --- | --- |
| `main.py` | Novas rotas, branch de busca por `sequencia_id`, seed e cache; preserva `json.dumps`. |
| novo módulo de persistência (ex.: `sequencias_db.py`) | Conexão SQLite, esquema, CRUD, deduplicação e pré-cálculo dos matches. |
| `Dockerfile` | Criar `/app/instance` (sem `VOLUME`; o volume é nomeado no `docker run`). |
| `README.md` | Comando de execução com volume nomeado. |
| `.dockerignore`, `.gitignore` | Ignorar `instance/` e arquivos do banco. |
| `static/assets/js/controllers/sequencia.js` | Catálogo via API, cadastro, busca por `sequencia_id`, seção colapsável e seleção por `id`. |
| `static/templates/sequencia.html` | Cadastro colapsável acima do catálogo, mensagens, linha selecionada e lista vinda do backend. |
| `static/assets/css/app.css` | Revisão visual: seção colapsável, contraste, botão/campo e estado selecionado. |
| `tests/` | Testes de algoritmo, validação, API e regressão contra `tests/baseline/`. |
| `docs/adr/0002-persist-custom-sequences.md` | Registro da decisão de persistência. |

## Alternativas consideradas e descartadas

- **Só contígua:** mais intuitiva e com mais resultados (866 vs 199 para
  `Bm,G,D,A`), mas quebra a regressão das 6. Descartada.
- **Híbrida (6 pela tag, novas por outra regra):** passaria na regressão, mas cria
  comportamento inconsistente e impede que as 6 validem o algoritmo novo.
  Descartada.
- **Minúsculas:** reproduz a tag, mas colapsa `7M` e `7m`. Descartada.
- **Cálculo em tempo real a cada busca:** simples, porém ~0,28 s por varredura,
  repetido a cada página; o `CONTEXT.md` pede para evitar varrer todas as músicas.
  Descartada.
- **TinyDB, `shelve`/`dbm`, DuckDB:** dependência nova ou falta de consultas e
  transações; DuckDB não é pensado para escrita concorrente. Descartadas.
- **Postgres/MySQL/Mongo:** exigem serviço externo e conflitam com o ADR 0001.
  Descartados.
- **Camada gravável do container:** perde o catálogo em `docker rm`/recriação.
  Descartada.
- **Chave concatenada (`BmGDA`) como identidade:** ambígua para sequências novas.
  Descartada em favor de `id` + lista canônica.
- **Página separada de cadastro:** mais navegação e código; a mesma página atende
  ao fluxo cadastrar-e-buscar. Descartada.
- **Criar duplicatas:** polui o catálogo sem benefício. Descartada.

## Escopo explícito

**Dentro do escopo:**

- Banco SQLite com catálogo de sequências, lista ordenada e matches pré-calculados.
- Semeadura idempotente das 6 originais e recálculo por `dataset_version`.
- `GET /sequencias`, `POST /sequencias`, `GET /similares?sequencia_id=...` e
  compatibilidade com `GET /similares?sequencia=...`.
- Validação (mínimo 2 acordes, separadores `,` e `;`, trim, caixa preservada,
  limite de tamanho bruto) e duplicata devolvendo a existente.
- Cache LRU em memória para buscas populares.
- Frontend `#/porsequencia` lendo o catálogo, cadastrando e buscando por `id`.
- Volume nomeado, atualização de `Dockerfile`/`README.md` e dos arquivos de
  ignore.
- Testes de regressão contra `tests/baseline/`.

**Fora do escopo (e por quê):**

- Edição/exclusão de sequências: sem login, qualquer visitante poderia apagar o
  catálogo; não está no enunciado.
- Login, autenticação e rate limiting sofisticado: o catálogo é aberto e anônimo
  por requisito; só há limites básicos de tamanho de entrada.
- Normalização de caixa, enarmonia, transposição e tom: quebrariam a regressão ou
  estão fora do escopo declarado.
- Migrar `musicas`/`generos` para o banco: o enunciado fixa o CSV em memória.
- Alterar `json.dumps`/`Content-Type`: comportamento legado intencional.
- Paginação completa no frontend e total de resultados: problema pré-existente,
  não exigido pela feature.
- Cache distribuído (Redis etc.): exigiria serviço externo, contra o ADR 0001.
- Modernização do frontend/build step: fora do escopo; a página segue o padrão
  AngularJS atual.

## Validação e critérios de aceite

- **Algoritmo:** testes unitários para bloco contíguo + conjunto, caixa
  preservada, acordes repetidos, música sem cifra e sequência com repetição.
- **Regressão obrigatória:** para as 6 originais, comparar o conjunto de
  `id_unico_musica` retornado por `GET /similares?sequencia_id=...` com
  `tests/baseline/seq1.json`..`seq6.json`; o resultado deve ser idêntico. Atenção:
  a ordem de `gerar_baseline.py:3` não é a de `main.py:40-45`, então o teste deve
  mapear cada sequência ao arquivo certo, não assumir `seq1 = id 0`. Repetir pelo
  parâmetro legado `sequencia=`.
- **API:** criação válida (201), duplicata (200, mesmo `id`), entrada inválida
  (400), `sequencia_id` inexistente (404), lista em ordem de cadastro e
  compatibilidade do parâmetro legado.
- **Persistência:** teste manual no Docker com volume nomeado: criar sequência,
  `docker rm` do container, subir de novo com o mesmo volume e confirmar que o
  catálogo continua lá. Testar também que sem volume o dado só sobrevive a
  `docker restart`.
- **Desempenho:** cadastro abaixo de ~0,5 s por sequência; primeira busca
  próxima dos ~0,03 s atuais; busca cacheada abaixo de ~50 ms. Medir com o mesmo
  dataset de 67.585 músicas.
- **Frontend:** cadastrar uma sequência nova, vê-la na lista, buscar por ela e
  confirmar que as 6 originais continuam acessíveis; testar duplicata e erro de
  validação.

## Riscos e trade-offs

- **Regra restritiva:** sequências novas podem retornar poucos ou nenhum
  resultado. É o custo de manter o comportamento idêntico ao de hoje.
- **Entrada sensível à caixa:** `bm,g,d,a` não casa com o dataset. A UI deve
  mostrar exemplos e mensagens claras; a validação não corrige a caixa
  automaticamente.
- **SQLite com um escritor:** adequado ao worker único atual; se o número de
  workers subir, WAL e `busy_timeout` precisam ser mantidos e testados.
- **Matches pré-calculados podem ficar obsoletos** se o CSV mudar sem atualizar
  `dataset_version`; a reconstrução no startup cobre o caso previsto (restart é
  necessário para reler o CSV).
- **Cache por processo:** não é compartilhado entre workers e é perdido no
  restart; é uma otimização, não a fonte de verdade.
- **Volume exige mudança no comando de execução:** o `Dockerfile` sozinho não
  garante persistência; o `README.md` precisa deixar isso explícito.
- **Duplicata case-sensitive:** `Bm,G,D,A` e `bm,g,d,a` são sequências distintas,
  embora a segunda não case com o dataset. É consistente com a caixa preservada.

## Questões em aberto

- Método exato de `dataset_version` (tamanho + `mtime` vs hash do CSV): a proposta
  assume tamanho + `mtime` por simplicidade; validar se é suficiente no fluxo de
  deploy.
- Tamanho do LRU (256 entradas) e se vale cachear também a lista completa de
  matches por sequência além da página final.
- Manter o parâmetro legado `sequencia=` indefinidamente ou apenas enquanto o
  frontend antigo existir.
- Exibir total de resultados/paginação no frontend: fica para uma correção
  separada, se for desejado.
