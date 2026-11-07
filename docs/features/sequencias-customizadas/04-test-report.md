# Relatório de testes — Sequências de Acordes Customizadas

> Sessão de verificação em 06/11/2026. Nenhum arquivo de aplicação foi alterado
> nesta sessão; só este relatório foi preenchido. Os comandos abaixo foram
> executados na raiz do projeto, com o virtualenv `.venv` (Python 3.10.12) e o
> dataset real em `data/top/dataset_final.csv`.

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

A suíte cobre o backend, o banco, o matching e a regressão. Persistência Docker,
tempo de busca e interface não estão automatizados na suíte; essas verificações
foram feitas manualmente/por script descartável nesta sessão e estão registradas
abaixo, com as lacunas listadas ao final.

## Teste de regressão obrigatório

Você já executou `tests/baseline/gerar_baseline.py` contra a versão nova e o
resultado foi **sem diferenças**. Isso também foi confirmado pelo estado do
repositório: os 6 arquivos de baseline têm o mesmo SHA-256 do commit `HEAD` e
`git status` não mostra alteração neles.

```
$ git status --porcelain tests/baseline/
(sem saída)

$ sha256sum tests/baseline/seq*.json
c448e035... seq1.json    254aaba5... seq2.json     d3ce1c89... seq3.json
221dded4... seq4.json    543ecb66... seq5.json     2acefe3d... seq6.json
# os mesmos hashes aparecem em `git cat-file -p HEAD:tests/baseline/seqN.json`
```

As 6 sequências foram comparadas por conjunto de `id_unico_musica` (não por
ordem) com os arquivos de `tests/baseline/`:

| arquivo     | sequência    | músicas | resultado |
| ----------- | ------------ | ------: | --------- |
| `seq1.json` | `Bm,G,D,A`   |     199 | igual     |
| `seq2.json` | `C,G,Am,F`   |     296 | igual     |
| `seq3.json` | `Gm,F`       |       7 | igual     |
| `seq4.json` | `C,C7,F,Fm`  |       3 | igual     |
| `seq5.json` | `Em,G`       |       4 | igual     |
| `seq6.json` | `C,A7,Dm,G7` |       5 | igual     |

A regressão automatizada passou pelo parâmetro legado e por `sequencia_id`
(`test_parametro_legado_reproduz_baseline` e
`test_sequencia_id_reproduz_baseline`). O mapeamento de `seq1..seq6` para as
sequências foi o correto, sem assumir a ordem de `gerar_baseline.py:3`.

## Como rodar

```
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Resultado: **40 testes, todos verdes**, em 1,816 s.

```
Ran 40 tests in 1.816s

OK
```

Verificações complementares:

```
$ node --check static/assets/js/controllers/sequencia.js
node --check: OK

$ .venv/bin/python -m py_compile main.py musica.py matching.py sequencias_db.py tests/*.py
py_compile: OK
```

## Verificação funcional da API

### Matching de uma sequência nova

Usei a sequência nova `Dm,G,C`. O cálculo direto pelo matching retornou 4
músicas:

```
$ DATABASE_PATH=/tmp/opencode/verify.db .venv/bin/python - <<'PY'
import main
from matching import calcular_matches
print(calcular_matches(['Dm','G','C'], main.musicas.values()))
PY
[2026-11-06 22:30:41,264] INFO in main: Catálogo de sequências: 6 sequências, ...
['os-paralamas-do-sucesso_melo-do-marinheiro',
 'capital-inicial_terceiro-mundo-digital',
 'corinhos-evangelicos_diz-ai-igreja',
 'leonardo_simply-you']
```

Conferência manual de uma música:

- `os-paralamas-do-sucesso_melo-do-marinheiro` (Melô do Marinheiro — Os
  Paralamas do Sucesso) tem cifra
  `['C', 'Dm', 'G', 'C', 'Dm', 'C', 'G', ...]`. O bloco exato `Dm,G,C` aparece
  nas posições 1–3, e o conjunto de acordes da cifra é `{C, Dm, G}`, que está
  contido em `{Dm, G, C}`. Portanto casa pelas duas condições da regra.
- Controle negativo: `guns-n-roses_november-rain` (November Rain) também contém
  o bloco `Dm,G,C`, mas a cifra tem `F7M`, `C/E`, `Dm7`, `G5` etc. Como o
  conjunto da cifra **não** está contido em `{Dm, G, C}`, a música não casa.
  Isso confirma que a condição de conjunto está sendo aplicada.

A busca pela API, no catálogo temporário de verificação, retornou exatamente as
mesmas 4 músicas:

```
$ DATABASE_PATH=/tmp/opencode/api-verify.db .venv/bin/python /tmp/opencode/verify_api.py
...
=== BUSCA POR sequencia_id DA NOVA SEQUENCIA ===
status=200 content-type=text/html; charset=utf-8 total=4
  leonardo_simply-you | Simply You - Leonardo | cifra=['C', 'Dm', 'G']
  os-paralamas-do-sucesso_melo-do-marinheiro | Melô do Marinheiro - Os Paralamas do Sucesso | cifra=['C', 'Dm', 'G']
  capital-inicial_terceiro-mundo-digital | Terceiro Mundo Digital - Capital Inicial | cifra=['C', 'Dm', 'G']
  corinhos-evangelicos_diz-ai-igreja | Diz Ai Igreja - Corinhos Evangélicos | cifra=['C', 'Dm', 'G']
```

### Cadastro válido, duplicata e entradas inválidas

Verificação com o client de teste do Flask e banco temporário:

```
$ DATABASE_PATH=/tmp/opencode/api-verify.db .venv/bin/python /tmp/opencode/verify_api.py
```

O script é descartável e não foi versionado. Saída observada:

| caso             | entrada    | status | resposta observada                                          |
| ---------------- | ---------- | -----: | ----------------------------------------------------------- |
| cadastro válido  | `Dm, G, C` |    201 | `id=7`, `Location: /sequencias/7`, acordes `["Dm","G","C"]` |
| duplicata        | `Dm, G, C` |    200 | mesmo `id=7`, sem `Location`                                |
| separador `;`    | `Dm;G;C`   |    200 | mesmo `id=7` (duplicata da válida)                          |
| vazia            | `""`       |    400 | `{"erro": "informe pelo menos 2 acordes"}`                  |
| 1 acorde         | `Bm`       |    400 | `{"erro": "informe pelo menos 2 acordes"}`                  |
| só separador `;` | `;`        |    400 | `{"erro": "informe pelo menos 2 acordes"}`                  |
| campo ausente    | `{}`       |    400 | `{"erro": "envie o campo acordes"}`                         |
| tipo inválido    | `42`       |    400 | `{"erro": "acordes deve ser string ou lista"}`              |

Para `7M` × `7m`, a caixa é preservada e as sequências não são colapsadas:

| entrada   | status | resultado                       |
| --------- | -----: | ------------------------------- |
| `C7M,C7m` |    201 | `id=8`, acordes `["C7M","C7m"]` |
| `C7m,C7M` |    201 | `id=9`, acordes `["C7m","C7M"]` |
| `C7M;C7m` |    200 | duplicata da `id=8`             |

Ou seja, `C7M,C7m` e `C7m,C7M` são sequências distintas por ordem, e `7M` não é
confundido com `7m`. A validação também rejeita lista vazia, um único acorde e
texto bruto acima de 1000 caracteres (coberto em `test_entradas_invalidas`).

## Rotas existentes

Inventário obtido de `main.app.url_map`:

```
/                                      GET
/<path:path>                           GET   (catch-all de estáticos)
/acordes                               GET
/generos                               GET
/musica/<m_id>/                        GET
/musicas                               GET
/search                                GET
/sequencias                            GET
/sequencias                            POST
/sequencias/<int:sequencia_id>         GET
/similares                             GET
/static/<path:filename>                GET
```

- **Não há rota de exclusão**: nenhum `DELETE`/`PUT`/`PATCH`; a única escrita é
  `POST /sequencias`. `test_sem_metodos_de_mutacao_inesperados` e
  `test_post_somente_no_catalogo` passam.
- **Nenhuma rota nova com verbo no path**: o teste bloqueia `/cadastra`,
  `/lista`, `/remove`, `/deleta`, `/exclui`, `/atualiza` e `/edita`
  (`test_sem_verbos_no_path`, verde).
- Observação: a rota legada `/search` tem nome de ação em inglês, mas já existia
  antes desta feature, é somente leitura e não é rota de exclusão/edição. Não foi
  alterada nesta feature.

## Respostas em `json.dumps` (não `jsonify`)

- Não há ocorrência de `jsonify` no código Python (`grep`/busca retornou nenhum
  arquivo).
- `GET /sequencias` responde com `Content-Type: text/html; charset=utf-8` e
  corpo serializado como string:

```
status=200 content-type=text/html; charset=utf-8
b'[{"id": 1, "acordes": ["Bm", "G", "D", "A"], "criada_em": "...'
```

- O parâmetro legado também mantém o comportamento:
  `legado content-type=text/html; charset=utf-8`. O teste
  `test_respostas_continuam_text_html` passa. Nada foi migrado para `jsonify`.

## Persistência (Docker com volume nomeado)

Imagem reconstruída a partir do código atual (`docker build -t ciframe:test .`),
container em `18081`, volume de teste `deciframe-test-data-verify` montado em
`/app/instance`:

```
$ docker run -d --name deciframe-persist-test \
    -v deciframe-test-data-verify:/app/instance -p 18081:8080 ciframe:test
app no ar apos 2s

$ curl -s -X POST http://localhost:18081/sequencias \
    -H 'Content-Type: application/json' -d '{"acordes":"Am,F,C,G"}'
HTTP/1.1 201 CREATED
Location: /sequencias/7
{"id": 7, "acordes": ["Am", "F", "C", "G"], "criada_em": "..."}

$ curl -s http://localhost:18081/sequencias
[..., {"id": 7, "acordes": ["Am", "F", "C", "G"], "criada_em": "..."}]

$ docker rm -f deciframe-persist-test
$ docker run -d --name deciframe-persist-test \
    -v deciframe-test-data-verify:/app/instance -p 18081:8080 ciframe:test
app no ar apos 2s

$ curl -s http://localhost:18081/sequencias
[..., {"id": 7, "acordes": ["Am", "F", "C", "G"], "criada_em": "..."}]

$ curl -s "http://localhost:18081/similares?sequencia_id=7&pagina=1"
total pagina 1: 100
damien-rice_9-crimes - 9 Crimes
```

A sequência criada (`id=7`, `Am,F,C,G`) continuou no catálogo após `docker rm`
e recriação do container com o mesmo volume, e a busca por ela continuou
funcionando. Container, volume e imagem de teste foram removidos ao final.
O caso “sem volume, sobrevive só a `docker restart`” não foi reexecutado nesta
sessão; já havia sido verificado anteriormente e permanece como teste manual.

## Desempenho

Benchmark contra o container real (gunicorn), com o dataset completo, 30
requisições por sequência, página 1 (`TAM_PAGINA = 100`), descartando a primeira
requisição de cada sequência:

|  id | sequência         | mediana |     min |     max |   média |
| --: | ----------------- | ------: | ------: | ------: | ------: |
|   1 | `Bm,G,D,A`        | 34,1 ms | 25,1 ms | 40,5 ms | 33,7 ms |
|   2 | `C,G,Am,F`        | 39,2 ms | 32,2 ms | 46,3 ms | 38,9 ms |
|   3 | `Em,G`            | 32,9 ms | 17,2 ms | 63,6 ms | 31,3 ms |
|   4 | `C,A7,Dm,G7`      | 36,4 ms | 24,1 ms | 49,3 ms | 36,3 ms |
|   5 | `Gm,F`            | 32,7 ms | 16,3 ms | 71,6 ms | 33,9 ms |
|   6 | `C,C7,F,Fm`       | 41,7 ms | 21,4 ms | 67,0 ms | 40,5 ms |
|   7 | `Am,F,C,G` (nova) | 40,9 ms | 25,5 ms | 87,9 ms | 43,6 ms |

As medianas ficaram entre **32,7 e 41,7 ms**, na mesma faixa da linha de base
de **40–60 ms** (algumas ligeiramente abaixo, por serem execuções locais já
aquecidas). A sequência nova ficou em **40,9 ms** de mediana. Não foi
necessário implementar o cache LRU nesta fase; a decisão anterior de não
implementá-lo continua válida para este dataset e este deploy.

## Frontend

### Primeira versão rejeitada e refeita

A primeira implementação do frontend (Passo 5) entregou catálogo, cadastro e
busca por `id`, mas foi **rejeitada na revisão de uso** e refeita antes desta
validação. Os problemas apontados foram: título do cadastro solto junto da
lista; destaque calculado por nome de acorde (acordes iguais em outras
sequências também acendiam); formulário empurrado para baixo pelo catálogo;
ajuda/sucesso com pouco contraste sobre o magenta; sucesso sem nomear a
sequência; e campo/botão fora do padrão visual do app. A revisão R1–R4
(`03-plan.md`) refez a seção colapsável acima do catálogo, a seleção/destaque
por `id`, as mensagens nomeando a sequência e o contraste de campo, botão e
status. O roteiro abaixo deve ser executado na versão revisada.

### Roteiro de teste manual de interface

1. Suba a aplicação com Docker e volume nomeado:
   `docker run -v deciframe-data:/app/instance -p 8080:8080 ciframe`. Abra
   `http://localhost:8080/#/porsequencia`. **Deve aparecer** o título “Aponte
   uma sequencia de acordes”, a seção “Cadastre uma sequência” fechada e
   “Sequências disponíveis” com as 6 originais: `Bm,G,D,A`, `C,G,Am,F`, `Em,G`,
   `C,A7,Dm,G7`, `Gm,F`, `C,C7,F,Fm`. O painel direito não deve aparecer.
2. Clique no cabeçalho “Cadastre uma sequência”. **Deve aparecer** o formulário
   expandido, com o foco no campo, placeholder “Ex.: Bm,G,D,A”, ajuda “Separe os
   acordes por vírgula. Mínimo de 2.” e botão “Cadastrar”. A seção deve ficar
   acima do divisor e da lista.
3. Clique novamente no cabeçalho. **Deve** fechar o formulário. Clique outra vez
   e confirme que reabre e recebe foco. A seção não deve abrir/fechar sozinha em
   nenhum outro momento.
4. Com a seção aberta, digite `Dm,G,C` e clique em “Cadastrar”. **Deve aparecer**
   o texto “Cadastrando...” enquanto envia; depois “Sequência Dm,G,C
   cadastrada.”, o campo deve ser limpo, a seção deve continuar aberta e a nova
   sequência deve aparecer no fim da lista, selecionada e destacada (4 hexágonos
   brancos) com o painel direito aberto mostrando os resultados.
5. Envie `Dm,G,C` novamente. **Deve aparecer** “Sequência Dm,G,C já estava
   cadastrada.”, sem criar uma segunda linha; a linha existente deve continuar
   selecionada e os resultados não devem mudar.
6. Apague o campo e clique em “Cadastrar”. **Deve aparecer** “Informe os acordes
   da sequência.”, sem recarregar a lista e com a seção aberta.
7. Digite `Bm` e envie. **Deve aparecer** o erro de validação dentro da seção
   (“informe pelo menos 2 acordes”), o texto digitado deve ser preservado e a
   seção deve continuar aberta.
8. Digite `;` e envie. **Deve aparecer** o mesmo tipo de erro de mínimo de 2
   acordes, sem criar sequência.
9. Digite `C7M,C7m` e envie; depois `C7m,C7M`. **Devem aparecer** duas
   sequências distintas na lista, cada uma com a caixa preservada, e a mensagem
   de sucesso deve nomear a sequência correspondente. Envie `C7M;C7m` e confirme
   que é tratada como duplicata da primeira.
10. Clique em `Bm,G,D,A` e depois em `C,G,Am,F`. **Deve acontecer** a troca da
    seleção: apenas os 4 hexágonos da sequência escolhida ficam brancos; acordes
    iguais em outras linhas não devem acender. A linha selecionada deve ter
    apenas fundo sutil, sem contorno/sombra branca.
11. Na tela de resultados, troque o filtro “-- Gênero --” para um gênero, por
    exemplo Rock. **Deve acontecer** a atualização da lista de músicas sem perder
    a sequência selecionada.
12. Clique em um dos acordes da sequência no painel direito. **Deve acontecer** a
    limpeza da seleção, o painel direito deve desaparecer e o painel esquerdo
    deve voltar a ocupar a largura toda.
13. Reduza a janela para 375×667 (modo responsivo). **Deve aparecer** o cadastro
    visível, o catálogo rolando internamente e nenhum overflow horizontal.
14. Navegue por teclado: `Tab` até o cabeçalho “Cadastre uma sequência”, `Enter`
    para abrir, confirme o foco no campo, `Tab` até “Cadastrar” e `Enter` para
    enviar. **Não deve haver** erro de JavaScript no console (o `400` do teste de
    entrada inválida e a imagem externa `deciframe.png` são esperados e
    pré-existentes).
15. Confirme que as 6 sequências originais continuam acessíveis e buscáveis
    após cadastrar novas. Opcionalmente, recrie o container com o mesmo volume e
    recarregue a página: as sequências novas devem continuar na lista.

### Resultado do teste manual (a preencher)

> Cole aqui o resultado da execução no navegador (data, navegador/versão,
> viewport e OK/problema por passo). Se algum passo falhar, anexe o print e o
> erro do console.

| Passo | Resultado (OK / problema) | Observações |
| ----: | ------------------------- | ----------- |
|     1 | OK                        |             |
|     2 | OK                        |             |
|     3 | OK                        |             |
|     4 | OK                        |             |
|     5 | OK                        |             |
|     6 | OK                        |             |
|     7 | OK                        |             |
|     9 | OK                        |             |
|     8 | OK                        |             |
|    10 | OK                        |             |
|    11 | OK                        |             |
|    12 | OK                        |             |
|    13 | OK                        |             |
|    14 | OK                        |             |
|    15 | OK                        |             |

## O que ficou de fora

- Automação de UI na suíte do projeto: o roteiro acima é manual; não foi
  adicionado Selenium/Playwright.
- Persistência Docker automatizada: foi verificada manualmente nesta sessão
  (volume nomeado + `docker rm` + recriação); a suíte não sobe containers.
- Benchmark automatizado: a medição de tempo foi feita por script descartável,
  não virou teste de performance na suíte.
- Cobertura de alguns casos de API só na verificação ad hoc: a suíte cobre
  `Bm` (1 acorde), campo ausente, tipo inválido e limite de tamanho; os casos
  `""`, `";"` e `7M`/`7m` no endpoint foram verificados aqui, mas não foram
  adicionados como testes novos.
- Teste de concorrência de escrita no SQLite: o deploy atual usa 1 worker do
  gunicorn.
- Paginação completa e total de resultados no frontend: problema pré-existente,
  fora do escopo da feature.
- Autenticação/rate limiting: o catálogo é anônimo por requisito; só há limites
  básicos de tamanho e mínimo de 2 acordes.
- Teste de carga e cache LRU: a busca ficou dentro da meta sem cache; um cache
  pode ser adicionado depois se o volume de tráfego justificar.

## Observações e bugs

Nenhum bug funcional foi encontrado nas verificações desta sessão. A única
observação de nomenclatura é a rota legada `GET /search`, que tem nome de ação
em inglês e já existia antes da feature; ela é somente leitura, não é rota de
exclusão/edição e não foi alterada. Se o critério de REST for aplicado também a
rotas antigas, isso pode ser tratado em uma correção separada.
