import baixar_e_ler_dioe
import expresso_funcoes as ef
from informacoes import converter_txt_para_pdf, extrair_e_salvar_informacoes_dioe # Importe a nova função
from datetime import date
import os
import glob

caminho_diretorio = os.getcwd()

def iniciar():
    # Baixa e faz a leitura do diário, gerando os resultados em txt.
    baixar_e_ler_dioe.start(caminho_diretorio)

    # NOVO PASSO: Extrair informações e salvar em CSV e TXT formatado
    extrair_e_salvar_informacoes_dioe(caminho_diretorio)
    
    # Adiciona o arquivo TXT formatado para a conversão em PDF
    caminho_txt_formatado_para_pdf = os.path.join(caminho_diretorio, "informacoes_formatadas_para_pdf.txt")
    
    caminho_arquivo_pdf = os.path.join(caminho_diretorio, f"Diário.pdf")
    converter_txt_para_pdf(caminho_txt_formatado_para_pdf, caminho_arquivo_pdf) # Passa a lista completa

    # Converte os resultados de txt para pdf.
    # Agora, além dos arquivos EX_*.txt, também incluímos o TXT formatado
    padrao_arquivo_txt = f"{caminho_diretorio}\\EX*.txt"
    arquivos_txt_originais = glob.glob(padrao_arquivo_txt)

    # Envia email com anexos.
    ef.email_expresso()
    ef.novo_email()

    destinatarios = {
        "ter.brunokawan@iat.pr.gov.br"
    }

    ef.inserir_destinatarios(destinatarios)
    ef.inserir_assunto("teste")
    ef.inserir_anexos(caminho_arquivo_pdf)
    ef.inserir_texto("Teste")
    ef.assinatura()
    ef.enviar_email()

if __name__ == "__main__":
    iniciar()