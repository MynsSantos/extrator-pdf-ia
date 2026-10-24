"""CLI: python -m extrator_ia <pasta> [--provedor regex|claude] [--saida output/]"""

import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from .pipeline import processar_pasta
from .provedores import criar_provedor
from .schemas import ESQUEMAS


def _linha_planilha(r) -> dict:
    linha = {"arquivo": r.arquivo, "status": r.status, "detalhe": r.detalhe}
    if r.dados:
        linha.update(pd.json_normalize(r.dados, sep="_").iloc[0].to_dict())
    return linha


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Extrai dados estruturados de PDFs usando IA.")
    parser.add_argument("pasta", type=Path)
    parser.add_argument("--provedor", default="regex", choices=["regex", "claude"])
    parser.add_argument("--esquema", default="nfse", choices=list(ESQUEMAS))
    parser.add_argument("--saida", type=Path, default=Path("output"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    resultados = processar_pasta(args.pasta, criar_provedor(args.provedor), ESQUEMAS[args.esquema])

    args.saida.mkdir(parents=True, exist_ok=True)
    (args.saida / "resultado.json").write_text(
        json.dumps([asdict(r) for r in resultados], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame([_linha_planilha(r) for r in resultados]).to_excel(args.saida / "resultado.xlsx", index=False)

    ok = sum(r.status == "sucesso" for r in resultados)
    print(f"{ok}/{len(resultados)} documento(s) extraído(s) com sucesso → {args.saida}/")


if __name__ == "__main__":
    main()
