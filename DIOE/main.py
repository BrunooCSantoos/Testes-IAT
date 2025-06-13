import baixar_e_ler_dioe
import expresso_funcoes as ef
from informacoes import extrair_e_salvar_informacoes_dioe
import os

caminho_diretorio = os.getcwd()

# Adiciona um parâmetro de callback para reportar o status
def iniciar(status_callback=None):
    if status_callback:
        status_callback("Iniciando processo de e-mail...")

    # Baixa e faz a leitura do diário, gerando os resultados em txt.
    if status_callback:
        status_callback("Baixando e lendo o diário...")
    numero_diario, arquivos_txt_para_processar = baixar_e_ler_dioe.start(caminho_diretorio)
    if status_callback:
        status_callback(f"Diário número {numero_diario} processado. Arquivos TXT gerados.")

    # Extrair informações e salvar em CSV e PDF
    if status_callback:
        status_callback("Extraindo informações e salvando em CSV e PDF...")
    anexos_pdf_gerados = extrair_e_salvar_informacoes_dioe(caminho_diretorio, arquivos_txt_para_processar, numero_diario)
    if status_callback:
        status_callback(f"{len(anexos_pdf_gerados)} PDFs gerados.")

    if len(anexos_pdf_gerados) > 0:
        if status_callback:
            status_callback("Iniciando processo de envio de e-mail Expresso...")
        # A função email_expresso agora espera login e senha.
        # Estes serão passados pelo chamador (GUI).
        # Por simplicidade, assumimos que a GUI já lidou com isso ou que ef.email_expresso
        # foi temporariamente adaptado para usar as credenciais salvas antes desta chamada.
        ef.email_expresso() # Esta chamada agora usará as credenciais passadas ou as do patch temporário
        ef.novo_email()
        if status_callback:
            status_callback("Novo e-mail iniciado.")

        # O gerenciamento de destinatários será tratado pela nova GUI, passando-os dinamicamente
        # Por enquanto, mantenha hardcoded para demonstração, mas isso mudará.
        # Esta parte será alimentada pelos destinatários salvos da GUI.
        destinatarios = {
            "ter.brunokawan@iat.pr.gov.br",
            "gleiserdossantos@iat.pr.gov.br"
        }

        if status_callback:
            status_callback(f"Inserindo destinatários: {', '.join(destinatarios)}")
        ef.inserir_destinatarios(destinatarios)
        
        if status_callback:
            status_callback("Inserindo assunto: Teste")
        ef.inserir_assunto("Teste")
        
        # Inserir todos os PDFs gerados como anexos
        if status_callback:
            status_callback("Anexando PDFs...")
        for anexo in anexos_pdf_gerados:
            ef.inserir_anexos(anexo)
            if status_callback:
                status_callback(f"Anexado: {os.path.basename(anexo)}")
            
        if status_callback:
            status_callback("Inserindo texto do e-mail.")
        ef.inserir_texto("Teste")
        
        if status_callback:
            status_callback("Adicionando assinatura.")
        ef.assinatura()
        
        if status_callback:
            status_callback("Enviando e-mail...")
        ef.enviar_email()

        print("\n\nEmail enviado\n")
        if status_callback:
            status_callback("E-mail enviado com sucesso!")

        # Opcional: Remover os arquivos TXT temporários após a geração dos PDFs e envio do email
        if status_callback:
            status_callback("Removendo arquivos temporários...")
        for txt_file in arquivos_txt_para_processar:
            if os.path.exists(txt_file):
                try:
                    os.remove(txt_file)
                    if status_callback:
                        status_callback(f"Arquivo TXT temporário removido: {os.path.basename(txt_file)}")
                except Exception as e:
                    if status_callback:
                        status_callback(f"Erro ao remover arquivo TXT temporário '{os.path.basename(txt_file)}': {e}")
        for anexo in anexos_pdf_gerados:
            if os.path.exists(anexo):
                try:
                    os.remove(anexo)
                    if status_callback:
                        status_callback(f"Arquivo PDF temporário removido: {os.path.basename(anexo)}")
                except Exception as e:
                    if status_callback:
                        status_callback(f"Erro ao remover arquivo PDF temporário '{os.path.basename(anexo)}': {e}")
        if status_callback:
            status_callback("Processo concluído.")
    else:
        if status_callback:
            status_callback("Nenhum PDF gerado. E-mail não enviado.")

if __name__ == "__main__":
    # Para testes autônomos, você pode fornecer um callback dummy
    def dummy_callback(status):
        print(f"STATUS: {status}")
    iniciar(dummy_callback)