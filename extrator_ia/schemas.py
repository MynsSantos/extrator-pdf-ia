"""Esquemas de saída. A IA precisa devolver exatamente estes campos — o Pydantic valida."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

_CNPJ = re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")


class Parte(BaseModel):
    razao_social: str
    cnpj: str = Field(description="Formato 00.000.000/0000-00")

    @field_validator("cnpj")
    @classmethod
    def formatar_cnpj(cls, v: str) -> str:
        digitos = re.sub(r"\D", "", v)
        if len(digitos) != 14:
            raise ValueError("CNPJ deve ter 14 dígitos")
        formatado = f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"
        assert _CNPJ.match(formatado)
        return formatado


class Retencoes(BaseModel):
    iss: Decimal = Decimal("0")
    inss: Decimal = Decimal("0")
    irrf: Decimal = Decimal("0")
    pis: Decimal = Decimal("0")
    cofins: Decimal = Decimal("0")
    csll: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return self.iss + self.inss + self.irrf + self.pis + self.cofins + self.csll


class NotaFiscalServico(BaseModel):
    """Campos principais de uma NFS-e."""

    numero: str
    data_emissao: date
    prestador: Parte
    tomador: Parte
    descricao_servico: str
    valor_servicos: Decimal = Field(gt=0)
    retencoes: Retencoes = Retencoes()
    valor_liquido: Decimal

    @model_validator(mode="after")
    def conferir_liquido(self) -> "NotaFiscalServico":
        esperado = self.valor_servicos - self.retencoes.total
        if abs(esperado - self.valor_liquido) > Decimal("0.05"):
            raise ValueError(
                f"valor_liquido ({self.valor_liquido}) não bate com serviços - retenções ({esperado})"
            )
        return self


ESQUEMAS: dict[str, type[BaseModel]] = {
    "nfse": NotaFiscalServico,
}
