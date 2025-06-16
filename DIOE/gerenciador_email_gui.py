import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import tkinter.ttk as ttk
import threading
import json
import os
from datetime import datetime, timedelta
import time # Importa a biblioteca time

# Importa a função iniciar modificada do main.py
import main as automacao_email_principal
# Importa as funções do expresso_funcoes.py
import expresso_dioe as funcoes_expresso

ARQUIVO_CONFIG = "configuracao_email.json"

class GerenciadorEmailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Leitura do Diário Oficial")
        # Ajuste o tamanho da janela para acomodar os novos campos
        self.root.geometry("850x780") # Ajustado para acomodar o timer ao lado

        self.config = self.carregar_configuracao()

        # Adiciona um evento para sinalizar a thread do agendador para parar
        self.stop_scheduler_event = threading.Event()
        self.thread_verificacao_diaria = None # Inicializa a thread como None
        self.thread_automacao = None # Para controlar a thread de execução da automação

        # Variável para o timer
        self.proxima_execucao_label_var = tk.StringVar()
        self.proxima_execucao_label_var.set("Aguardando agendamento...")

        self.criar_widgets()
        # Inicia o agendador apenas após a GUI estar pronta e as funções de status disponíveis
        self.agendar_verificacao_diaria()
        # Inicia a atualização do timer
        self.atualizar_timer_proxima_execucao()

        # Configura o que acontece ao fechar a janela
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar_aplicacao)

    def carregar_configuracao(self):
        """Carrega as configurações do arquivo JSON ou retorna padrões."""
        if os.path.exists(ARQUIVO_CONFIG):
            with open(ARQUIVO_CONFIG, 'r') as f:
                config = json.load(f)
                # Garante que 'horarios_agendamento' seja sempre uma lista
                if "horario_agendamento" in config and not isinstance(config["horario_agendamento"], list):
                    config["horarios_agendamento"] = [config.pop("horario_agendamento")]
                elif "horario_agendamento" in config:
                    config["horarios_agendamento"] = config.pop("horario_agendamento")
                elif "horarios_agendamento" not in config:
                    config["horarios_agendamento"] = ["08:00"]
                
                # Adiciona novos campos de assunto e texto com valores padrão se não existirem
                if "assunto_email" not in config:
                    config["assunto_email"] = "DIOE - Processamento do Diário Oficial Eletrônico"
                if "texto_email_padrao" not in config:
                    config["texto_email_padrao"] = "Prezados,\n\nSegue o Diário Oficial Eletrônico (DIOE) processado.\n\nAtenciosamente,\n\nEquipe de Automação."
                
                # Garante que destinatarios é uma lista (e não um set ao carregar)
                if "destinatarios" not in config or not isinstance(config["destinatarios"], list):
                    config["destinatarios"] = []

                return config
        
        # Retorna a configuração padrão se o arquivo não existir
        return {
            "login_remetente": "",
            "senha_remetente": "",
            "destinatarios": [],
            "horarios_agendamento": ["08:00"],
            "assunto_email": "DIOE - Di\u00e1rio de {data_diario} N\u00ba {numero_diario}",
            "texto_email_padrao": "Bom dia,\n\nSegue o Di\u00e1rio Ofical de n\u00famero {numero_diario}, publicado em {data_diario}, processado.\n\nAtenciosamente,"
        }

    def salvar_configuracao(self):
        """Salva a configuração atual em um arquivo JSON."""
        # Garante que os horários são únicos e estão ordenados
        self.config["horarios_agendamento"] = sorted(list(set(self.config["horarios_agendamento"])))
        
        # Pega os valores atuais dos campos da GUI para salvar
        self.config["login_remetente"] = self.entrada_login_remetente.get()
        self.config["senha_remetente"] = self.entrada_senha_remetente.get()
        self.config["assunto_email"] = self.entrada_assunto_email.get()
        self.config["texto_email_padrao"] = self.texto_corpo_email.get("1.0", tk.END).strip()

        with open(ARQUIVO_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=4)
        
        self.atualizar_timer_proxima_execucao() # Recalcula o timer ao salvar

    def criar_widgets(self):
        """Cria e organiza todos os widgets da interface gráfica."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Aba de Remetente e Agendamento
        self.frame_remetente_agendamento = tk.Frame(self.notebook)
        self.notebook.add(self.frame_remetente_agendamento, text="Agendamento")
        self.criar_aba_remetente_agendamento(self.frame_remetente_agendamento)

        # Aba de Destinatários
        self.frame_destinatarios = tk.Frame(self.notebook)
        self.notebook.add(self.frame_destinatarios, text="Destinatários")
        self.criar_aba_destinatarios(self.frame_destinatarios)

        # Aba de Log de Status
        self.frame_status = tk.Frame(self.notebook)
        self.notebook.add(self.frame_status, text="Log de Status")
        self.criar_aba_status(self.frame_status)

    def criar_aba_remetente_agendamento(self, frame_pai):
        """Cria os widgets para a aba de credenciais e agendamento."""
        
        # Use grid para organizar as seções principais no frame_pai
        frame_pai.grid_columnconfigure(0, weight=1) # Coluna da esquerda para credenciais/agendamento
        frame_pai.grid_columnconfigure(1, weight=1) # Coluna da direita para o timer
        frame_pai.grid_rowconfigure(0, weight=0) # Linha superior para credenciais e timer
        frame_pai.grid_rowconfigure(1, weight=0) # Linha para o agendamento de horários
        frame_pai.grid_rowconfigure(2, weight=1) # Linha para o conteúdo do e-mail (permite expandir)
        frame_pai.grid_rowconfigure(3, weight=0) # Linha para o acionamento manual

        # Seção de Credenciais do Remetente
        frame_remetente = tk.LabelFrame(frame_pai, text="Credenciais do Remetente Expresso")
        frame_remetente.grid(row=0, column=0, padx=10, pady=10, sticky="nsew") # Coluna 0, Linha 0
        
        # Configure a grade dentro do frame_remetente
        frame_remetente.grid_columnconfigure(1, weight=1) # Permite que a entrada de login/senha se expanda

        tk.Label(frame_remetente, text="Login:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entrada_login_remetente = tk.Entry(frame_remetente, width=30) # Reduzido a largura
        self.entrada_login_remetente.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entrada_login_remetente.insert(0, self.config["login_remetente"])

        tk.Label(frame_remetente, text="Senha:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entrada_senha_remetente = tk.Entry(frame_remetente, show="*", width=30) # Reduzido a largura
        self.entrada_senha_remetente.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entrada_senha_remetente.insert(0, self.config["senha_remetente"])

        tk.Button(frame_remetente, text="Salvar Credenciais", command=self.salvar_credenciais_remetente).grid(row=2, column=0, columnspan=2, pady=10)

        # Timer para a próxima execução - MOVIDO PARA CIMA E PARA A DIREITA
        frame_timer = tk.LabelFrame(frame_pai, text="Próxima Execução Agendada")
        frame_timer.grid(row=0, column=1, padx=10, pady=10, sticky="nsew") # Coluna 1, Linha 0
        self.label_proxima_execucao = tk.Label(frame_timer, textvariable=self.proxima_execucao_label_var, font=("Helvetica", 12, "bold"))
        self.label_proxima_execucao.pack(expand=True) # Centraliza o texto dentro do frame_timer

        # Seção de Agendamento
        frame_agendamento = tk.LabelFrame(frame_pai, text="Horários Agendados")
        # span as duas colunas e abaixo das credenciais/timer
        frame_agendamento.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        # Configura a grade dentro do frame_agendamento
        frame_agendamento.grid_columnconfigure(1, weight=1) # Permite que a lista de horários se expanda

        tk.Label(frame_agendamento, text="Horários (HH:MM):").grid(row=0, column=0, padx=5, pady=5, sticky="nw")
        
        self.lista_horarios_box = tk.Listbox(frame_agendamento, height=5, width=20)
        self.lista_horarios_box.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        scrollbar_horarios = tk.Scrollbar(frame_agendamento, orient="vertical", command=self.lista_horarios_box.yview)
        scrollbar_horarios.grid(row=0, column=2, sticky="ns", pady=5)
        self.lista_horarios_box.config(yscrollcommand=scrollbar_horarios.set)

        self.popular_lista_horarios()

        frame_botoes_horario = tk.Frame(frame_agendamento)
        frame_botoes_horario.grid(row=1, column=0, columnspan=3, pady=5)

        tk.Button(frame_botoes_horario, text="Adicionar Horário", command=self.adicionar_horario).pack(side="left", padx=5)
        tk.Button(frame_botoes_horario, text="Remover Horário", command=self.remover_horario).pack(side="left", padx=5)
        
        # Botão para parar o agendamento
        self.btn_parar_agendamento = tk.Button(frame_botoes_horario, text="Parar Agendamento", command=self.parar_agendamento)
        self.btn_parar_agendamento.pack(side="left", padx=5)

        # --- NOVOS CAMPOS PARA ASSUNTO E CORPO DO E-MAIL ---
        frame_conteudo_email = tk.LabelFrame(frame_pai, text="Conteúdo do E-mail")
        # span as duas colunas e abaixo do agendamento
        # Removido 'fill="both", expand=True)' pois não são opções para grid
        frame_conteudo_email.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        tk.Label(frame_conteudo_email, text="Assunto:").pack(padx=5, pady=2, anchor="w")
        self.entrada_assunto_email = tk.Entry(frame_conteudo_email, width=70)
        self.entrada_assunto_email.pack(padx=5, pady=2, fill="x")
        self.entrada_assunto_email.insert(0, self.config["assunto_email"])

        tk.Label(frame_conteudo_email, text="Corpo do E-mail:").pack(padx=5, pady=2, anchor="w")
        self.texto_corpo_email = scrolledtext.ScrolledText(frame_conteudo_email, wrap=tk.WORD, height=8)
        self.texto_corpo_email.pack(padx=5, pady=2, fill="both", expand=True) # Essas opções são para pack, dentro do frame
        self.texto_corpo_email.insert(tk.END, self.config["texto_email_padrao"])

        tk.Button(frame_conteudo_email, text="Salvar Conteúdo do E-mail", command=self.salvar_conteudo_email).pack(pady=10)
        # --- FIM DOS NOVOS CAMPOS ---

        # Seção de Acionamento Manual
        frame_gatilho_manual = tk.LabelFrame(frame_pai, text="Acionamento Manual")
        # span as duas colunas e abaixo do conteúdo do e-mail
        # Removido 'fill="x", expand=True)' pois não são opções para grid
        frame_gatilho_manual.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        tk.Button(frame_gatilho_manual, text="Executar Envio Agora", command=self.executar_automacao_email_em_thread).pack(pady=10)


    def criar_aba_destinatarios(self, frame_pai):
        """Cria os widgets para a aba de gerenciamento de destinatários."""
        self.lista_destinatarios_box = tk.Listbox(frame_pai, height=15)
        self.lista_destinatarios_box.pack(padx=10, pady=10, fill="both", expand=True)

        self.popular_lista_destinatarios()

        frame_acoes = tk.Frame(frame_pai)
        frame_acoes.pack(pady=5)

        tk.Button(frame_acoes, text="Adicionar Destinatário", command=self.adicionar_destinatario).pack(side="left", padx=5)
        tk.Button(frame_acoes, text="Remover Destinatário", command=self.remover_destinatario).pack(side="left", padx=5)
        tk.Button(frame_acoes, text="Editar Destinatário", command=self.editar_destinatario).pack(side="left", padx=5)

    def criar_aba_status(self, frame_pai):
        """Cria o widget para a aba de log de status."""
        self.texto_status = scrolledtext.ScrolledText(frame_pai, wrap=tk.WORD, state="disabled")
        self.texto_status.pack(padx=10, pady=10, fill="both", expand=True)

    def atualizar_status(self, mensagem):
        """Atualiza a caixa de texto de status com uma nova mensagem e timestamp."""
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.texto_status.config(state="normal")
        self.texto_status.insert(tk.END, f"{timestamp} {mensagem}\n")
        self.texto_status.see(tk.END) # Rola para o final
        self.texto_status.config(state="disabled")
        self.root.update_idletasks() # Atualiza a GUI imediatamente

    def salvar_credenciais_remetente(self):
        """Salva as credenciais do remetente e notifica o usuário."""
        self.salvar_configuracao() # Chama a função que já pega os valores dos campos
        messagebox.showinfo("Sucesso", "Credenciais do remetente salvas com sucesso!")
        self.atualizar_status("Credenciais do remetente salvas.")

    def salvar_conteudo_email(self):
        """Salva o assunto e texto do e-mail e notifica o usuário."""
        self.salvar_configuracao() # Chama a função que já pega os valores dos campos
        messagebox.showinfo("Sucesso", "Assunto e texto do e-mail salvos com sucesso!")
        self.atualizar_status("Assunto e texto do e-mail salvos.")

    def popular_lista_horarios(self):
        """Preenche a Listbox de horários com os horários da configuração."""
        self.lista_horarios_box.delete(0, tk.END)
        for horario in self.config["horarios_agendamento"]:
            self.lista_horarios_box.insert(tk.END, horario)
        self.atualizar_timer_proxima_execucao() # Recalcula o timer ao popular a lista

    def validar_horario(self, horario_str):
        """Valida se uma string está no formato HH:MM e é um horário válido."""
        if not horario_str or len(horario_str) != 5 or horario_str.count(":") != 1:
            return False
        try:
            hora, minuto = map(int, horario_str.split(':'))
            if not (0 <= hora <= 23 and 0 <= minuto <= 59):
                return False
        except ValueError:
            return False
        return True

    def adicionar_horario(self):
        """Pede um novo horário ao usuário e o adiciona à lista se for válido, usando comboboxes."""
        
        # Cria uma nova janela Toplevel para a seleção de horário
        top = tk.Toplevel(self.root)
        top.title("Adicionar Horário")
        top.transient(self.root) # Torna-a uma janela filha da principal
        top.grab_set() # Bloqueia interações com outras janelas até que esta seja fechada
        top.resizable(False, False)

        # Frame para os widgets de hora e minuto
        frame_input = tk.Frame(top, padx=20, pady=20)
        frame_input.pack()

        tk.Label(frame_input, text="Hora:").grid(row=0, column=0, padx=5, pady=5)
        # Combobox para a hora (00 a 23)
        self.hora_var = tk.StringVar(top)
        self.hora_combobox = ttk.Combobox(frame_input, textvariable=self.hora_var,
                                        values=[f"{i:02d}" for i in range(24)], state="readonly", width=5)
        self.hora_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.hora_combobox.set("08") # Valor padrão

        tk.Label(frame_input, text="Minuto:").grid(row=1, column=0, padx=5, pady=5)
        # Combobox para o minuto (00 a 59)
        self.minuto_var = tk.StringVar(top)
        self.minuto_combobox = ttk.Combobox(frame_input, textvariable=self.minuto_var,
                                          values=[f"{i:02d}" for i in range(60)], state="readonly", width=5)
        self.minuto_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.minuto_combobox.set("00") # Valor padrão

        def on_adicionar_confirm():
            hora_selecionada = self.hora_var.get()
            minuto_selecionado = self.minuto_var.get()
            novo_horario = f"{hora_selecionada}:{minuto_selecionado}"

            if not self.validar_horario(novo_horario):
                messagebox.showerror("Erro", "Formato de hora inválido. Selecione HH:MM.", parent=top)
                return
            
            if novo_horario not in self.config["horarios_agendamento"]:
                self.config["horarios_agendamento"].append(novo_horario)
                self.salvar_configuracao()
                self.popular_lista_horarios()
                self.atualizar_status(f"Horário adicionado: {novo_horario}")
                self.agendar_verificacao_diaria() # Reinicia o agendador para incluir o novo horário
                top.destroy() # Fecha a janela de seleção
            else:
                messagebox.showwarning("Aviso", "Este horário já está na lista.", parent=top)

        tk.Button(top, text="Adicionar", command=on_adicionar_confirm).pack(pady=10)
        
        # Centraliza a janela Toplevel
        self.root.update_idletasks() # Garante que a geometria da janela principal está atualizada
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (top.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (top.winfo_height() // 2)
        top.geometry(f"+{x}+{y}")


    def remover_horario(self):
        """Remove o horário selecionado da lista."""
        indices_selecionados = self.lista_horarios_box.curselection()
        if indices_selecionados:
            horario_para_remover = self.lista_horarios_box.get(indices_selecionados[0])
            if messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover o horário '{horario_para_remover}'?"):
                self.config["horarios_agendamento"].remove(horario_para_remover)
                self.salvar_configuracao()
                self.popular_lista_horarios()
                self.atualizar_status(f"Horário removido: {horario_para_remover}")
                # Reinicia o agendador para remover o horário
                self.agendar_verificacao_diaria()
                self.atualizar_timer_proxima_execucao() # Recalcula o timer ao remover
        else:
            messagebox.showwarning("Aviso", "Selecione um horário para remover.")

    def popular_lista_destinatarios(self):
        """Preenche a Listbox de destinatários com os e-mails da configuração."""
        self.lista_destinatarios_box.delete(0, tk.END)
        for destinatario in self.config["destinatarios"]:
            self.lista_destinatarios_box.insert(tk.END, destinatario)

    def adicionar_destinatario(self):
        """Pede um novo e-mail de destinatário ao usuário e o adiciona à lista."""
        novo_destinatario = simpledialog.askstring("Adicionar Destinatário", "Insira o novo endereço de e-mail:")
        if novo_destinatario:
            if novo_destinatario not in self.config["destinatarios"]:
                self.config["destinatarios"].append(novo_destinatario)
                self.salvar_configuracao()
                self.popular_lista_destinatarios()
                self.atualizar_status(f"Destinatário adicionado: {novo_destinatario}")
            else:
                messagebox.showwarning("Aviso", "Este endereço de e-mail já existe na lista.")

    def remover_destinatario(self):
        """Remove o destinatário selecionado da lista."""
        indices_selecionados = self.lista_destinatarios_box.curselection()
        if indices_selecionados:
            destinatario_para_remover = self.lista_destinatarios_box.get(indices_selecionados[0])
            if messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover '{destinatario_para_remover}'?"):
                self.config["destinatarios"].remove(destinatario_para_remover)
                self.salvar_configuracao()
                self.popular_lista_destinatarios()
                self.atualizar_status(f"Destinatário removido: {destinatario_para_remover}")
        else:
            messagebox.showwarning("Aviso", "Selecione um destinatário para remover.")

    def editar_destinatario(self):
        """Permite editar o e-mail de um destinatário selecionado."""
        indices_selecionados = self.lista_destinatarios_box.curselection()
        if indices_selecionados:
            destinatario_antigo = self.lista_destinatarios_box.get(indices_selecionados[0])
            novo_destinatario = simpledialog.askstring("Editar Destinatário", f"Editar endereço de e-mail:", initialvalue=destinatario_antigo)
            if novo_destinatario and novo_destinatario != destinatario_antigo:
                if novo_destinatario in self.config["destinatarios"]:
                    messagebox.showwarning("Aviso", "Este endereço de e-mail já existe na lista.")
                    return
                self.config["destinatarios"][indices_selecionados[0]] = novo_destinatario
                self.salvar_configuracao()
                self.popular_lista_destinatarios()
                self.atualizar_status(f"Destinatário alterado de '{destinatario_antigo}' para '{novo_destinatario}'")
        else:
            messagebox.showwarning("Aviso", "Selecione um destinatário para editar.")

    def executar_automacao_email(self):
        """
        Função principal que executa a automação de e-mail.
        Chamada pela thread separada.
        """
        self.atualizar_status("Iniciando automação de e-mail...")
        login = self.config["login_remetente"]
        senha = self.config["senha_remetente"]
        # Destinatários são um set para garantir unicidade, mas precisa ser lista para passar
        destinatarios = list(set(self.config["destinatarios"])) 
        assunto = self.entrada_assunto_email.get()
        texto = self.texto_corpo_email.get("1.0", tk.END).strip()

        if not login or not senha:
            self.atualizar_status("ERRO: Login e/ou senha do remetente não configurados.")
            messagebox.showerror("Erro", "Por favor, configure o login e a senha do remetente na aba 'Remetente e Agendamento'.")
            return

        if not destinatarios:
            self.atualizar_status("AVISO: Nenhum destinatário configurado. O e-mail não será enviado.")
            messagebox.showwarning("Aviso", "Nenhum destinatário configurado. Adicione destinatários na aba 'Destinatários'.")
            return

        try:
            # Atualiza o dicionário config com os dados mais recentes da GUI antes de passar para 'iniciar'
            current_config = self.config.copy()
            current_config["login_remetente"] = login
            current_config["senha_remetente"] = senha
            current_config["destinatarios"] = destinatarios
            current_config["assunto_email"] = assunto
            current_config["texto_email_padrao"] = texto

            automacao_email_principal.iniciar(
                update_status_gui=self.atualizar_status,
                app_config=current_config # Passa o dicionário de configuração completo
            )

            self.atualizar_status("Automação de e-mail concluída.")
        except Exception as e:
            self.atualizar_status(f"ERRO durante a automação de e-mail: {e}")
            messagebox.showerror("Erro de Automação", f"Ocorreu um erro durante a execução da automação: {e}")
        finally:
            self.atualizar_status("Finalizando automação.")
            self.atualizar_timer_proxima_execucao() # Atualiza o timer após a execução

    def executar_automacao_email_em_thread(self):
        """Executa a automação de e-mail em uma thread separada para manter a GUI responsiva."""
        if self.thread_automacao and self.thread_automacao.is_alive():
            messagebox.showwarning("Aviso", "A automação de e-mail já está em execução. Por favor, aguarde.")
            return

        self.thread_automacao = threading.Thread(target=self.executar_automacao_email)
        self.thread_automacao.daemon = True # Define como daemon para fechar com a aplicação principal
        self.thread_automacao.start()

    def agendar_verificacao_diaria(self):
        """Inicia (ou reinicia) a thread do agendador."""
        # Sinaliza para a thread existente parar antes de iniciar uma nova
        if self.thread_verificacao_diaria and self.thread_verificacao_diaria.is_alive():
            self.atualizar_status("Parando agendador existente para reconfigurar...")
            self.stop_scheduler_event.set() # Sinaliza para parar
            self.thread_verificacao_diaria.join(timeout=5) # Espera a thread terminar (com timeout)
            if self.thread_verificacao_diaria.is_alive():
                self.atualizar_status("Aviso: Agendador anterior não parou a tempo.")
            self.stop_scheduler_event.clear() # Limpa o evento para o novo agendamento

        self.atualizar_status(f"Agendador de e-mail configurado para verificar horários diariamente.")
        self.thread_verificacao_diaria = threading.Thread(target=self._loop_agendador_diario)
        self.thread_verificacao_diaria.daemon = True # Garante que a thread termine com a aplicação
        self.thread_verificacao_diaria.start()

    def parar_agendamento(self):
        """Solicita a parada da thread do agendador."""
        if self.thread_verificacao_diaria and self.thread_verificacao_diaria.is_alive():
            self.atualizar_status("Solicitando parada do agendamento...")
            self.stop_scheduler_event.set() # Define o evento para sinalizar a thread
            messagebox.showinfo("Agendamento", "Pedido de parada do agendamento enviado. O agendador será interrompido em breve.")
            self.proxima_execucao_label_var.set("Agendamento Parado.")
        else:
            messagebox.showwarning("Agendamento", "O agendamento não está ativo.")

    def _loop_agendador_diario(self):
        """
        Loop principal da thread do agendador. Verifica os horários e aciona a automação.
        Executa estritamente no minuto agendado e uma única vez por dia para cada horário.
        """
        agendamentos_executados_diariamente = {}
        primeira_execucao_do_dia = True

        self.atualizar_status("Agendador em execução...")

        while not self.stop_scheduler_event.is_set(): # Verifica o evento para continuar ou parar
            now = datetime.now()
            
            # Limpa o registro de execuções do dia anterior à meia-noite
            if agendamentos_executados_diariamente and list(agendamentos_executados_diariamente.values())[0].date() < now.date():
                self.atualizar_status("Um novo dia começou. Reiniciando o registro de agendamentos para o próximo dia.")
                agendamentos_executados_diariamente.clear()
                primeira_execucao_do_dia = True
            elif not agendamentos_executados_diariamente and now.hour == 0 and now.minute == 0 and now.second < 5 and not primeira_execucao_do_dia:
                 self.atualizar_status("Início do dia detectado e agendador reiniciado.")
                 primeira_execucao_do_dia = True # Garante que o estado seja resetado

            for horario_str in self.config["horarios_agendamento"]:
                if self.stop_scheduler_event.is_set(): # Verifica a cada iteração do loop dos horários
                    break # Sai do loop se a parada foi solicitada

                if not self.validar_horario(horario_str):
                    self.atualizar_status(f"AVISO: Horário inválido na configuração: '{horario_str}'. Ignorando.")
                    continue

                hora_agendada, minuto_agendado = map(int, horario_str.split(':'))
                horario_alvo_hoje = now.replace(hour=hora_agendada, minute=minuto_agendado, second=0, microsecond=0)

                executar_agora = (
                    now.hour == horario_alvo_hoje.hour and
                    now.minute == horario_alvo_hoje.minute and
                    now.second >= 0 and now.second < 30 # Executa nos primeiros 30 segundos do minuto agendado
                )

                if executar_agora:
                    ultima_execucao = agendamentos_executados_diariamente.get(horario_str)
                    
                    if ultima_execucao is None or ultima_execucao.date() < now.date():
                        self.atualizar_status(f"Hora agendada '{horario_str}' alcançada. Iniciando automação de e-mail (agendado)...")
                        self.executar_automacao_email_em_thread()
                        agendamentos_executados_diariamente[horario_str] = now
                        self.atualizar_timer_proxima_execucao() # Recalcula o timer após uma execução
            
            primeira_execucao_do_dia = False

            if self.stop_scheduler_event.is_set():
                self.atualizar_status("Agendador parado por solicitação.")
                break

            self.stop_scheduler_event.wait(1) 

        self.atualizar_status("Loop do agendador finalizado.")
        self.stop_scheduler_event.clear()

    def calcular_proxima_execucao(self):
        """Calcula o próximo horário agendado mais próximo."""
        horarios_validos = [h for h in self.config["horarios_agendamento"] if self.validar_horario(h)]
        if not horarios_validos:
            return None

        now = datetime.now()
        proxima_execucao = None
        
        # Considera os horários de hoje
        for horario_str in horarios_validos:
            h, m = map(int, horario_str.split(':'))
            horario_hoje = now.replace(hour=h, minute=m, second=0, microsecond=0)
            
            if horario_hoje > now: # Se o horário ainda não passou hoje
                if proxima_execucao is None or horario_hoje < proxima_execucao:
                    proxima_execucao = horario_hoje
        
        # Se nenhum horário de hoje for futuro, considera os horários de amanhã
        if proxima_execucao is None:
            tomorrow = now + timedelta(days=1)
            for horario_str in horarios_validos:
                h, m = map(int, horario_str.split(':'))
                horario_amanha = tomorrow.replace(hour=h, minute=m, second=0, microsecond=0)
                if proxima_execucao is None or horario_amanha < proxima_execucao:
                    proxima_execucao = horario_amanha
        
        return proxima_execucao

    def atualizar_timer_proxima_execucao(self):
        """Atualiza a label do timer com o tempo restante para a próxima execução."""
        if self.stop_scheduler_event.is_set():
            self.proxima_execucao_label_var.set("Agendamento Parado.")
            return

        proxima_execucao = self.calcular_proxima_execucao()
        
        if proxima_execucao:
            tempo_restante = proxima_execucao - datetime.now()
            
            # Garante que o tempo restante não seja negativo (pode acontecer por pequenas defasagens)
            if tempo_restante.total_seconds() < 0:
                self.proxima_execucao_label_var.set("Calculando próximo agendamento...")
                # Agende uma nova atualização em breve para recalcular
                self.root.after(1000, self.atualizar_timer_proxima_execucao)
                return

            dias = tempo_restante.days
            horas = tempo_restante.seconds // 3600
            minutos = (tempo_restante.seconds % 3600) // 60
            segundos = tempo_restante.seconds % 60

            if dias > 0:
                timer_str = f"{dias}d {horas:02d}h {minutos:02d}m {segundos:02d}s"
            else:
                timer_str = f"{horas:02d}h {minutos:02d}m {segundos:02d}s"
            
            self.proxima_execucao_label_var.set(f"Próxima execução em {timer_str} ({proxima_execucao.strftime('%H:%M')})")
        else:
            self.proxima_execucao_label_var.set("Nenhum horário agendado.")
        
        # Agenda a próxima atualização para daqui a 1 segundo
        self.root.after(1000, self.atualizar_timer_proxima_execucao)


    def ao_fechar_aplicacao(self):
        """Função chamada quando o usuário tenta fechar a janela."""
        if messagebox.askokcancel("Fechar Aplicação", "Tem certeza que deseja fechar a aplicação? O agendamento será parado."):
            self.stop_scheduler_event.set() # Sinaliza para parar a thread do agendador
            
            # Espera a thread do agendador terminar
            if self.thread_verificacao_diaria and self.thread_verificacao_diaria.is_alive():
                self.atualizar_status("Aguardando o agendador finalizar...")
                self.thread_verificacao_diaria.join(timeout=5) # Dá um tempo para a thread terminar
                if self.thread_verificacao_diaria.is_alive():
                    self.atualizar_status("Aviso: Agendador não finalizou.")

            # Se houver uma automação em andamento, tente fechar o driver
            if self.thread_automacao and self.thread_automacao.is_alive():
                 self.atualizar_status("Tentando fechar o navegador da automação em andamento...")
                 # Chamar fechar_driver diretamente na thread principal (GUI) pode ser problemático
                 # É melhor que a própria automação trate isso no finally.
                 # Mas para garantir, podemos tentar aqui também, embora não seja ideal para o driver
                 # que está sendo controlado por outra thread.
                 funcoes_expresso.fechar_driver() # Isso pode ou não funcionar dependendo do estado da outra thread

            self.root.destroy() # Fecha a janela principal da GUI

if __name__ == "__main__":
    root = tk.Tk()
    app = GerenciadorEmailApp(root)
    root.mainloop()