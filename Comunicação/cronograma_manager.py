# cronograma_manager.py

import pandas as pd
from datetime import datetime, timedelta
import json
import os

class GerenciadorCronograma:
    def __init__(self, arquivo_dados_equipe='equipe.json', arquivo_dados_tarefas='tarefas.json'):
        self.arquivo_dados_equipe = arquivo_dados_equipe
        self.arquivo_dados_tarefas = arquivo_dados_tarefas
        
        self.equipe = pd.DataFrame(columns=['Nome', 'Habilidades', 'DisponibilidadeDiariaHoras'])
        self.tarefas = pd.DataFrame(columns=['Nome', 'PrazoFinal', 'DuracaoEstimadaHoras',
                                            'Prioridade', 'HabilidadesRequeridas',
                                            'AtribuidaA', 'Status', 'Passos', 'PassoAtualIndice'])
        self.cronograma_gerado = pd.DataFrame(columns=['Data', 'Membro', 'Tarefa', 'HorasDedicadas'])
        
        self.carregar_dados()

    def carregar_dados(self):
        if os.path.exists(self.arquivo_dados_equipe):
            with open(self.arquivo_dados_equipe, 'r') as f:
                self.equipe = pd.DataFrame(json.load(f))
            if 'Habilidades' in self.equipe.columns:
                self.equipe['Habilidades'] = self.equipe['Habilidades'].apply(lambda x: x if isinstance(x, list) else json.loads(x))
            print(f"Dados da equipe carregados de {self.arquivo_dados_equipe}")

        if os.path.exists(self.arquivo_dados_tarefas):
            with open(self.arquivo_dados_tarefas, 'r') as f:
                tarefas_data = json.load(f)
                self.tarefas = pd.DataFrame(tarefas_data)

            self.tarefas['PrazoFinal'] = pd.to_datetime(self.tarefas['PrazoFinal']) #

            if 'HabilidadesRequeridas' in self.tarefas.columns:
                self.tarefas['HabilidadesRequeridas'] = self.tarefas['HabilidadesRequeridas'].apply(lambda x: x if isinstance(x, list) else json.loads(x))
            if 'Passos' in self.tarefas.columns:
                self.tarefas['Passos'] = self.tarefas['Passos'].apply(lambda x: x if isinstance(x, list) else json.loads(x))

            print(f"Dados das tarefas carregados de {self.arquivo_dados_tarefas}")

    def salvar_dados(self):
        self.equipe.to_json(self.arquivo_dados_equipe, orient='records', indent=4)
        print(f"Dados da equipe salvos em {self.arquivo_dados_equipe}") #

        tarefas_para_salvar = self.tarefas.copy()

        # --- CORREÇÃO: Verifique se o DataFrame de tarefas não está vazio antes de formatar datas ---
        if not tarefas_para_salvar.empty: #
            # Certifique-se que a coluna é datetime ANTES de formatar para salvar.
            # Isso é redundante se carregar_dados() já faz isso, mas garante robustez.
            if not pd.api.types.is_datetime64_any_dtype(tarefas_para_salvar['PrazoFinal']): #
                 tarefas_para_salvar['PrazoFinal'] = pd.to_datetime(tarefas_para_salvar['PrazoFinal']) #

            tarefas_para_salvar['PrazoFinal'] = tarefas_para_salvar['PrazoFinal'].dt.strftime('%Y-%m-%d') #

        if 'HabilidadesRequeridas' in tarefas_para_salvar.columns: #
            # Apenas tente converter se a coluna existir e não for vazia
            if not tarefas_para_salvar['HabilidadesRequeridas'].empty: #
                tarefas_para_salvar['HabilidadesRequeridas'] = tarefas_para_salvar['HabilidadesRequeridas'].apply(json.dumps) #
            else: # Lida com a criação de uma coluna vazia se ainda não tiver dados
                 tarefas_para_salvar['HabilidadesRequeridas'] = tarefas_para_salvar['HabilidadesRequeridas'].astype(str) #
        
        if 'Passos' in tarefas_para_salvar.columns: #
            # Apenas tente converter se a coluna existir e não for vazia
            if not tarefas_para_salvar['Passos'].empty: #
                tarefas_para_salvar['Passos'] = tarefas_para_salvar['Passos'].apply(json.dumps) #
            else: # Lida com a criação de uma coluna vazia se ainda não tiver dados
                 tarefas_para_salvar['Passos'] = tarefas_para_salvar['Passos'].astype(str) #


        tarefas_para_salvar.to_json(self.arquivo_dados_tarefas, orient='records', indent=4) #
        print(f"Dados das tarefas salvos em {self.arquivo_dados_tarefas}") #

    def adicionar_membro(self, nome, habilidades, disponibilidade_diaria_horas):
        nova_linha = pd.DataFrame([{'Nome': nome, 'Habilidades': habilidades, 'DisponibilidadeDiariaHoras': disponibilidade_diaria_horas}]) #
        self.equipe = pd.concat([self.equipe, nova_linha], ignore_index=True) #
        self.salvar_dados() #

    def adicionar_tarefa(self, nome, prazo_final, duracao_estimada_horas, prioridade, habilidades_requeridas=None, passos=None):
        prazo_final_dt = datetime.strptime(prazo_final, '%Y-%m-%d') if isinstance(prazo_final, str) else prazo_final #
        if passos is None: #
            passos = [{'nome': 'Concluir', 'habilidades': habilidades_requeridas}] # Passo único se não especificado

        nova_linha = pd.DataFrame([{ #
            'Nome': nome, #
            'PrazoFinal': prazo_final_dt, #
            'DuracaoEstimadaHoras': duracao_estimada_horas, #
            'Prioridade': prioridade, #
            'HabilidadesRequeridas': habilidades_requeridas, #
            'AtribuidaA': None, #
            'Status': 'Pendente', # Novo campo
            'Passos': passos,     # Novo campo: lista de dicionários
            'PassoAtualIndice': 0 # Novo campo: índice do passo atual
        }])
        self.tarefas = pd.concat([self.tarefas, nova_linha], ignore_index=True) #
        self.salvar_dados() #

    def _encontrar_membro_para_passo(self, habilidades_requeridas_passo, data_inicio, horas_necessarias):
        for _, membro in self.equipe.iterrows(): #
            if habilidades_requeridas_passo is None or any(h in membro['Habilidades'] for h in habilidades_requeridas_passo): #
                return membro['Nome'] #
        return None #

    def gerar_cronograma(self, data_inicio, data_fim):
        self.cronograma_gerado = pd.DataFrame(columns=['Data', 'Membro', 'Tarefa', 'HorasDedicadas']) #
        data_atual = data_inicio #

        tarefas_ordenadas = self.tarefas[self.tarefas['Status'] == 'Em Andamento'].copy() #
        tarefas_ordenadas = pd.concat([ #
            tarefas_ordenadas, #
            self.tarefas[self.tarefas['Status'] == 'Pendente'].sort_values(by=['Prioridade', 'PrazoFinal'], ascending=[True, True]) #
        ])
        tarefas_ordenadas = tarefas_ordenadas[tarefas_ordenadas['Status'] != 'Concluida'] # Não inclui tarefas concluídas

        while data_atual <= data_fim and not tarefas_ordenadas.empty: #
            for index, tarefa in tarefas_ordenadas.iterrows(): #
                if tarefa['AtribuidaA'] is None or (tarefa['Status'] == 'Em Andamento' and tarefa['AtribuidaA'] not in self.equipe['Nome'].tolist()): #
                    passo_atual = tarefa['Passos'][tarefa['PassoAtualIndice']] #
                    membro_atribuido = self._encontrar_membro_para_passo( #
                        passo_atual['habilidades'], data_atual, tarefa['DuracaoEstimadaHoras'] # Usamos a duração total da tarefa por simplicidade aqui
                    )

                    if membro_atribuido: #
                        nova_entrada_cronograma = pd.DataFrame([{ #
                            'Data': data_atual.date(), #
                            'Membro': membro_atribuido, #
                            'Tarefa': f"{tarefa['Nome']} ({passo_atual['nome']})", # Mostra o passo atual
                            'HorasDedicadas': tarefa['DuracaoEstimadaHoras'] #
                        }])
                        self.cronograma_gerado = pd.concat([self.cronograma_gerado, nova_entrada_cronograma], ignore_index=True) #

                        self.tarefas.loc[index, 'AtribuidaA'] = membro_atribuido #
                        self.tarefas.loc[index, 'Status'] = 'Em Andamento' # Marca como em andamento
                        self.salvar_dados() # Salva o estado da tarefa
                        tarefas_ordenadas = tarefas_ordenadas.drop(index) # Remove da lista de pendentes para essa iteração
                        break # Procede para o próximo dia

            data_atual += timedelta(days=1) #
        return self.cronograma_gerado #

    def marcar_tarefa_concluida(self, nome_tarefa, membro_que_concluiu):
        tarefa_index = self.tarefas[(self.tarefas['Nome'] == nome_tarefa) & (self.tarefas['AtribuidaA'] == membro_que_concluiu)].index #

        if not tarefa_index.empty: #
            tarefa = self.tarefas.loc[tarefa_index[0]] #
            proximo_passo_indice = tarefa['PassoAtualIndice'] + 1 #

            if proximo_passo_indice < len(tarefa['Passos']): #
                self.tarefas.loc[tarefa_index[0], 'PassoAtualIndice'] = proximo_passo_indice #
                self.tarefas.loc[tarefa_index[0], 'AtribuidaA'] = None # Desatribui para o próximo ciclo de geração
                self.tarefas.loc[tarefa_index[0], 'Status'] = 'Pendente' # Volta a ser pendente para nova atribuição
                print(f"Tarefa '{nome_tarefa}' avançou para o próximo passo. Necessita de nova atribuição.") #
            else:
                self.tarefas.loc[tarefa_index[0], 'Status'] = 'Concluida' #
                self.tarefas.loc[tarefa_index[0], 'AtribuidaA'] = None # Remove atribuição
                print(f"Tarefa '{nome_tarefa}' concluída por {membro_que_concluiu}!") #
            self.salvar_dados() #
            return True #
        print(f"Erro: Tarefa '{nome_tarefa}' não encontrada ou não atribuída a '{membro_que_concluiu}'.") #
        return False #

    def obter_tarefas_por_membro(self, nome_membro):
        return self.tarefas[ #
            (self.tarefas['AtribuidaA'] == nome_membro) & #
            (self.tarefas['Status'] == 'Em Andamento') # Mostra apenas as que estão em andamento para o membro
        ]

    def obter_todas_tarefas(self):
        return self.tarefas #