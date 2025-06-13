import chromedriver_funcoes
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait # Importar para esperas explícitas
from selenium.webdriver.support import expected_conditions as EC # Importar para condições de espera
from tkinter import Tk, Label, Entry, Button
import time

caminho_driver = chromedriver_funcoes.chromedriver_path
opcoes_chrome = Options()
preferencias = {
    "safeBrowse.enabled": True
}
opcoes_chrome.add_experimental_option("prefs", preferencias)
# ATENÇÃO: Descomente a linha abaixo apenas se você realmente quiser o modo headless
opcoes_chrome.add_argument("--headless") # Executa o navegador em modo headless (sem interface gráfica)

servico = ChromeService(executable_path=caminho_driver)
driver = webdriver.Chrome(service=servico, options=opcoes_chrome)

# caminho_diretorio = os.getcwd() # Não é usado globalmente, pode ser removido

def email_expresso(login, senha): # Modificado para aceitar login e senha
    """
    Navega até a página de login do Expresso e utiliza as credenciais fornecidas.
    """
    try:
        url = "https://expresso.celepar.pr.gov.br/login.php?cd=10&phpgw_forward=%2FexpressoMail1_2%2Findex.php"
        driver.get(url)
        time.sleep(2)

        campo_login = driver.find_element(By.ID, "user")
        campo_senha = driver.find_element(By.ID, "passwd")
        campo_login.send_keys(login)
        campo_senha.send_keys(senha)
        btn_entrar = driver.find_element(By.ID, "submitit")
        btn_entrar.click()
        WebDriverWait(driver, 15).until(EC.url_contains("expressoMail1_2"))
        time.sleep(3)

    except Exception as e:
        print(f"Ocorreu um erro durante o processo de login: {e}")
        driver.quit()
        raise

def solicitar_login_expresso():
    """
    Abre uma janela Tkinter para que o usuário insira o login e a senha do Expresso.
    """
    janela_raiz = Tk()
    janela_raiz.title("Login E-mail Expresso")
    janela_raiz.geometry("400x250")
    janela_raiz.resizable(False, False)

    label_instrucao = Label(janela_raiz, text="Insira seu login e senha do Expresso:")
    label_instrucao.pack(pady=10)

    label_login = Label(janela_raiz, text="Login:")
    label_login.pack()
    entrada_login = Entry(janela_raiz, width=30)
    entrada_login.pack(pady=5)
    entrada_login.focus_set()

    label_senha = Label(janela_raiz, text="Senha:")
    label_senha.pack()
    entrada_senha = Entry(janela_raiz, show="*", width=30)
    entrada_senha.pack(pady=5)

    resposta_login = ""
    resposta_senha = ""

    def enviar_resposta_usuario():
        nonlocal resposta_login, resposta_senha
        resposta_login = entrada_login.get()
        resposta_senha = entrada_senha.get()
        janela_raiz.destroy()

    janela_raiz.bind('<Return>',lambda event=None: enviar_resposta_usuario())

    botao_enviar = Button(janela_raiz, text="Entrar", command=enviar_resposta_usuario)
    botao_enviar.pack(pady=15)

    janela_raiz.mainloop()
    return resposta_login, resposta_senha

def inserir_anexos(anexos, i=0):
    """
    Insere múltiplos anexos no e-mail.
    """
    if isinstance(anexos, str):
        anexos = [anexos]
        
    for anexo in anexos:
        i += 1
        try:
            adicionar_anexo = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='div_message_scroll_1']/form/table/tbody/tr[10]/td[2]/a"))
            )
            adicionar_anexo.click()
            time.sleep(1) # Pequena espera para o campo aparecer

            inserir_anexo = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, f"file_{i}"))
            )
            inserir_anexo.send_keys(anexo)
            time.sleep(1) # Espera o arquivo ser anexado
        except Exception as e:
            print(f"Erro ao inserir anexo '{anexo}': {e}")
            raise # Re-levanta para notificar a GUI

def inserir_destinatarios(destinatarios):
    """
    Insere os destinatários na caixa 'Para'.
    """
    try:
        campo_destinatarios = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "input_to"))
        )
        for destinatario in destinatarios:
            campo_destinatarios.send_keys(f"{destinatario}, ")
    except Exception as e:
        print(f"Erro ao inserir destinatários 'Para': {e}")
        raise

def inserir_assunto(assunto):
    """
    Insere o assunto do e-mail.
    """
    try:
        campo_assunto = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "subject_1"))
        )
        campo_assunto.send_keys(assunto)
    except Exception as e:
        print(f"Erro ao inserir assunto: {e}")
        raise

def inserir_texto(texto):
    """
    Insere o corpo do e-mail.
    """
    try:
        campo_texto = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "body_1"))
        )
        campo_texto.send_keys(texto)
    except Exception as e:
        print(f"Erro ao inserir texto do corpo: {e}")
        raise

def novo_email():
    """
    Clica no botão para compor uma nova mensagem.
    """
    try:
        # Espera até que o elemento 'em_sidebox_menu' seja clicável
        nova_mensagem = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "em_sidebox_menu"))
        )
        nova_mensagem.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "subject_1"))) # Espera o campo de assunto aparecer
        time.sleep(1) # Pequena espera adicional
    except Exception as e:
        print(f"Erro ao encontrar ou clicar no botão 'Nova Mensagem': {e}")
        raise

def enviar_email():
    """
    Clica no botão de enviar e-mail.
    """
    try:
        botao_enviar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "send_button_1"))
        )
        botao_enviar.click()
        # Após enviar, pode haver um alerta ou a página mudar. Adicione uma espera aqui se necessário.
        # Por exemplo, esperar que a URL retorne para a caixa de saída ou um elemento de sucesso apareça.
        time.sleep(3) # Tempo para a ação de envio ser processada
    except Exception as e:
        print(f"Erro ao clicar no botão 'Enviar E-mail': {e}")
        raise

def confirmar_leitura():
    """
    Clica na opção de confirmação de leitura.
    """
    try:
        # Assumindo que o ID 'input_return_receipt' é de um checkbox ou botão clicável
        botao_leitura = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "input_return_receipt"))
        )
        if not botao_leitura.is_selected(): # Clica apenas se não estiver selecionado
            botao_leitura.click()
        time.sleep(0.5)
    except Exception as e:
        print(f"Erro ao tentar confirmar leitura: {e}")
        raise

def adicionar_CC(destinatarios):
    """
    Adiciona destinatários no campo CC.
    """
    try:
        adicionar_campo_cc = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "a_cc_link_1"))
        )
        adicionar_campo_cc.click()
        time.sleep(1) # Espera o campo CC aparecer

        campo_cc = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "input_cc"))
        )
        for destinatario in destinatarios:
            campo_cc.send_keys(f"{destinatario}, ")
    except Exception as e:
        print(f"Erro ao adicionar CC: {e}")
        raise

def adicionar_CCo(destinatarios):
    """
    Adiciona destinatários no campo CCO.
    """
    try:
        adicionar_campo_cco = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "a_cco_link_1"))
        )
        adicionar_campo_cco.click()
        time.sleep(1) # Espera o campo CCO aparecer

        campo_cco = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "input_cco"))
        )
        for destinatario in destinatarios:
            campo_cco.send_keys(f"{destinatario}, ")
    except Exception as e:
        print(f"Erro ao adicionar CCO: {e}")
        raise

def assinatura():
    """
    Clica para adicionar a assinatura.
    """
    try:
        # Supondo que a assinatura é um botão que insere o texto da assinatura
        botao_assinatura = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "signature"))
        )
        botao_assinatura.click()
        time.sleep(1)
    except Exception as e:
        print(f"Erro ao tentar adicionar assinatura: {e}")
        raise

# A função iniciar_envio_email não é mais chamada diretamente,
# a lógica foi movida para processar_envio_email na InterfaceEnvioEmail.
# Você pode remover ou manter, mas não será usada a partir da GUI.
# def iniciar_envio_email(destinatarios, assunto, anexos, texto):
#     # ... (código existente) ...