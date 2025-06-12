import baixar_e_ler_dioe
import expresso_funcoes as ef
from informacoes import extrair_e_salvar_informacoes_dioe # Importe a nova função
import os
import glob

caminho_diretorio = os.getcwd()

def iniciar():
    # Baixa e faz a leitura do diário, gerando os resultados em txt.
    numero_diario, arquivos_txt = baixar_e_ler_dioe.start(caminho_diretorio)

    # Extrair informações e salvar em CSV e PDF
    anexo = extrair_e_salvar_informacoes_dioe(caminho_diretorio, arquivos_txt, numero_diario)

    # Envia email com anexos.
    ef.email_expresso()
    ef.novo_email()

    destinatarios = {
        "ter.brunokawan@iat.pr.gov.br",
        "gleiserdossantos@iat.pr.gov.br"
    }

    ef.inserir_destinatarios(destinatarios)
    ef.inserir_assunto("Teste")
    ef.inserir_anexos(anexo)
    ef.inserir_texto("Teste")
    ef.assinatura()
    ef.enviar_email()

    print("\n\nEmail enviado\n")

if __name__ == "__main__":
    iniciar() 