"""Pipeline: PDF → texto → IA → validação Pydantic (com 1 nova tentativa) → resultado."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from pydantic import BaseModel, ValidationError

from .provedores import Provedor

logger = logging.getLogger(__name__)

MIN_CARACTERES = 50  # abaixo disso o PDF provavelmente é imagem (precisa de OCR)


@dataclass
class Resultado:
    arquivo: str
    status: str                 # sucesso | sem_texto | falha_validacao | erro
    dados: dict | None = None
    detalhe: str | None = None
    tentativas: int = 0


def extrair_texto(caminho: Path) -> str:
    with pymupdf.open(caminho) as doc:
        return "\n".join(p.get_text() for p in doc).strip()


def processar_arquivo(caminho: Path, provedor: Provedor, esquema: type[BaseModel], max_tentativas: int = 2) -> Resultado:
    try:
        texto = extrair_texto(caminho)
    except Exception as exc:
        return Resultado(caminho.name, "erro", detalhe=f"Falha ao abrir PDF: {exc}")

    if len(texto) < MIN_CARACTERES:
        return Resultado(caminho.name, "sem_texto", detalhe="PDF sem camada de texto — aplicar OCR antes")

    feedback = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            bruto = provedor.extrair(texto, esquema, feedback)
            modelo = esquema.model_validate(bruto)
            return Resultado(caminho.name, "sucesso", dados=modelo.model_dump(mode="json"), tentativas=tentativa)
        except ValidationError as exc:
            feedback = "; ".join(
                f"{'.'.join(map(str, e['loc'])) or 'documento'}: {e['msg']}" for e in exc.errors()
            )
            logger.info("%s: validação falhou na tentativa %d (%s)", caminho.name, tentativa, feedback)
        except Exception as exc:  # erro de rede, JSON malformado etc.
            feedback = str(exc)
            logger.warning("%s: erro na tentativa %d: %s", caminho.name, tentativa, exc)

    return Resultado(caminho.name, "falha_validacao", detalhe=feedback, tentativas=max_tentativas)


def processar_pasta(pasta: Path, provedor: Provedor, esquema: type[BaseModel]) -> list[Resultado]:
    pdfs = sorted(p for p in pasta.iterdir() if p.suffix.lower() == ".pdf")
    logger.info("Processando %d PDF(s) com o provedor '%s'", len(pdfs), provedor.nome)
    return [processar_arquivo(p, provedor, esquema) for p in pdfs]
