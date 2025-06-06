import tkinter as tk
from interface_app import InterfaceEnvioEmail
import os
import sys

def verificar_chromedriver():
    """
    Verifica se o chromedriver.exe está presente e, se não, tenta guiar o usuário.
    """
    try:
        # Tenta importar chromedriver_funcoes para verificar o caminho
        import chromedriver_funcoes
        caminho_driver = chromedriver_funcoes.chromedriver_path
        if not os.path.exists(caminho_driver):
            tk.messagebox.showerror(
                "Erro de Configuração",
                f"ChromeDriver não encontrado em: {caminho_driver}\n"
                "Por favor, certifique-se de que 'chromedriver_funcoes.py' "
                "está configurado corretamente e que o ChromeDriver.exe "
                "está no caminho especificado ou no PATH do sistema."
            )
            return False
    except ImportError:
        tk.messagebox.showerror(
            "Erro de Módulo",
            "O módulo 'chromedriver_funcoes.py' não foi encontrado.\n"
            "Por favor, crie este módulo para configurar o caminho do ChromeDriver."
        )
        return False
    except Exception as e:
        tk.messagebox.showerror(
            "Erro Inesperado",
            f"Ocorreu um erro ao verificar o ChromeDriver: {e}"
        )
        return False
    return True

if __name__ == "__main__":
    # Verifica se o chromedriver está configurado antes de iniciar a GUI
    if not verificar_chromedriver():
        sys.exit(1) # Sai do programa se o ChromeDriver não for encontrado

    root = tk.Tk()
    app = InterfaceEnvioEmail(root)
    root.mainloop()