# Frontend — `#/porsequencia`

## Tela entendida

O painel esquerdo listava 4 sequências hardcoded; ao clicar, o painel direito
mostrava as músicas e permitia filtrar por gênero. Não havia cadastro nem como
ver as outras 2 sequências originais.

## Decisões

- O catálogo passa a vir de `GET /sequencias`; cada item é convertido para o
  formato do `df-hex` (`{acorde, cor: '#2E1C74'}`).
- O cadastro fica na própria página, com campo de texto, botão e mensagens de
  carregando/erro/sucesso. O corpo enviado é `{"acordes": "..."}` para
  `POST /sequencias`.
- Em duplicata, a API responde `200` com a sequência existente; a tela informa
  que ela já estava cadastrada e seleciona a existente.
- A busca usa `GET /similares?sequencia_id=<id>` e mantém o filtro de gênero.
  A paginação continua fora da UI, como antes.
- O padrão visual (AngularJS 1.4.9 + Bootstrap, sem build) foi mantido; o botão
  de cadastro usa as classes existentes (`form-control`, `btn btn-default`).
- As mensagens de erro da API (`{"erro": "..."}`) são exibidas ao usuário.

## Arquivos

- `static/assets/js/controllers/sequencia.js`: remove as 4 sequências
  hardcoded, carrega o catálogo, cadastra e busca por `id`.
- `static/templates/sequencia.html`: formulário de cadastro e mensagens.
