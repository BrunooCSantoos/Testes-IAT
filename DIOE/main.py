import baixar_e_ler_dioe
import expresso_funcoes as ef
from informacoes import extrair_e_salvar_informacoes_dioe # Importe a nova função
import os

caminho_diretorio = os.getcwd()

def iniciar():
    # Baixa e faz a leitura do diário, gerando os resultados em txt.
    numero_diario, arquivos_txt_para_processar = baixar_e_ler_dioe.start(caminho_diretorio)

    # Extrair informações e salvar em CSV e PDF
    # 'anexos_pdf_gerados' agora será uma lista de caminhos para os PDFs
    anexos_pdf_gerados = extrair_e_salvar_informacoes_dioe(caminho_diretorio, arquivos_txt_para_processar, numero_diario)

    if len(anexos_pdf_gerados) > 0:
        # Envia email com anexos.
        ef.email_expresso()
        ef.novo_email()

        destinatarios = {
            "ter.brunokawan@iat.pr.gov.br",
            "gleiserdossantos@iat.pr.gov.br"
        }

        ef.inserir_destinatarios(destinatarios)
        ef.inserir_assunto("Teste")
        
        # Inserir todos os PDFs gerados como anexos
        for anexo_path in anexos_pdf_gerados:
            ef.inserir_anexos(anexo_path)
            
        ef.inserir_texto("Teste")
        ef.assinatura()
        ef.enviar_email()

        print("\n\nEmail enviado\n")

        # Opcional: Remover os arquivos TXT temporários após a geração dos PDFs e envio do email
        for txt_file in arquivos_txt_para_processar:
            if os.path.exists(txt_file):
                try:
                    os.remove(txt_file)
                    print(f"Arquivo TXT temporário removido: {txt_file}")
                except Exception as e:
                    print(f"Erro ao remover arquivo TXT temporário '{txt_file}': {e}")
        
        os.remove(anexos_pdf_gerados)

if __name__ == "__main__":
    iniciar()