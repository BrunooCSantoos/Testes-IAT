# calculadora_aposentadoria.py
import datetime

# Constantes para as datas de referência
DATA_REFORMA_PREVIDENCIA = datetime.date(2019, 12, 4)
DATA_PRE_REFORMA = datetime.date(2003, 12, 31)

class CalculadoraAposentadoria:
    def __init__(self):
        # Atributos para armazenar os dados da pessoa
        self.data_nascimento = None
        self.tempo_contribuicao_anos = 0
        self.tempo_contribuicao_meses = 0
        self.tempo_contribuicao_dias = 0
        self.data_inicio_servico = None 
        self.data_inicio_cargo = None 
        self.genero = ""  # "Mulher" ou "Homem"

    def _calcular_idade(self):
        """Calcula a idade em anos a partir da data de nascimento."""
        if not self.data_nascimento:
            return 0
        today = datetime.date.today()
        # Calculate approximate age, then adjust for birthday not yet passed
        age = today.year - self.data_nascimento.year
        if (today.month < self.data_nascimento.month) or \
           (today.month == self.data_nascimento.month and today.day < self.data_nascimento.day):
            age -= 1
        return age

    def _calcular_anos_desde_data_inicio(self, data_inicio, data_fim=None):
        """
        Calcula a diferença em anos entre uma data de início e uma data de fim.
        Se data_fim for None, usa a data atual.
        Retorna 0.0 se data_inicio for None.
        """
        if not data_inicio:
            return 0.0
        
        if data_fim is None:
            data_fim = datetime.date.today()
        
        delta = data_fim - data_inicio
        return delta.days / 365.25 # Using 365.25 for average year length (includes leap years)

    def _converter_decimal_para_tempo(self, anos_decimais):
        """
        Converte anos decimais em anos, meses e dias.
        Retorna uma tupla (anos, meses, dias).
        """
        if anos_decimais < 0:
            return (0, 0, 0)
        
        anos = int(anos_decimais)
        resto_anos = anos_decimais - anos
        
        meses_decimais = resto_anos * 12
        meses = int(meses_decimais)
        resto_meses = meses_decimais - meses
        
        dias = int(resto_meses * 30.4375) # Média de dias por mês (365.25/12)
        
        return (anos, meses, dias)

    def _obter_tempo_contribuicao_total(self):
        """Retorna o tempo de contribuição total em anos decimais."""
        return self.tempo_contribuicao_anos + \
               (self.tempo_contribuicao_meses / 12) + \
               (self.tempo_contribuicao_dias / 365.25) # Using 365.25 for average year length


    def _calcular_requisitos_faltantes(self, limites_minimos, pessoa_atual, soma_pontos_alvo=None):
        """
        Calcula os requisitos que ainda faltam para a elegibilidade.
        """
        faltantes = {}
        
        for requisito, minimo in limites_minimos.items():
            valor_atual = pessoa_atual.get(requisito, 0) # Get from the passed dict

            if isinstance(valor_atual, (int, float)) and valor_atual < minimo:
                faltantes[requisito] = minimo - valor_atual
        
        # Lógica específica para a soma de idade + tempo de contribuição (para Regra de Pontos)
        if soma_pontos_alvo:
            soma_atual = pessoa_atual['idade'] + pessoa_atual['tempo_contribuicao']
            if soma_atual < soma_pontos_alvo:
                faltantes['soma_idade_tempo_contribuicao'] = soma_pontos_alvo - soma_atual
        
        return faltantes

    def regra_permanente(self):
        """
        Aplica a regra da aposentadoria permanente.
        Retorna um dicionário com elegibilidade e requisitos faltantes.
        """
        idade = self._calcular_idade()
        tempo_servico = self._calcular_anos_desde_data_inicio(self.data_inicio_servico)
        tempo_cargo = self._calcular_anos_desde_data_inicio(self.data_inicio_cargo)
        tempo_contribuicao = self._obter_tempo_contribuicao_total() # Use direct input

        limites = {
            "Mulher": {"tempo_cargo": 5, "tempo_servico": 10, "tempo_contribuicao": 25, "idade": 62},
            "Homem": {"tempo_cargo": 5, "tempo_servico": 10, "tempo_contribuicao": 25, "idade": 65}
        }

        requisitos_genero = limites.get(self.genero)
        elegivel = False
        beneficio = ""
        requisitos_faltantes = {}

        if requisitos_genero:
            if (tempo_cargo >= requisitos_genero["tempo_cargo"] and
                tempo_servico >= requisitos_genero["tempo_servico"] and
                tempo_contribuicao >= requisitos_genero["tempo_contribuicao"] and
                idade >= requisitos_genero["idade"]):
                
                elegivel = True

                beneficio = "Calculado com base na Média de Contribuições."
            else:
                requisitos_faltantes = self._calcular_requisitos_faltantes(
                    requisitos_genero,
                    {
                        'idade': idade,
                        'tempo_contribuicao': tempo_contribuicao,
                        'tempo_servico': tempo_servico,
                        'tempo_cargo': tempo_cargo
                    }
                )
        
        return {"elegivel": elegivel, "beneficio": beneficio, "requisitos_faltantes": requisitos_faltantes}

    def regra_transicao_pedagio(self):
        """
        Aplica a regra de transição por pedágio.
        Retorna um dicionário com elegibilidade e requisitos faltantes.
        """
        idade = self._calcular_idade()
        tempo_servico = self._calcular_anos_desde_data_inicio(self.data_inicio_servico)
        tempo_cargo = self._calcular_anos_desde_data_inicio(self.data_inicio_cargo)
        tempo_contribuicao = self._obter_tempo_contribuicao_total()

        limites = {
            "Mulher": {"tempo_cargo": 5, "tempo_servico": 20, "tempo_contribuicao": 30, "idade": 57},
            "Homem": {"tempo_cargo": 5, "tempo_servico": 20, "tempo_contribuicao": 35, "idade": 60}
        }

        requisitos_genero = limites.get(self.genero)
        elegivel = False
        beneficio = ""
        requisitos_faltantes = {}

        if requisitos_genero:
            if (tempo_cargo >= requisitos_genero["tempo_cargo"] and
                tempo_servico >= requisitos_genero["tempo_servico"] and
                tempo_contribuicao >= requisitos_genero["tempo_contribuicao"] and
                idade >= requisitos_genero["idade"]):
                
                elegivel = True

                if self.data_inicio_servico < DATA_PRE_REFORMA:
                    beneficio = "Integral do Salário."
                else:
                    beneficio = "Integral da Média de Contribuições."
            else:
                requisitos_faltantes = self._calcular_requisitos_faltantes(
                    requisitos_genero,
                    {
                        'idade': idade,
                        'tempo_contribuicao': tempo_contribuicao,
                        'tempo_servico': tempo_servico,
                        'tempo_cargo': tempo_cargo
                    }
                )
        
        return {"elegivel": elegivel, "beneficio": beneficio, "requisitos_faltantes": requisitos_faltantes}


    def regra_transicao_pontos(self):
        """
        Aplica a regra de transição por pontos.
        Retorna um dicionário com elegibilidade e requisitos faltantes.
        """
        idade = self._calcular_idade()
        tempo_servico = self._calcular_anos_desde_data_inicio(self.data_inicio_servico)
        tempo_cargo = self._calcular_anos_desde_data_inicio(self.data_inicio_cargo)
        tempo_contribuicao = self._obter_tempo_contribuicao_total()

        limites_comuns = {"tempo_cargo": 5, "tempo_servico": 20}
        limites_genero = {
            "Mulher": {
                "idade_inicial": 56, "tempo_contribuicao_base": 30,
                "pontos_idade_56": 86, "pontos_idade_57_ou_mais": 89
            },
            "Homem": {
                "idade_inicial": 61, "tempo_contribuicao_base": 35,
                "pontos_idade_61": 96, "pontos_idade_62_ou_mais": 99
            }
        }

        requisitos_genero = limites_genero.get(self.genero)
        elegivel = False
        beneficio = ""
        requisitos_faltantes = {}

        if requisitos_genero:
            # Check common requirements
            if tempo_cargo < limites_comuns["tempo_cargo"]:
                requisitos_faltantes['tempo_cargo'] = limites_comuns["tempo_cargo"] - tempo_cargo
            if tempo_servico < limites_comuns["tempo_servico"]:
                requisitos_faltantes['tempo_servico'] = limites_comuns["tempo_servico"] - tempo_servico

            # Check specific gender and age requirements
            if idade < requisitos_genero["idade_inicial"]:
                if 'idade' not in requisitos_faltantes: # Only add if not already missing
                    requisitos_faltantes['idade'] = requisitos_genero["idade_inicial"] - idade
                
                soma_pontos_necessaria = requisitos_genero[f"pontos_idade_{requisitos_genero['idade_inicial']}"]
                soma_atual = idade + tempo_contribuicao
                if soma_atual < soma_pontos_necessaria:
                    requisitos_faltantes['soma_idade_tempo_contribuicao'] = soma_pontos_necessaria - soma_atual
            
            else: # Age >= initial_age
                if tempo_contribuicao < requisitos_genero["tempo_contribuicao_base"]:
                    requisitos_faltantes['tempo_contribuicao'] = requisitos_genero["tempo_contribuicao_base"] - tempo_contribuicao

                pontos_alvo = 0
                if idade == requisitos_genero["idade_inicial"]:
                    pontos_alvo = requisitos_genero[f"pontos_idade_{requisitos_genero['idade_inicial']}"]
                elif idade >= requisitos_genero["idade_inicial"] + 1:
                    pontos_alvo = requisitos_genero[f"pontos_idade_{requisitos_genero['idade_inicial'] + 1}_ou_mais"]

                soma_atual = idade + tempo_contribuicao
                if pontos_alvo > 0 and soma_atual < pontos_alvo:
                    requisitos_faltantes['soma_idade_tempo_contribuicao'] = pontos_alvo - soma_atual
                
            if not requisitos_faltantes: # If all requirements are met
                elegivel = True

                if (self.data_inicio_servico < DATA_PRE_REFORMA and 
                    (self.genero == "Mulher" and idade >= 62) or (self.genero == "Homem" and idade >= 65)):
                    beneficio = "Integral do Salário."
                else:
                    beneficio = "Calculado com base na Média de Contribuições."

        return {"elegivel": elegivel,"beneficio": beneficio, "requisitos_faltantes": requisitos_faltantes}