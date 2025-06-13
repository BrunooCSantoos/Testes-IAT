import chromedriver_funcoes
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
import leitor_captcha
import time
import os
import glob
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
        "safeBrowse.enabled": True 
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
                return numero_diario, True # Retorna o número do diário e True para indicar que já foi baixado

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
        
        while elemento_captcha:
            try:
                elemento_captcha.screenshot(caminho_captcha)
                time.sleep(1)
                resposta_captcha = leitor_captcha.resolver_captcha_auto(caminho_captcha)
                campo_resposta = driver.find_element(By.ID, "imagemVerificacao")
                campo_resposta.send_keys(resposta_captcha)
                botao_download = driver.find_element(By.ID, "Enviar")
                botao_download.click()
                time.sleep(1)

                try:
                    elemento_captcha = driver.find_element(By.XPATH, xpath_captcha_img)
                except:
                    elemento_captcha = None
                    
            except Exception as e:
                print(f"Erro durante a tentativa de resolução do CAPTCHA: {e}")

        time.sleep(10) # Espera o download ser concluído

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
        return numero_diario, data_diario, False # Retorna None e False em caso de erro

def start(caminho_diretorio):
    os.makedirs(caminho_diretorio, exist_ok=True)
    nome_arquivo_csv = "datas_dioe_baixadas.csv"
    caminho_arquivo_csv = os.path.join(caminho_diretorio, nome_arquivo_csv)
    
    # Baixa o DIOE
    numero_diario, data_diario, ja_baixado = baixar_dioe(caminho_diretorio, caminho_arquivo_csv)
    
    arquivos_txt_gerados = []

    # Se o diário já foi baixado, pode não haver PDFs para processar.
    # Neste caso, podemos procurar por arquivos TXT existentes que possam ter sido gerados
    # em uma execução anterior e não foram removidos.
    if ja_baixado:
        print(f"Diário {numero_diario} já foi baixado. Procurando por arquivos TXT existentes para processamento.")
        # Procura por arquivos TXT de decretos e portarias gerados anteriormente
        padrao_decreto = os.path.join(caminho_diretorio, "EX*_decretos.txt")
        padrao_portaria = os.path.join(caminho_diretorio, "EX*_portarias.txt")
        arquivos_txt_gerados.extend(glob.glob(padrao_decreto))
        arquivos_txt_gerados.extend(glob.glob(padrao_portaria))
        if not arquivos_txt_gerados:
            print("Nenhum arquivo TXT de decretos ou portarias encontrado para processamento.")
            return numero_diario, data_diario, [] # Retorna lista vazia se não encontrar TXT

    # Se não foi baixado (ou se queremos processar mesmo que já baixado,
    # caso haja um erro na lógica de 'ja_baixado'), continue com a leitura.
    # O `if not ja_baixado or arquivos_txt_gerados` garante que, se já baixado,
    # ele só tentará ler se houver arquivos TXT pré-existentes para processar.
    if not ja_baixado or arquivos_txt_gerados:
        # Realiza a leitura das portarias e decretos
        arquivo_portarias_path = leitura_portaria.ler(caminho_diretorio)
        arquivo_decretos_path = leitura_decreto.ler(caminho_diretorio)

        if arquivo_portarias_path and arquivo_portarias_path not in arquivos_txt_gerados:
            arquivos_txt_gerados.append(arquivo_portarias_path)
        
        if arquivo_decretos_path and arquivo_decretos_path not in arquivos_txt_gerados:
            arquivos_txt_gerados.append(arquivo_decretos_path)

    # Remove os diários baixados (arquivos PDF originais)
    padrao_arquivo_pdf = f"{caminho_diretorio}{os.sep}EX*.pdf" # Usa os.sep para compatibilidade
    arquivos_pdf_originais = glob.glob(padrao_arquivo_pdf)

    for arquivo_pdf_orig in arquivos_pdf_originais:
        try:
            os.remove(arquivo_pdf_orig)
            print(f"\nArquivo {arquivo_pdf_orig} removido.")
        except Exception as e:
            print(f"Erro ao remover o arquivo PDF original '{arquivo_pdf_orig}': {e}")
    
    print("\nConcluído\n")

    return numero_diario, data_diario, arquivos_txt_gerados
    
if __name__ == "__main__":
    caminho_diretorio = os.getcwd()
    start(caminho_diretorio)