# Relatório de testes — Sequências de Acordes Customizadas

## Cobertura

- `tests/test_matching.py`: normalização (vírgula, ponto e vírgula, trim, caixa
  preservada), regra de bloco contíguo + conjunto, repetições dentro/fora do
  bloco, música sem cifra, caixa (`7M` ≠ `7m`) e regressão do algoritmo contra
  os 6 baselines.
- `tests/test_sequencias_db.py`: criação do esquema e `PRAGMA user_version=1`,
  seed idempotente das 6 originais, ordem de cadastro, deduplicação, cálculo de
  matches, recálculo por `dataset_version` e persistência da versão em `meta`.
- `tests/test_api_sequencias.py`: `GET /sequencias` em ordem de cadastro,
  `POST /sequencias` com string e lista (201), duplicata (200, mesmo id, sem
  `Location`), entradas inválidas (400), `sequencia_id` inexistente/inválido
  (404), parâmetro legado inexistente (`[]`), legado com `;` e `Content-Type`
  `text/html`.
- `tests/test_regression.py`: as 6 sequências originais comparadas com
  `tests/baseline/seq1..seq6.json`, tanto pelo parâmetro legado `sequencia=`
  quanto por `sequencia_id=`.
- `tests/test_routes.py`: inventário de rotas, bloqueio de verbos no path
  (`/cadastra`, `/lista`, ...), ausência de `DELETE`/`PUT`/`PATCH` e `POST`
  somente em `/sequencias`.
- `tests/support.py` / `tests/__init__.py`: isolam a suíte em um
  `DATABASE_PATH` temporário, sem tocar em `instance/`.

## Teste de regressão obrigatório

As 6 sequências foram comparadas por conjunto de `id_unico_musica` (não por
ordem) com os arquivos de `tests/baseline/`:

| arquivo | sequência | músicas | resultado |
| --- | --- | ---: | --- |
| `seq1.json` | `Bm,G,D,A` | 199 | igual |
| `seq2.json` | `C,G,Am,F` | 296 | igual |
| `seq3.json` | `Gm,F` | 7 | igual |
| `seq4.json` | `C,C7,F,Fm` | 3 | igual |
| `seq5.json` | `Em,G` | 4 | igual |
| `seq6.json` | `C,A7,Dm,G7` | 5 | igual |

A regressão passou pelo parâmetro legado e por `sequencia_id`, e também foi
repetida contra o container Docker na porta 18080 com os mesmos 6 resultados.

## Como rodar

```
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Resultado: 40 testes, todos verdes.

Verificações complementares:

```
node --check static/assets/js/controllers/sequencia.js
.venv/bin/python -m py_compile main.py musica.py matching.py sequencias_db.py tests/*.py
```

## Persistência e desempenho

- Docker com volume nomeado: sequência criada (`id=7`), sobreviveu a
  `docker restart` e a `docker rm` + recriação com o mesmo volume.
- Docker sem volume: sobreviveu a `docker restart` e foi perdida após
  `docker rm` + recriação (voltou às 6 originais), como esperado.
- Benchmark local com o dataset real (Flask test client):
  `GET /sequencias` ~6 ms; `GET /similares?sequencia_id=1` ~18 ms;
  legado `sequencia=Bm,G,D,A` ~17 ms; `POST /sequencias` ~121 ms. As buscas
  ficaram dentro da meta de poucas centenas de ms e próximas dos ~30 ms
  anteriores, então o cache LRU foi deliberadamente **não** implementado nesta
  fase.

## Frontend

A página `#/porsequencia` foi carregada em Chrome headless com o app em Docker:
o DOM final tinha 6 contêineres de sequência (as 6 originais) e o formulário de
cadastro renderizado. Não houve automação de clique/preenchimento no browser;
o cadastro, a duplicata e a busca foram exercitados pela API e o controller foi
validado com `node --check`.

## O que ficou de fora

- Automação completa de UI (clicar nas sequências, preencher o formulário e
  conferir mensagens no browser). A verificação foi headless (renderização) mais
  testes de API; não há Selenium/Playwright no projeto.
- Teste de concorrência de escrita no SQLite: o deploy atual usa 1 worker do
  gunicorn.
- Paginação completa e total de resultados no frontend: problema pré-existente,
  fora do escopo da feature.
- Autenticação/rate limiting: o catálogo é anônimo por requisito; só há limites
  básicos de tamanho e mínimo de 2 acordes.
- Teste de carga e cache LRU: a busca ficou dentro da meta sem cache; um cache
  pode ser adicionado depois se o volume de tráfego justificar.
