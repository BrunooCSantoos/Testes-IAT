# app_interface.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime

# Importa a classe CalculadoraAposentadoria do nosso módulo
from calculadora_aposentadoria import CalculadoraAposentadoria

# Import reportlab modules for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

class AppCalculadoraAposentadoria:
    def __init__(self, root):
        self.root = root
        root.title("Calculadora de Aposentadoria")
        root.geometry("800x800") # Tamanho da janela ajustado
        root.resizable(False, False)

        # Configuração de estilo (opcional, mas melhora a aparência)
        self.style = ttk.Style()
        self.style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'
        self.style.configure('TFrame', background='#e0e0e0')
        self.style.configure('TLabel', background='#e0e0e0', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10, 'bold'))
        self.style.configure('TEntry', font=('Arial', 10))
        self.style.configure('TRadiobutton', background='#e0e0e0', font=('Arial', 10))

        # Instancia a calculadora importada
        self.calculadora = CalculadoraAposentadoria()

        self._criar_widgets()

    def _criar_widgets(self):
        # Frame para entrada de dados
        input_frame = ttk.LabelFrame(self.root, text="Dados do Contribuinte", padding="10 10 10 10")
        input_frame.pack(padx=10, pady=10, fill="x", expand=True)

        # Layout de grade para os campos de entrada
        input_frame.columnconfigure(1, weight=1) # A coluna de entrada expande

        # Registra a função de validação uma vez
        vcmd = (self.root.register(self._validate_date_input), '%P', '%S', '%i', '%d')
        int_vcmd = (self.root.register(self._validate_int_input), '%P')

        self.entry_vars = {} # Dicionário para armazenar as variáveis Tkinter associadas às entradas

        current_row = 0

        # --- Campos de Data com Validação ---
        date_fields = [
            ("Data de Nascimento (DD/MM/AAAA):", "data_nascimento_var"),
            ("Data de Início no Serviço Público (DD/MM/AAAA):", "data_inicio_servico_var"),
            ("Data de Início no Cargo Atual (DD/MM/AAAA):", "data_inicio_cargo_var")
        ]

        for label_text, var_name in date_fields:
            ttk.Label(input_frame, text=label_text).grid(row=current_row, column=0, sticky="w", pady=2, padx=5)
            var = tk.StringVar()
            entry = ttk.Entry(input_frame, textvariable=var, validate="key", validatecommand=vcmd)
            entry.grid(row=current_row, column=1, sticky="ew", pady=2, padx=5)
            self.entry_vars[var_name] = var
            entry.bind("<KeyRelease>", self._format_date_entry)
            current_row += 1

        # --- Campos de Tempo de Contribuição ---
        ttk.Label(input_frame, text="Tempo de Contribuição:").grid(row=current_row, column=0, sticky="w", pady=5, padx=5)

        time_frame = ttk.Frame(input_frame)
        time_frame.grid(row=current_row, column=1, sticky="ew", pady=2, padx=5)

        self.tempo_contribuicao_anos_var = tk.IntVar(value=0)
        self.tempo_contribuicao_meses_var = tk.IntVar(value=0)
        self.tempo_contribuicao_dias_var = tk.IntVar(value=0)

        ttk.Entry(time_frame, textvariable=self.tempo_contribuicao_anos_var, width=5, validate="key", validatecommand=int_vcmd).pack(side="left", padx=2)
        ttk.Label(time_frame, text="anos").pack(side="left")
        ttk.Entry(time_frame, textvariable=self.tempo_contribuicao_meses_var, width=5, validate="key", validatecommand=int_vcmd).pack(side="left", padx=2)
        ttk.Label(time_frame, text="meses").pack(side="left")
        ttk.Entry(time_frame, textvariable=self.tempo_contribuicao_dias_var, width=5, validate="key", validatecommand=int_vcmd).pack(side="left", padx=2)
        ttk.Label(time_frame, text="dias").pack(side="left")

        current_row += 1

        # Gênero
        ttk.Label(input_frame, text="Gênero:").grid(row=current_row, column=0, sticky="w", pady=5, padx=5)
        self.genero_var = tk.StringVar(value="Mulher") # Valor padrão
        ttk.Radiobutton(input_frame, text="Mulher", variable=self.genero_var, value="Mulher").grid(row=current_row, column=1, sticky="w", padx=5)
        ttk.Radiobutton(input_frame, text="Homem", variable=self.genero_var, value="Homem").grid(row=current_row, column=1, sticky="w", padx=90)
        current_row += 1

        # Frame para botões de cálculo
        button_frame = ttk.Frame(self.root, padding="10 0 10 0")
        button_frame.pack(padx=10, pady=5, fill="x", expand=True)

        ttk.Button(button_frame, text="Calcular Permanência", command=self._calcular_permanente).pack(side="left", padx=5, pady=5, expand=True)
        ttk.Button(button_frame, text="Calcular Transição por Pedágio", command=self._calcular_transicao_pedagio).pack(side="left", padx=5, pady=5, expand=True)
        ttk.Button(button_frame, text="Calcular Transição por Pontos", command=self._calcular_transicao_pontos).pack(side="left", padx=5, pady=5, expand=True)

        # Frame para resultados
        results_frame = ttk.LabelFrame(self.root, text="Resultado", padding="10 10 10 10")
        results_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.result_text = tk.Text(results_frame, wrap="word", height=15, width=70, font=('Arial', 10))
        self.result_text.pack(padx=5, pady=5, fill="both", expand=True)
        self.result_text.config(state="disabled") # Torna o campo de texto somente leitura

        # NOVO: Frame para o botão de impressão, abaixo da caixa de resultados
        print_button_frame = ttk.Frame(self.root, padding="0 5 0 10")
        print_button_frame.pack(padx=10, pady=5, fill="x", expand=True)

        ttk.Button(print_button_frame, text="Imprimir Opções (PDF)", command=self._imprimir_opcoes_pdf).pack(side="right", padx=5, pady=5) # 'side="right"' para alinhar à direita

    def _validate_date_input(self, P, S, index, action):
        """
        Valida a entrada de data, permitindo apenas números.
        A formatação com barras é feita no _format_date_entry.
        """
        if action == '1': # Inserção
            if not S.isdigit():
                return False
            if len(P) > 10:
                return False
        return True

    def _validate_int_input(self, P):
        """Valida a entrada para permitir apenas números inteiros."""
        if P.strip() == "":
            return True # Allow empty string for clearing
        try:
            int(P)
            return True
        except ValueError:
            return False

    def _format_date_entry(self, event):
        """
        Formata o texto no campo de data para DD/MM/AAAA automaticamente.
        Chamada no evento <KeyRelease>.
        """
        entry_widget = event.widget
        var = entry_widget.cget("textvariable")
        current_text = self.root.getvar(var)

        clean_digits = "".join(filter(str.isdigit, current_text))
        formatted_text = ""

        for i, digit in enumerate(clean_digits):
            if i < 8: # Limita a 8 dígitos para DDMMYYYY
                formatted_text += digit
            if (i == 1 or i == 3) and i + 1 < len(clean_digits): # Adiciona barras após o 2º e 4º dígito se houver mais dígitos
                formatted_text += '/'

        if event.keysym.isdigit():
            cursor_pos = entry_widget.index(tk.INSERT)
            if cursor_pos in [2, 5] and formatted_text and formatted_text[cursor_pos-1] != '/':
                entry_widget.icursor(cursor_pos + 1)

        if formatted_text != current_text:
            self.root.setvar(var, formatted_text)
            new_cursor_pos = len(formatted_text)
            if len(clean_digits) == 2 or len(clean_digits) == 4:
                new_cursor_pos = event.widget.index(tk.INSERT) + 1
            entry_widget.icursor(new_cursor_pos)

    def _obter_e_validar_dados(self):
        """Obtém os dados da interface e os atribui ao objeto calculadora."""
        try:
            self.calculadora.genero = self.genero_var.get()

            # Get and validate tempo_contribuicao parts
            anos = self.tempo_contribuicao_anos_var.get()
            meses = self.tempo_contribuicao_meses_var.get()
            dias = self.tempo_contribuicao_dias_var.get()

            # --- New validation for months and days ---
            if meses < 0 or meses > 12:
                messagebox.showerror("Erro de Entrada", "Meses de contribuição devem ser entre 0 e 12.")
                return False
            if dias < 0 or dias > 31:
                messagebox.showerror("Erro de Entrada", "Dias de contribuição devem ser entre 0 e 31.")
                return False
            # --- End of new validation ---

            self.calculadora.tempo_contribuicao_anos = anos
            self.calculadora.tempo_contribuicao_meses = meses
            self.calculadora.tempo_contribuicao_dias = dias

            # Validação e conversão de datas (DD/MM/AAAA)
            date_attr_map = {
                "data_nascimento_var": "data_nascimento",
                "data_inicio_servico_var": "data_inicio_servico",
                "data_inicio_cargo_var": "data_inicio_cargo"
            }

            for ui_var, calc_attr in date_attr_map.items():
                date_str = self.entry_vars[ui_var].get()
                if date_str:
                    try:
                        setattr(self.calculadora, calc_attr, datetime.datetime.strptime(date_str, '%d/%m/%Y').date())
                    except ValueError:
                        messagebox.showerror("Erro de Entrada", f"Formato de data inválido para '{date_str}'. Use DD/MM/AAAA.")
                        return False
                else:
                    setattr(self.calculadora, calc_attr, None)

            if self.calculadora.data_nascimento is None:
                messagebox.showerror("Erro de Entrada", "Data de Nascimento é obrigatória.")
                return False

            return True
        except ValueError as e:
            messagebox.showerror("Erro de Entrada", f"Por favor, insira valores válidos. Erro: {e}\n"
                                                  "Certifique-se de que Tempo de Contribuição são números e datas são no formato DD/MM/AAAA.")
            return False

    def _exibir_resultado(self, titulo, resultado):
        """Formata e exibe os resultados na área de texto."""
        self.result_text.config(state="normal") # Habilita para escrita
        self.result_text.delete(1.0, tk.END) # Limpa resultados anteriores

        output = f"--- {titulo} ---\n\n"

        # Display input data
        output += "Dados Informados:\n"
        output += f"  Gênero: {self.calculadora.genero}\n"
        output += f"  Data de Nascimento: {self.calculadora.data_nascimento.strftime('%d/%m/%Y') if self.calculadora.data_nascimento else 'Não Informada'}\n"
        output += f"  Tempo de Contribuição: {self.calculadora.tempo_contribuicao_anos} anos, {self.calculadora.tempo_contribuicao_meses} meses e {self.calculadora.tempo_contribuicao_dias} dias\n"
        output += f"  Data de Início no Serviço Público: {self.calculadora.data_inicio_servico.strftime('%d/%m/%Y') if self.calculadora.data_inicio_servico else 'Não Informada'}\n"
        output += f"  Data de Início no Cargo Atual: {self.calculadora.data_inicio_cargo.strftime('%d/%m/%Y') if self.calculadora.data_inicio_cargo else 'Não Informada'}\n\n"

        if resultado["elegivel"]:
            output += "✅ **Elegível!**\n"
            output += f"\nBenefício: {resultado['beneficio']}"
        else:
            output += "❌ **Não Elegível.**\n\n"
            output += "Requisitos Faltantes:\n"
            if not resultado["requisitos_faltantes"]:
                output += "- Não foi possível determinar os requisitos faltantes (verifique os dados de entrada ou lógica da regra).\n"
            for req, val in resultado["requisitos_faltantes"].items():
                if req == 'soma_idade_tempo_contribuicao': # Specific handling for this key
                    req_nome = "Soma idade + tempo de contribuicao"
                else:
                    req_nome = req.replace('_', ' ').capitalize() # Formata o nome para exibir

                if "tempo" in req_nome.lower() or "pedagio" in req_nome.lower() or "idade" in req_nome.lower():
                    # Format missing time or age requirements using _converter_decimal_para_tempo
                    anos, meses, dias = self.calculadora._converter_decimal_para_tempo(val)
                    output += f"- {req_nome}: {anos} anos, {meses} meses e {dias} dias\n"
                elif "pontos" in req_nome.lower() or "soma" in req_nome.lower():
                    output += f"- {req_nome}: {val:.2f}\n" # For points, keep decimal if applicable
                else:
                    output += f"- {req_nome}: {val}\n" # Catch-all for other types

        self.result_text.insert(tk.END, output)
        self.result_text.config(state="disabled") # Desabilita novamente

    def _calcular_permanente(self):
        if self._obter_e_validar_dados():
            resultado = self.calculadora.regra_permanente()
            self._exibir_resultado("Regra de Permanência", resultado)

    def _calcular_transicao_pedagio(self):
        if self._obter_e_validar_dados():
            resultado = self.calculadora.regra_transicao_pedagio()
            self._exibir_resultado("Regra de Transição por Pedágio", resultado)

    def _calcular_transicao_pontos(self):
        if self._obter_e_validar_dados():
            resultado = self.calculadora.regra_transicao_pontos()
            self._exibir_resultado("Regra de Transição por Pontos", resultado)

    def _format_result_for_pdf(self, title, result):
        """Helper to format calculation results for PDF."""
        content = []
        styles = getSampleStyleSheet()

        content.append(Paragraph(f"<b>--- {title} ---</b>", styles['h2']))
        content.append(Spacer(1, 0.1 * inch))

        if result["elegivel"]:
            content.append(Paragraph("<b>✅ Elegível!</b>", styles['Normal']))
            content.append(Paragraph(f"Benefício: {result['beneficio']}", styles['Normal']))
        else:
            content.append(Paragraph("<b>❌ Não Elegível.</b>", styles['Normal']))
            content.append(Paragraph("Requisitos Faltantes:", styles['Normal']))
            if not result["requisitos_faltantes"]:
                content.append(Paragraph("- Não foi possível determinar os requisitos faltantes (verifique os dados de entrada ou lógica da regra).", styles['Normal']))
            for req, val in result["requisitos_faltantes"].items():
                if req == 'soma_idade_tempo_contribuicao': # Specific handling for this key
                    req_nome = "Soma idade + tempo de contribuicao"
                else:
                    req_nome = req.replace('_', ' ').capitalize()

                if "tempo" in req_nome.lower() or "pedagio" in req_nome.lower() or "idade" in req_nome.lower():
                    anos, meses, dias = self.calculadora._converter_decimal_para_tempo(val)
                    content.append(Paragraph(f"- {req_nome}: {anos} anos, {meses} meses e {dias} dias", styles['Normal']))
                elif "pontos" in req_nome.lower() or "soma" in req_nome.lower():
                    content.append(Paragraph(f"- {req_nome}: {val:.2f}", styles['Normal']))
                else:
                    content.append(Paragraph(f"- {req_nome}: {val}", styles['Normal']))
        content.append(Spacer(1, 0.2 * inch))
        return content

    def _imprimir_opcoes_pdf(self):
        if not self._obter_e_validar_dados():
            return

        # Abre o prompt para selecionar o local e nome do arquivo
        file_name = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os Arquivos", "*.*")],
            initialfile="RelatorioAposentadoria.pdf", # Nome de arquivo sugerido
            title="Salvar Relatório de Aposentadoria como"
        )

        if not file_name: # Se o usuário cancelar a seleção
            return

        doc = SimpleDocTemplate(file_name, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # ... (restante do seu código para gerar o PDF) ...
        # Seções de "Dados Informados", "Regra de Aposentadoria Permanente", etc.
        # Todo o código abaixo desta parte permanece o mesmo.

        # Dados Informados
        story.append(Paragraph("<b>Dados Informados</b>", styles['h1']))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"Gênero: {self.calculadora.genero}", styles['Normal']))
        story.append(Paragraph(f"Data de Nascimento: {self.calculadora.data_nascimento.strftime('%d/%m/%Y') if self.calculadora.data_nascimento else 'Não Informada'}", styles['Normal']))
        story.append(Paragraph(f"Tempo de Contribuicao: {self.calculadora.tempo_contribuicao_anos} anos, {self.calculadora.tempo_contribuicao_meses} meses e {self.calculadora.tempo_contribuicao_dias} dias", styles['Normal']))
        story.append(Paragraph(f"Data de Inicio no Servico Publico: {self.calculadora.data_inicio_servico.strftime('%d/%m/%Y') if self.calculadora.data_inicio_servico else 'Não Informada'}", styles['Normal']))
        story.append(Paragraph(f"Data de Inicio no Cargo Atual: {self.calculadora.data_inicio_cargo.strftime('%d/%m/%Y') if self.calculadora.data_inicio_cargo else 'Não Informada'}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))

        # Calcular e adicionar resultados para cada regra
        resultado_permanente = self.calculadora.regra_permanente()
        story.extend(self._format_result_for_pdf("Regra de Permanência", resultado_permanente))

        resultado_pedagio = self.calculadora.regra_transicao_pedagio()
        story.extend(self._format_result_for_pdf("Regra de Transicao por Pedagio", resultado_pedagio))

        resultado_pontos = self.calculadora.regra_transicao_pontos()
        story.extend(self._format_result_for_pdf("Regra de Transicao por Pontos", resultado_pontos))

        try:
            doc.build(story)
            messagebox.showinfo("PDF Gerado", f"O relatorio de aposentadoria foi salvo como '{file_name}'.")
        except Exception as e:
            messagebox.showerror("Erro ao Gerar PDF", f"Ocorreu um erro ao gerar o PDF: {e}")