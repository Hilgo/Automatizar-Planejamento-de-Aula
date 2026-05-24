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
  "descricao_template": "As aulas serão ministradas de maneira expositiva visando a apresentação dos conceitos para os alunos avançarem no conteúdo do material digital (Educação Profissional) e desenvolverem as habilidades correspondentes. {descricoes_dia} {descricao_pratica}",
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

### Template da descrição da aula

O campo `descricao_template` permite personalizar o texto da coluna `DescriçãoAula`.

O código substitui automaticamente estes valores:

- `{descricoes_dia}`: frases com os objetivos de aprendizagem agrupados por dia;
- `{descricao_pratica}`: frase sobre os dias com aula prática;
- `{dias_com_aula}`: lista dos dias do planejamento que possuem aula;
- `{dias_praticos}`: lista dos dias que possuem aula prática.

Exemplo:

```json
{
  "descricao_template": "As aulas serão desenvolvidas com exposição dialogada e atividades orientadas. {descricoes_dia} {descricao_pratica}"
}
```

Se o template não tiver um dos campos acima, ele simplesmente não será usado no texto final. O arquivo ainda aceita `descricao_padrao` por compatibilidade com versões antigas, mas o recomendado é usar `descricao_template`.

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

Quando a validação passa, o script também imprime no terminal uma sugestão de `config.json` para a próxima geração. Essa sugestão não sobrescreve o arquivo atual; ela apenas mostra quais valores copiar caso o professor queira avançar para a próxima semana de planejamento.

Exemplo: depois de validar um planejamento de `25/05/2026` a `29/05/2026`, o debug pode sugerir um config que gera o próximo período, de `01/06/2026` a `05/06/2026`, já atualizando `ultima_semana`, `ultima_aula` e `ultimo_inicio_planejamento` de cada disciplina.

## Dependências

O projeto usa:

```bash
pip install pandas openpyxl rapidfuzz
```

`pandas` e `openpyxl` são usados para ler e escrever planilhas. `rapidfuzz` é usado na comparação de similaridade com o modelo.
