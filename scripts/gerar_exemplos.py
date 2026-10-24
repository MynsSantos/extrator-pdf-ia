"""Gera NFS-e 100% fictícias em exemplos/ (empresas, CNPJs e valores inventados)."""

from pathlib import Path

import pymupdf

PASTA = Path(__file__).resolve().parents[1] / "exemplos"

NOTAS = [
    dict(numero="2026000123", emissao="05/10/2026", prestador="Alfa Consultoria Ficticia LTDA",
         cnpj_p="12.345.678/0001-00", tomador="Empresa Exemplo Industria S.A.", cnpj_t="98.765.432/0001-00",
         descricao="Consultoria em processos financeiros - outubro/2026", valor="10.000,00",
         iss="200,00", inss="1.100,00", irrf="150,00", pis="65,00", cofins="300,00", csll="100,00",
         liquido="8.085,00"),
    dict(numero="845", emissao="12/10/2026", prestador="Beta Manutencao Predial ME",
         cnpj_p="11.222.333/0001-00", tomador="Empresa Exemplo Industria S.A.", cnpj_t="98.765.432/0001-00",
         descricao="Manutencao preventiva de ar-condicionado", valor="2.500,00",
         iss="125,00", inss="275,00", irrf="0,00", pis="0,00", cofins="0,00", csll="0,00",
         liquido="2.100,00"),
    # Nota com valor líquido inconsistente: deve falhar na validação.
    dict(numero="77", emissao="15/10/2026", prestador="Gama Servicos de Limpeza LTDA",
         cnpj_p="44.555.666/0001-00", tomador="Empresa Exemplo Industria S.A.", cnpj_t="98.765.432/0001-00",
         descricao="Servicos de limpeza - outubro/2026", valor="4.000,00",
         iss="80,00", inss="440,00", irrf="60,00", pis="0,00", cofins="0,00", csll="0,00",
         liquido="3.900,00"),
]


def criar_nota(n: dict) -> None:
    linhas = [
        "NOTA FISCAL DE SERVICOS ELETRONICA - DOCUMENTO FICTICIO",
        f"Numero da nota: {n['numero']}",
        f"Data de emissao: {n['emissao']}",
        f"Prestador: {n['prestador']}",
        f"CNPJ do prestador: {n['cnpj_p']}",
        f"Tomador: {n['tomador']}",
        f"CNPJ do tomador: {n['cnpj_t']}",
        f"Discriminacao: {n['descricao']}",
        f"Valor dos servicos: R$ {n['valor']}",
        f"ISS retido: R$ {n['iss']}",
        f"INSS retido: R$ {n['inss']}",
        f"IRRF retido: R$ {n['irrf']}",
        f"PIS retido: R$ {n['pis']}",
        f"COFINS retido: R$ {n['cofins']}",
        f"CSLL retido: R$ {n['csll']}",
        f"Valor liquido: R$ {n['liquido']}",
    ]
    doc = pymupdf.open()
    pagina = doc.new_page()
    for i, texto in enumerate(linhas):
        pagina.insert_text((50, 72 + i * 20), texto, fontsize=10)
    doc.save(PASTA / f"nfse_{n['numero']}.pdf")
    doc.close()


def criar_pdf_escaneado() -> None:
    """PDF só com imagem (sem camada de texto) para demonstrar o status 'sem_texto'."""
    doc = pymupdf.open()
    pagina = doc.new_page()
    pagina.draw_rect(pymupdf.Rect(50, 50, 400, 300), color=(0, 0, 0), fill=(0.9, 0.9, 0.9))
    doc.save(PASTA / "documento_escaneado.pdf")
    doc.close()


if __name__ == "__main__":
    PASTA.mkdir(exist_ok=True)
    for nota in NOTAS:
        criar_nota(nota)
    criar_pdf_escaneado()
    print(f"Exemplos gerados em {PASTA}")
