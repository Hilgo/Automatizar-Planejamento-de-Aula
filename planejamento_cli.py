from planejamento import generate_planning


if __name__ == "__main__":
    output_path = "saida/base_maladireta.xlsx"
    result_path = generate_planning(
        config_path="config.json",
        output_path=output_path,
        save_config=False,
    )
    print(f"OK: Planilha gerada em {result_path}")
