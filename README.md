# Validador de Inscrição Estadual (IE) — Brasil

[![Licença: MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Sem dependências](https://img.shields.io/badge/depend%C3%AAncias-nenhuma-success.svg)](#)
[![Cobertura](https://img.shields.io/badge/UFs-27%20(26%20estados%20%2B%20DF)-orange.svg)](#ufs-suportadas)

**Validador de Inscrição Estadual para os 26 estados + Distrito Federal**, escrito em Python puro (sem dependências externas), acompanhado das **regras oficiais de cada estado** em formato legível.

O projeto tem duas partes:

1. **Regras documentadas** ([`regras/`](regras/)) — um arquivo `.txt` por estado, em formato padronizado, descrevendo o formato da IE, o cálculo do dígito verificador e um exemplo.
2. **Validador** ([`validador_ie.py`](validador_ie.py)) — implementa o cálculo do dígito verificador de cada estado a partir dessas regras e diz se um número de IE é válido.

---

## De onde vêm as regras

Todas as regras foram obtidas da fonte oficial do **Sintegra** (Sistema Integrado de Informações sobre Operações Interestaduais com Mercadorias e Serviços), que mantém um "Roteiro de Crítica da Inscrição Estadual" por estado:

> http://www.sintegra.gov.br/insc_est.html
> (cada estado em `Cad_Estados/cad_XX.html`)

Os roteiros originais têm formatação irregular e, em alguns estados, exemplos confusos. Por isso, o conteúdo foi **reorganizado em um formato padronizado e legível** — cada arquivo em [`regras/`](regras/) segue a mesma estrutura de seções: **FORMATO**, **CÁLCULO DO DÍGITO VERIFICADOR**, **EXEMPLO** e **OBSERVAÇÕES**. Os arquivos são nomeados pelo estado (minúsculo, sem acento — ex.: `sao_paulo.txt`).

**Dois casos especiais:** os roteiros do **Distrito Federal** e do **Rio de Janeiro** não estavam em texto na página oficial — o conteúdo vinha em **imagens** (`df1t.gif`, `df2t.gif`, `rj.gif`). Essas imagens foram lidas e o conteúdo transcrito. As imagens originais ficaram preservadas em [`regras/imagens/`](regras/imagens/) para conferência.

> ✅ Cada algoritmo do validador foi conferido contra o **exemplo numérico de cada regra** — os exemplos documentados em `regras/` são exatamente os usados nos auto-testes.

---

## As regras ainda são válidas? (atualizado em junho de 2026)

**Sim.** Os algoritmos de dígito verificador da Inscrição Estadual são estáveis e seguem em uso — diversas Secretarias de Fazenda ainda publicam oficialmente o "Cálculo do DV" (por exemplo, a [Sefaz-BA](https://www.sefaz.ba.gov.br/inspetoria-eletronica/icms/cadastro/calculo-dv/)).

O **Sintegra não foi descontinuado**: o portal nacional ([sintegra.gov.br](http://www.sintegra.gov.br/)) continua no ar, mas a **consulta pública de cada estado hoje é feita pelo portal da respectiva SEFAZ** (ex.: Sintegra/PR, Sintegra/PB, Sefaz-GO, Sefaz-MA, etc.). Para consultar uma IE específica, prefira o portal da SEFAZ do estado.

> ⚠️ **Validação estrutural ≠ situação cadastral.** Este projeto confere apenas o **formato e o dígito verificador** do número. Uma IE estruturalmente válida pode estar **baixada, suspensa, inapta, nula** ou nunca ter existido. Para saber a situação real (Ativa/Suspensa/Baixada/Inapta/Nula), é preciso consultar o portal da SEFAZ.

**De olho na Reforma Tributária:** a transição para IBS/CBS (LC 214/2025) cria um cadastro unificado de contribuintes e, a partir de **julho de 2026**, um **CNPJ alfanumérico** (cujo dígito verificador continua sendo calculado por módulo 11, usando o valor dos caracteres). Durante a transição (2026–2033), as Inscrições Estaduais continuam em uso e as regras deste repositório permanecem aplicáveis — mas vale acompanhar as SEFAZ e o Comitê Gestor do IBS, pois mudanças futuras podem exigir atualização.

---

## Estrutura do projeto

```
.
├── README.md
├── validador_ie.py            # validador por estado + CLI + auto-testes
├── regras/
│   ├── acre.txt ... tocantins.txt   # 27 regras padronizadas (26 estados + DF)
│   └── imagens/               # GIFs originais de DF e RJ (fonte das transcrições)
└── dados/                     # dados de teste / validação em lote
    ├── ies_exemplo.csv        # exemplo de lista de IEs (entrada)
    └── resultado_validacao.csv # saída da validação em lote
```

---

## Uso do validador

Não há dependências — basta Python 3.8+.

### Como biblioteca

```python
from validador_ie import validar, validar_todos

validar("SP", "110.042.490.114")   # True
validar("RS", "224/3658792")       # True
validar("MG", "062.307.904/0080")  # False

# Quando não se sabe o estado: testa em todas as UFs e retorna as siglas válidas
validar_todos("110.042.490.114")   # ['SP']
```

- O `numero` pode vir com **qualquer formatação** (pontos, barras, traços, espaços) — apenas os dígitos são usados (e a letra `P`, no caso de produtor rural de SP).
- A função `validar` levanta `ValueError` se a UF não for reconhecida.

### Na linha de comando

```bash
python3 validador_ie.py SP 110.042.490.114   # valida numa UF específica
python3 validador_ie.py 110.042.490.114       # testa em TODAS as UFs
python3 validador_ie.py -v 110.042.490.114    # idem, detalhando UF por UF
python3 validador_ie.py --listar             # lista as UFs suportadas
python3 validador_ie.py --teste              # roda os auto-testes
```

> Como vários estados usam o mesmo algoritmo de dígito verificador, um número
> pode ser estruturalmente válido em mais de uma UF. O modo "todas as UFs" lista
> todas as siglas em que o número é válido (ou avisa se for inválido em todas).

### UFs suportadas

`AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PI, PR, RJ, RN, RO, RR, RS, SC, SE, SP, TO` (27 — todos os estados + DF).

---

## Como a validação funciona

A maioria dos estados usa **módulo 11** (alguns módulo 10 ou 9) sobre os dígitos "base", comparando o dígito verificador calculado com o informado. Cada estado tem seu próprio formato, pesos e tratamento de exceções — tudo derivado do roteiro em `regras/`.

Três decisões de robustez vale destacar:

- **Zero à esquerda (`zfill`):** IEs são frequentemente armazenadas como números, perdendo zeros iniciais. O validador normaliza preenchendo zeros até o tamanho canônico de cada estado. Ex.: `84498838` (ES) é tratado como `084498838`.
- **Estados com mais de um formato:** BA (8/9 dígitos), RN (9/10), PE (9 atual / 14 antigo CACEPE), RO (9 antigo / 14 atual), TO (9 atual / 11 antigo) — o validador testa **todos** os formatos válidos e aceita se qualquer um conferir.
- **Rejeição de lixo / todo-zero:** uma entrada **sem nenhum dígito** (ex.: o texto `"Minas Gerais"`) ou **composta só de zeros** é sempre inválida. Sem essa guarda, um número todo-zero passaria, pois seu dígito verificador calculado também é zero. A guarda é intrínseca a cada validador.

---

## Testes

Os auto-testes usam o **exemplo numérico oficial de cada roteiro** (24 dos 27 estados trazem um exemplo concreto; os demais foram construídos aplicando o algoritmo descrito). Cada exemplo válido também é testado:

- com o **último dígito trocado** (deve dar inválido);
- contra entradas de **lixo / todo-zero / vazio** para as 27 UFs (devem dar inválido).

```bash
python3 validador_ie.py --teste
# ...
# TODOS OS TESTES PASSARAM
```

---

## Validação em lote (CSV)

O repositório inclui um exemplo de entrada [`dados/ies_exemplo.csv`](dados/ies_exemplo.csv) (separador `;`, colunas `state;state_registration`) e o resultado [`dados/resultado_validacao.csv`](dados/resultado_validacao.csv).

Exemplo de script para validar um CSV próprio:

```python
import csv
from validador_ie import validar

with open("entrada.csv", encoding="utf-8-sig") as f, \
     open("saida.csv", "w", newline="", encoding="utf-8") as out:
    leitor = csv.reader(f, delimiter=";")
    escritor = csv.writer(out, delimiter=";")
    next(leitor)  # cabeçalho
    escritor.writerow(["state", "state_registration", "situacao"])
    for uf, ie in leitor:
        try:
            ok = validar(uf.strip(), ie.strip())
        except ValueError:
            ok = False
        escritor.writerow([uf, ie, "VALIDA" if ok else "INVALIDA"])
```

Na lista de exemplo, 204 de 210 IEs são válidas; as 6 inválidas são dados defeituosos (texto no lugar do número, dígitos faltando/sobrando ou dígito verificador incorreto).

---

## Limitações e avisos

- A validação confere **formato e dígito verificador** conforme os roteiros do Sintegra. Ela **não** consulta a base do Sintegra e, portanto, **não garante que a inscrição existe ou está ativa** — apenas que o número é estruturalmente válido.
- **Tocantins:** o roteiro oficial descreve o formato antigo de 11 dígitos; o validador também aceita o formato atual de 9 dígitos.
- **Goiás:** inclui a faixa especial documentada (resto 1 → dígito 1 entre 10103105 e 10119997).
- Alguns estados possuem regras que mudaram ao longo do tempo (PE, RO, RN, TO); ambos os formatos são aceitos quando documentados.

---

## Autor

Fábio Fila — [contato@fabiofila.com.br](mailto:contato@fabiofila.com.br)

---

## Licença

Distribuído sob a licença [MIT](LICENSE). As regras em `regras/` são de origem pública (Sintegra/governos estaduais); este repositório apenas as organiza e implementa a validação correspondente.
