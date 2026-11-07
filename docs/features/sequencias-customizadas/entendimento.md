# Entendimento — Sequências de Acordes Customizadas

Registro curto do que foi alinhado nesta sessão, antes da pesquisa. O glossário
completo está em [`glossario.md`](glossario.md).

## Orientações principais

- **A regressão das 6 prevalece.** As 6 sequências originais precisam continuar
  produzindo os mesmos resultados de busca de hoje. Isso não é decisão nossa.
- **Não decidir o algoritmo agora.** Antes, investigar nos dados reais como a
  `SEQ_FAMOSA` foi calculada e quanto a definição contígua/exata diverge dela,
  registrando a evidência na pesquisa. A escolha do algoritmo fica para a
  proposta.
- **Investigar as 4 sequências do JS vs as 6 do backend antes de decidir.** Listar
  as 4 e as 6, verificar se há sobreposição e o que acontece hoje quando o
  usuário clica numa sequência que o backend não conhece. A decisão do que fazer
  com elas fica para a proposta.

## Decisões já dadas

- **Match:** a sequência aparece como bloco contínuo e ordenado, em qualquer
  ponto da música.
- **Identidade do acorde:** string exata; o único ajuste automático é aparar
  espaços nas pontas de cada acorde. Caixa importa.
- **Entrada:** texto livre com separadores.
- **Metadados:** a sequência tem só a lista de acordes, sem nome, descrição ou
  autor.
- **Validação:** mínimo de 2 acordes; sem limite máximo.
- **Duplicata:** devolver a sequência já existente como sucesso, sem criar outra.
- **Escopo do catálogo:** só cadastrar e consultar; sem edição ou exclusão.
- **Originais no catálogo:** as 6 viram entradas normais do catálogo persistido.
- **Frontend:** a página `#/porsequencia` deve mostrar as 6 originais + as novas,
  em ordem de cadastro.
- **Busca:** decidir na proposta se é por item do catálogo ou por texto livre
  avulso.

## Termos de domínio discutidos

- **Acorde**, **cifra**, **sequência/progressão**, **bloco contínuo**, **match**.
- **7M** = sétima maior; **7m** = sétima menor; **m** = menor; **M** = maior. A
  caixa é significativa.
- **Baixo invertido** (`C/G`), **extensões** (`9`, `11`, `13`, `add`, `sus`),
  **diminuto/aumentado**, **enarmonia** (`C#`/`Db`), **transposição**, **tom**,
  **grau**, **compasso**.
- **`SEQ_FAMOSA`**: tag pré-computada no CSV.
- **`musica.acordes`**: conjunto sem ordem; **`musica.cifra`**: lista ordenada.

## Dúvidas em aberto

- Como a `SEQ_FAMOSA` foi calculada e quanto o match contínuo/exato diverge dela.
- As 4 do JS vs as 6 do backend: sobreposição e comportamento ao clicar numa
  sequência desconhecida.
- Repetições: na música e dentro da própria sequência (colapsar, quebrar ou
  exigir literalmente).
- Separadores: quais aceitar sem impedir acordes como `C/G` e `C-7`.
- Transposição: o match deve ser sensível ao tom? Investigar o comportamento
  atual.
- Fonte da ordem: `musica.acordes` vs `musica.cifra` — usar a que preservar
  melhor ordem e repetições.
- Métrica/compasso: existe informação suficiente no dataset?
- Ordenação e limite dos resultados para sequências novas: investigar e replicar
  o comportamento atual.
- Busca por catálogo ou texto livre, fluxo pós-cadastro, rótulo na lista,
  sequências sem match e proteção contra abuso: decidir na proposta.

## Fatos verificados no código

- As 6 sequências estão em `main.py:40-45`; a tag `SEQ_FAMOSA` é lida em
  `main.py:33,63` e usada em `main.py:209`.
- As 4 do JS estão em `static/assets/js/controllers/sequencia.js:2-31` e são
  Bm-G-D-A, C-G-Am-F, Gm-F e C-C7-F-Fm — um subconjunto das 6, sem Em-G e
  C-A7-Dm-G7.
- Sequência desconhecida em `/similares?sequencia=` retorna `[]`
  (`main.py:190-197`).
- `musica.acordes` é `list(set(cifra))` (`musica.py:17`), então não preserva
  ordem nem repetição; `musica.cifra` preserva (`musica.py:16`).
