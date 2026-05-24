# Automatizar Planejamento de Aula

Projeto em Python para gerar uma planilha base de mala direta com planejamentos de aula a partir de:

- arquivo de configuração das turmas e disciplinas;
- planilhas de escopo/sequência;
- grade horária;
- modelo de planilha usado como referência.

## Autoria

Desenvolvido por Lucas Palma Stabile.

## Como funciona

O fluxo principal está no arquivo `gerar_planejamento.py`.

Ele lê o `config.json`, encontra a última aula planejada de cada disciplina, consulta a grade horária para saber quantas aulas devem entrar no próximo planejamento e gera a planilha final em:

```text
saida/base_maladireta.xlsx
```

O script também monta automaticamente campos como:

- `InicioPlanejamento`;
- `FimPlanejamento`;
- `ComponenteCurricular`;
- `AnoSérie`;
- `NumAulaES1`;
- `NumAulaES2`;
- `Conteudo1` até `Conteudo4`;
- `ObjetivosAprendizagem1` até `ObjetivosAprendizagem4`;
- `Habilidades`;
- `DescriçãoAula`;
- `DataElaboração`.

## Estrutura esperada

```text
.
├── config.json
├── gerar_planejamento.py
├── validar_planejamento.py
├── debug_gerar_validacao.py
├── dados/
│   ├── grade_horaria.xlsx
│   └── arquivos_de_escopo.xlsx
├── modelo/
│   └── planejamento_modelo.xlsx
└── saida/
    └── base_maladireta.xlsx
```

Os arquivos `.xlsx` são ignorados pelo Git, pois costumam conter dados locais de turmas, planejamentos e materiais da escola.

## Configuração

Antes de rodar o projeto, o professor precisa configurar o arquivo `config.json`.

Exemplo dos principais campos:

```json
{
  "bimestre": "2º",
  "descricao_padrao": "As aulas serão ministradas de maneira expositiva e prática.",
  "grade_horaria": "dados/grade_horaria.xlsx",
  "turmas_sufixo": {
    "2DS": "2DS F",
    "3DS": "3DS Y"
  },
  "arquivos_escopo": [
    {
      "arquivo": "dados/Escopo-sequência 2DS.xlsx",
      "turma": "2DS",
      "abas": ["SIS"]
    }
  ],
  "disciplinas": {
    "Nome da Disciplina": {
      "ultima_semana": 10,
      "ultima_aula": 2,
      "ultimo_inicio_planejamento": "18/05/2026"
    }
  }
}
```

Cada disciplina deve informar:

- `ultima_semana`: última semana já planejada;
- `ultima_aula`: última aula já planejada dentro dessa semana;
- `ultimo_inicio_planejamento`: data de início do último planejamento, no formato `dd/mm/aaaa`.

Com esses dados, o script calcula a próxima semana de planejamento automaticamente.

## Arquivos necessários

Para o projeto funcionar, inclua os arquivos nas pastas correspondentes:

- `dados/grade_horaria.xlsx`: grade com as colunas `Dia`, `Horario`, `Turma` e `Disciplina`;
- `dados/*.xlsx`: arquivos de escopo/sequência das turmas;
- `modelo/planejamento_modelo.xlsx`: modelo usado para comparar a estrutura e o conteúdo esperado;
- `saida/base_maladireta.xlsx`: arquivo gerado pelo script principal.

### Formato da grade horária

O arquivo `dados/grade_horaria.xlsx` precisa ter, no mínimo, estas colunas:

```text
Dia | Horario | Turma | Disciplina
```

A coluna `Dia` deve usar exatamente estas abreviações:

```text
Seg, Ter, Qua, Qui, Sex
```

A coluna `Turma` deve ser igual ao valor informado em `turma` dentro do `config.json`.

Exemplo:

```json
{
  "arquivo": "dados/Escopo-sequência 2DS.xlsx",
  "turma": "2DS",
  "abas": ["SIS"]
}
```

Nesse caso, a grade horária também deve usar `2DS` na coluna `Turma`.

## Como gerar o planejamento

Execute:

```bash
python gerar_planejamento.py
```

Ao final, a planilha será salva em:

```text
saida/base_maladireta.xlsx
```

## Como validar o resultado

Para comparar a planilha gerada com o modelo:

```bash
python validar_planejamento.py
```

Esse script verifica:

- estrutura das colunas;
- quantidade de linhas;
- datas;
- turma;
- conteúdos;
- objetivos de aprendizagem;
- habilidades;
- descrição da aula;
- similaridade geral com o modelo.

## Como validar a geração

Para conferir se o arquivo gerado está coerente com `config.json`, grade horária e escopos:

```bash
python debug_gerar_validacao.py
```

Esse script verifica:

- data correta de início e fim do planejamento;
- dias corretos das aulas conforme a grade;
- `NumAulaES1` e `NumAulaES2`;
- conteúdos esperados;
- objetivos de aprendizagem esperados;
- quantidade de aulas por disciplina;
- colunas obrigatórias no arquivo final.

## Dependências

O projeto usa:

```bash
pip install pandas openpyxl rapidfuzz
```

`pandas` e `openpyxl` são usados para ler e escrever planilhas. `rapidfuzz` é usado na comparação de similaridade com o modelo.
