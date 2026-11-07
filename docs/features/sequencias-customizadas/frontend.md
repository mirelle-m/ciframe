# Frontend — `#/porsequencia`

## Tela entendida

O painel esquerdo listava 4 sequências hardcoded; ao clicar, o painel direito
mostrava as músicas e permitia filtrar por gênero. Não havia cadastro nem como
ver as outras 2 sequências originais.

A primeira implementação passou a carregar o catálogo real, cadastrar e buscar
por `id`, mas a revisão de uso encontrou os problemas abaixo:

- o título “Cadastre uma sequência” ficava no mesmo fluxo da última linha de
  hexágonos, sem separação visual;
- o destaque era calculado por nome de acorde (`temAcorde`), então acordes
  iguais em outras sequências também mudavam de cor;
- o formulário ficava abaixo da lista e era empurrado para baixo conforme o
  catálogo crescia;
- ajuda e mensagem de sucesso herdavam cores escuras do Bootstrap sobre o
  magenta, com pouco contraste;
- o sucesso não dizia qual sequência foi cadastrada e não havia estado visual
  de linha selecionada;
- campo e botão não seguiam o padrão dos demais painéis do app.

## Decisões

### Layout e fluxo

- O painel esquerdo mantém o título da página e passa a ter o cadastro **acima**
  do catálogo, separado da lista por um divisor.
- O cadastro é uma **seção colapsável inline**, não um modal. O cabeçalho
  “Cadastre uma sequência” funciona como título da seção e como acionador do
  abrir/fechar; o campo fica alinhado a esse cabeçalho quando expandido.
- A seção começa fechada e só é aberta/fechada por ação do usuário. Após
  sucesso, duplicata ou erro, ela **não** colapsa sozinha; o usuário fecha
  manualmente.
- Ao abrir, o foco vai para o campo de texto. O formulário tem campo, botão,
  texto de ajuda e área de mensagens na mesma seção.
- O catálogo fica abaixo do divisor, com título próprio e lista rolável dentro
  do painel. O crescimento da lista não empurra o cadastro para baixo.
- Antes de qualquer seleção, o painel esquerdo ocupa toda a largura e o painel
  direito não é renderizado; a divisão em duas metades só acontece depois que
  uma sequência é selecionada.
- O espaçamento superior do painel respeita a navbar/logo, sem sobrepor o
  título da página.
- Em telas estreitas, campo e botão podem empilhar; o painel continua rolando
  sem esconder o cadastro.

### Seleção e feedback

- A seleção passa a ser por `id` da sequência, não por nome de acorde. Apenas os
  hexágonos da sequência selecionada recebem `acorde-checked`; acordes iguais em
  outras sequências permanecem com a cor normal.
- A linha selecionada ganha apenas um fundo sutil, além dos hexágonos brancos;
  não usa contorno ou sombra branca por cima da sequência.
- Ao cadastrar, a mensagem de sucesso fica **dentro da seção de cadastro** e
  nomeia a sequência, por exemplo: “Sequência Bm,G,D,A cadastrada.” A sequência
  criada é recarregada, selecionada e destacada na lista.
- Em duplicata, a mensagem informa que a sequência já existia e nomeia a
  sequência; a existente é selecionada. O campo é limpo após o sucesso.
- Erros de validação/API continuam dentro da seção, com texto legível e sem
  perder o conteúdo digitado.

### Aparência e contraste

- Textos de ajuda, status e mensagens usam branco sobre o magenta do painel,
  seguindo os textos existentes. A mensagem de sucesso usa texto branco sobre o
  roxo escuro `#372478` (mesma família do painel A), com contraste ≈12:1.
- O campo usa o `form-control` existente, com borda branca; o placeholder e o
  foco são ajustados para ficarem visíveis no fundo magenta.
- O botão de cadastro deixa de usar o cinza padrão do `btn-default`: usa o
  tratamento dos controles do painel (fundo transparente, borda/texto brancos e
  inversão para branco/magenta no hover), sem introduzir uma nova linguagem
  visual.
- O título da seção não deve herdar a margem grande de
  `.viewWindow-panel-container h4:first-child`; o espaçamento é escopado para a
  seção de cadastro.
- A scrollbar do catálogo acompanha o fundo magenta, com trilho escuro
  translúcido e polegar branco, em vez do trilho branco padrão do navegador.

## Arquivos

- `static/templates/sequencia.html`: seção colapsável de cadastro acima do
  catálogo, cabeçalho, divisor, estado selecionado da linha e mensagens.
- `static/assets/js/controllers/sequencia.js`: estado de abertura/fechamento da
  seção, seleção por `id`, mensagens com a sequência, foco e recarga do catálogo.
- `static/assets/css/app.css`: estilos escopados para a seção colapsável,
  contraste, botão, placeholder e linha selecionada.
- `static/templates/directives/df-hex.html`: sem mudança; continua recebendo
  `acorde-checked` apenas quando a sequência está selecionada.

## Fora de escopo

- Backend, banco, API, contratos de `/sequencias` e `/similares`.
- Edição/exclusão de sequências, login ou paginação.
- Modernização do AngularJS/Bootstrap ou introdução de build step.

## Validação

- Manual no browser: abrir/fechar a seção, cadastrar sequência nova, duplicata e
  entrada inválida; confirmar mensagem com o nome da sequência, seleção e
  destaque apenas na sequência escolhida.
- Rolar um catálogo longo e confirmar que o cadastro permanece acima da lista.
- Testar viewport estreito e navegação por teclado (foco no campo, abertura e
  fechamento da seção).
- Conferir contraste no DevTools e ausência de erros no console.
- `node --check static/assets/js/controllers/sequencia.js`; rodar a suíte
  existente para garantir que nenhum contrato de backend foi alterado.

## Revisão após implementação

Motivo: a implementação inicial priorizou a integração com a API e entregou o
fluxo funcional, mas a revisão visual e de uso mostrou que o cadastro, o
destaque e o contraste não seguiam o padrão do app nem o fluxo esperado. Esta
revisão corrige apenas o frontend de `#/porsequencia`; backend, banco e API não
mudam. Os passos estão detalhados em `03-plan.md` na seção “Revisão após
implementação”.
