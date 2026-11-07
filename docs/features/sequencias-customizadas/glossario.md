# Glossário — Sequências de Acordes Customizadas

Termos usados nesta feature e no domínio musical do deciframe. A intenção é
fixar o vocabulário antes da pesquisa e da proposta, evitando que a mesma
palavra signifique coisas diferentes em cada fase.

> Convenções já alinhadas para esta feature:
>
> - **Sequência** = lista ordenada de acordes.
> - **Match** = a sequência aparece como **bloco contínuo e ordenado** dentro da
>   música (sem acordes estranhos no meio).
> - A comparação de acordes é **sensível a caixa** e à grafia; o único ajuste
>   automático é aparar espaços nas pontas de cada acorde.
> - As 6 sequências originais são o critério de regressão: precisam continuar
>   produzindo os mesmos resultados de busca de hoje.

## Termos musicais

### Acorde

Conjunto de notas tocadas simultaneamente. Na cifra, é representado por um
símbolo compacto (por exemplo, `C`, `Am`, `G7`, `F#m7(b5)`). Nesta feature, o
símbolo do acorde é a unidade que compõe uma sequência.

### Tríade

Acorde básico de três notas: fundamental, terça e quinta. A qualidade da terça
define se a tríade é maior ou menor; a qualidade da quinta define se é justa,
diminuta ou aumentada.

### Fundamental

Nota que dá nome ao acorde e a partir da qual os intervalos são medidos. Em
`C7M`, a fundamental é dó; em `Am`, é lá. Não confundir com a nota mais grave
que está sendo tocada (ver **baixo invertido**).

### Cifra

Forma textual de representar a harmonia de uma música por meio de símbolos de
acorde, geralmente alinhados à letra. Uma cifra pode conter acordes, indicações
de seção, repetições e, às vezes, tablatura ou melodia.

### CifraClub

Site de cifras usado como origem dos dados do deciframe. Nesta feature, aparece
apenas como contexto histórico do catálogo de músicas; o catálogo de sequências
é novo e independente.

### Harmonia

Relação entre acordes ao longo de uma música. É o que uma progressão descreve.

### Melodia

Sequência de notas cantadas ou tocadas, geralmente a parte mais reconhecível da
música. Não é o foco desta feature, que trabalha com acordes.

### Progressão / sequência de acordes

Lista ordenada de acordes tocados um após o outro. Neste projeto, "sequência" é
sinônimo de progressão quando o contexto for musical. Uma progressão pode se
repetir várias vezes dentro da mesma música.

### Acorde maior

Tríade com terça maior. Pode ser escrito só pela fundamental (`C`) ou com
sufixos como `M`, `maj` (`CM`, `Cmaj`). Em `7M`, o `M` maiúsculo indica que a
sétima é maior.

### Acorde menor

Tríade com terça menor, indicada pelo sufixo `m` minúsculo (`Cm`, `Am`). A caixa
importa: `m` é menor; `M` costuma indicar maior, sobretudo em `7M`.

### Sétima

Intervalo de sétima adicionado ao acorde. É a principal fonte de ambiguidade na
notação de cifras, porque `7`, `7M` e `7m` não são a mesma coisa.

| Símbolo | Nome | Notas em dó | Observação |
|---|---|---|---|
| `C` | dó maior | C E G | tríade maior |
| `Cm` | dó menor | C E♭ G | tríade menor |
| `C7` | dó com sétima (dominante) | C E G B♭ | tríade maior + sétima menor |
| `C7M` | dó com sétima maior | C E G B | tríade maior + sétima maior |
| `Cm7` | dó menor com sétima | C E♭ G B♭ | tríade menor + sétima menor |
| `Cm7M` | dó menor com sétima maior | C E♭ G B | tríade menor + sétima maior |
| `Cdim` / `C°` | dó diminuto | C E♭ G♭ | tríade diminuta |
| `Caug` / `C+` | dó aumentado | C E G# | tríade aumentada |
| `Csus4` | dó suspenso na quarta | C F G | sem terça |
| `Cadd9` | dó com nona adicionada | C E G D | nona sem sétima |
| `C/G` | dó com sol no baixo | G C E G | baixo invertido |

### 7M

Sétima **maior**. Exemplo: `C7M` = dó, mi, sol, si. Grafias equivalentes comuns
na prática: `Cmaj7`, `CM7`, `C7+`. Para esta feature, a comparação é por string
exata; portanto, `C7M` e `Cmaj7` são acordes diferentes até que a pesquisa
mostre necessidade de normalização.

### 7m

Sétima **menor**. O sufixo `7m` indica o intervalo de sétima menor acima da
fundamental. Na notação mais comum, a tríade menor com sétima menor é escrita
`Cm7` (não `C7m`). `C7m` é uma grafia não padronizada e potencialmente ambígua:
pode ser lida como `C7` (tríade maior + sétima menor) ou como `Cm7` (tríade
menor + sétima menor). A feature deve tratar o texto literal; a interpretação
musical fica documentada aqui para evitar confusão.

### Extensões e alterações

Sufixos que modificam o acorde além da tríade: `9`, `11`, `13` (nonas, décimas
primeiras e décimas terceiras), `add` (nota adicionada sem sétima), `sus`
(terça substituída por segunda ou quarta), `dim`/`°` (diminuto), `aug`/`+`
(aumentado), `#` (sustenido) e `b` (bemol). Nesta feature, fazem parte do texto
do acorde e não são descartados automaticamente.

### Baixo invertido / slash chord

Acorde cuja nota mais grave não é a fundamental, escrito com barra: `C/G`
significa um acorde de dó maior com sol no baixo. Como a barra também pode ser
usada como separador na entrada do usuário, esse é um ponto a investigar antes
de fechar o parser.

### Tom / tonalidade

Centro tonal de uma música. Duas músicas em tons diferentes podem tocar a mesma
progressão relativa (ver **transposição**).

### Transposição

Deslocamento de todos os acordes de uma progressão pelo mesmo intervalo. Por
exemplo, `C - G - Am - F` transposta dois semitons acima vira
`D - A - Bm - G`. A feature ainda **não decidiu** se o match deve ser sensível
ao tom ou invariante por transposição; isso é item de pesquisa.

### Enarmonia

Nomes diferentes para a mesma altura. Por exemplo, `C#` e `Db` soam iguais na
afinação temperada. Com a regra atual de string exata, são acordes diferentes;
a pesquisa deve medir o impacto disso.

### Intervalo

Distância entre duas notas, medida em semitons ou em graus. É a base para
comparar progressões de forma transposta.

### Grau

Posição de um acorde dentro de uma tonalidade, geralmente escrito em algarismos
romanos (`I`, `ii`, `V7`). Ajuda a descrever a mesma progressão em tons
diferentes.

### Compasso

Unidade rítmica da música, delimitada por tempos fortes. Nesta feature, ainda
não se sabe se o dataset traz informação suficiente para considerar compassos
no match; a decisão depende da pesquisa.

### Seções da música

Partes como introdução, verso, refrão, ponte e solo. A semântica alinhada é que
a sequência pode aparecer em **qualquer ponto** da música, inclusive atravessando
a fronteira entre seções.

### Sequência famosa

Rótulo histórico do deciframe para progressões pré-cadastradas. Hoje são 6 no
backend (tag `SEQ_FAMOSA`) e 4 no frontend (hardcoded em JavaScript). Depois da
feature, "sequência famosa" deixa de ser um conjunto fixo e passa a designar
qualquer entrada do catálogo, seja original ou cadastrada por visitante.

## Termos da feature e do sistema

### Catálogo

Conjunto persistido de sequências disponíveis para busca. Nesta feature, o
catálogo inclui as 6 sequências originais e as novas cadastradas por qualquer
visitante. É aberto e anônimo: não há login nem curadoria.

### Sequência original

Uma das 6 progressões hoje hardcoded em `main.py`. Elas viram entradas normais
do catálogo persistido e continuam sendo o critério de regressão.

### Sequência cadastrada

Sequência criada por um visitante pela interface. Tem apenas a lista ordenada de
acordes, sem nome próprio, descrição ou autor.

### Match

Relação entre uma sequência e uma música: dizemos que há match quando a
sequência aparece como bloco contínuo e ordenado na música. Um match não exige
que a sequência ocupe a música inteira nem que esteja em uma seção específica.

### Bloco contínuo e ordenado

Semântica escolhida para o match: os acordes da sequência precisam aparecer na
mesma ordem e sem acordes estranhos no meio. Exemplo: `[C, G, Am]` casa com
`[C, G, Am, F]`, mas não casa com `[C, Dm, G, Am]`.

### Subsequência

Sequência contida dentro de outra, mantendo a ordem. O match desta feature é a
busca por uma subsequência contígua dentro da lista de acordes da música.

### Normalização

Redução de variações de escrita a uma forma canônica antes da comparação. Nesta
feature, a única normalização alinhada até agora é aparar espaços nas pontas de
cada acorde; caixa, acentos, enarmonia, extensões e baixo invertido permanecem
significativos.

### Token

Cada acorde individual obtido depois de dividir o texto digitado pelo usuário.
Por exemplo, a entrada `C - G - Am - F` gera os tokens `C`, `G`, `Am`, `F`.

### Parser

Componente que transforma o texto livre digitado pelo visitante em uma lista de
tokens de acorde. A lista exata de separadores ainda será definida com base nos
acordes reais do dataset.

### Duplicata

Sequência cuja lista ordenada de acordes é igual à de uma entrada já existente.
A regra alinhada é devolver a entrada existente como sucesso, sem criar outra.

### Seed

Dados iniciais inseridos no banco na primeira inicialização. Nesta feature, as 6
sequências originais serão semeadas como entradas normais do catálogo.

### Persistência

Capacidade de o catálogo sobreviver a reinícios do servidor/container. É o motivo
de introduzir um banco de dados; as músicas e os gêneros continuam vindo do CSV
em memória.

### Banco embarcado

Banco de dados que roda dentro do próprio container, sem serviço externo. É a
categoria de solução compatível com o deploy local-only documentado em
`docs/adr/0001-local-only-docker-deploy.md`. A escolha concreta fica para a
proposta.

### SEQ_FAMOSA

Tag pré-computada no CSV que hoje indica quais músicas contêm quais sequências
famosas. É a fonte atual dos resultados das 6 sequências e o ponto de partida da
investigação sobre como o match era calculado.

### Dataset

Arquivo `data/top/dataset_final.csv`, carregado em memória no startup. Contém as
músicas, gêneros, cifras/acordes e a tag `SEQ_FAMOSA`. Nesta feature, ele não é
migrado para o banco.

### Baseline

Conjunto de resultados atuais capturado para comparação. Serve para provar que as
6 sequências originais continuam retornando as mesmas músicas depois da mudança.

### Regressão

Verificação de que o comportamento existente não piorou. Nesta feature, o teste
de regressão obrigatório é: as 6 sequências originais devem produzir os mesmos
resultados de busca de hoje.

### Endpoint

Rota HTTP da API Flask. Os endpoints existentes continuam retornando
`json.dumps(...)` como string, não `jsonify`; isso é comportamento legado
intencional e não deve ser "corrigido" sem tratar como mudança de API.

### Frontend / Backend

- **Backend**: aplicação Flask em `main.py`, que carrega o CSV e expõe a API.
- **Frontend**: aplicação AngularJS estática em `static/`, sem build step, que
  consome a API e renderiza as páginas, incluindo `#/porsequencia`.
