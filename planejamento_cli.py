import sys

from planejamento import PlanningValidationError, generate_planning


if __name__ == "__main__":
    output_path = "saida/base_maladireta.xlsx"
    try:
        result_path = generate_planning(
            config_path="config.json",
            output_path=output_path,
            save_config=False,
        )
    except PlanningValidationError as exc:
        print(f"Erro ao gerar o planejamento:\n{exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"OK: Planilha gerada em {result_path}")
