import tkinter as tk
from app_interface import AppCalculadoraAposentadoria

if __name__ == "__main__":
    root = tk.Tk()
    # Define o ícone da janela
    try:
        root.iconbitmap("C:\\Users\\ter.brunokawan\\Documents\\Projeto Eloá\\Aposentadoria\\iconeAposentadoria.ico")
    except tk.TclError:
        # Lidar com o erro se o ícone não for encontrado ou inválido
        pass
    app = AppCalculadoraAposentadoria(root)
    root.mainloop()