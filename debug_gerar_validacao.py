import json
import re
import sys
from copy import deepcopy
from datetime import datetime, timedelta

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ARQUIVO_GERADO = "saida/base_maladireta.xlsx"

DIAS = {
    "Seg": 0,
    "Ter": 1,
    "Qua": 2,
    "Qui": 3,
    "Sex": 4,
}

COLUNAS_OBRIGATORIAS = [
    "InicioPlanejamento",
    "FimPlanejamento",
    "ComponenteCurricular",
    "AnoSérie",
    "Bimestre",
    "NumAulaES1",
    "NumAulaES2",
    "Conteudo1",
    "Habilidades",
    "ObjetivosAprendizagem1",
    "QtdeAulas",
    "DescriçãoAula",
    "DataElaboração",
]


def normalizar_semana(valor):
    if pd.isna(valor):
        return None

    valor = str(valor)
    valor = valor.upper()
    valor = valor.replace("SEMANA", "")
    valor = valor.replace("S", "")
    valor = valor.replace(" ", "")
    valor = valor.replace(".0", "")
    valor = valor.strip()

    try:
        return int(valor)
    except ValueError:
        return None


def normalizar_texto(valor):
    if pd.isna(valor):
        return ""

    valor = str(valor).strip()
    valor = valor.replace("\r\n", "\n")
    valor = valor.replace("\r", "\n")
    return "\n".join(" ".join(linha.split()) for linha in valor.split("\n"))


def calcular_inicio_fim(ultimo_inicio_planejamento):
    ultimo_inicio = datetime.strptime(
        ultimo_inicio_planejamento,
        "%d/%m/%Y",
    )

    dias_para_segunda = (7 - ultimo_inicio.weekday()) % 7

    if dias_para_segunda == 0:
        dias_para_segunda = 7

    inicio = ultimo_inicio + timedelta(days=dias_para_segunda)
    fim = inicio + timedelta(days=4)

    return (
        inicio.strftime("%d/%m/%Y"),
        fim.strftime("%d/%m/%Y"),
    )


def calcular_data(inicio, dia):
    data_inicio = datetime.strptime(
        inicio,
        "%d/%m/%Y",
    )

    data = data_inicio + timedelta(days=DIAS[dia])

    return data.strftime("%d/%m/%Y")


def encontrar_colunas(df):
    colunas = {}

    colunas["semana"] = next(
        c for c in df.columns
        if c.strip() == "semana"
    )

    colunas["tipo"] = next(
        c for c in df.columns
        if "teórica/prática" in c
        or "teorica/pratica" in c
    )

    colunas["componente"] = next(
        c for c in df.columns
        if "nome do componente" in c
    )

    colunas["titulo"] = next(
        c for c in df.columns
        if "título da aula" in c
        or "titulo da aula" in c
    )

    colunas["habilidade"] = next(
        (
            c for c in df.columns
            if "habilidades técnicas" in c
            or "habilidades t" in c
        ),
        next(c for c in df.columns if "habilidades" in c),
    )

    colunas["objetivo"] = next(
        c for c in df.columns
        if "objetivo" in c
    )

    return colunas


def limpar_titulo(titulo):
    return re.sub(
        r"^aula\s+\d+:\s*",
        "",
        str(titulo).strip(),
        flags=re.IGNORECASE,
    )


def montar_linhas_num_aula(proximas, aulas_grade, colunas, inicio):
    aulas_por_dia = {}

    for i, (_, aula) in enumerate(proximas.iterrows()):
        dia_semana = aulas_grade.iloc[i]["Dia"]
        data = calcular_data(inicio, dia_semana)
        data_curta = datetime.strptime(data, "%d/%m/%Y").strftime("%d/%m")

        semana = int(aula["semana_normalizada"])
        numero = int(aula["numero_aula"])
        tipo = "Prática" if aula[colunas["tipo"]] == "P" else "Teórica"
        texto = f"S{semana} Aula {numero} {tipo}"

        if data_curta not in aulas_por_dia:
            aulas_por_dia[data_curta] = []

        aulas_por_dia[data_curta].append(texto)

    linhas = []

    for data in sorted(aulas_por_dia.keys()):
        linhas.append(
            f"{data} - "
            + ", ".join(aulas_por_dia[data])
        )

    return linhas


def montar_esperado(config):
    grade = pd.read_excel(
        config["grade_horaria"],
        dtype=str,
    )

    turmas_sufixo = config.get(
        "turmas_sufixo",
        {},
    )

    esperados = []
    erros = []

    for item in config["arquivos_escopo"]:
        arquivo = item["arquivo"]
        turma = item["turma"]

        for aba in item["abas"]:
            df = pd.read_excel(
                arquivo,
                sheet_name=aba,
                dtype=str,
            )
            df.columns = [col.strip().lower() for col in df.columns]

            try:
                colunas = encontrar_colunas(df)
            except StopIteration:
                erros.append(
                    f"{arquivo} | {aba}: coluna obrigatória não encontrada"
                )
                continue

            df["semana_normalizada"] = df[colunas["semana"]].apply(
                normalizar_semana
            )

            df["numero_aula"] = (
                df.groupby(
                    [
                        colunas["componente"],
                        "semana_normalizada",
                    ]
                ).cumcount()
                + 1
            )

            for componente, dados in config["disciplinas"].items():
                aulas_disciplina = df[
                    df[colunas["componente"]].str.lower()
                    == componente.lower()
                ].copy()

                if aulas_disciplina.empty:
                    continue

                aulas_disciplina = (
                    aulas_disciplina
                    .sort_values(
                        by=[
                            "semana_normalizada",
                            "numero_aula",
                        ]
                    )
                    .reset_index(drop=True)
                )

                ultima_semana = int(dados["ultima_semana"])
                ultima_aula = int(dados["ultima_aula"])

                posicao = aulas_disciplina[
                    (
                        aulas_disciplina["semana_normalizada"]
                        == ultima_semana
                    )
                    & (
                        aulas_disciplina["numero_aula"]
                        == ultima_aula
                    )
                ]

                if posicao.empty:
                    erros.append(
                        f"{componente}: última aula S{ultima_semana} "
                        f"Aula {ultima_aula} não encontrada"
                    )
                    continue

                aulas_grade = grade[
                    (grade["Turma"] == turma)
                    & (grade["Disciplina"] == componente)
                ]

                if aulas_grade.empty:
                    erros.append(
                        f"{componente}: grade horária não encontrada "
                        f"para {turma}"
                    )
                    continue

                inicio, fim = calcular_inicio_fim(
                    dados["ultimo_inicio_planejamento"]
                )

                qtd_aulas = len(aulas_grade)
                indice_atual = posicao.index[0]
                proximas = aulas_disciplina.iloc[
                    indice_atual + 1:
                    indice_atual + 1 + qtd_aulas
                ]

                if len(proximas) != qtd_aulas:
                    erros.append(
                        f"{componente}: esperado {qtd_aulas} próximas "
                        f"aulas, encontrado {len(proximas)}"
                    )
                    continue

                linhas_num_aula = montar_linhas_num_aula(
                    proximas,
                    aulas_grade,
                    colunas,
                    inicio,
                )

                registro = {
                    "ComponenteCurricular": componente.upper(),
                    "InicioPlanejamento": inicio,
                    "FimPlanejamento": fim,
                    "AnoSérie": turmas_sufixo.get(turma, f"{turma} F"),
                    "Bimestre": config["bimestre"],
                    "QtdeAulas": str(qtd_aulas),
                    "NumAulaES1": linhas_num_aula[0],
                    "NumAulaES2": "\n".join(linhas_num_aula[1:]),
                }

                for i, (_, aula) in enumerate(proximas.iterrows(), start=1):
                    semana = int(aula["semana_normalizada"])
                    numero = int(aula["numero_aula"])

                    registro[f"Conteudo{i}"] = (
                        f"S{semana} Aula {numero}: "
                        f"{limpar_titulo(aula[colunas['titulo']])}"
                    )

                    registro[f"ObjetivosAprendizagem{i}"] = aula[
                        colunas["objetivo"]
                    ]

                ultima = proximas.iloc[-1]
                registro["_disciplina_config"] = componente
                registro["_proxima_ultima_semana"] = int(
                    ultima["semana_normalizada"]
                )
                registro["_proxima_ultima_aula"] = int(
                    ultima["numero_aula"]
                )

                esperados.append(registro)

    return esperados, erros


def montar_config_sugerido(config, esperados):
    config_sugerido = deepcopy(config)

    for esperado in esperados:
        disciplina = esperado["_disciplina_config"]

        if disciplina not in config_sugerido["disciplinas"]:
            continue

        config_sugerido["disciplinas"][disciplina][
            "ultima_semana"
        ] = esperado["_proxima_ultima_semana"]

        config_sugerido["disciplinas"][disciplina][
            "ultima_aula"
        ] = esperado["_proxima_ultima_aula"]

        config_sugerido["disciplinas"][disciplina][
            "ultimo_inicio_planejamento"
        ] = esperado["InicioPlanejamento"]

    return config_sugerido


def obter_periodo_proxima_geracao(config_sugerido):
    periodos = set()

    for dados in config_sugerido["disciplinas"].values():
        inicio, fim = calcular_inicio_fim(
            dados["ultimo_inicio_planejamento"]
        )
        periodos.add((inicio, fim))

    return sorted(periodos)


def imprimir_config_sugerido(config, esperados):
    if not esperados:
        return

    config_sugerido = montar_config_sugerido(
        config,
        esperados,
    )

    periodos = obter_periodo_proxima_geracao(
        config_sugerido
    )

    print("\n" + "=" * 70)
    print("SUGESTÃO DE CONFIG PARA A PRÓXIMA GERAÇÃO")
    print("=" * 70)

    if periodos:
        for inicio, fim in periodos:
            print(
                f"Próximo planejamento estimado: {inicio} a {fim}"
            )

    print(
        "\nObservação: o campo ultimo_inicio_planejamento continua "
        "representando o início do planejamento já gerado. "
        "O gerar_planejamento.py calcula a próxima segunda-feira "
        "a partir dele."
    )

    print("\nJSON sugerido para copiar para o config.json:\n")
    print(
        json.dumps(
            config_sugerido,
            ensure_ascii=False,
            indent=4,
        )
    )


def comparar_valor(rotulo, esperado, gerado):
    esperado = normalizar_texto(esperado)
    gerado = normalizar_texto(gerado)

    if esperado == gerado:
        print(f"  [OK] {rotulo}: {gerado}")
        return True

    print(f"  [ERRO] {rotulo}")
    print(f"    esperado: {esperado}")
    print(f"    gerado:   {gerado}")
    return False


def validar_colunas(df_gerado):
    ok = True

    print("\nVALIDANDO COLUNAS OBRIGATÓRIAS")

    for coluna in COLUNAS_OBRIGATORIAS:
        if coluna in df_gerado.columns:
            print(f"  [OK] {coluna}")
        else:
            print(f"  [ERRO] Coluna ausente: {coluna}")
            ok = False

    return ok


def main():
    with open(
        "config.json",
        "r",
        encoding="utf-8",
    ) as arquivo:
        config = json.load(arquivo)

    df_gerado = pd.read_excel(
        ARQUIVO_GERADO,
        dtype=str,
    )

    print("=" * 70)
    print("VALIDAÇÃO DA GERAÇÃO DO PLANEJAMENTO")
    print("=" * 70)

    sucesso = validar_colunas(df_gerado)
    esperados, erros = montar_esperado(config)

    if erros:
        sucesso = False
        print("\nERROS ENCONTRADOS AO LER CONFIG/ESCOPO/GRADE")

        for erro in erros:
            print(f"  [ERRO] {erro}")

    print("\nVALIDANDO REGISTROS GERADOS")

    for esperado in esperados:
        componente = esperado["ComponenteCurricular"]

        gerados = df_gerado[
            df_gerado["ComponenteCurricular"] == componente
        ]

        print(f"\n{componente}")

        if gerados.empty:
            print("  [ERRO] Registro não encontrado na planilha gerada")
            sucesso = False
            continue

        gerado = gerados.iloc[0]

        colunas_para_comparar = [
            "InicioPlanejamento",
            "FimPlanejamento",
            "AnoSérie",
            "Bimestre",
            "QtdeAulas",
            "NumAulaES1",
            "NumAulaES2",
            "Conteudo1",
            "Conteudo2",
            "Conteudo3",
            "Conteudo4",
            "ObjetivosAprendizagem1",
            "ObjetivosAprendizagem2",
            "ObjetivosAprendizagem3",
            "ObjetivosAprendizagem4",
        ]

        for coluna in colunas_para_comparar:
            if coluna not in esperado and coluna not in gerado.index:
                continue

            if not comparar_valor(
                coluna,
                esperado.get(coluna, ""),
                gerado.get(coluna, ""),
            ):
                sucesso = False

    print("\n" + "=" * 70)

    if sucesso:
        print("[OK] Geração coerente com config, grade e escopo")
        imprimir_config_sugerido(
            config,
            esperados,
        )
    else:
        print("[ERRO] Foram encontradas divergências na geração")

    print("=" * 70)


if __name__ == "__main__":
    main()
