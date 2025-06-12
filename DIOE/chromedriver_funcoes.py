import tkinter as tk
from tkinter import simpledialog, messagebox
import requests
import zipfile
import os
import re
import subprocess
import platform
import json

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