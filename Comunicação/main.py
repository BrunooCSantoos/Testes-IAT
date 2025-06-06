import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
from cronograma_manager import GerenciadorCronograma
import json
from datetime import datetime, timedelta

class AppCronograma:
    def __init__(self, master):
        self.master = master
        master.title("Gerenciador de Cronograma da Equipe")
        master.geometry("600x400") # Tamanho inicial da janela

        self.gerenciador = GerenciadorCronograma() # Instancia o gerenciador

        self.criar_widgets_menu_principal()

    def criar_widgets_menu_principal(self):
        self.frame_principal = tk.Frame(self.master, padx=20, pady=20)
        self.frame_principal.pack(expand=True, fill='both')

        tk.Label(self.frame_principal, text="Selecione um Membro ou Gerencie:", font=("Arial", 16, "bold")).pack(pady=10)

        # Botões para cada membro da equipe
        for _, membro in self.gerenciador.equipe.iterrows():
            btn_membro = tk.Button(self.frame_principal, text=f"Entrar como {membro['Nome']}",
                                   command=lambda m=membro['Nome']: self.abrir_interface_membro(m),
                                   width=30, height=2, font=("Arial", 12))
            btn_membro.pack(pady=5)

        tk.Label(self.frame_principal, text="\n--- Gerenciamento ---", font=("Arial", 14, "bold")).pack(pady=10)

        # Botões de gerenciamento
        tk.Button(self.frame_principal, text="Visualizar Cronograma Completo",
                  command=self.visualizar_cronograma_completo, width=30, height=2, font=("Arial", 12)).pack(pady=5)
        tk.Button(self.frame_principal, text="Adicionar Membro",
                  command=self.adicionar_membro_gui, width=30, height=2, font=("Arial", 12)).pack(pady=5)
        tk.Button(self.frame_principal, text="Adicionar Tarefa",
                  command=self.adicionar_tarefa_gui, width=30, height=2, font=("Arial", 12)).pack(pady=5)
        tk.Button(self.frame_principal, text="Gerar Cronograma",
                  command=self.gerar_cronograma_gui, width=30, height=2, font=("Arial", 12)).pack(pady=5)


    def adicionar_membro_gui(self):
        nome = simpledialog.askstring("Adicionar Membro", "Nome do membro:")
        if nome:
            habilidades_str = simpledialog.askstring("Adicionar Membro", "Habilidades (separadas por vírgula):")
            habilidades = [h.strip() for h in habilidades_str.split(',')] if habilidades_str else []
            disponibilidade_str = simpledialog.askstring("Adicionar Membro", "Disponibilidade Diária (horas):")
            try:
                disponibilidade = float(disponibilidade_str)
                self.gerenciador.adicionar_membro(nome, habilidades, disponibilidade)
                messagebox.showinfo("Sucesso", f"Membro '{nome}' adicionado.")
                self.atualizar_menu_principal()
            except ValueError:
                messagebox.showerror("Erro", "Disponibilidade inválida. Use um número.")

    def adicionar_tarefa_gui(self):
        nome = simpledialog.askstring("Adicionar Tarefa", "Nome da tarefa:")
        if nome:
            prazo_str = simpledialog.askstring("Adicionar Tarefa", "Prazo final (AAAA-MM-DD):")
            duracao_str = simpledialog.askstring("Adicionar Tarefa", "Duração estimada (horas):")
            prioridade_str = simpledialog.askstring("Adicionar Tarefa", "Prioridade (0=alta, 1=média, 2=baixa):")
            habilidades_str = simpledialog.askstring("Adicionar Tarefa", "Habilidades requeridas (separadas por vírgula):")
            passos_str = simpledialog.askstring("Adicionar Tarefa", "Passos (JSON, ex: [{\"nome\":\"Design\",\"habilidades\":[\"Design\"]}, {\"nome\":\"Dev\",\"habilidades\":[\"Desenvolvimento\"]}])\nDeixe vazio para um único passo 'Concluir':")

            try:
                duracao = float(duracao_str)
                prioridade = int(prioridade_str)
                habilidades = [h.strip() for h in habilidades_str.split(',')] if habilidades_str else None
                passos = json.loads(passos_str) if passos_str else None

                self.gerenciador.adicionar_tarefa(nome, prazo_str, duracao, prioridade, habilidades, passos)
                messagebox.showinfo("Sucesso", f"Tarefa '{nome}' adicionada.")
            except (ValueError, json.JSONDecodeError) as e:
                messagebox.showerror("Erro", f"Entrada inválida: {e}")

    def gerar_cronograma_gui(self):
        data_inicio_str = simpledialog.askstring("Gerar Cronograma", "Data de Início (AAAA-MM-DD):")
        data_fim_str = simpledialog.askstring("Gerar Cronograma", "Data de Fim (AAAA-MM-DD):")

        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
            self.gerenciador.gerar_cronograma(data_inicio, data_fim)
            messagebox.showinfo("Sucesso", "Cronograma gerado com sucesso!")
            self.visualizar_cronograma_completo() # Mostra o cronograma após gerar
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido. Use AAAA-MM-DD.")


    def visualizar_cronograma_completo(self):
        cronograma_window = tk.Toplevel(self.master)
        cronograma_window.title("Cronograma Completo")
        cronograma_window.geometry("800x600")

        tk.Label(cronograma_window, text="Cronograma Geral:", font=("Arial", 14, "bold")).pack(pady=10)

        # Usar um Text widget para exibir o cronograma
        text_widget = tk.Text(cronograma_window, wrap='word', height=30, width=90)
        text_widget.pack(padx=10, pady=10)

        if not self.gerenciador.cronograma_gerado.empty:
            # Formata para exibir melhor
            cronograma_str = self.gerenciador.cronograma_gerado.to_string(index=False)
            text_widget.insert(tk.END, cronograma_str)
        else:
            text_widget.insert(tk.END, "Nenhum cronograma gerado ainda ou está vazio.")

        text_widget.config(state='disabled') # Torna o texto somente leitura


    def atualizar_menu_principal(self):
        # Limpa e recria os widgets para refletir novos membros
        for widget in self.frame_principal.winfo_children():
            widget.destroy()
        self.criar_widgets_menu_principal()


    def abrir_interface_membro(self, nome_membro):
        membro_window = tk.Toplevel(self.master)
        membro_window.title(f"Tarefas de {nome_membro}")
        membro_window.geometry("700x500")

        tk.Label(membro_window, text=f"Bem-vindo(a), {nome_membro}!", font=("Arial", 16, "bold")).pack(pady=10)

        frame_tarefas = tk.Frame(membro_window)
        frame_tarefas.pack(padx=20, pady=10, fill='both', expand=True)

        self.lista_tarefas_membro(frame_tarefas, nome_membro)

        btn_voltar = tk.Button(membro_window, text="Voltar", command=membro_window.destroy)
        btn_voltar.pack(pady=10)

    def lista_tarefas_membro(self, parent_frame, nome_membro):
        # Limpa o frame antes de adicionar novos widgets
        for widget in parent_frame.winfo_children():
            widget.destroy()

        tarefas_do_membro = self.gerenciador.obter_tarefas_por_membro(nome_membro)

        if tarefas_do_membro.empty:
            tk.Label(parent_frame, text="Você não tem tarefas atribuídas no momento.", font=("Arial", 12)).pack(pady=20)
        else:
            tk.Label(parent_frame, text="Suas Tarefas Atribuídas:", font=("Arial", 14)).pack(pady=10)
            for index, tarefa in tarefas_do_membro.iterrows():
                passo_atual = tarefa['Passos'][tarefa['PassoAtualIndice']]
                tarefa_info = f"Tarefa: {tarefa['Nome']} - Passo: {passo_atual['nome']}\nDuração Estimada: {tarefa['DuracaoEstimadaHoras']}h - Prazo: {tarefa['PrazoFinal'].strftime('%Y-%m-%d')}"
                tk.Label(parent_frame, text=tarefa_info, justify='left', wraplength=400, font=("Arial", 10)).pack(pady=5, anchor='w')

                btn_concluir = tk.Button(parent_frame, text=f"Concluir '{passo_atual['nome']}'",
                                         command=lambda t=tarefa['Nome'], m=nome_membro: self.marcar_e_atualizar(t, m, parent_frame, nome_membro))
                btn_concluir.pack(pady=2)
                tk.Frame(parent_frame, height=1, bg='lightgray').pack(fill='x', pady=5) # Separador

    def marcar_e_atualizar(self, nome_tarefa, nome_membro, parent_frame, nome_membro_original):
        if self.gerenciador.marcar_tarefa_concluida(nome_tarefa, nome_membro):
            messagebox.showinfo("Sucesso", f"Tarefa '{nome_tarefa}' atualizada!")
            # Atualiza a lista de tarefas para o membro
            self.lista_tarefas_membro(parent_frame, nome_membro_original)
            # Re-gerar o cronograma para reatribuir a tarefa ao próximo membro se houver
            self.gerenciador.gerar_cronograma(datetime.now(), datetime.now() + timedelta(days=30)) # Regenera para o próximo mês
        else:
            messagebox.showerror("Erro", "Não foi possível atualizar a tarefa.")

# --- Execução da Aplicação ---
if __name__ == "__main__":
    # Inicializa alguns dados se os arquivos não existirem
    gerenciador_inicial = GerenciadorCronograma()
    if gerenciador_inicial.equipe.empty:
        gerenciador_inicial.adicionar_membro("Alice", ["Desenvolvimento", "Testes"], 8)
        gerenciador_inicial.adicionar_membro("Bob", ["Desenvolvimento"], 6)
        gerenciador_inicial.adicionar_membro("Charlie", ["Testes", "Design"], 7)
    if gerenciador_inicial.tarefas.empty:
        gerenciador_inicial.adicionar_tarefa(
            "Desenvolvimento do Módulo X", "2025-07-01", 40, 0, # Prioridade 0 = mais alta
            passos=[
                {"nome": "Design da Interface", "habilidades": ["Design"]},
                {"nome": "Codificação Front-end", "habilidades": ["Desenvolvimento"]},
                {"nome": "Codificação Back-end", "habilidades": ["Desenvolvimento"]},
                {"nome": "Testes de Integração", "habilidades": ["Testes"]}
            ]
        )
        gerenciador_inicial.adicionar_tarefa("Revisão de Código", "2025-06-15", 8, 1, ["Desenvolvimento"])
        gerenciador_inicial.adicionar_tarefa("Preparar Documentação", "2025-06-20", 12, 2, ["Desenvolvimento"])

    # Re-instancia o gerenciador para garantir que os dados sejam carregados corretamente
    # (ou você pode passar a instância gerenciador_inicial para o AppCronograma)
    root = tk.Tk()
    app = AppCronograma(root)
    root.mainloop()