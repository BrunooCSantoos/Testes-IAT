import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import threading
import os
import time
import expresso_funcoes as ef
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class InterfaceEnvioEmail:
    def __init__(self, master):
        self.master = master
        master.title("Expresso Mail Sender")
        master.geometry("600x850") # Aumenta a altura para os novos botões
        master.resizable(False, False)

        self.lista_anexos = []
        self.destinatarios_cc = []
        self.destinatarios_cco = []
        self.confirmacao_leitura_ativada = tk.BooleanVar(value=False)
        self.assinatura_ativada = tk.BooleanVar(value=False)


        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Campos de Entrada ---
        tk.Label(master, text="Destinatários:", font=("Arial", 10, "bold")).pack(pady=5)

        self.frame_destinatarios = tk.Frame(master)
        self.frame_destinatarios.pack(pady=5)

        self.entrada_destinatarios = tk.Entry(self.frame_destinatarios, width=55)
        self.entrada_destinatarios.pack(side=tk.LEFT, padx=5)

        botao_carregar_txt = tk.Button(self.frame_destinatarios, text="Emails (.txt)", command=self.carregar_destinatarios_txt)
        botao_carregar_txt.pack(side=tk.RIGHT, padx=5)

        tk.Label(master, text="Assunto:", font=("Arial", 10, "bold")).pack(pady=5)
        self.entrada_assunto = tk.Entry(master, width=70)
        self.entrada_assunto.pack(pady=5)

        tk.Label(master, text="Anexos:", font=("Arial", 10, "bold")).pack(pady=5)
        self.frame_anexos = tk.Frame(master)
        self.frame_anexos.pack(pady=5)

        self.listbox_anexos = tk.Listbox(self.frame_anexos, width=60, height=5)
        self.listbox_anexos.pack(side=tk.LEFT, padx=5)

        barra_rolagem_anexos = tk.Scrollbar(self.frame_anexos, orient="vertical")
        barra_rolagem_anexos.config(command=self.listbox_anexos.yview)
        barra_rolagem_anexos.pack(side=tk.RIGHT, fill="y")
        self.listbox_anexos.config(yscrollcommand=barra_rolagem_anexos.set)

        botao_add_anexo = tk.Button(master, text="Adicionar Anexo(s)", command=self.adicionar_anexo)
        botao_add_anexo.pack(pady=5)

        botao_remover_anexo = tk.Button(master, text="Remover Anexo Selecionado", command=self.remover_anexo)
        botao_remover_anexo.pack(pady=5)

        # --- Frame para os novos botões (CC, CCO, Assinatura, Leitura) ---
        self.frame_opcoes_email = tk.Frame(master)
        self.frame_opcoes_email.pack(pady=10)

        self.botao_cc = tk.Button(self.frame_opcoes_email, text="Adicionar CC", command=self.abrir_janela_cc)
        self.botao_cc.pack(side=tk.LEFT, padx=5)

        self.botao_cco = tk.Button(self.frame_opcoes_email, text="Adicionar CCO", command=self.abrir_janela_cco)
        self.botao_cco.pack(side=tk.LEFT, padx=5)

        self.checkbutton_assinatura = tk.Checkbutton(self.frame_opcoes_email, text="Adicionar Assinatura", variable=self.assinatura_ativada)
        self.checkbutton_assinatura.pack(side=tk.LEFT, padx=5)

        self.checkbutton_confirmacao_leitura = tk.Checkbutton(self.frame_opcoes_email, text="Confirmação de Leitura", variable=self.confirmacao_leitura_ativada)
        self.checkbutton_confirmacao_leitura.pack(side=tk.LEFT, padx=5)


        tk.Label(master, text="Corpo do E-mail:", font=("Arial", 10, "bold")).pack(pady=5)
        self.entrada_texto = tk.Text(master, width=70, height=12)
        self.entrada_texto.pack(pady=5)

        # --- Botão Enviar ---
        self.botao_enviar = tk.Button(master, text="Enviar E-mail", command=self.iniciar_thread_envio,
                                      font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", relief=tk.RAISED)
        self.botao_enviar.pack(pady=20)

        # --- Barra de Progresso ---
        self.label_progresso = tk.Label(master, text="Status: Aguardando...", font=("Arial", 10))
        self.label_progresso.pack(pady=5)

        self.barra_progresso = ttk.Progressbar(master, orient="horizontal", length=400, mode="determinate")
        self.barra_progresso.pack(pady=10)

    def adicionar_anexo(self):
        caminhos_arquivos = filedialog.askopenfilenames()
        if caminhos_arquivos:
            for caminho_arquivo in caminhos_arquivos:
                self.lista_anexos.append(caminho_arquivo)
                self.listbox_anexos.insert(tk.END, os.path.basename(caminho_arquivo))

    def remover_anexo(self):
        indices_selecionados = self.listbox_anexos.curselection()
        if indices_selecionados:
            for index in indices_selecionados[::-1]:
                self.listbox_anexos.delete(index)
                del self.lista_anexos[index]

    def carregar_destinatarios_txt(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    emails = []
                    for line in f:
                        email = line.strip()
                        if email:
                            emails.append(email)

                    if emails:
                        self.entrada_destinatarios.delete(0, tk.END)
                        self.entrada_destinatarios.insert(0, ", ".join(emails))
                        messagebox.showinfo("Sucesso", f"{len(emails)} e-mails carregados do arquivo TXT.")
                    else:
                        messagebox.showwarning("Arquivo Vazio", "O arquivo TXT selecionado não contém e-mails válidos.")

            except Exception as e:
                messagebox.showerror("Erro ao Carregar TXT", f"Ocorreu um erro ao ler o arquivo: {e}")

    def abrir_janela_cc(self):
        self._abrir_janela_destinatarios_secundaria("CC", self.destinatarios_cc)

    def abrir_janela_cco(self):
        self._abrir_janela_destinatarios_secundaria("CCO", self.destinatarios_cco)

    def _abrir_janela_destinatarios_secundaria(self, tipo, lista_destino):
        janela_secundaria = tk.Toplevel(self.master)
        janela_secundaria.title(f"Adicionar Destinatários {tipo}")
        janela_secundaria.geometry("400x250")
        janela_secundaria.transient(self.master) # Mantém a janela secundária acima da principal
        janela_secundaria.grab_set() # Bloqueia interação com a janela principal

        tk.Label(janela_secundaria, text=f"Insira Destinatários {tipo} (separados por vírgula):").pack(pady=10)
        entrada_manual = tk.Entry(janela_secundaria, width=50)
        entrada_manual.pack(pady=5)
        entrada_manual.insert(0, ", ".join(lista_destino)) # Preenche com valores existentes

        def carregar_txt_secundario():
            file_path = filedialog.askopenfilename(
                parent=janela_secundaria, # Define a janela pai
                filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        emails_lidos = []
                        for line in f:
                            email = line.strip()
                            if email:
                                emails_lidos.append(email)
                        entrada_manual.delete(0, tk.END)
                        entrada_manual.insert(0, ", ".join(emails_lidos))
                        messagebox.showinfo("Sucesso", f"{len(emails_lidos)} e-mails carregados.", parent=janela_secundaria)
                except Exception as e:
                    messagebox.showerror("Erro ao Carregar TXT", f"Ocorreu um erro ao ler o arquivo: {e}", parent=janela_secundaria)

        def salvar_destinatarios():
            lista_destino.clear() # Limpa a lista existente
            dest_str = entrada_manual.get()
            if dest_str:
                novos_destinatarios = [d.strip() for d in dest_str.split(',') if d.strip()]
                lista_destino.extend(novos_destinatarios)
            janela_secundaria.destroy()

        tk.Button(janela_secundaria, text="Emails (.txt)", command=carregar_txt_secundario).pack(pady=5)
        tk.Button(janela_secundaria, text="Salvar", command=salvar_destinatarios).pack(pady=10)

        janela_secundaria.protocol("WM_DELETE_WINDOW", salvar_destinatarios) # Salva ao fechar janela secundária
        self.master.wait_window(janela_secundaria) # Espera a janela secundária fechar antes de continuar

    def iniciar_thread_envio(self):
        destinatarios_str = self.entrada_destinatarios.get()
        assunto = self.entrada_assunto.get()
        texto = self.entrada_texto.get("1.0", tk.END).strip()

        if not destinatarios_str:
            messagebox.showwarning("Entrada Inválida", "Por favor, insira pelo menos um destinatário PRINCIPAL (Para).")
            return
        if not assunto:
            messagebox.showwarning("Entrada Inválida", "Por favor, insira o assunto do e-mail.")
            return
        if not texto:
            messagebox.showwarning("Entrada Inválida", "Por favor, insira o corpo do e-mail.")
            return

        destinatarios = [d.strip() for d in destinatarios_str.split(',') if d.strip()]

        self.botao_enviar.config(state=tk.DISABLED)
        self.barra_progresso["value"] = 0
        self.label_progresso.config(text="Status: Iniciando envio do e-mail...")

        thread_envio = threading.Thread(target=self.processar_envio_email,
                                        args=(destinatarios, assunto, self.lista_anexos, texto,
                                              self.destinatarios_cc, self.destinatarios_cco,
                                              self.assinatura_ativada.get(), self.confirmacao_leitura_ativada.get()))
        thread_envio.start()

    def processar_envio_email(self, destinatarios, assunto, anexos, texto,
                               destinatarios_cc, destinatarios_cco, usar_assinatura, usar_confirmacao_leitura):
        try:
            self.atualizar_progresso(10, "Status: Abrindo navegador e fazendo login...")
            ef.email_expresso()
            time.sleep(5)
            self.atualizar_progresso(30, "Status: Criando nova mensagem...")

            try:
                nova_mensagem = WebDriverWait(ef.driver, 20).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "em_sidebox_menu"))
                )
                nova_mensagem.click()
                time.sleep(5)
                self.atualizar_progresso(40, "Status: Inserindo destinatários PRINCIPAIS...")
            except Exception as e:
                raise Exception(f"Erro ao encontrar ou clicar no botão 'Nova Mensagem': {e}")

            ef.inserir_destinatarios(destinatarios)
            time.sleep(2) # Pequena espera entre inserções
            self.atualizar_progresso(50, "Status: Inserindo assunto...")

            ef.inserir_assunto(assunto)
            time.sleep(2)

            if destinatarios_cc:
                self.atualizar_progresso(55, "Status: Inserindo destinatários CC...")
                ef.adicionar_CC(destinatarios_cc)
                time.sleep(2)

            if destinatarios_cco:
                self.atualizar_progresso(60, "Status: Inserindo destinatários CCO...")
                ef.adicionar_CCo(destinatarios_cco)
                time.sleep(2)

            self.atualizar_progresso(70, "Status: Inserindo anexos (se houver)...")
            if anexos:
                ef.inserir_anexos(anexos)
                time.sleep(2) # Mais tempo para anexos

            self.atualizar_progresso(80, "Status: Inserindo corpo do e-mail...")
            ef.inserir_texto(texto)
            time.sleep(2)

            if usar_assinatura:
                self.atualizar_progresso(85, "Status: Adicionando assinatura...")
                ef.assinatura()
                time.sleep(1)

            if usar_confirmacao_leitura:
                self.atualizar_progresso(88, "Status: Solicitando confirmação de leitura...")
                ef.confirmar_leitura()
                time.sleep(1)

            self.atualizar_progresso(90, "Status: Enviando e-mail...")
            ef.enviar_email()
            time.sleep(3) # Mais tempo para o envio

            self.atualizar_progresso(100, "Status: E-mail enviado com sucesso!")
            messagebox.showinfo("Sucesso", "E-mail enviado com sucesso!")

        except Exception as e:
            self.label_progresso.config(text=f"Status: Erro - {e}")
            messagebox.showerror("Erro no Envio", f"Ocorreu um erro ao enviar o e-mail: {e}")
        finally:
            self.botao_enviar.config(state=tk.NORMAL)

    def atualizar_progresso(self, valor, texto):
        self.master.after(0, self._atualizar_gui_thread_safe, valor, texto)

    def _atualizar_gui_thread_safe(self, valor, texto):
        self.barra_progresso["value"] = valor
        self.label_progresso.config(text=texto)
        self.master.update_idletasks()

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Deseja realmente sair e fechar o navegador?"):
            try:
                if ef.driver:
                    ef.driver.quit()
                    print("Navegador Selenium encerrado.")
            except WebDriverException as e:
                print(f"Erro ao tentar encerrar o navegador: {e}")
            finally:
                self.master.destroy()
                os._exit(0)