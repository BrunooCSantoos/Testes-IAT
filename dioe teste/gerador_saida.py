import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import os

def criar_csv_a_partir_dados(lista_dados, caminho_csv_saida="informacoes_documentos.csv"):
    """
    Cria um arquivo CSV a partir de uma lista de dicionários de dados.
    Cada dicionário representa um documento (Portaria/Decreto).
    """
    if not lista_dados:
        print("Nenhum dado para gerar CSV.")
        return

    df = pd.DataFrame(lista_dados)
    df.to_csv(caminho_csv_saida, index=False, encoding='utf-8')
    print(f"Informações salvas em CSV: {caminho_csv_saida}")

def criar_pdf_resumo(lista_dados, caminho_pdf_saida="resumo_documentos.pdf"):
    """
    Cria um PDF de resumo com as informações chave para envio por e-mail.
    Agora, lista as informações de cada documento encontrado.
    """
    if not lista_dados:
        print("Nenhum dado para gerar PDF de resumo.")
        return

    doc = SimpleDocTemplate(caminho_pdf_saida, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Resumo das Informações dos Documentos", styles['h1']))
    story.append(Spacer(1, 0.2 * letter[1]))

    for i, dados in enumerate(lista_dados):
        story.append(Paragraph(f"<b>Documento {i+1}:</b>", styles['h3']))
        
        # Filtrar apenas os campos que você quer mostrar e na ordem desejada
        campos_para_mostrar = [
            "Tipo do Documento",
            "Número do Documento",
            "Situação",
            "Nome",
            "Cargo",
            "Data da Edição",
            "Número da Edição",
            "CNPJ"
        ]

        for campo in campos_para_mostrar:
            valor = dados.get(campo)
            if valor is not None:
                story.append(Paragraph(f"<b>{campo}:</b> {valor}", styles['Normal']))
        story.append(Spacer(1, 0.2 * letter[1])) # Espaço entre documentos

    try:
        doc.build(story)
        print(f"PDF de resumo criado: {caminho_pdf_saida}")
    except Exception as e:
        print(f"Erro ao gerar PDF de resumo: {e}")