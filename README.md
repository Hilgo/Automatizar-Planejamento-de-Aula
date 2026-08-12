# Automatizar Planejamento de Aula

Projeto em Python para gerar automaticamente uma planilha de mala direta com planejamentos de aula baseados em:

- arquivo de configuração das turmas e disciplinas (`config.json`);
- arquivos de escopo / sequência por disciplina;
- grade horária semanal;
- modelo de planilha para formato final.

O objetivo é reduzir o trabalho manual de montar o planejamento em Excel e permitir gerar a base de mala direta com campos prontos para impressão ou importação em sistemas de planejamento escolar. Observação: Foi criado com foco no planejamento semanal para professores da Educação Profissional do Estado de São Paulo.

---

## 🚀 Funcionalidades

- Geração automática de `saida/base_maladireta.xlsx` a partir dos dados de entrada
- Cálculo da próxima semana de planejamento a partir da última aula planejada
- Tratamento de dias e datas não letivas
- Preenchimento automático de campos como:
  - `InicioPlanejamento`
  - `FimPlanejamento`
  - `ComponenteCurricular`
  - `AnoSérie`
  - `NumAulaES1`, `NumAulaES2`
  - `Conteudo1` a `Conteudo4`
  - `ObjetivosAprendizagem1` a `ObjetivosAprendizagem4`
  - `Habilidades`
  - `DescriçãoAula`
  - `DataElaboração`
- Interface web simples para gerar o arquivo em um navegador

---

## 📁 Estrutura do projeto

```text
.
├── app.py
├── config.json
├── planejamento_cli.py
├── planejamento.py
├── validar_planejamento.py
├── debug_gerar_validacao.py
├── requirements.txt
├── templates/
│   └── index.html
├── dados/
│   ├── grade_horaria.xlsx
│   └── Escopo-sequência ... .xlsx
├── modelo/
│   └── planejamento_modelo.xlsx
└── saida/
    └── base_maladireta.xlsx
```

> Observação: os arquivos `.xlsx` geralmente não são versionados, pois contêm dados locais e sensíveis de turmas.

---

## 🛠️ Requisitos

- Python 3.10+ (recomendado)
- `pip`
- Dependências do projeto:
  - `pandas`
  - `openpyxl`
  - `rapidfuzz`
  - `flask`
- `authlib`
pip install -r requirements.txt
```

---

## ⚙️ Configuração do `config.json`

O arquivo `config.json` é o ponto central do fluxo. Ele informa:

- qual é a grade horária
- quais são os arquivos de escopo
- como mapear cada disciplina
- quais dias são não letivos
- o bimestre e descrições do planejamento

### Exemplo básico

```json
{
  "bimestre": "2º",
  "descricao_template": "As aulas serão ministradas de maneira expositiva visando a apresentação dos conceitos para os alunos avançarem no conteúdo do material digital (Educação Profissional) e desenvolverem as habilidades correspondentes. {descricoes_dia} {descricao_pratica}",
  "dias_nao_letivos": ["Qui", "Sex"],
  "datas_nao_letivas": [],
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

### Campos principais de cada disciplina

- `ultima_semana`: última semana planejada no escopo
- `ultima_aula`: última aula planejada dentro dessa semana
- `ultimo_inicio_planejamento`: data de início da última semana planejada (`dd/mm/aaaa`)

A partir desses dados, o script calcula a próxima segunda-feira e monta o planejamento seguinte.

### Dias e datas não letivas

- `dias_nao_letivos`: dias fixos da semana sem aula
- `datas_nao_letivas`: datas específicas sem aula

Exemplos válidos:

```json
"dias_nao_letivos": ["Qui", "Sex"]
"datas_nao_letivas": ["04/06/2026", "05/06/2026"]
```

As datas podem ser informadas como `dd/mm/aaaa` ou `dd/mm`.

Quando um dia é marcado como não letivo:

- `NumAulaES` recebe `Dia não letivo`
- `QtdeAulas` conta somente as aulas letivas
- `Conteudo*`, `ObjetivosAprendizagem*` e `Habilidades` não são preenchidos para esse dia
- a `DescriçãoAula` não inclui o dia não letivo
- a sequência do escopo não avança nesse dia

### Template de descrição da aula

O campo `descricao_template` personaliza o texto da coluna `DescriçãoAula`.

O template aceita os seguintes marcadores:

- `{descricoes_dia}`
- `{descricao_pratica}`
- `{dias_com_aula}`
- `{dias_praticos}`

Exemplo:

```json
"descricao_template": "As aulas serão desenvolvidas com exposição dialogada e atividades orientadas. {descricoes_dia} {descricao_pratica}"
```

Se algum marcador não estiver presente no template, ele será simplesmente omitido.

---

## 📄 Formato dos arquivos de entrada

### Grade horária

O arquivo `dados/grade_horaria.xlsx` deve conter pelo menos as colunas:

- `Dia`
- `Horario`
- `Turma`
- `Disciplina`

A coluna `Dia` deve usar exatamente as abreviações:

```text
Seg, Ter, Qua, Qui, Sex
```

A coluna `Turma` deve coincidir com o valor de `turma` em cada item de `arquivos_escopo` do `config.json`.

### Arquivos de escopo / sequência

Cada arquivo de escopo deve estar listado em `arquivos_escopo` com:

- `arquivo`: caminho do arquivo `.xlsx`
- `turma`: código da turma
- `abas`: lista de abas a serem lidas

Exemplo:

```json
{
  "arquivo": "dados/Escopo-sequência 2DS.xlsx",
  "turma": "2DS",
  "abas": ["SIS"]
}
```

### Modelo de planilha

O arquivo `modelo/planejamento_modelo.xlsx` é utilizado como referência de formato, mas não é obrigatório para a geração.

---

## ▶️ Uso

### 1. Executando no modo CLI

```bash
python planejamento_cli.py
```

A planilha final será gerada em:

```text
saida/base_maladireta.xlsx
```

### 2. Executando no modo web

```bash
python app.py
```

Abra no navegador:

```text
http://127.0.0.1:5000/
```

Antes de usar, defina as variáveis de ambiente:

- `SECRET_KEY` — chave secreta do Flask
- `GOOGLE_CLIENT_ID` — ID do cliente OAuth do Google
- `GOOGLE_CLIENT_SECRET` — segredo do cliente OAuth do Google

No Console do Google Cloud, configure o URI de redirecionamento OAuth:

```text
http://localhost:5000/authorize
```

Na página web, faça login com o Google e então envie:

- `config.json`
- arquivo da grade horária (`.xlsx`)
- arquivos de escopo (`.xlsx`)

O sistema retorna a planilha `base_maladireta.xlsx` para download.

---

## 🚀 Deploy no Render

1. Adicione todos os requisitos:

```bash
pip install -r requirements.txt
```

2. No painel do Render, crie um serviço web com estas configurações:

- `Environment`: Python
- `Build Command`: `pip install -r requirements.txt`
- `Start Command`: `gunicorn app:app`

3. Defina as variáveis de ambiente no Render:

- `SECRET_KEY` — chave segura para sessão Flask
- `GOOGLE_CLIENT_ID` — ID do cliente OAuth do Google
- `GOOGLE_CLIENT_SECRET` — segredo do cliente OAuth do Google

4. O app já usa arquivos temporários e não salva uploads ou resultados permanentemente no servidor.

> Dica: o app também está preparado para executar localmente com `python app.py`, mas em produção o `gunicorn app:app` é a forma recomendada.

---

## ✅ Validação

### Validar contra o modelo

```bash
python validar_planejamento.py
```

Verifica itens como:

- estrutura das colunas
- quantidade de linhas
- datas
- turma
- conteúdos e objetivos
- habilidades
- descrição da aula
- similaridade geral com o modelo

### Debug da geração

```bash
python debug_gerar_validacao.py
```

Verifica itens como:

- início e fim do planejamento
- dias corretos conforme a grade
- dias não letivos
- valores de `NumAulaES1` e `NumAulaES2`
- conteúdos e objetivos esperados
- quantidade de aulas letivas por disciplina
- colunas obrigatórias no arquivo final

---

## 📌 Observações

- Os arquivos `.xlsx` normalmente não devem ser versionados no repositório.
- O app web usa uploads temporários e gera o arquivo localmente.
- Para publicação, o projeto pode ser convertido em um serviço web em Flask em plataforma como Railway, Render ou Docker.

---

## 📝 Autor

Lucas Palma Stabile

Quando a validação passa, o script também imprime no terminal uma sugestão de `config.json` para a próxima geração. Essa sugestão não sobrescreve o arquivo atual; ela apenas mostra quais valores copiar caso o professor queira avançar para a próxima semana de planejamento.

Exemplo: depois de validar um planejamento de `25/05/2026` a `29/05/2026`, o debug pode sugerir um config que gera o próximo período, de `01/06/2026` a `05/06/2026`, já atualizando `ultima_semana`, `ultima_aula` e `ultimo_inicio_planejamento` de cada disciplina.

