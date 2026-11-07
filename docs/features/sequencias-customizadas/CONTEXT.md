# Contexto da atividade

Feature: cadastrar sequências de acordes e buscar músicas por elas, com o catálogo
de sequências persistido em banco. Enunciado em
docs/features/sequencias-customizadas/00-enunciado.md. A pesquisa já está pronta em
01-research.md. O que importa é a qualidade do processo, não só o resultado.

## Regras de trabalho

- Trabalhe só no que a etapa atual pede. Não altere código fora do escopo sem me
  perguntar antes.
- Quando houver alternativas, apresente-as com prós e contras e espere minha decisão.
- Se precisar se desviar do plano ou da proposta, pare e me avise antes.
- Ao final de cada etapa, liste: arquivos alterados, por quê, e o que ficou diferente
  do planejado.

## Fonte de verdade

- As 6 sequências originais (main.py:40-45) precisam produzir as mesmas músicas de
  hoje. O gabarito está em tests/baseline/ (gerado por gerar_baseline.py; compara o
  conjunto de IDs, não a ordem). Nenhuma mudança pode alterar esse resultado sem
  decisão minha registrada.
- Se o resultado não me agradar, corrigimos primeiro o documento da fase (proposta
  ou plano) e depois o código.

## Armadilhas de domínio

- 7M (sétima maior) ≠ 7m (sétima menor). Não colapsar sem verificar a regressão.
- Separadores: a API usa vírgula; o CSV usa ponto e vírgula.
- Enarmonia e transposição estão fora do escopo.

## Requisitos não funcionais

- Segurança: sem login. Sem rota de exclusão/edição pública; limites mínimos de
  tamanho e quantidade de acordes.
- REST: recursos como substantivos, ação pelo verbo HTTP (ex.: GET /sequencias,
  POST /sequencias). Nada de /cadastra, /lista, /remove.
- Endpoints retornam json.dumps(...) como string, não jsonify.
- Desempenho: busca em poucas centenas de ms. Evitar varrer todas as músicas a cada
  busca (pré-cálculo, cache, duplicata retorna a existente).
- Container Docker único e local-only (ADR 0001). Músicas e gêneros continuam vindo
  do CSV; só o catálogo de sequências vai para o banco.

## Frontend

- Mudanças de frontend em sessão separada: entender a tela, propor opções, esperar
  minha escolha, manter o padrão visual e registrar as decisões em frontend.md.
