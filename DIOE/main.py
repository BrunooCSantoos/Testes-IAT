import baixar_e_ler_dioe
import DIOE.expresso_dioe as ef
from informacoes import extrair_e_salvar_informacoes_dioe
import os
from datetime import datetime # Importar para usar a data atual

caminho_diretorio = os.getcwd()

def iniciar(update_status_gui=None, destinatarios_email=None, assunto_email=None, texto_email=None):
    if update_status_gui is None:
        update_status_gui = print

    numero_diario = None
    data_diario_final = None
    arquivos_txt_para_processar = []
    anexos_pdf_gerados = []
    
    try:
        update_status_gui("Iniciando o download e leitura do diário...")
        
        try:
            numero_diario, data_diario_original, arquivos_txt_para_processar = baixar_e_ler_dioe.start(caminho_diretorio)
            data_diario_objeto = datetime.strptime(data_diario_original, "%Y-%m-%d")
            data_diario_final = data_diario_objeto.strftime("%d-%m-%Y")
            update_status_gui("Download e leitura do diário concluídos.")
        except Exception as e:
            update_status_gui(f"ERRO: Falha ao baixar ou ler o diário: {e}. Abortando automação.")
            return 

        if numero_diario is None or not arquivos_txt_para_processar:
            update_status_gui("AVISO: Nenhum diário foi baixado ou processado. Não há informações para extrair. Abortando automação.")
            return 

        update_status_gui("Extraindo informações e gerando PDFs...")
        anexos_pdf_gerados = extrair_e_salvar_informacoes_dioe(caminho_diretorio, arquivos_txt_para_processar, numero_diario)
        update_status_gui("Extração de informações e geração de PDFs concluídas.")

        if len(anexos_pdf_gerados) > 0:
            update_status_gui("Iniciando envio de e-mail...")
            
            ef.email_expresso() 
            ef.novo_email()

            destinatarios_para_envio = destinatarios_email if destinatarios_email else {}
            ef.inserir_destinatarios(destinatarios_para_envio)

            # --- AQUI ESTÁ A MUDANÇA PRINCIPAL ---
            # Prepara os valores que podem ser substituídos
            replacements = {
                "{numero_diario}": str(numero_diario), # Garante que é string
                "{data_diario}": data_diario_final
            }

            # Formata o assunto
            # Usa o assunto_email da GUI, ou um padrão se não fornecido
            assunto_base = assunto_email if assunto_email else "DIOE - Processamento do {numero_diario} Nº {numero_diario}"
            # Itera sobre os replacements para substituir no assunto
            assunto_final = assunto_base
            for placeholder, value in replacements.items():
                assunto_final = assunto_final.replace(placeholder, value)
            
            ef.inserir_assunto(assunto_final)
            
            for anexo in anexos_pdf_gerados:
                ef.inserir_anexos(anexo)
            
            # Formata o texto do e-mail
            # Usa o texto_email da GUI, ou um padrão se não fornecido
            texto_base = texto_email if texto_email else (
                "Bom dia, \n\nSegue o {data_diario} de número {numero_diario} "
                "processado.\n\nAtenciosamente,"
            )
            # Itera sobre os replacements para substituir no texto
            texto_final = texto_base
            for placeholder, value in replacements.items():
                texto_final = texto_final.replace(placeholder, value)
            
            ef.inserir_texto(texto_final)
            # --- FIM DA MUDANÇA PRINCIPAL ---

            ef.assinatura()
            ef.enviar_email()

            update_status_gui("Email enviado com sucesso.")

            for txt_file in arquivos_txt_para_processar:
                if os.path.exists(txt_file):
                    try:
                        os.remove(txt_file)
                        update_status_gui(f"Arquivo TXT temporário removido: {txt_file}")
                    except Exception as e:
                        update_status_gui(f"Erro ao remover arquivo TXT temporário '{txt_file}': {e}")
            
            for anexo_pdf in anexos_pdf_gerados:
                if os.path.exists(anexo_pdf):
                    try:
                        os.remove(anexo_pdf)
                        update_status_gui(f"Arquivo PDF temporário removido: {anexo_pdf}")
                    except Exception as e:
                        update_status_gui(f"Erro ao remover arquivo PDF temporário '{anexo_pdf}': {e}")
        else:
            update_status_gui("Nenhum PDF gerado. E-mail não será enviado.")

    except Exception as e:
        update_status_gui(f"ERRO: Ocorreu um erro inesperado durante a automação: {e}")
        raise 

    finally:
        update_status_gui("Finalizando o driver do navegador...")
        ef.fechar_driver()
        update_status_gui("Driver do navegador fechado.")

if __name__ == "__main__":
    iniciar()