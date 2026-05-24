import re
import sys

import pandas as pd

from rapidfuzz import fuzz

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# =====================================
# ARQUIVOS
# =====================================

ARQUIVO_MODELO = (
    "modelo/planejamento_modelo.xlsx"
)

ARQUIVO_GERADO = (
    "saida/base_maladireta.xlsx"
)

# =====================================
# CONFIGURAÇÕES
# =====================================

LIMIAR_SIMILARIDADE = 90

# =====================================
# LER PLANILHAS
# =====================================

modelo = pd.read_excel(
    ARQUIVO_MODELO
)

gerado = pd.read_excel(
    ARQUIVO_GERADO
)

# =====================================
# NORMALIZAR TEXTO
# =====================================

def normalizar(valor):

    if pd.isna(valor):
        return ""

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%d/%m/%Y")

    valor = str(valor)

    valor = valor.strip()

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}( 00:00:00)?", valor):
        return pd.to_datetime(valor).strftime("%d/%m/%Y")

    valor = valor.replace(
        "\n",
        " "
    )

    valor = " ".join(valor.split())

    return valor.lower()

# =====================================
# VALIDAR COLUNAS
# =====================================

print("\n====================================")
print("VALIDANDO ESTRUTURA")
print("====================================\n")

colunas_modelo = list(modelo.columns)
colunas_gerado = list(gerado.columns)

if colunas_modelo == colunas_gerado:

    print("✔ Colunas iguais")

else:

    print("❌ Estrutura diferente")

    print("\nMODELO:\n")
    print(colunas_modelo)

    print("\nGERADO:\n")
    print(colunas_gerado)

# =====================================
# VALIDAR QUANTIDADE DE LINHAS
# =====================================

print("\n====================================")
print("VALIDANDO LINHAS")
print("====================================\n")

if len(modelo) == len(gerado):

    print(
        f"✔ Quantidade de linhas igual: {len(modelo)}"
    )

else:

    print(
        f"❌ Modelo possui {len(modelo)} linhas "
        f"e gerado possui {len(gerado)}"
    )

# =====================================
# COMPARAÇÃO CÉLULA POR CÉLULA
# =====================================

print("\n====================================")
print("VALIDANDO CONTEÚDO")
print("====================================\n")

colunas_importantes = [

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

    "ObjetivosAprendizagem1",
    "ObjetivosAprendizagem2",
    "ObjetivosAprendizagem3",
    "ObjetivosAprendizagem4",

    "Habilidades",

    "QtdeAulas",
    "DescriçãoAula",
    "DataElaboração"
]

resultado_geral = []

for linha in range(
    min(
        len(modelo),
        len(gerado)
    )
):

    print(f"\nLINHA {linha + 2}\n")

    similaridades = []

    for coluna in colunas_importantes:

        if (
            coluna not in modelo.columns
            or coluna not in gerado.columns
        ):
            continue

        valor_modelo = normalizar(
            modelo.loc[linha, coluna]
        )

        valor_gerado = normalizar(
            gerado.loc[linha, coluna]
        )

        similaridade = fuzz.ratio(
            valor_modelo,
            valor_gerado
        )

        similaridades.append(
            similaridade
        )

        if similaridade >= LIMIAR_SIMILARIDADE:

            print(
                f"✔ {coluna} -> {similaridade}%"
            )

        else:

            print(
                f"❌ {coluna} -> {similaridade}%"
            )

            print(
                f"MODELO: {valor_modelo}"
            )

            print(
                f"GERADO: {valor_gerado}"
            )

            print()

    media = (
        sum(similaridades)
        / len(similaridades)
    )

    resultado_geral.append(media)

    print(
        f"\nSimilaridade média: "
        f"{media:.2f}%"
    )

# =====================================
# RESULTADO FINAL
# =====================================

print("\n====================================")
print("RESULTADO FINAL")
print("====================================\n")

media_geral = (
    sum(resultado_geral)
    / len(resultado_geral)
)

print(
    f"Similaridade geral: "
    f"{media_geral:.2f}%"
)

if media_geral >= LIMIAR_SIMILARIDADE:

    print(
        "\n✔ Planejamento muito próximo do modelo"
    )

else:

    print(
        "\n❌ Planejamento diferente do modelo"
    )
