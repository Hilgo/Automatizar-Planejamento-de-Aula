import json
import pandas as pd
import re

from datetime import (
    datetime,
    timedelta
)

# =====================================
# LER CONFIG
# =====================================

with open(
    "config.json",
    "r",
    encoding="utf-8"
) as arquivo:

    config = json.load(arquivo)

# =====================================
# CONFIG
# =====================================

BIMESTRE = config["bimestre"]

DESCRICAO_TEMPLATE_PADRAO = (
    "As aulas serão ministradas de maneira expositiva visando a apresentação "
    "dos conceitos para os alunos avançarem no conteúdo do material digital "
    "(Educação Profissional) e desenvolverem as habilidades correspondentes. "
    "{descricoes_dia} {descricao_pratica}"
)

DESCRICAO_TEMPLATE = config.get(
    "descricao_template",
    config.get(
        "descricao_padrao",
        DESCRICAO_TEMPLATE_PADRAO
    )
)

GRADE = config[
    "grade_horaria"
]

DISCIPLINAS = config[
    "disciplinas"
]

ARQUIVOS = config[
    "arquivos_escopo"
]

# =====================================
# MAPA TURMAS (do config)
# =====================================

TURMAS_SUFIXO = config.get(
    "turmas_sufixo",
    {
        "2DS": "2DS F",
        "3DS": "3DS Y"
    }
)

# =====================================
# MAPA DIAS
# =====================================

DIAS = {

    "Seg": 0,
    "Ter": 1,
    "Qua": 2,
    "Qui": 3,
    "Sex": 4
}

# =====================================
# TEXTO DA DESCRIÇÃO
# =====================================

def juntar_textos(textos):

    textos = [
        str(texto).strip()
        for texto in textos
        if pd.notna(texto)
        and str(texto).strip()
        and str(texto).strip().lower() != "nan"
    ]

    if not textos:
        return ""

    if len(textos) == 1:
        return textos[0]

    return (
        ", ".join(textos[:-1])
        + " e "
        + textos[-1]
    )


def formatar_objetivo_para_descricao(objetivo):

    objetivo = str(objetivo).strip()
    objetivo = objetivo.rstrip(".;")

    if not objetivo:
        return ""

    return objetivo[0].lower() + objetivo[1:]


def gerar_descricao_aula(aulas_por_dia):

    if not aulas_por_dia:
        return DESCRICAO_TEMPLATE.format(
            descricoes_dia="",
            descricao_pratica="",
            dias_com_aula="",
            dias_praticos="",
        ).strip()

    descricoes_dia = []
    dias_praticos = []

    for data in sorted(aulas_por_dia.keys()):
        aulas = aulas_por_dia[data]
        objetivos = []
        tem_pratica = False

        for aula in aulas:
            objetivos.append(
                formatar_objetivo_para_descricao(
                    aula["objetivo"]
                )
            )

            if aula["tipo"] == "Prática":
                tem_pratica = True

        if tem_pratica:
            dias_praticos.append(data)

        qtd = len(aulas)
        artigo = "A aula" if qtd == 1 else "As aulas"
        verbo = "será" if qtd == 1 else "serão"
        dia = data.split("/")[0]

        descricoes_dia.append(
            f"{artigo} do dia {dia} {verbo} sobre {juntar_textos(objetivos)}"
        )

    descricoes_dia_texto = ". ".join(descricoes_dia)

    if descricoes_dia_texto:
        descricoes_dia_texto += "."

    dias_praticos_texto = ""
    descricao_pratica = ""

    if dias_praticos:
        dias = [
            data.split("/")[0]
            for data in dias_praticos
        ]

        dias_praticos_texto = juntar_textos(dias)

        descricao_pratica = (
            f"As aulas do dia {dias_praticos_texto} terão caráter prático, "
            "visando contextualizar o que foi ministrado nas aulas anteriores, "
            "fazendo com que os alunos vivenciem o que foi estudado."
        )

    dias_com_aula = [
        data.split("/")[0]
        for data in sorted(aulas_por_dia.keys())
    ]

    descricao = DESCRICAO_TEMPLATE.format(
        descricoes_dia=descricoes_dia_texto,
        descricao_pratica=descricao_pratica,
        dias_com_aula=juntar_textos(dias_com_aula),
        dias_praticos=dias_praticos_texto,
    )

    return " ".join(descricao.split())

# =====================================
# CALCULAR DATA
# =====================================

def calcular_data(
    inicio,
    dia
):

    data_inicio = datetime.strptime(
        inicio,
        "%d/%m/%Y"
    )

    deslocamento = DIAS[dia]

    data = (
        data_inicio
        + timedelta(days=deslocamento)
    )

    return data.strftime("%d/%m/%Y")

# =====================================
# NORMALIZAR SEMANA
# =====================================

def normalizar_semana(valor):

    if pd.isna(valor):

        return None

    valor = str(valor)

    valor = valor.upper()

    valor = valor.replace(
        "SEMANA",
        ""
    )

    valor = valor.replace(
        "S",
        ""
    )

    valor = valor.replace(
        " ",
        ""
    )

    valor = valor.replace(
        ".0",
        ""
    )

    valor = valor.strip()

    try:
        return int(valor)
    except ValueError:
        return None

# =====================================
# LER GRADE
# =====================================

grade = pd.read_excel(
    GRADE,
    dtype=str
)

# =====================================
# LISTA FINAL
# =====================================

registros = []

# =====================================
# PROCESSAR ARQUIVOS
# =====================================

for item in ARQUIVOS:

    arquivo = item["arquivo"]

    turma = item["turma"]

    for aba in item["abas"]:

        print(
            "\n===================================="
        )

        print(
            f"PROCESSANDO: "
            f"{arquivo} - {aba}"
        )

        print(
            "====================================\n"
        )

        # =================================
        # LER PLANILHA
        # =================================

        df = pd.read_excel(
            arquivo,
            sheet_name=aba,
            dtype=str
        )

        # =================================
        # MOSTRAR COLUNAS
        # =================================

        print(
            "COLUNAS ENCONTRADAS:\n"
        )

        for c in df.columns:

            print(f"[{c}]")

        # =================================
        # NORMALIZAR COLUNAS
        # =================================

        df.columns = [

            col.strip().lower()

            for col in df.columns
        ]

        # =================================
        # IDENTIFICAR COLUNAS
        # =================================

        coluna_semana = next(
            c for c in df.columns
            if c.strip() == "semana"
        )

        coluna_tp = next(
            c for c in df.columns
            if "teórica/prática" in c
            or "teorica/pratica" in c
        )

        coluna_componente = next(
            c for c in df.columns
            if "nome do componente" in c
        )

        coluna_titulo = next(
            c for c in df.columns
            if "título da aula" in c
            or "titulo da aula" in c
        )

        coluna_habilidade = next(
            c for c in df.columns
            if "habilidades" in c
        )

        coluna_objetivo = next(
            c for c in df.columns
            if "objetivo" in c
        )

        # =================================
        # NORMALIZAR SEMANA
        # =================================

        df["semana_normalizada"] = (

            df[coluna_semana]
            .apply(normalizar_semana)
        )

        # =================================
        # GERAR NUMERO AULA
        # =================================

        df["numero_aula"] = (

            df.groupby(
                [
                    coluna_componente,
                    "semana_normalizada"
                ]
            ).cumcount() + 1
        )

        # =================================
        # PROCESSAR DISCIPLINAS CONFIG
        # =================================

        for componente in DISCIPLINAS.keys():

            print(
                "\n----------------------------"
            )

            print(
                f"DISCIPLINA:"
            )

            print(componente)

            print(
                "----------------------------"
            )

            # =============================
            # FILTRAR DISCIPLINA
            # =============================

            aulas_disciplina = df[

                df[coluna_componente].str.lower()
                == componente.lower()

            ].copy()

            # =============================
            # NÃO ENCONTROU
            # =============================

            if aulas_disciplina.empty:

                print(
                    "Aviso: Disciplina "
                    "nao encontrada "
                    "nesta aba"
                )

                continue

            print(
                f"Aulas encontradas: "
                f"{len(aulas_disciplina)}"
            )

            # =============================
            # DADOS CONFIG
            # =============================

            dados = DISCIPLINAS[
                componente
            ]

            ultima_semana = dados[
                "ultima_semana"
            ]

            ultima_aula = dados[
                "ultima_aula"
            ]

            print(
                f"Última semana: "
                f"{ultima_semana}"
            )

            print(
                f"Última aula: "
                f"{ultima_aula}"
            )

            # =============================
            # CALCULAR NOVAS DATAS
            # =============================

            ultimo_inicio = datetime.strptime(

                dados[
                    "ultimo_inicio_planejamento"
                ],

                "%d/%m/%Y"
            )

            # Calcular próxima segunda-feira
            dias_para_segunda = (
                (7 - ultimo_inicio.weekday()) % 7
            )
            
            if dias_para_segunda == 0:
                dias_para_segunda = 7

            novo_inicio = (

                ultimo_inicio
                + timedelta(days=dias_para_segunda)
            )

            novo_fim = (

                novo_inicio
                + timedelta(days=4)
            )

            INICIO = novo_inicio.strftime(
                "%d/%m/%Y"
            )

            FIM = novo_fim.strftime(
                "%d/%m/%Y"
            )

            # =============================
            # ORDENAR
            # =============================

            aulas_disciplina = (

                aulas_disciplina
                .sort_values(

                    by=[
                        "semana_normalizada",
                        "numero_aula"
                    ]
                )
                .reset_index(drop=True)
            )

            print(
                "\nAULAS DISPONÍVEIS:\n"
            )

            print(

                aulas_disciplina[
                    [
                        "semana_normalizada",
                        "numero_aula"
                    ]
                ]
            )

            # =============================
            # ENCONTRAR POSIÇÃO
            # =============================

            posicao = aulas_disciplina[

                (
                    aulas_disciplina[
                        "semana_normalizada"
                    ]
                    == int(ultima_semana)
                )

                &

                (
                    aulas_disciplina[
                        "numero_aula"
                    ]
                    == int(ultima_aula)
                )
            ]

            print(
                "\nBUSCANDO:\n"
            )

            print(
                f"Semana: "
                f"{ultima_semana}"
            )

            print(
                f"Aula: "
                f"{ultima_aula}"
            )

            # =============================
            # NÃO ENCONTROU
            # =============================

            if posicao.empty:

                print(
                    "Erro: Nao encontrou "
                    "ultima aula "
                    "no escopo"
                )

                continue

            indice_atual = posicao.index[0]

            print(
                f"Índice atual: "
                f"{indice_atual}"
            )

            # =============================
            # BUSCAR GRADE
            # =============================

            aulas_grade = grade[

                (
                    grade["Turma"]
                    == turma
                )

                &

                (
                    grade["Disciplina"]
                    == componente
                )
            ]

            # =============================
            # NÃO ENCONTROU GRADE
            # =============================

            if aulas_grade.empty:

                print(
                    "Erro: Nao encontrou "
                    "grade horaria"
                )

                continue

            qtd_aulas = len(
                aulas_grade
            )

            print(
                f"Qtd aulas: "
                f"{qtd_aulas}"
            )

            # =============================
            # PRÓXIMAS AULAS
            # =============================

            proximas = (

                aulas_disciplina.iloc[
                    indice_atual + 1:
                    indice_atual + 1 + qtd_aulas
                ]
            )

            # =============================
            # SEM PRÓXIMAS AULAS
            # =============================

            if proximas.empty:

                print(
                    "Erro: Nao encontrou "
                    "proximas aulas"
                )

                continue

            print(
                "\nPRÓXIMAS AULAS:\n"
            )

            print(

                proximas[
                    [
                        "semana_normalizada",
                        "numero_aula"
                    ]
                ]
            )

            # =============================
            # REGISTRO
            # =============================

            registro = {

                "InicioPlanejamento":
                    INICIO,

                "FimPlanejamento":
                    FIM,

                "ComponenteCurricular":
                    componente.upper(),

                "AnoSérie":
                    TURMAS_SUFIXO.get(turma, f"{turma} F"),

                "Bimestre":
                    BIMESTRE,

                "DataElaboração":
                    datetime.now().strftime("%d/%m/%Y"),

                "DescriçãoAula":
                    "",

                "QtdeAulas":
                    len(proximas),
            }

            habilidades = []

            aulas_por_dia = {}

            # =============================
            # PROCESSAR AULAS
            # =============================

            for i, (
                idx,
                aula
            ) in enumerate(
                proximas.iterrows()
            ):

                dia_semana = (

                    aulas_grade
                    .iloc[i]["Dia"]
                )

                data = calcular_data(
                    INICIO,
                    dia_semana
                )

                data_curta = datetime.strptime(

                    data,
                    "%d/%m/%Y"

                ).strftime("%d/%m")

                semana = aula[
                    "semana_normalizada"
                ]

                numero = aula[
                    "numero_aula"
                ]

                # Converter para int para remover decimais
                semana = int(semana) if pd.notna(semana) else None
                numero = int(numero) if pd.notna(numero) else None

                tipo = (

                    "Prática"

                    if aula[coluna_tp] == "P"

                    else "Teórica"
                )

                texto = (

                    f"S{semana} "
                    f"Aula {numero} "
                    f"{tipo}"
                )

                if (
                    data_curta
                    not in aulas_por_dia
                ):

                    aulas_por_dia[
                        data_curta
                    ] = []

                aulas_por_dia[
                    data_curta
                ].append(
                    {
                        "texto": texto,
                        "tipo": tipo,
                        "objetivo": aula[coluna_objetivo]
                    }
                )

                # =========================
                # CONTEÚDOS
                # =========================

                semana = int(aula["semana_normalizada"])
                numero = int(aula["numero_aula"])

                registro[
                    f"Conteudo{i + 1}"
                ] = (
                    f"S{semana} Aula {numero}: "
                    + re.sub(
                        r'^aula\s+\d+:\s*',
                        '',
                        str(aula[coluna_titulo]).strip(),
                        flags=re.IGNORECASE
                    )
                )

                registro[
                    f"ObjetivosAprendizagem{i + 1}"
                ] = aula[
                    coluna_objetivo
                ]

                habilidades.append(

                    str(
                        aula[
                            coluna_habilidade
                        ]
                    )
                )

            # =============================
            # NumAulaES
            # =============================

            linhas_num_aula = []

            for data in sorted(aulas_por_dia.keys()):
                aulas = aulas_por_dia[data]

                linhas_num_aula.append(
                    f"{data} - "
                    + ", ".join(
                        aula["texto"]
                        for aula in aulas
                    )
                )

            if linhas_num_aula:
                registro[
                    "NumAulaES1"
                ] = linhas_num_aula[0]

            if len(linhas_num_aula) > 1:
                registro[
                    "NumAulaES2"
                ] = "\n".join(
                    linhas_num_aula[1:]
                )

            registro[
                "DescriçãoAula"
            ] = gerar_descricao_aula(
                aulas_por_dia
            )

            # =============================
            # HABILIDADES
            # =============================

            registro[
                "Habilidades"
            ] = "\n".join(
                dict.fromkeys(habilidades)
            )

            registros.append(
                registro
            )

            print(
                "OK: Registro gerado"
            )

            # =============================
            # ATUALIZAR CONFIG
            # =============================

            ultima = proximas.iloc[-1]

            DISCIPLINAS[
                componente
            ][
                "ultima_semana"
            ] = int(

                ultima[
                    "semana_normalizada"
                ]
            )

            DISCIPLINAS[
                componente
            ][
                "ultima_aula"
            ] = int(

                ultima[
                    "numero_aula"
                ]
            )

            DISCIPLINAS[
                componente
            ][
                "ultimo_inicio_planejamento"
            ] = INICIO

# =====================================
# GERAR DATAFRAME
# =====================================

df_final = pd.DataFrame(
    registros
)

# =====================================
# REORDENAR COLUNAS
# =====================================

colunas_ordem = [
    "InicioPlanejamento",
    "FimPlanejamento",
    "ComponenteCurricular",
    "AnoSérie",
    "Bimestre",
    "NumAulaES1",
    "NumAulaES2",
    "Conteudo1",
    "Conteudo2",
    "Conteudo3",
    "Conteudo4",
    "Habilidades",
    "ObjetivosAprendizagem1",
    "ObjetivosAprendizagem2",
    "ObjetivosAprendizagem3",
    "ObjetivosAprendizagem4",
    "QtdeAulas",
    "DescriçãoAula",
    "DataElaboração"
]

df_final = df_final[[col for col in colunas_ordem if col in df_final.columns]]

print(
    "\n===================================="
)

print(
    "RESULTADO FINAL"
)

print(
    "====================================\n"
)

print(df_final)

# =====================================
# EXPORTAR
# =====================================

df_final.to_excel(
    "saida/base_maladireta.xlsx",
    index=False
)

# =====================================
# SALVAR CONFIG
# =====================================

# with open(
#     "config.json",
#     "w",
#     encoding="utf-8"
# ) as arquivo:

#     json.dump(
#         config,
#         arquivo,
#         ensure_ascii=False,
#         indent=4
#     )

print(
    "\nOK: Planilha gerada!"
)
