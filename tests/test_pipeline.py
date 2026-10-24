import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from extrator_ia.pipeline import processar_arquivo, processar_pasta
from extrator_ia.provedores import Provedor, RegexProvider, _json_da_resposta
from extrator_ia.schemas import NotaFiscalServico

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLOS = RAIZ / "exemplos"


@pytest.fixture(scope="session", autouse=True)
def gerar_exemplos():
    subprocess.run([sys.executable, str(RAIZ / "scripts" / "gerar_exemplos.py")], check=True)


def test_regex_extrai_nota_valida():
    r = processar_arquivo(EXEMPLOS / "nfse_2026000123.pdf", RegexProvider(), NotaFiscalServico)
    assert r.status == "sucesso"
    assert Decimal(r.dados["valor_liquido"]) == Decimal("8085.00")
    assert r.dados["prestador"]["cnpj"] == "12.345.678/0001-00"


def test_nota_inconsistente_falha_na_validacao():
    r = processar_arquivo(EXEMPLOS / "nfse_77.pdf", RegexProvider(), NotaFiscalServico)
    assert r.status == "falha_validacao"
    assert "valor_liquido" in r.detalhe


def test_pdf_escaneado_sem_texto():
    r = processar_arquivo(EXEMPLOS / "documento_escaneado.pdf", RegexProvider(), NotaFiscalServico)
    assert r.status == "sem_texto"


def test_processa_pasta_inteira():
    status = {r.arquivo: r.status for r in processar_pasta(EXEMPLOS, RegexProvider(), NotaFiscalServico)}
    assert list(status.values()).count("sucesso") == 2


class ProvedorQueErraNaPrimeira(Provedor):
    """Simula a IA devolvendo JSON inválido e corrigindo após o feedback."""

    nome = "fake"

    def __init__(self):
        self.feedbacks = []
        self.base = RegexProvider()

    def extrair(self, texto, esquema, feedback=None):
        self.feedbacks.append(feedback)
        dados = self.base.extrair(texto, esquema)
        if feedback is None:
            dados["prestador"]["cnpj"] = "123"  # erro proposital
        return dados


def test_nova_tentativa_envia_feedback_da_validacao():
    provedor = ProvedorQueErraNaPrimeira()
    r = processar_arquivo(EXEMPLOS / "nfse_845.pdf", provedor, NotaFiscalServico)
    assert r.status == "sucesso" and r.tentativas == 2
    assert "cnpj" in provedor.feedbacks[1]


def test_json_dentro_de_bloco_markdown():
    assert _json_da_resposta('Aqui está:\n```json\n{"a": 1}\n```') == {"a": 1}
