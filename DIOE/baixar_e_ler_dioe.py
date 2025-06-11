import chromedriver_funcoes
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import time
import os
import glob
from tkinter import Tk, Label, Entry, Button, PhotoImage
from PIL import Image, ImageTk
import csv
from datetime import datetime
import leitura_decreto
import leitura_portaria

caminho_driver = chromedriver_funcoes.chromedriver_path

def obter_datas_baixadas(caminho_csv):
    # Obtém as datas de diários já baixados de um arquivo CSV.
    datas = set()
    if os.path.exists(caminho_csv):
        with open(caminho_csv, 'r', newline='', encoding='utf-8') as f:
            leitor_csv = csv.reader(f)
            for linha in leitor_csv:
                if linha:
                    datas.add(linha[0])
    return datas

def adicionar_data_baixada(caminho_csv, data_str):
    # Adiciona uma data de diário baixado ao arquivo CSV.
    with open(caminho_csv, 'a', newline='', encoding='utf-8') as f:
        escritor_csv = csv.writer(f)
        escritor_csv.writerow([data_str])
    ocultar_arquivo(caminho_csv)

def ocultar_arquivo(caminho_csv):
    # Oculta um arquivo no Windows usando o comando attrib.
    try:
        os.system(f'attrib +h "{caminho_csv}"')
        print(f"Arquivo '{caminho_csv}' ocultado com sucesso.")
    except Exception as e:
        print(f"Erro ao ocultar o arquivo: {e}")

def extrair_data_diario(driver):
    # Extrai a data do diário da página web.
    try:
        xpath_data = "/html/body/table/tbody/tr/td[4]/table[2]/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr/td/table[3]/tbody/tr[3]/td[4]"
        elemento_data = driver.find_element(By.XPATH, xpath_data)
        texto_data = elemento_data.text.strip()
        data_parseada = datetime.strptime(texto_data, "%d/%m/%Y")
        return data_parseada.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Erro ao extrair a data do diário: {e}")
        print("Por favor, verifique o 'xpath_data' na função 'extrair_data_diario'.")
        return None

def resolver_interface_captcha(caminho_imagem, largura_desejada=200):
    # Abre uma interface gráfica para o usuário resolver o captcha.
    janela_raiz = Tk()
    janela_raiz.title("Resolver Captcha")
    janela_raiz.geometry("400x300")
    
    # Carrega e redimensiona a imagem do captcha
    imagem_original = Image.open(caminho_imagem)
    largura_original, altura_original = imagem_original.size
    altura_desejada = int(altura_original * (largura_desejada / largura_original))
    imagem_redimensionada = imagem_original.resize((largura_desejada, altura_desejada))
    imagem_tk = ImageTk.PhotoImage(imagem_redimensionada)

    label_imagem = Label(janela_raiz, image=imagem_tk)
    label_imagem.pack(pady=10)

    label_instrucao = Label(janela_raiz, text="Digite o texto da imagem:")
    label_instrucao.pack(pady=10)

    entrada_captcha = Entry(janela_raiz)
    entrada_captcha.pack(pady=10)
    entrada_captcha.focus_set() # Coloca o foco no campo de entrada

    resposta_usuario = ""

    def enviar_resposta_usuario():
        nonlocal resposta_usuario
        resposta_usuario = entrada_captcha.get()
        janela_raiz.destroy() # Fecha a janela Tkinter

    # Permite enviar a resposta pressionando Enter
    janela_raiz.bind('<Return>', lambda event=None: enviar_resposta_usuario())

    botao_enviar = Button(janela_raiz, text="Enviar", command=enviar_resposta_usuario)
    botao_enviar.pack(pady=15)

    janela_raiz.mainloop() # Inicia o loop principal da interface gráfica
    return resposta_usuario

def baixar_dioe(pasta_destino, caminho_arquivo_csv):
    """
    Baixa o Diário Oficial Eletrônico (DIOE), resolvendo o captcha se necessário,
    e registra a data do download em um arquivo CSV.
    """
    opcoes_chrome = Options()
    preferencias = {
        "download.default_directory": pasta_destino,
        "download.prompt_for_download": False, 
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True 
    }
    opcoes_chrome.add_experimental_option("prefs", preferencias)
    opcoes_chrome.add_argument("--headless") # Executa o navegador em modo headless (sem interface gráfica)

    servico = ChromeService(executable_path=caminho_driver)    
    driver = webdriver.Chrome(service=servico, options=opcoes_chrome)

    try:
        url = "https://www.documentos.dioe.pr.gov.br/dioe/consultaPublicaPDF.do?pg=1&action=pgLocalizar&enviado=true&numero=&search=&dataInicialEntrada=&dataFinalEntrada=&diarioCodigo=3&submit=+%A0+Consultar+%9B%9B++%A0+&qtd=5192&ec=yFnNFNmFNRfNOFnMFNrFNNfNO"
        driver.get(url)
        time.sleep(2) # Espera a página carregar
        
        data_diario = extrair_data_diario(driver)

        xpath_numero_diario = "/html/body/table/tbody/tr/td[4]/table[2]/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr/td/table[3]/tbody/tr[3]/td[5]"
        numero_diario = driver.find_element(By.XPATH, xpath_numero_diario).text
        
        if not data_diario:
            print("Não foi possível determinar a data do diário. Prosseguindo com o download sem verificação de data.")
        else:
            datas_baixadas = obter_datas_baixadas(caminho_arquivo_csv)
            if data_diario in datas_baixadas:
                print(f"Diário da data {data_diario} já foi baixado. Pulando o download.")
                return numero_diario

        # Clica no link inicial para abrir a consulta
        xpath_inicial = "/html/body/table/tbody/tr/td[4]/table[2]/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr/td/table[3]/tbody/tr[3]/td[2]/a"
        link_download_inicial = driver.find_element(By.XPATH, xpath_inicial)
        link_download_inicial.click()
        time.sleep(2) # Espera a página carregar

        # Clica no link da edição para download
        xpath_edicao = "/html/body/table/tbody/tr/td[4]/table[2]/tbody/tr/td/table/tbody/tr[3]/td/table/tbody/tr/td/table[3]/tbody/tr[4]/td/div/table/tbody/tr[1]/td[3]/a"
        link_download_edicao = driver.find_element(By.XPATH, xpath_edicao)
        link_download_edicao.click()
        time.sleep(2) # Espera a página carregar

        # Tira um screenshot do captcha
        xpath_captcha_img = "/html/body/div[3]/div[2]/div/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr/td[2]/img"
        elemento_captcha = driver.find_element(By.XPATH, xpath_captcha_img)
        caminho_captcha = os.path.join(pasta_destino, "captcha.png")
        elemento_captcha.screenshot(caminho_captcha)

        # Resolve o captcha usando a interface Tkinter
        resposta_captcha = resolver_interface_captcha(caminho_captcha, largura_desejada=300)

        # Remove o arquivo do captcha após a resolução
        if os.path.exists(caminho_captcha):
            os.remove(caminho_captcha)

        # Envia a resposta do captcha
        campo_resposta = driver.find_element(By.ID, "imagemVerificacao")
        campo_resposta.send_keys(resposta_captcha)

        # Clica no botão de download
        botao_download = driver.find_element(By.ID, "Enviar")
        botao_download.click()
        time.sleep(15) # Espera o download ser concluído

        if data_diario:
            adicionar_data_baixada(caminho_arquivo_csv, data_diario)
            print(f"Diário da data {data_diario} baixado e registrado no CSV.")
        else:
            print("Diário baixado, mas a data não foi registrada devido a um erro de extração.")

    except Exception as e:
        print(f"Ocorreu um erro durante o processo de download: {e}")
    finally:
        driver.quit()
        print("Navegador fechado.")
        return numero_diario
    
def start(caminho_diretorio):
    os.makedirs(caminho_diretorio, exist_ok=True)
    nome_arquivo_csv = "datas_dioe_baixadas.csv"
    caminho_arquivo_csv = os.path.join(caminho_diretorio, nome_arquivo_csv)
    
    # Baixa o DIOE
    numero_diario = baixar_dioe(caminho_diretorio, caminho_arquivo_csv)
    
    # Realiza a leitura das portarias e decretos
    leitura_portaria.ler(caminho_diretorio)
    leitura_decreto.ler(caminho_diretorio)

    # Remove os diários baixados
    padrao_arquivo_pdf = f"{caminho_diretorio}\\EX*.pdf"
    arquivos_pdf = glob.glob(padrao_arquivo_pdf)

    for arquivo_pdf in arquivos_pdf:
        #os.remove(arquivo_pdf)
        print(f"\nArquivo {arquivo_pdf} removido.")
    
    print("\nConcluído\n")

    return numero_diario
    
if __name__ == "__main__":
    caminho_diretorio = os.getcwd()
    start(caminho_diretorio)
