import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import tkinter.ttk as ttk # Importa ttk para o Notebook (abas)
import threading
import time
import json
import os
from datetime import datetime, timedelta

# Importa a função iniciar modificada
import main as automacao_email_principal
# Importa a função email_expresso modificada (e outras se necessário)
import expresso_funcoes as funcoes_expresso

ARQUIVO_CONFIG = "configuracao_email.json"

class GerenciadorEmailApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de E-mail Expresso")
        self.root.geometry("800x600")

        self.config = self.carregar_configuracao()

        self.criar_widgets()
        self.agendar_verificacao_diaria()

    def carregar_configuracao(self):
        if os.path.exists(ARQUIVO_CONFIG):
            with open(ARQUIVO_CONFIG, 'r') as f:
                return json.load(f)
        return {
            "login_remetente": "",
            "senha_remetente": "", # Considerar armazenamento mais seguro para produção
            "destinatarios": [],
            "horario_agendamento": "08:00" # Horário padrão
        }

    def salvar_configuracao(self):
        with open(ARQUIVO_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=4)

    def criar_widgets(self):
        # Notebook para abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Aba 1: Remetente e Agendamento
        self.frame_remetente_agendamento = tk.Frame(self.notebook)
        self.notebook.add(self.frame_remetente_agendamento, text="Remetente e Agendamento")
        self.criar_aba_remetente_agendamento(self.frame_remetente_agendamento)

        # Aba 2: Destinatários
        self.frame_destinatarios = tk.Frame(self.notebook)
        self.notebook.add(self.frame_destinatarios, text="Destinatários")
        self.criar_aba_destinatarios(self.frame_destinatarios)

        # Aba 3: Log de Status
        self.frame_status = tk.Frame(self.notebook)
        self.notebook.add(self.frame_status, text="Log de Status")
        self.criar_aba_status(self.frame_status)

    def criar_aba_remetente_agendamento(self, frame_pai):
        # Credenciais do Remetente
        frame_remetente = tk.LabelFrame(frame_pai, text="Credenciais do Remetente Expresso")
        frame_remetente.pack(padx=10, pady=10, fill="x")

        tk.Label(frame_remetente, text="Login:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entrada_login_remetente = tk.Entry(frame_remetente, width=40)
        self.entrada_login_remetente.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entrada_login_remetente.insert(0, self.config["login_remetente"])

        tk.Label(frame_remetente, text="Senha:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entrada_senha_remetente = tk.Entry(frame_remetente, show="*", width=40)
        self.entrada_senha_remetente.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entrada_senha_remetente.insert(0, self.config["senha_remetente"]) # Não é ideal para segurança, mas para simplicidade

        tk.Button(frame_remetente, text="Salvar Credenciais", command=self.salvar_credenciais_remetente).grid(row=2, column=0, columnspan=2, pady=10)

        # Configurações de Agendamento
        frame_agendamento = tk.LabelFrame(frame_pai, text="Agendamento Diário do E-mail")
        frame_agendamento.pack(padx=10, pady=10, fill="x")

        tk.Label(frame_agendamento, text="Horário de Envio (HH:MM):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entrada_horario_agendamento = tk.Entry(frame_agendamento, width=10)
        self.entrada_horario_agendamento.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entrada_horario_agendamento.insert(0, self.config["horario_agendamento"])

        tk.Button(frame_agendamento, text="Salvar Horário", command=self.salvar_horario_agendamento).grid(row=1, column=0, columnspan=2, pady=10)

        # Acionamento Manual
        frame_gatilho_manual = tk.LabelFrame(frame_pai, text="Acionamento Manual")
        frame_gatilho_manual.pack(padx=10, pady=10, fill="x")
        tk.Button(frame_gatilho_manual, text="Executar Envio Agora", command=self.executar_automacao_email_em_thread).pack(pady=10)

    def criar_aba_destinatarios(self, frame_pai):
        # Lista de Destinatários
        self.lista_destinatarios_box = tk.Listbox(frame_pai, height=15)
        self.lista_destinatarios_box.pack(padx=10, pady=10, fill="both", expand=True)

        self.popular_lista_destinatarios()

        # Ações de Destinatários
        frame_acoes = tk.Frame(frame_pai)
        frame_acoes.pack(pady=5)

        tk.Button(frame_acoes, text="Adicionar Destinatário", command=self.adicionar_destinatario).pack(side="left", padx=5)
        tk.Button(frame_acoes, text="Remover Destinatário", command=self.remover_destinatario).pack(side="left", padx=5)
        tk.Button(frame_acoes, text="Editar Destinatário", command=self.editar_destinatario).pack(side="left", padx=5)

    def criar_aba_status(self, frame_pai):
        self.texto_status = scrolledtext.ScrolledText(frame_pai, wrap=tk.WORD, state="disabled")
        self.texto_status.pack(padx=10, pady=10, fill="both", expand=True)

    def atualizar_status(self, mensagem):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.texto_status.config(state="normal")
        self.texto_status.insert(tk.END, f"{timestamp} {mensagem}\n")
        self.texto_status.see(tk.END) # Rola automaticamente para o final
        self.texto_status.config(state="disabled")
        self.root.update_idletasks() # Força a atualização da GUI

    def salvar_credenciais_remetente(self):
        self.config["login_remetente"] = self.entrada_login_remetente.get()
        self.config["senha_remetente"] = self.entrada_senha_remetente.get()
        self.salvar_configuracao()
        messagebox.showinfo("Sucesso", "Credenciais do remetente salvas com sucesso!")

    def salvar_horario_agendamento(self):
        novo_horario = self.entrada_horario_agendamento.get()
        if not novo_horario.replace(":", "").isdigit() or len(novo_horario) != 5 or novo_horario.count(":") != 1:
            messagebox.showerror("Erro", "Formato de hora inválido. Use HH:MM (ex: 08:00).")
            return

        try:
            hora, minuto = map(int, novo_horario.split(':'))
            if not (0 <= hora <= 23 and 0 <= minuto <= 59):
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Horário inválido. Horas devem ser entre 00 e 23, minutos entre 00 e 59.")
            return

        self.config["horario_agendamento"] = novo_horario
        self.salvar_configuracao()
        messagebox.showinfo("Sucesso", f"Horário de envio agendado para {novo_horario} diariamente.")
        self.agendar_verificacao_diaria() # Reagendar imediatamente se o horário mudar

    def popular_lista_destinatarios(self):
        self.lista_destinatarios_box.delete(0, tk.END)
        for destinatario in self.config["destinatarios"]:
            self.lista_destinatarios_box.insert(tk.END, destinatario)

    def adicionar_destinatario(self):
        novo_destinatario = simpledialog.askstring("Adicionar Destinatário", "Insira o novo endereço de e-mail:")
        if novo_destinatario and novo_destinatario not in self.config["destinatarios"]:
            self.config["destinatarios"].append(novo_destinatario)
            self.salvar_configuracao()
            self.popular_lista_destinatarios()
            self.atualizar_status(f"Destinatário adicionado: {novo_destinatario}")

    def remover_destinatario(self):
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
        self.atualizar_status("Iniciando automação de e-mail...")
        login = self.config["login_remetente"]
        senha = self.config["senha_remetente"]
        destinatarios = set(self.config["destinatarios"]) # Usa um set para destinatários

        if not login or not senha:
            self.atualizar_status("ERRO: Login e/ou senha do remetente não configurados.")
            messagebox.showerror("Erro", "Por favor, configure o login e a senha do remetente na aba 'Remetente e Agendamento'.")
            return

        if not destinatarios:
            self.atualizar_status("AVISO: Nenhum destinatário configurado. O e-mail não será enviado.")
            messagebox.showwarning("Aviso", "Nenhum destinatário configurado. Adicione destinatários na aba 'Destinatários'.")
            return

        try:
            # Sobrescreve funcoes_expresso.email_expresso para usar as credenciais armazenadas
            # Isso é um patch temporário. Um design melhor seria passar as credenciais
            # diretamente para automacao_email_principal.iniciar ou modificar funcoes_expresso
            # para aceitar uma configuração global.
            # Para este exemplo, vamos fazer o patch antes de chamar iniciar.
            original_email_expresso = funcoes_expresso.email_expresso
            funcoes_expresso.email_expresso = lambda: original_email_expresso(login, senha)

            # Para que main.py use os destinatários da GUI, você precisa modificar a função 'iniciar' em main.py
            # para aceitar um argumento 'destinatarios' e usar essa lista.
            # Exemplo de como chamaria se 'iniciar' aceitasse 'destinatarios':
            # automacao_email_principal.iniciar(self.atualizar_status, destinatarios)

            # Chamada atual (considerando que main.py ainda tem destinatários hardcoded para demonstração)
            automacao_email_principal.iniciar(self.atualizar_status)

            # Restaura o email_expresso original após a chamada
            funcoes_expresso.email_expresso = original_email_expresso

            self.atualizar_status("Automação de e-mail concluída.")
        except Exception as e:
            self.atualizar_status(f"ERRO durante a automação de e-mail: {e}")
            messagebox.showerror("Erro de Automação", f"Ocorreu um erro durante a execução da automação: {e}")
        finally:
            self.atualizar_status("Finalizando automação.")

    def executar_automacao_email_em_thread(self):
        """Executa a automação de e-mail em uma thread separada para manter a GUI responsiva."""
        if hasattr(self, 'thread_automacao') and self.thread_automacao.is_alive():
            messagebox.showwarning("Aviso", "A automação de e-mail já está em execução. Por favor, aguarde.")
            return

        self.thread_automacao = threading.Thread(target=self.executar_automacao_email)
        self.thread_automacao.start()


    def agendar_verificacao_diaria(self):
        # Limpa quaisquer verificações agendadas existentes para evitar duplicatas
        if hasattr(self, 'thread_verificacao_diaria') and self.thread_verificacao_diaria.is_alive():
            # Em uma aplicação real, você precisaria de uma maneira mais robusta para parar uma thread em execução
            # ou garantir que apenas uma thread de agendamento esteja ativa. Para simplicidade, assumimos
            # que uma nova thread substitui a lógica antiga na mudança de agendamento.
            pass

        self.atualizar_status(f"Agendador de e-mail configurado para verificar às {self.config['horario_agendamento']} diariamente.")
        self.thread_verificacao_diaria = threading.Thread(target=self._loop_agendador_diario)
        self.thread_verificacao_diaria.daemon = True # Permite que a thread saia quando o programa principal sai
        self.thread_verificacao_diaria.start()

    def _loop_agendador_diario(self):
        while True:
            now = datetime.now()
            hora_agendada, minuto_agendado = map(int, self.config["horario_agendamento"].split(':'))
            
            # Calcula o próximo horário de execução
            horario_agendado_hoje = now.replace(hour=hora_agendada, minute=minuto_agendado, second=0, microsecond=0)

            if now >= horario_agendado_hoje:
                # Se o horário agendado para hoje já passou, agende para amanhã
                proximo_horario_execucao = horario_agendado_hoje + timedelta(days=1)
            else:
                # Caso contrário, agende para hoje
                proximo_horario_execucao = horario_agendado_hoje

            tempo_para_esperar = (proximo_horario_execucao - now).total_seconds()

            if tempo_para_esperar > 0:
                self.atualizar_status(f"Próxima verificação agendada para: {proximo_horario_execucao.strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(tempo_para_esperar) # Espera até o próximo horário agendado

            # Verifica novamente se o horário está exatamente certo, ou se acabamos de acordar de um longo sono
            now_depois_espera = datetime.now()
            if now_depois_espera.hour == hora_agendada and now_depois_espera.minute == minuto_agendado:
                self.atualizar_status("Hora agendada alcançada. Iniciando automação de e-mail (agendado)...")
                self.executar_automacao_email_em_thread()
            
            # Após a execução (ou se não for o minuto exato), aguarde um minuto completo
            # antes de verificar novamente para evitar looping constante e reacionamento.
            # Isso também garante que não acionemos várias vezes no mesmo minuto.
            time.sleep(60) # Espera por um minuto antes da próxima verificação

if __name__ == "__main__":
    root = tk.Tk()
    app = GerenciadorEmailApp(root)
    root.mainloop()