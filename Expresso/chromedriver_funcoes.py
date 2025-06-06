import tkinter as tk
from tkinter import simpledialog, messagebox
import requests
import zipfile
import os
import re
import cv2
import numpy as np
import subprocess
import platform
import json
import easyocr
from PIL import Image, ImageEnhance, ImageFilter

chromedriver_path = "S:\\GEAD-DRH\\DIAFI-DRH\\DRH - GESTÃO DE PESSOAS\\CONJUNTO DE ATIVIDADES DRH - PLANILHAS\\Selenium\\chromedriver-win64\\chromedriver.exe"

class chromedriver_func:
    def obter_versao_chrome():
        version = None
        try:
            if platform.system() == "Windows":
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                    version_string = winreg.QueryValueEx(key, "version")[0]
                    version = version_string.split(".")[0]
                    winreg.CloseKey(key)
                except Exception as e:
                    print(f"Erro ao obter versão do Chrome (Windows): {e}")
            elif platform.system() == "Linux":
                try:
                    process = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True, check=True)
                    version_string = process.stdout.strip().split(" ")[2]
                    version = version_string.split(".")[0]
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        process = subprocess.run(['chromium-browser', '--version'], capture_output=True, text=True, check=True)
                        version_string = process.stdout.strip().split(" ")[2]
                        version = version_string.split(".")[0]
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        print("Google Chrome ou Chromium não encontrados.")
            elif platform.system() == "Darwin":  # macOS
                try:
                    process = subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'], capture_output=True, text=True, check=True)
                    version_string = process.stdout.strip().split(" ")[2]
                    version = version_string.split(".")[0]
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("Google Chrome não encontrado.")
        except Exception as e:
            print(f"Erro ao obter versão do Chrome: {e}")
        return version

    def obter_versao_chromedriver(chromedriver_path):
        version = None
        if os.path.exists(chromedriver_path):
            try:
                process = subprocess.run([chromedriver_path, '--version'], capture_output=True, text=True, check=True)
                output = process.stdout.strip()
                match = re.search(r'ChromeDriver (\d+\.\d+\.\d+\.\d+)', output)
                if match:
                    version_string = match.group(1)
                    version = version_string.split(".")[0]
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"ChromeDriver não encontrado no caminho: {chromedriver_path}")
            except Exception as e:
                print(f"Erro ao obter versão do ChromeDriver: {e}")
        else:
            print(f"Arquivo ChromeDriver não encontrado em: {chromedriver_path}")
        return version

    def verificar_compatibilidade_chromedriver(chrome_major_version, chromedriver_major_version):
        """Verifica se a versão principal do Chrome e do ChromeDriver são compatíveis."""
        if chrome_major_version and chromedriver_major_version:
            if chrome_major_version == chromedriver_major_version:
                return True
            else:
                return False
        else:
            return None  # Não foi possível obter uma ou ambas as versões

    def chromedriver_compatibilidade(chromedriver_path):

        chrome_version = chromedriver_func.obter_versao_chrome()
        chromedriver_version = chromedriver_func.obter_versao_chromedriver(chromedriver_path)

        print(f"Versão do Chrome detectada: {chrome_version}")
        print(f"Versão do ChromeDriver detectada: {chromedriver_version}")

        compativel = chromedriver_func.verificar_compatibilidade_chromedriver(chrome_version, chromedriver_version)

        return compativel
    
    def baixar_chromedriver(proxy_url=None, proxy_username=None, proxy_password=None):
        pasta_destino = "S:\\GEAD-DRH\\DIAFI-DRH\\DRH - GESTÃO DE PESSOAS\\CONJUNTO DE ATIVIDADES DRH - PLANILHAS\\Selenium\\"
        proxies = None
        if proxy_url:
            if proxy_username and proxy_password:
                proxies = {
                    "http": f"http://{proxy_username}:{proxy_password}@{proxy_url}",
                    "https": f"http://{proxy_username}:{proxy_password}@{proxy_url}",
                }
            else:
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url,
                }

        try:
            # 1. Detectar a versão do Chrome (método aproximado)
            chrome_version_str = ""
            if platform.system() == "Windows":
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                    chrome_version_str = winreg.QueryValueEx(key, "version")[0].split(".")[0]
                    winreg.CloseKey(key)
                except Exception as e:
                    print(f"Erro ao detectar versão do Chrome (Windows): {e}")
            elif platform.system() == "Linux":
                try:
                    result = os.popen("google-chrome --version").read()
                    chrome_version_str = result.split(" ")[2].split(".")[0]
                except Exception as e:
                    print(f"Erro ao detectar versão do Chrome (Linux): {e}")
            elif platform.system() == "Darwin":  # macOS
                try:
                    result = os.popen("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --version").read()
                    chrome_version_str = result.split(" ")[2].split(".")[0]
                except Exception as e:
                    print(f"Erro ao detectar versão do Chrome (macOS): {e}")

            if not chrome_version_str:
                messagebox.showerror("Erro", "Não foi possível detectar a versão do Chrome.")
                return False

            print(f"Versão do Chrome detectada (aproximada): {chrome_version_str}")

            # 2. Obter informações de download do ChromeDriver usando "Chrome for Testing"
            api_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
            response = requests.get(api_url, proxies=proxies)
            response.raise_for_status()
            data = response.json()

            chromedriver_download_url = None
            for version_data in data["versions"]:
                if version_data["version"].startswith(f"{chrome_version_str}."):
                    for driver in version_data["downloads"]["chromedriver"]:
                        if driver["platform"] == "win64":
                            chromedriver_download_url = driver["url"]
                            break
                    if chromedriver_download_url:
                        break

            if not chromedriver_download_url:
                messagebox.showerror("Erro", f"Nenhuma versão correspondente do ChromeDriver encontrada para Chrome {chrome_version_str} (win64).")
                return False

            print(f"URL de download do ChromeDriver encontrado: {chromedriver_download_url}")

            # 3. Baixar o ChromeDriver
            download_response = requests.get(chromedriver_download_url, stream=True, proxies=proxies)
            download_response.raise_for_status()

            # 4. Criar a pasta de destino
            os.makedirs(pasta_destino, exist_ok=True)
            chromedriver_zip_path = os.path.join(pasta_destino, "chromedriver.zip")

            with open(chromedriver_zip_path, "wb") as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 5. Extrair o ChromeDriver
            with zipfile.ZipFile(chromedriver_zip_path, 'r') as zip_ref:
                zip_ref.extractall(pasta_destino)

            os.remove(chromedriver_zip_path)

            # 6. Tornar executável (Windows não precisa disso geralmente)
            system_name = platform.system().lower()
            if system_name in ["linux", "darwin"]:
                chromedriver_executable_path = os.path.join(pasta_destino, "chromedriver")
                os.chmod(chromedriver_executable_path, 0o755)

            messagebox.showinfo("Sucesso", f"ChromeDriver baixado e colocado em: {pasta_destino}")
            return True

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro", f"Erro ao baixar informações ou o ChromeDriver: {e}")
            return False
        except json.JSONDecodeError as e:
            messagebox.showerror("Erro", f"Erro ao decodificar a resposta JSON: {e}")
            return False
        except zipfile.BadZipFile as e:
            messagebox.showerror("Erro", f"Erro ao extrair o ChromeDriver: {e}")
            return False
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}")
            return False

    def obter_credenciais_proxy():
            root = tk.Tk()
            root.withdraw()  # Oculta a janela principal

            proxy_url = "10.15.54.113:8080"

            proxy_username = simpledialog.askstring("Proxy", "Nome de Usuário do Proxy:")
            if proxy_username is None:
                return None, None, None

            proxy_password = simpledialog.askstring("Proxy", "Senha do Proxy:", show='*')
            if proxy_password is None:
                return None, None, None

            return proxy_url, proxy_username, proxy_password
    
    def segmentar_imagem(imagem):
        gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

        # Binariza a imagem usando o método de Otsu
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Encontra os contornos dos caracteres na imagem binarizada
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Ordena os contornos da esquerda para a direita
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])

        # Segmenta os caracteres com base nos contornos encontrados
        caracteres_segmentados = []
        for contorno in contours:
            x, y, largura, altura = cv2.boundingRect(contorno)
            # Filtra contornos muito pequenos ou muito grandes, que provavelmente não são caracteres
            if largura > 5 and altura > 10 and largura < 50 and altura < 50:
                # Extrai a imagem do caractere usando as coordenadas do contorno
                caractere_imagem = imagem[y:y+altura, x:x+largura]
                caracteres_segmentados.append(caractere_imagem)
        return caracteres_segmentados

    def resolver_captcha_auto(self, caminho_captcha, idioma=['pt']):
        func = chromedriver_func()
        try:
            print(f"Lendo CAPTCHA do arquivo: {caminho_captcha}")
            # Abre a imagem do CAPTCHA usando PIL
            imagem = Image.open(caminho_captcha)
            print("Imagem aberta com sucesso usando PIL.")

            # Converte a imagem PIL para um array NumPy para usar com OpenCV
            imagem_np = np.array(imagem)

            # Converte a imagem para escala de cinza para simplificar o processamento
            imagem_gray = cv2.cvtColor(imagem_np, cv2.COLOR_BGR2GRAY)

            # Melhora o contraste da imagem usando CLAHE (Contrast Limited Adaptive Histogram Equalization)
            # Isso ajuda a destacar os caracteres em CAPTCHAs com iluminação ruim ou ruído
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            imagem_clahe = clahe.apply(imagem_gray)

            # Binariza a imagem usando o método de Otsu para separar os caracteres do fundo
            _, imagem_binarizada = cv2.threshold(imagem_clahe, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Aplica um filtro de mediana para reduzir o ruído na imagem binarizada
            imagem_mediana = cv2.medianBlur(imagem_binarizada, 3)

            # Segmenta os caracteres na imagem pré-processada
            caracteres_segmentados = func.segmentar_imagem()
            if not caracteres_segmentados:
                caracteres_segmentados = [imagem_np]  # Processa a imagem inteira se nenhum caractere for segmentado

            print(f"Imagem pré-processada com sucesso. Caracteres segmentados: {len(caracteres_segmentados)}")

            # Inicializa o leitor EasyOCR com os idiomas especificados
            reader = easyocr.Reader(idioma)
            print("Leitor EasyOCR inicializado.")

            # Tenta reconhecer o texto em cada caractere segmentado
            resultados_ocr = []
            for caractere_imagem in caracteres_segmentados:
                resultado_ocr = reader.readtext(caractere_imagem)
                if resultado_ocr:
                    # Adiciona o texto reconhecido ao resultado, convertendo para maiúsculas e removendo espaços
                    resultados_ocr.append(resultado_ocr[0][1].strip().upper())
                else:
                    resultados_ocr.append("")  # Adiciona uma string vazia se nenhum texto for reconhecido

            # Junta os resultados do OCR para formar o texto do CAPTCHA
            texto_captcha = "".join(resultados_ocr)
            print(f"Resultado da leitura do OCR: {texto_captcha}")

            # Remove espaços extras no texto do CAPTCHA
            texto_captcha = texto_captcha.replace(" ", "")
            print(f"Texto do CAPTCHA resolvido: {texto_captcha}")
            return texto_captcha

        except Exception as e:
            # Captura e imprime qualquer exceção que ocorra durante o processo
            print(f"Erro ao processar CAPTCHA: {e}")
            return None