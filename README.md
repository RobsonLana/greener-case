# greener-case
Repositório para realizar o case do processo seletivo da Greener

## Crawlers

Os dois crawlers do case são, respectivamente solplace e aldo.

### Crawler Solplace

O Crawler destinado à página da [Solplace][1] é responsável por coletar as informações dos produtos através do web scraping no DOM disponível no front-end.

Seu arquivo de Spider se encontra em `./scrapy/crawlers/spiders/solplace.py`

#### Seletores CSS

O principal seletor CSS do crawler aponta para o elemento que contém todas as informações requisitadas (Preço, porte, estrutura) separadas pelo nome e preço do item:

```css
#products_grid > div > table > tbody > tr > td > div > form > div.card-body.rounded-bottom.p-0.o_wsale_product_information > div.p-2.o_wsale_product_information_text
```

Observe que em `#products_grid > div > table > tbody > tr` é necessário que o elemento `tr` seja selecionado sem índice, permitindo que todos os items da página atual sejam selecionados em lista.

Os demais seletores usam o seletor acima como base para especificar a busca do nome e preço.

#### Regular Expression

Para extrair do nome o porte e estrutura, o seguinte Regex é utilizado:

```regex
kit (\w*\s)?((\d|,|\.)+(?=\s?kwp)).* -\s+(\S*)
```

A expressão busca pelos seguintes blocos:

- a sequência `kit ` no começo da linha

- `(\w*\s)?` - grupo 1: uma palavra de tamanho qualquer seguida de um espaço, denotados pelo token `?`, indicando que esse Pattern pode ocorrer uma ou zero vezes.

- `((\d|,|\.)+(?=\s?kwp))` - grupo 2: Grupo que captura o porte do produto, visando extrair textos no formato de exemplo: `123,45`.

  - `(\d|,|\.)+` - grupo 3: Utilizado pra detectar qualquer digito, virgula ou ponto que ocorra pelo menos uma vez (pela denotação do token `+`).

  - `(?=\s?kwp)` - Positive Lookahead: Lookahead positivo para o padrão de uma sequência `kwp` que pode ser precedida ou não por um espaço vazio. Esse bloco utiliza essa detecção sem incluir o trecho no grupo 3, separando o número da unidade 'kWp'.

- `.* -\s+` - bloco do grupo 0 (raiz): Uma sequência de zero ou muitos caracteres quaisquer (para capturar 'kWp' após o bloco acima) seguida de ` -` que precede um ou mais espaços vazios, descrito dessa forma para ser compatível com alguns casos como `...-  Fibrometal` ou `...-   Metalico`.

- `(\S*)` - grupo 4: Grupo que separa a estrutura do produto, procurando por qualquer digito que não seja da categoria espaço (`\r, \s, \t`) de tamanho zero ou maior, descrito dessa forma para não conflitar com o bloco acima, que possui detecção de tamnho variado.

A utilização de grupos pode ser observada em linhas como: `portage = matches.group(2)` por exemplo.

O segundo Regex utilizado nesse Crawler (também no segundo Crawler) é responsável pela sanitização de números oriundos de texto que não esteja no formato númerico para computadores:

```regex
(\D(?!(\d+)(?!.*(,|\.)\d+)))
```

A expressão busca todos os caracteres que não são digitos, com exceção do único caracter que pode ser interpretado como floating point de um valor.

- `(\D(?!(\d+)(?!.*(,|\.)\d+)))` - Grupo 0
  - `\D` - Bloco do grupo 0: Busca por caracteres fora do grupo de digitos.
  - `(?!(\d+)(?!.*(,|\.)\d+))` - Negative Lookahead: Lookahead para desconsiderar qualquer caracter não-digito que precede a descrita sequência.
    - `(\d+)` - Grupo 1: Pelo menos 1 digito que não precede a sequência descrita no Negative Lookahead a seguir.
    - `(?!.*(,|\.)\d+)` - Negative Lookahead: Lookahead que desconsidera qualquer digito que segue uma sequência de quaisquer caracteres que precedem pelo menos uma vírgula ou ponto, e esse mesmo caracter (vírgula ou ponto) precede pelo menos um dígito.
      - `(,|\.)` - Grupo interno do Negative Lookahead: Seleciona uma vírgula ou um ponto.

O objetivo dessa expressão é buscar e limpar qualquer dígito que não possa ser utilizado para preservar o valor original de um número; a mesma deve ser utilizada em conjunto com uma substituição simples de `,` para `.` e certificar que o caracter resultante seja o correto para conversão de string para número.

Exemplos:

- `12.345,67` > `12345.67`
- `1.234.567,89` > `1234567.89`
- `12.14.15,236,645,` > `121415236.645`
- `...,,,232124.,123.,.` > `232124.123`

Repare que a expressão também limpa caracteres que estão no fim da linha, pois os mesmos não podem representar um floating point no número. A expressão foi desenvolvida primariamente para casos como os dois primeiros exemplos.

### Crawler Aldo

O segundo Crawler consome informações da API [Aldo][2], onde é necessário primeiro gerar um id de filtro pela rota `/getfiltrosporsegmento` e então paginar a lista pela rota `/getprodutosporsegmentonotlogin`.

Seu arquivo de Spider se encontra em `./scrapy/crawlers/spiders/aldo.py`

#### Regular Expression

De forma similar ao Crawler Solplace, um Regex é utilizado para extrair o porte do produto disponível na descrição / nome:

```regex
\w*\s+(([0-9]|,|\.)+(?=kwp))
```

- `\w*\s+` - grupo 0: Procura no início da linha uma palavra de tamanho variado seguida de pelo menos um espaço.

- `(([0-9]|,|\.)+(?=kwp))` - grupo 1: Grupo que captura o porte do produto, em formato similar ao do Solplace.

  - `([0-9]|,|\.)+` - grupo 2: Grupo utilizado para detectar qualquer digito, virgula ou ponto que ocorra pelo menos uma vez.

  - `(?=\s?kwp))` - Positive Lookahead: Lookahead que busca pela sequência `kwp` precedida de um ou nenhum espaço.

#### Desafios desse scraping

Inicialmente, comunicar com a API foi simples, entretanto, ao decorrer do dia 27/08 (Domingo), todas as tentativas de extrair dados pelo Crawler resultavam em Gateway Timeout (504) ou Forbbiden (403).

No primeiro caso, a forma como o código do crawler foi escrito fazia com que muitos requests fossem enfileirados para execução, o que sobrecarregava tanto a máquina host quanto o servidor em si.

Quanto a proibição de acesso, a hipótese mais provavel deve se dar pelo exceço de requests gerados pelos Bots, causando o bloqueio por parte do Cloudflare.

### Desafios gerais dos crawlers

#### Containers internos

Inicialmente, o plano seria utilizar imagens customizadas de containers para rodar os crawlers através do Docker Operator no Airflow, entretanto, para poder utilizar uma imagem customizada local, seria necessário um servidor de Registry habilitado para receber chamadas HTTPS, uma vez que Airflow se conecta apenas por HTTPS em vez de HTTP, que permitira a utilização de um container local para compartilar as imagens disponíveis no host.

Juntamente a este requirimento técnico, também foi optado por não utilizar containers para execução no Airflow para evitar configurações detalhadas de Netowrk entre os containers que estariam hosteados pelo container do Airflow. Nessa situação, os crawlers não teriam acesso ao container do MySQL para gravarem os dados.

Uma possibilidade para essa solução, seria passar os dados coletados para o Airflow e ligar as tasks dos crawlers para uma outra task que teria acesso ao MySQL.

#### Proxies para os Crawlers

Para mitigar os possíveis bloqueios anti-BOTs que as páginas poderiam utilizar contra os crawlers, a implementação de proxy através de Middlewares do Scrapy foi testada, entretando nenhuma Proxy Pool ou qualquer servidor Proxy conseguiu estabelecer um tunel para prosseguir com a tarefa.

[1]: https://www.solplace.com.br/shop
[2]: https://www.aldo.com.br/wcf/Produto.svc
