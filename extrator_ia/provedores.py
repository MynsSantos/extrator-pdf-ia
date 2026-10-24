"""Provedores de extração. Todos recebem texto + esquema e devolvem um dict.

* ``ClaudeProvider`` — usa a API da Anthropic (requer ``ANTHROPIC_API_KEY``).
* ``RegexProvider``  — heurística local, sem IA, para rodar a demo e os testes offline.

Para trocar de fornecedor de IA basta implementar ``Provedor.extrair``.
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod

from pydantic import BaseModel

PROMPT_SISTEMA = (
    "Você extrai dados de documentos fiscais brasileiros. "
    "Responda SOMENTE com um objeto JSON válido que siga o JSON Schema informado. "
    "Use ponto como separador decimal, datas em AAAA-MM-DD e não invente valores: "
    "se um campo de retenção não aparecer no documento, use 0."
)


class Provedor(ABC):
    nome: str

    @abstractmethod
    def extrair(self, texto: str, esquema: type[BaseModel], feedback: str | None = None) -> dict: ...


def _json_da_resposta(resposta: str) -> dict:
    """Aceita JSON puro ou dentro de bloco ```json```."""
    bloco = re.search(r"\{.*\}", resposta, re.DOTALL)
    if not bloco:
        raise ValueError("A resposta da IA não contém JSON")
    return json.loads(bloco.group())


class ClaudeProvider(Provedor):
    nome = "claude"

    def __init__(self, modelo: str | None = None):
        import anthropic  # import tardio: só exige a lib quando o provedor é usado

        self.cliente = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente
        self.modelo = modelo or os.getenv("AI_MODEL", "claude-sonnet-5-5")

    def extrair(self, texto: str, esquema: type[BaseModel], feedback: str | None = None) -> dict:
        conteudo = (
            f"JSON Schema:\n{json.dumps(esquema.model_json_schema(), ensure_ascii=False)}\n\n"
            f"Documento:\n<<<\n{texto}\n>>>"
        )
        if feedback:
            conteudo += f"\n\nSua resposta anterior falhou na validação: {feedback}\nCorrija e responda de novo."
        resposta = self.cliente.messages.create(
            model=self.modelo,
            max_tokens=2000,
            system=PROMPT_SISTEMA,
            messages=[{"role": "user", "content": conteudo}],
        )
        return _json_da_resposta(resposta.content[0].text)


class RegexProvider(Provedor):
    """Extração por regras para o layout dos PDFs de exemplo (modo offline)."""

    nome = "regex"

    @staticmethod
    def _valor(rotulo: str, texto: str) -> str:
        m = re.search(rf"{rotulo}\s*:?\s*R?\$?\s*([\d.]+,\d{{2}})", texto, re.IGNORECASE)
        return m.group(1).replace(".", "").replace(",", ".") if m else "0"

    @staticmethod
    def _campo(rotulo: str, texto: str) -> str:
        m = re.search(rf"{rotulo}\s*:\s*(.+)", texto, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    def extrair(self, texto: str, esquema: type[BaseModel], feedback: str | None = None) -> dict:
        dia, mes, ano = self._campo("Data de emiss[aã]o", texto).split("/")
        return {
            "numero": self._campo("N[uú]mero da nota", texto),
            "data_emissao": f"{ano}-{mes}-{dia}",
            "prestador": {
                "razao_social": self._campo("Prestador", texto),
                "cnpj": self._campo("CNPJ do prestador", texto),
            },
            "tomador": {
                "razao_social": self._campo("Tomador", texto),
                "cnpj": self._campo("CNPJ do tomador", texto),
            },
            "descricao_servico": self._campo("Discrimina[cç][aã]o", texto),
            "valor_servicos": self._valor("Valor dos servi[cç]os", texto),
            "retencoes": {
                imposto.lower(): self._valor(f"{imposto} retido", texto)
                for imposto in ("ISS", "INSS", "IRRF", "PIS", "COFINS", "CSLL")
            },
            "valor_liquido": self._valor("Valor l[ií]quido", texto),
        }


def criar_provedor(nome: str) -> Provedor:
    if nome == "claude":
        return ClaudeProvider()
    if nome == "regex":
        return RegexProvider()
    raise ValueError(f"Provedor desconhecido: {nome}")
