import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

DIAS = {
    "Seg": 0,
    "Ter": 1,
    "Qua": 2,
    "Qui": 3,
    "Sex": 4,
}

DIAS_NORMALIZADOS = {
    dia.lower(): dia
    for dia in DIAS
}

DESCRICAO_TEMPLATE_PADRAO = (
    "As aulas serão ministradas de maneira expositiva visando a apresentação "
    "dos conceitos para os alunos avançarem no conteúdo do material digital "
    "(Educação Profissional) e desenvolverem as habilidades correspondentes. "
    "{descricoes_dia} {descricao_pratica}"
)


def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def juntar_textos(textos: List[str]) -> str:
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

    return ", ".join(textos[:-1]) + " e " + textos[-1]


def formatar_objetivo_para_descricao(objetivo: Any) -> str:
    objetivo = str(objetivo).strip()
    objetivo = objetivo.rstrip(".;")

    if not objetivo:
        return ""

    return objetivo[0].lower() + objetivo[1:]


def converter_data_curta(data_curta: str, inicio: str) -> datetime:
    data_inicio = datetime.strptime(inicio, "%d/%m/%Y")
    data = datetime.strptime(f"{data_curta}/{data_inicio.year}", "%d/%m/%Y")

    if data < data_inicio:
        data = data.replace(year=data_inicio.year + 1)

    return data


def ordenar_datas_curta(datas: List[str], inicio: str) -> List[str]:
    return sorted(
        datas,
        key=lambda data: converter_data_curta(data, inicio),
    )


def normalizar_data_nao_letiva(valor: Any) -> str:
    texto = str(valor).strip()

    for formato in ("%d/%m/%Y", "%d/%m"):
        try:
            return datetime.strptime(texto, formato).strftime(formato)
        except ValueError:
            continue

    return texto


def eh_dia_nao_letivo(
    dia_semana: str,
    data: str,
    dias_nao_letivos: List[str],
    datas_nao_letivas: List[str],
) -> bool:
    dia = str(dia_semana).strip()
    dia_normalizado = DIAS_NORMALIZADOS.get(dia.lower(), dia)

    dias_config = {
        DIAS_NORMALIZADOS.get(str(item).strip().lower(), str(item).strip())
        for item in dias_nao_letivos
    }

    datas_config = {
        normalizar_data_nao_letiva(item)
        for item in datas_nao_letivas
    }

    data_completa = datetime.strptime(data, "%d/%m/%Y").strftime("%d/%m/%Y")
    data_curta = datetime.strptime(data, "%d/%m/%Y").strftime("%d/%m")

    return (
        dia_normalizado in dias_config
        or data_completa in datas_config
        or data_curta in datas_config
    )


def gerar_descricao_aula(
    aulas_por_dia: Dict[str, List[Dict[str, Any]]],
    inicio: str,
    descricao_template: str,
) -> str:
    if not aulas_por_dia:
        return descricao_template.format(
            descricoes_dia="",
            descricao_pratica="",
            dias_com_aula="",
            dias_praticos="",
        ).strip()

    descricoes_dia = []
    dias_praticos = []
    qtd_aulas_praticas = 0

    for data in ordenar_datas_curta(aulas_por_dia.keys(), inicio):
        aulas = aulas_por_dia[data]
        objetivos = []
        tem_pratica = False

        for aula in aulas:
            objetivos.append(formatar_objetivo_para_descricao(aula["objetivo"]))

            if aula["tipo"] == "Prática":
                tem_pratica = True
                qtd_aulas_praticas += 1

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

    dias_com_aula = [
        data.split("/")[0]
        for data in ordenar_datas_curta(aulas_por_dia.keys(), inicio)
    ]

    descricao_pratica = ""

    if dias_praticos:
        dias = [data.split("/")[0] for data in dias_praticos]
        dias_praticos_texto = juntar_textos(dias)
        artigo_pratica = "A aula" if qtd_aulas_praticas == 1 else "As aulas"
        verbo_pratica = "terá" if qtd_aulas_praticas == 1 else "terão"
        texto_dia = "do dia" if len(dias) == 1 else "dos dias"

        descricao_pratica = (
            f"{artigo_pratica} {texto_dia} {dias_praticos_texto} {verbo_pratica} caráter prático, "
            "visando contextualizar o que foi ministrado nas aulas anteriores, "
            "fazendo com que os alunos vivenciem o que foi estudado."
        )

    descricao = descricao_template.format(
        descricoes_dia=descricoes_dia_texto,
        descricao_pratica=descricao_pratica,
        dias_com_aula=juntar_textos(dias_com_aula),
        dias_praticos=juntar_textos([data.split("/")[0] for data in dias_praticos]),
    )

    return " ".join(descricao.split())


def calcular_data(inicio: str, dia: str) -> str:
    data_inicio = datetime.strptime(inicio, "%d/%m/%Y")
    deslocamento = DIAS[dia]
    data = data_inicio + timedelta(days=deslocamento)
    return data.strftime("%d/%m/%Y")


def normalizar_semana(valor: Any) -> Optional[int]:
    if pd.isna(valor):
        return None

    valor = str(valor).upper()
    valor = valor.replace("SEMANA", "")
    valor = valor.replace("S", "")
    valor = valor.replace(" ", "")
    valor = valor.replace(".0", "")
    valor = valor.strip()

    try:
        return int(valor)
    except ValueError:
        return None


def generate_records(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    descricao_template = config.get(
        "descricao_template",
        config.get("descricao_padrao", DESCRICAO_TEMPLATE_PADRAO),
    )

    grade_path = config["grade_horaria"]
    disciplinas = config["disciplinas"]
    arquivos = config["arquivos_escopo"]
    dias_nao_letivos = config.get("dias_nao_letivos", [])
    datas_nao_letivas = config.get("datas_nao_letivas", [])
    turmas_sufixo = config.get("turmas_sufixo", {})
    bimestre = config["bimestre"]

    grade = pd.read_excel(grade_path, dtype=str)
    registros: List[Dict[str, Any]] = []

    for item in arquivos:
        arquivo = item["arquivo"]
        turma = item["turma"]

        for aba in item["abas"]:
            df = pd.read_excel(arquivo, sheet_name=aba, dtype=str)
            df.columns = [col.strip().lower() for col in df.columns]

            coluna_semana = next(c for c in df.columns if c.strip() == "semana")
            coluna_tp = next(
                c
                for c in df.columns
                if "teórica/prática" in c
                or "teorica/pratica" in c
            )
            coluna_componente = next(c for c in df.columns if "nome do componente" in c)
            coluna_titulo = next(
                c
                for c in df.columns
                if "título da aula" in c
                or "titulo da aula" in c
            )
            coluna_habilidade = next(c for c in df.columns if "habilidades" in c)
            coluna_objetivo = next(c for c in df.columns if "objetivo" in c)

            df["semana_normalizada"] = df[coluna_semana].apply(normalizar_semana)
            df["numero_aula"] = df.groupby([coluna_componente, "semana_normalizada"]).cumcount() + 1

            for componente in disciplinas.keys():
                aulas_disciplina = df[df[coluna_componente].str.lower() == componente.lower()].copy()

                if aulas_disciplina.empty:
                    continue

                dados = disciplinas[componente]
                ultima_semana = dados["ultima_semana"]
                ultima_aula = dados["ultima_aula"]
                ultimo_inicio = datetime.strptime(dados["ultimo_inicio_planejamento"], "%d/%m/%Y")

                dias_para_segunda = (7 - ultimo_inicio.weekday()) % 7
                if dias_para_segunda == 0:
                    dias_para_segunda = 7

                novo_inicio = ultimo_inicio + timedelta(days=dias_para_segunda)
                novo_fim = novo_inicio + timedelta(days=4)
                inicio = novo_inicio.strftime("%d/%m/%Y")
                fim = novo_fim.strftime("%d/%m/%Y")

                aulas_disciplina = (
                    aulas_disciplina.sort_values(by=["semana_normalizada", "numero_aula"]).reset_index(drop=True)
                )

                posicao = aulas_disciplina[
                    (aulas_disciplina["semana_normalizada"] == int(ultima_semana))
                    & (aulas_disciplina["numero_aula"] == int(ultima_aula))
                ]

                if posicao.empty:
                    continue

                indice_atual = posicao.index[0]
                aulas_grade = grade[(grade["Turma"] == turma) & (grade["Disciplina"] == componente)]

                if aulas_grade.empty:
                    continue

                qtd_aulas_letivas = 0
                for _, aula_grade in aulas_grade.iterrows():
                    data_grade = calcular_data(inicio, aula_grade["Dia"])
                    if not eh_dia_nao_letivo(aula_grade["Dia"], data_grade, dias_nao_letivos, datas_nao_letivas):
                        qtd_aulas_letivas += 1

                proximas = aulas_disciplina.iloc[indice_atual + 1 : indice_atual + 1 + qtd_aulas_letivas]
                if qtd_aulas_letivas > 0 and proximas.empty:
                    continue

                registro: Dict[str, Any] = {
                    "InicioPlanejamento": inicio,
                    "FimPlanejamento": fim,
                    "ComponenteCurricular": componente.upper(),
                    "AnoSérie": turmas_sufixo.get(turma, f"{turma} F"),
                    "Bimestre": bimestre,
                    "DataElaboração": datetime.now().strftime("%d/%m/%Y"),
                    "DescriçãoAula": "",
                    "QtdeAulas": qtd_aulas_letivas,
                }

                habilidades: List[str] = []
                aulas_por_dia: Dict[str, List[Dict[str, Any]]] = {}
                num_aula_por_dia: Dict[str, List[str]] = {}
                indice_proxima = 0

                for _, aula_grade in aulas_grade.iterrows():
                    dia_semana = aula_grade["Dia"]
                    data = calcular_data(inicio, dia_semana)
                    data_curta = datetime.strptime(data, "%d/%m/%Y").strftime("%d/%m")

                    num_aula_por_dia.setdefault(data_curta, [])

                    if eh_dia_nao_letivo(dia_semana, data, dias_nao_letivos, datas_nao_letivas):
                        num_aula_por_dia[data_curta].append("Dia não letivo")
                        continue

                    if indice_proxima >= len(proximas):
                        continue

                    aula = proximas.iloc[indice_proxima]
                    semana = int(aula["semana_normalizada"]) if pd.notna(aula["semana_normalizada"]) else None
                    numero = int(aula["numero_aula"]) if pd.notna(aula["numero_aula"]) else None
                    tipo = "Prática" if aula[coluna_tp] == "P" else "Teórica"
                    texto = f"S{semana} Aula {numero} {tipo}"

                    num_aula_por_dia[data_curta].append(texto)
                    aulas_por_dia.setdefault(data_curta, []).append(
                        {
                            "texto": texto,
                            "tipo": tipo,
                            "objetivo": aula[coluna_objetivo],
                        }
                    )

                    registro[f"Conteudo{indice_proxima + 1}"] = (
                        f"S{semana} Aula {numero}: "
                        + re.sub(
                            r'^aula\s+\d+:\s*',
                            '',
                            str(aula[coluna_titulo]).strip(),
                            flags=re.IGNORECASE,
                        )
                    )
                    registro[f"ObjetivosAprendizagem{indice_proxima + 1}"] = aula[coluna_objetivo]
                    habilidades.append(str(aula[coluna_habilidade]))
                    indice_proxima += 1

                linhas_num_aula = []
                for data in ordenar_datas_curta(num_aula_por_dia.keys(), inicio):
                    aulas = num_aula_por_dia[data]
                    linhas_num_aula.append(f"{data} - " + ", ".join(aulas))

                if linhas_num_aula:
                    registro["NumAulaES1"] = linhas_num_aula[0]
                if len(linhas_num_aula) > 1:
                    registro["NumAulaES2"] = "\n".join(linhas_num_aula[1:])

                registro["DescriçãoAula"] = gerar_descricao_aula(aulas_por_dia, inicio, descricao_template)
                registro["Habilidades"] = "\n".join(dict.fromkeys(habilidades))
                registros.append(registro)

                if indice_proxima > 0:
                    ultima = proximas.iloc[indice_proxima - 1]
                    disciplinas[componente]["ultima_semana"] = int(ultima["semana_normalizada"])
                    disciplinas[componente]["ultima_aula"] = int(ultima["numero_aula"])
                    disciplinas[componente]["ultimo_inicio_planejamento"] = inicio

    return registros


def generate_planning_from_dict(
    config: Dict[str, Any],
    output_path: str,
    save_config: bool = False,
    config_path: Optional[str] = None,
) -> str:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.exists():
        output_file.unlink()

    registros = generate_records(config)
    df_final = pd.DataFrame(registros)

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
        "DataElaboração",
    ]

    df_final = df_final[[col for col in colunas_ordem if col in df_final.columns]]

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_final.to_excel(writer, index=False)

    if save_config and config_path:
        with open(config_path, "w", encoding="utf-8") as arquivo:
            json.dump(config, arquivo, ensure_ascii=False, indent=4)

    return str(output_file)


def generate_planning(
    config_path: str,
    output_path: str = "saida/base_maladireta.xlsx",
    save_config: bool = False,
) -> str:
    config = load_config(config_path)
    return generate_planning_from_dict(
        config,
        output_path=output_path,
        save_config=save_config,
        config_path=config_path,
    )
