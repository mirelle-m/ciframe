# Plano — Sequências de Acordes Customizadas

> Este documento é só o plano da fase 3; nenhuma mudança de código foi feita.
> A implementação segue `02-proposal.md` e o ADR `docs/adr/0002-persist-custom-sequences.md`.

## Passos

**Escopo e premissas**
- Só o catálogo de sequências vai para o banco; `musicas`/`generos` continuam no CSV em memória.
- SQLite via `sqlite3` da stdlib; container único/local; sem dependência nova.
- API mantém `json.dumps(...)` (Content-Type `text/html`), sem `jsonify`.
- Sem login, edição ou exclusão; validação mínima de entrada.
- `tests/baseline/seq*.json` é a fonte de verdade; comparação por conjunto de `id_unico_musica`, não por ordem.
- Portão comum a todo passo: rodar a regressão das 6 e o inventário de rotas antes e depois da mudança; se falhar, parar e corrigir antes de seguir.

**Timeline (estimativa, 1 dev, dataset já presente)**
- Passo 1: 1–2h; Passo 2: 2–3h; Passo 3: 2–3h; Passo 4: 2–3h; Passo 5: 2–3h; Passo 6: 1–2h.
- Revisão após implementação (frontend): 4h adicionais (R1–R4).
- Total: ~14–20h (~2–2,5 dias). Não inclui revisão de código nem imprevistos de dataset.

1. [ ] **Passo 1 — Harness de regressão + inventário de rotas (antes de tocar no código)**
   - Criar `tests/test_regression.py` (stdlib `unittest`; `pytest` não está instalado) que sobe o app com o client de teste e compara `/similares?sequencia=...` com os baselines, paginando até página vazia.
   - Mapear corretamente: `seq1=Bm,G,D,A` (199), `seq2=C,G,Am,F` (296), `seq3=Gm,F` (7), `seq4=C,C7,F,Fm` (3), `seq5=Em,G` (4), `seq6=C,A7,Dm,G7` (5). Não assumir que a ordem do `gerar_baseline.py` é a de `main.py:40-45`.
   - Usar `DATABASE_PATH` temporário nos testes; não tocar em `instance/`.
   - Criar `tests/test_routes.py` que inspeciona `app.url_map` e falha se houver rota com verbo no path (`/cadastra`, `/lista`, `/remove`, `/deleta`, `/exclui`, `/atualiza`, `/edita`), `DELETE`/`PUT`/`PATCH`, ou rota explícita fora da lista esperada. Ignorar `HEAD`/`OPTIONS` automáticos e o catch-all `/<path:path>`.
   - Verificação: os dois testes passam no código atual; a regressão mostra exatamente os 6 conjuntos de baseline.
   - Estimativa: 1–2h.

2. [ ] **Passo 2 — Banco SQLite + seed do catálogo**
   - Criar `sequencias_db.py` com conexão (`DATABASE_PATH`, default `instance/deciframe.db` relativo ao WORKDIR; no container vira `/app/instance/deciframe.db`), `journal_mode=WAL`, `busy_timeout`, `foreign_keys=ON` e `PRAGMA user_version=1`.
   - Criar esquema `sequencias(id, acordes TEXT UNIQUE, criada_em)`, `sequencia_matches(sequencia_id, id_unico_musica, PK composta, FK ON DELETE CASCADE, índice por música)` e `meta(chave, valor)`.
   - Lista canônica = `json.dumps(acordes, ensure_ascii=False, separators=(',', ':'))`; usar para deduplicar e para o `UNIQUE`.
   - Semear as 6 originais na ordem de `main.py:40-45`, de forma idempotente (`INSERT OR IGNORE`); nesta etapa gravar só as linhas do catálogo, sem matches.
   - Criar `tests/test_sequencias_db.py` com banco temporário: esquema criado, seed duas vezes = 6 linhas e mesmos ids, ordem de cadastro, duplicata não cria linha.
   - Verificação: testes novos verdes; regressão e rotas continuam verdes (nenhuma rota nova ainda).
   - Estimativa: 2–3h.

3. [ ] **Passo 3 — Algoritmo de matching validado contra o gabarito**
   - Criar `matching.py` com `normalizar_acordes(entrada)` (aceita string ou lista; separadores `,` e `;`; trim; caixa preservada) e `sequencia_aparece(cifra, acordes)`.
   - Regra: bloco contíguo e ordenado em `musica.cifra` **e** `set(musica.cifra) ⊆ set(acordes)`; comparação exata, sem lowercase/enarmonia/transposição. Usar `cifra`, nunca `acordes` (`list(set(...))` perde ordem).
   - Criar `tests/test_matching.py` com os casos sintéticos da pesquisa (repetição dentro/fora do bloco, caixa, música sem cifra, subconjunto) e com um teste de dados reais que calcula os matches das 6 e compara com `tests/baseline/`.
   - Ampliar o seed para calcular e persistir `sequencia_matches`; gravar `meta.dataset_version` (tamanho + mtime do CSV) e apagar/recalcular matches se a versão mudar.
   - Verificação: 0 divergências contra os 6 baselines; regressão e rotas continuam verdes (a API ainda usa o caminho antigo).
   - Estimativa: 2–3h.

4. [ ] **Passo 4 — API REST do catálogo e busca por id**
   - Em `main.py`: substituir o dict hardcoded pelo catálogo do banco; manter `json.dumps(...)` e o `Content-Type: text/html`.
   - `GET /sequencias`: lista em ordem de cadastro (`id` crescente), com `id`, `acordes`, `criada_em`.
   - `POST /sequencias`: aceita `{"acordes": "Bm,G,D,A"}` ou `{"acordes": [...]}`; mínimo 2 acordes; limite bruto de 1000 caracteres (proteção, não limite de quantidade); `201` + objeto + `Location` na criação; `200` + objeto existente na duplicata (mesma caixa e ordem); `400` + `{"erro": ...}` em entrada inválida.
   - `GET /similares?sequencia_id=<id>`: aceita `generos` e `pagina`; retorna os mesmos campos e a mesma ordem de hoje, `TAM_PAGINA=100`; `404` + `{"erro": ...}` para id inexistente. A busca lê o set de `sequencia_matches` e percorre `apply_filtro(musicas.values(), generos_key)` para preservar a ordem.
   - Parâmetro legado `GET /similares?sequencia=...`: dividir por `,` ou `;`, aparar tokens, buscar a lista canônica no catálogo; se não existir, `[]` com `200`; se existir, usar o mesmo caminho do `sequencia_id`. As 6 continuam funcionando.
   - Cache LRU (`maxsize=256`, chave `(sequencia_id, generos, pagina)`) só se o benchmark indicar necessidade; limpar no rebuild de matches. Se a busca já estiver dentro da meta, registrar a decisão de pular.
   - Criar `tests/test_api_sequencias.py` cobrindo 201/200/400/404, lista ordenada, legado e duplicata; atualizar `tests/test_routes.py` para esperar `POST /sequencias` como única rota de escrita.
   - Verificação: regressão das 6 passa pelo parâmetro legado **e** pelo `sequencia_id`; inventário de rotas verde; nenhum `DELETE`/`PUT`/`PATCH`; benchmark de busca próximo de hoje.
   - Estimativa: 2–3h.

5. [ ] **Passo 5 — Frontend `#/porsequencia`**
   - `static/assets/js/controllers/sequencia.js`: remover as 4 sequências hardcoded; carregar `GET /sequencias`; converter `acordes` para `[{acorde, cor:'#2E1C74'}]`; adicionar campo/botão de cadastro (`POST /sequencias`), mensagens de carregando/erro/sucesso; ao cadastrar, recarregar a lista e selecionar a criada (ou a existente, na duplicata); buscar com `similares?sequencia_id=<id>` mantendo o filtro de gênero.
   - `static/templates/sequencia.html`: adicionar o formulário de cadastro e as mensagens, mantendo o padrão visual e o `df-hex`; garantir que `minhaSequencia.acordes` exista antes do `ng-show`.
   - Verificação manual no browser (`/#/porsequencia`): aparecem as 6; cadastrar nova; duplicata devolve a existente; entrada inválida mostra erro; busca funciona com e sem gênero; as 6 continuam acessíveis; sem erro no console. Regressão e rotas continuam verdes.
   - Estimativa: 2–3h.

6. [ ] **Passo 6 — Testes finais, persistência e rollout local**
   - Rodar a suíte completa: `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`; rodar a regressão também contra o container Docker (gerador em diretório temporário, sem sobrescrever `tests/baseline/`).
   - Ajustar `Dockerfile` para criar `/app/instance` (sem `VOLUME`); atualizar `README.md` com `docker run -v deciframe-data:/app/instance -p 8080:8080 ciframe`; incluir `instance/`, `*.db`, `*.db-wal`, `*.db-shm` em `.gitignore` e `.dockerignore`.
   - Testar persistência: criar sequência, `docker restart` (persiste), `docker rm` e subir de novo com o mesmo volume (persiste); confirmar que sem volume o dado só sobrevive ao restart. Usar volume de teste e remover ao final.
   - Preencher `docs/features/sequencias-customizadas/04-test-report.md` com cobertura, comando e resultado da regressão.
   - Observabilidade: uma linha de log no startup com quantas sequências foram semeadas/recalculadas; sem métricas/alertas novos neste deploy local.
   - Verificação: suíte verde, persistência comprovada, regressão idêntica ao baseline, rotas sem verbos/`DELETE`; README reproduz o comando.
   - Estimativa: 1–2h.

## Revisão após implementação — frontend `#/porsequencia`

**Motivo:** a primeira implementação do Passo 5 entregou catálogo, cadastro e
busca por `id`, mas a revisão de uso apontou que o título do cadastro ficava
solto junto da lista, o destaque acendia acordes iguais em outras sequências, o
formulário era empurrado para baixo pelo catálogo, ajuda/sucesso tinham pouco
contraste no magenta, o sucesso não identificava a sequência e campo/botão não
seguiam o padrão visual. Esta revisão altera apenas o frontend; backend, banco e
API não mudam.

7. [ ] **Revisão após implementação — R1: seção de cadastro colapsável acima do catálogo**
   - Em `static/templates/sequencia.html`, criar uma seção inline colapsável antes
     do catálogo, com o cabeçalho “Cadastre uma sequência” como título e
     acionador; alinhar o campo ao cabeçalho e separar cadastro e lista com um
     divisor. Antes de haver seleção, o painel esquerdo ocupa a largura toda; o
     painel direito só é renderizado depois que uma sequência é escolhida.
   - Em `static/assets/js/controllers/sequencia.js`, adicionar o estado de
     aberto/fechado, abrir com foco no campo e não colapsar automaticamente após
     sucesso, duplicata ou erro; o fechamento é manual.
   - Em `static/assets/css/app.css`, escopar os estilos da seção sem herdar a
     margem de `.viewWindow-panel-container h4:first-child`, preservar o
     espaçamento superior da navbar/logo e ajustar o empilhamento em telas
     estreitas.
   - Verificação: abrir/fechar pelo cabeçalho, cadastrar mantendo a seção aberta,
     confirmar cadastro acima da lista e catálogo longo sem empurrar o formulário.
   - Estimativa: 1h.

8. [ ] **Revisão após implementação — R2: seleção e destaque por sequência**
   - Em `static/assets/js/controllers/sequencia.js`, substituir `temAcorde` por
     uma verificação baseada no `id` da sequência selecionada
     (`isSequenciaSelecionada(sequencia)`), mantendo `minhaSequencia` para a busca.
   - Em `static/templates/sequencia.html`, aplicar `acorde-checked` apenas aos
     hexágonos da sequência selecionada e marcar a linha ativa apenas com fundo
     sutil, sem contorno ou sombra branca; após cadastrar ou detectar duplicata,
     selecionar a sequência retornada pela API.
   - Verificação: clicar em `Bm,G,D,A` e depois em `C,G,Am,F`; apenas os
     hexágonos da segunda devem mudar de cor. Cadastro novo e duplicata devem
     selecionar/destacar a sequência correta.
   - Estimativa: 1h.

9. [ ] **Revisão após implementação — R3: mensagens, contraste e estilo de campo/botão**
   - Em `static/assets/js/controllers/sequencia.js`, montar a mensagem com os
     acordes da sequência criada (“Sequência Bm,G,D,A cadastrada.”) e informar a
     sequência existente na duplicata; manter a área de mensagens dentro da seção.
   - Em `static/assets/css/app.css`, usar texto branco para ajuda/status e uma
     área de sucesso de alto contraste sobre `#372478`; ajustar placeholder, foco
     do campo e a scrollbar do catálogo (trilho escuro translúcido, polegar
     branco); substituir o cinza do `btn-default` pelo tratamento dos controles do
     painel (fundo transparente, borda/texto brancos, inversão no hover).
   - Verificação: conferir contraste no DevTools, foco visível, botão no padrão do
     app, mensagens de sucesso/duplicata/erro legíveis e nomeando a sequência.
   - Estimativa: 1h.

10. [ ] **Revisão após implementação — R4: validação visual e regressão**
    - Testar no browser em desktop e viewport estreito: abrir/fechar a seção,
      cadastrar, duplicar, errar a entrada, buscar com e sem gênero, rolar o
      catálogo e confirmar que só a sequência escolhida é destacada.
    - Testar navegação por teclado (foco no campo, abertura/fechamento) e
      ausência de erros no console.
    - Rodar `node --check static/assets/js/controllers/sequencia.js` e a suíte
      existente; confirmar que não há mudanças em backend, banco ou API.
    - Atualizar `04-test-report.md` com o resultado da validação visual.
    - Estimativa: 1h.

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `tests/test_regression.py` | Novo: regressão das 6 contra `tests/baseline/` (legado e, depois, `sequencia_id`). |
| `tests/test_routes.py` | Novo: inventário de rotas; bloqueia verbos no path e `DELETE`/`PUT`/`PATCH`. |
| `tests/test_sequencias_db.py` | Novo: esquema, seed idempotente, deduplicação. |
| `tests/test_matching.py` | Novo: casos sintéticos + validação das 6 contra o gabarito. |
| `tests/test_api_sequencias.py` | Novo: 201/200/400/404, lista, legado, duplicata. |
| `matching.py` | Novo: normalização, regra contígua + subconjunto, cálculo de matches. |
| `sequencias_db.py` | Novo: SQLite, esquema, seed, CRUD, matches, `dataset_version`. |
| `main.py` | Rotas `/sequencias` (GET/POST), busca por `sequencia_id`, compatibilidade com `sequencia=`, seed/cache. |
| `static/assets/js/controllers/sequencia.js` | Catálogo via API, cadastro, busca por id, seção colapsável e seleção por `id` (revisão). |
| `static/templates/sequencia.html` | Cadastro colapsável acima da lista, mensagens, linha selecionada e catálogo vindo do backend (revisão). |
| `static/assets/css/app.css` | Revisão visual: seção colapsável, contraste, campo/botão e estado selecionado. |
| `docs/features/sequencias-customizadas/frontend.md` | Decisões de layout, fluxo, seleção e contraste da revisão. |
| `Dockerfile` | Criar `/app/instance` (sem `VOLUME`). |
| `README.md` | Comando de execução com volume nomeado. |
| `.gitignore`, `.dockerignore` | Ignorar `instance/` e arquivos do banco. |
| `docs/features/sequencias-customizadas/04-test-report.md` | Preenchido na fase 5. |
| `musica.py` | Sem mudança; só consome `cifra`/`acordes`. |
| `data/top/dataset_final.csv` | Sem mudança; continua sendo a fonte de músicas/gêneros. |

## Riscos e mitigação

- **Quebrar a regressão das 6:** portão de regressão antes/depois de cada passo; comparar conjunto de IDs, não ordem; mapear `seq1..seq6` corretamente; parar no primeiro desvio.
- **Algoritmo restritivo demais para sequências novas:** é o custo de reproduzir a tag; a UI deve mostrar exemplos e mensagens claras; não relaxar a regra sem decisão registrada.
- **Caixa sensível (`7M` ≠ `7m`):** preservar exatamente; não normalizar para minúsculas; testar os casos sintéticos.
- **SQLite com um escritor:** o gunicorn roda com 1 worker hoje; manter WAL + `busy_timeout`; se workers aumentarem, reavaliar.
- **Matches obsoletos após trocar o CSV:** `meta.dataset_version` (tamanho + mtime) dispara reconstrução no startup; restart é necessário para reler o CSV.
- **Persistência depende do volume nomeado:** documentar no README; testar `docker rm`/recriação; ignorar arquivos do banco no git e na imagem.
- **Rotas com verbo ou `DELETE` inesperado:** teste de inventário bloqueia; `POST /sequencias` é a única escrita; sem edição/exclusão.
- **Segurança:** catálogo anônimo por requisito; validar entrada e limitar tamanho bruto; sem rotas de mutação além do `POST`; não versionar o banco.
- **Performance da busca:** matches pré-calculados evitam varrer cifras; medir; só adicionar LRU se necessário.
- **Frontend legado sem build:** testar manualmente no browser; manter AngularJS 1.4.9 e o padrão visual; não modernizar a stack.
- **Observabilidade limitada:** uma linha de log no startup; sem métricas/alertas novos; suficiente para o deploy local.

## Definição de pronto

- [ ] Regressão das 6 passa antes e depois de cada passo, pelo parâmetro legado e por `sequencia_id`, com conjunto de `id_unico_musica` idêntico a `tests/baseline/seq1..seq6.json`.
- [ ] Inventário de rotas verde: só as rotas esperadas; nenhum path com verbo; nenhum `DELETE`/`PUT`/`PATCH`; `POST` apenas em `/sequencias`.
- [ ] Banco SQLite criado, 6 originais semeadas de forma idempotente e matches iguais ao gabarito; `dataset_version` reconstruindo quando o CSV muda.
- [ ] `GET /sequencias`, `POST /sequencias` (201/200/400) e `GET /similares?sequencia_id=` (200/404) funcionando; parâmetro `sequencia=` preservado; respostas em `json.dumps`.
- [ ] Frontend `#/porsequencia` lista as 6 + novas, cadastra em seção colapsável acima da lista, trata duplicata/erro, busca por id e mantém o filtro de gênero.
- [ ] Revisão após implementação: apenas a sequência escolhida é destacada, a mensagem de sucesso nomeia a sequência e campo/botão/ajuda seguem o contraste e o padrão visual do app.
- [ ] Persistência comprovada com volume nomeado após `docker restart` e `docker rm`/recriação; README e ignores atualizados.
- [ ] Suíte completa verde e `04-test-report.md` preenchido com cobertura, comando e resultado da regressão.
- [ ] Nenhuma mudança fora do escopo: músicas/gêneros continuam no CSV, sem login/edição/exclusão, sem dependência nova.
