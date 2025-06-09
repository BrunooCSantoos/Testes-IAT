import re
import os

def extrair_paragrafos_relevantes(todos_textos_paginas, palavras_chave_paragrafos, tamanho_janela=3, diretorio_saida="paragrafos_relevantes"):
    """
    Extrai parágrafos relevantes de um documento usando uma janela deslizante.
    """
    if not os.path.exists(diretorio_saida):
        os.makedirs(diretorio_saida)

    paragrafos_relevantes_encontrados = []

    total_paginas = len(todos_textos_paginas)
    for i in range(total_paginas):
        inicio_janela_pagina = i
        fim_janela_pagina = min(i + tamanho_janela, total_paginas)
        
        textos_janela_atual = todos_textos_paginas[inicio_janela_pagina:fim_janela_pagina]
        texto_combinado_na_janela = "\n".join(textos_janela_atual)

        paragrafos = re.split(r'\n\s*\n|\n\n', texto_combinado_na_janela)

        for paragrafo in paragrafos:
            paragrafo = paragrafo.strip()
            if not paragrafo:
                continue
            for palavra_chave in palavras_chave_paragrafos:
                if re.search(r'\b' + re.escape(palavra_chave) + r'\b', paragrafo, re.IGNORECASE):
                    paragrafos_relevantes_encontrados.append(paragrafo)
                    break
    
    caminho_arquivo_saida = os.path.join(diretorio_saida, "paragrafos_relevantes_agrupados.txt")
    with open(caminho_arquivo_saida, 'w', encoding='utf-8') as f:
        for paragrafo in paragrafos_relevantes_encontrados:
            f.write(paragrafo + "\n\n---\n\n")
    print(f"Parágrafos relevantes salvos em: {caminho_arquivo_saida}")
    return paragrafos_relevantes_encontrados

def extrair_informacoes_chave(dados_texto):
    """
    Extrai informações chave como tipo do documento, número, nome, situação, cargo,
    número e data da edição, de TODAS as ocorrências de Portaria/Decreto.
    Retorna uma lista de dicionários, onde cada dicionário representa um documento.
    """
    texto_completo = "\n".join(dados_texto)
    informacoes_documentos = []

    # Informações gerais do Diário Oficial (capturadas uma vez)
    num_edicao_geral = None
    data_edicao_geral = None
    
    match_num_edicao = re.search(r'Edição Digital nº\s*(\d+)', texto_completo)
    if match_num_edicao:
        num_edicao_geral = match_num_edicao.group(1)

    match_data_edicao = re.search(r'Curitiba, \w+, (\d{2} de \w+ de \d{4})', texto_completo, re.IGNORECASE)
    if match_data_edicao:
        data_edicao_geral = match_data_edicao.group(1)

    # CNPJ (assumindo que o CNPJ pode estar em qualquer lugar e não é específico de uma portaria/decreto)
    cnpj_padrao = r'\b\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}\b'
    cnpjs_encontrados = "; ".join(re.findall(cnpj_padrao, texto_completo))

    # Padrão para encontrar o início de uma Portaria ou Decreto
    # Captura o tipo (Portaria/Decreto) e o número.
    # Adiciona um lookahead para o próximo "PORTARIA Nº" ou "DECRETO Nº" ou o fim do documento
    # para segmentar o texto de cada documento.
    
    # A regex abaixo tenta capturar um bloco de texto que começa com "PORTARIA Nº" ou "DECRETO Nº"
    # e vai até o próximo "PORTARIA Nº", "DECRETO Nº" ou o final do texto.
    # Isso ajuda a isolar o contexto de cada documento.
    padrao_documento = r'(PORTARIA|DECRETO)\s*Nº\s*(\d+\/?\d*)(.*?)(?=(?:PORTARIA|DECRETO)\s*Nº|\Z)'
    
    for match_doc in re.finditer(padrao_documento, texto_completo, re.IGNORECASE | re.DOTALL):
        tipo_documento = match_doc.group(1).title()
        numero_documento = match_doc.group(2)
        conteudo_documento = match_doc.group(3) # O conteúdo entre o início deste documento e o próximo

        info_atual = {
            "Tipo do Documento": tipo_documento,
            "Número do Documento": numero_documento,
            "Nome": None,
            "Situação": None,
            "Cargo": None,
            "Número da Edição": num_edicao_geral,
            "Data da Edição": data_edicao_geral,
            "CNPJ": cnpjs_encontrados # CNPJ é geral, não específico por Portaria/Decreto
        }

        # --- Extração de Nome, Situação e Cargo DENTRO do conteúdo do documento atual ---
        situacoes = ["Nomear", "Exonerar", "Designar", "Dispensar", "Retificar", "Reconhecer", "Autorizar"]
        
        # Esta regex é crucial e precisa ser refinada com base nos seus dados.
        # Tentativa de regex para capturar Nome e Cargo dentro de um contexto de Portaria/Decreto.
        # Ela busca por um verbo de situação, seguido por um nome (geralmente capitalizado, com múltiplos nomes),
        # e então opcionalmente um cargo após "para o cargo de", "no cargo de", etc.
        # Considera que o nome pode vir em maiúsculas ou Capitalizado.
        
        # Padrão 1: "NOMEAR NOME COMPLETO para o cargo de CARGO"
        # Nome completo: capturando palavras com capitalização inicial/maiúsculas
        # Cargo: capturando palavras após "cargo de", "função de"
        # Esta é uma regex complexa e pode exigir ajuste fino.
        # Captura: (Situação) (Nome) (Cargo)
        
        # Regex para buscar "situação (verbo) NOME (Capitalizado ou MAIÚSCULAS) (para o cargo de) CARGO"
        
        # Vamos tentar uma abordagem mais modular para a regex, buscando primeiro a situação
        # e depois, dentro do texto próximo, o nome e o cargo.
        
        # Tenta pegar a situação e o nome (assumindo que o nome é um conjunto de palavras capitalizadas ou maiúsculas)
        # e o cargo (também um conjunto de palavras).
        
        # Regex para NOME (assumindo NOME e sobrenomes, pode conter preposições como 'de', 'e')
        # Tenta pegar sequências de palavras capitalizadas, com 'de', 'da', 'do', 'e' no meio.
        # Ex: João DA Silva, Maria E Santos.
        # (\b[A-ZÀ-ÚÄ-Ü][a-zá-üä-ü]+\s+(?:da|de|do|e|das|dos)?\s*[A-ZÀ-ÚÄ-Ü][a-zá-üä-ü]+\b(?:, \b[A-ZÀ-ÚÄ-Ü][a-zá-üä-ü]+\s+(?:da|de|do|e|das|dos)?\s*[A-ZÀ-ÚÄ-Ü][a-zá-üä-ü]+\b)*)
        # ^ Este é complexo. Vamos tentar algo mais direto primeiro.
        
        # Nome e Cargo são os mais difíceis, pois não seguem um padrão fixo.
        # Tentar uma regex que capture o "verbo de situação" e o trecho subsequente,
        # e dentro desse trecho tentar extrair nome e cargo.
        
        # Primeiro, identificar a situação e tentar capturar o nome logo após o verbo.
        # O cargo viria depois.
        
        # Regex para tentar capturar "SITUAÇÃO NOME para o cargo de CARGO"
        # NOME: Assume que é uma sequência de 2 a 5 palavras capitalizadas.
        # CARGO: Assume que é uma sequência de 1 a 5 palavras capitalizadas após "cargo de", "função de".
        
        # Esta regex é uma tentativa mais focada. Ela busca um dos verbos de situação,
        # depois um "nome" (grupo 1), e um "cargo" (grupo 2).
        # Ajuste a regex para o padrão REAL do seu documento.
        
        # Exemplo baseado no que geralmente se vê:
        # "VERBO NOME_COMPLETO (com ou sem CPF/Matrícula) para o cargo de CARGO"
        nome_cargo_situacao_padrao = (
            r'(?:' + '|'.join(situacoes) + r')\s+'  # Situação (verbo)
            r'(.+?)'  # Grupo 1: Nome (captura o que vier depois do verbo, não-ganancioso)
            r'(?:,\s*matrícula\s*\d+)?' # Opcional: matrícula
            r'(?:\s*CPF\s*\d{3}\.\d{3}\.\d{3}-\d{2})?' # Opcional: CPF
            r'(?:\s*para o cargo de|\s*no cargo de|\s*na função de|\s*como)?\s*' # Prefixo do cargo (opcional)
            r'(.+?)?'  # Grupo 2: Cargo (captura o que vier depois do prefixo, opcional)
            r'(?:\s*(?:e\s+designar|\s*,\s*nos\s*termos|\s*,\s*a\s*partir|\s*\.|\n|$))?' # Delimitador final (opcional, para não capturar demais)
        )
        
        # Busca a primeira ocorrência dentro do conteúdo do documento atual
        match_info = re.search(nome_cargo_situacao_padrao, conteudo_documento, re.IGNORECASE | re.DOTALL)
        
        if match_info:
            extracted_name = match_info.group(1).strip()
            extracted_cargo = match_info.group(2).strip() if match_info.group(2) else None
            
            # Refinar a Situação com base no texto do match
            match_text_info = match_info.group(0).lower()
            if "nomear" in match_text_info:
                info_atual["Situação"] = "Nomeação"
            elif "exonerar" in match_text_info:
                info_atual["Situação"] = "Exoneração"
            elif "designar" in match_text_info:
                info_atual["Situação"] = "Designação"
            elif "dispensar" in match_text_info:
                info_atual["Situação"] = "Dispensa"
            elif "retificar" in match_text_info:
                info_atual["Situação"] = "Retificação"
            elif "reconhecer" in match_text_info:
                info_atual["Situação"] = "Reconhecimento"
            elif "autorizar" in match_text_info:
                info_atual["Situação"] = "Autorização"

            # Atribui o nome e cargo, tentando limpar excessos.
            # O nome muitas vezes é até a primeira vírgula ou "para o cargo de".
            # O cargo muitas vezes é do "para o cargo de" até o final da linha ou um ponto.
            
            # É muito comum o nome ser em MAIÚSCULAS. Vamos tentar capturar isso.
            # Se o nome capturado é muito longo ou genérico, tenta refinar.
            
            # Para Nome: Tentar capturar Nomes Próprios (capitalizados ou MAIÚSCULAS)
            # Pode ser útil usar uma regex que busque um padrão de nome, ex:
            # (Nome Sobrenome | Nome Sobrenome Sobrenome | NOME COMPLETO EM MAIÚSCULAS)
            
            # Tentar limpar o nome e cargo capturados.
            # Se o nome capturado é muito longo, talvez seja um trecho de frase.
            
            # Uma abordagem para Nome/Cargo é tentar buscar padrões mais definidos.
            # Ex: "NOMEAR (.*?), para o cargo de (.*?)" - isso funcionaria melhor
            # se o formato fosse sempre idêntico.
            
            # Vamos tentar uma limpeza básica no Nome e Cargo extraídos.
            # Remover excesso de texto após o nome, se não for parte do nome.
            
            # Limpeza do Nome: se contém "para o cargo de" ou "no cargo de", corta antes.
            if extracted_name:
                match_corte_nome = re.search(r'(.*?)(?:para o cargo de|no cargo de|na função de|como)', extracted_name, re.IGNORECASE | re.DOTALL)
                if match_corte_nome:
                    extracted_name = match_corte_nome.group(1).strip()
                
                # Tenta pegar apenas nomes próprios (duas ou mais palavras capitalizadas)
                # ou nomes em maiúsculas (se for o padrão).
                match_nome_limpo = re.search(r'\b(?:[A-ZÀ-ÚÄ-Ü][a-zá-üä-ü]+\s*){2,}\b|\b[A-Z\s.-]+\b', extracted_name)
                if match_nome_limpo:
                    info_atual["Nome"] = match_nome_limpo.group(0).strip()
                else:
                    info_atual["Nome"] = extracted_name # fallback para o que foi extraído

            # Limpeza do Cargo: se contém vírgulas ou pontos após o cargo, remove-os.
            if extracted_cargo:
                info_atual["Cargo"] = re.sub(r'[,.\n]$', '', extracted_cargo).strip()
                # Se o cargo for muito curto ou genérico, como "a", "s", pode ser erro.
                if len(info_atual["Cargo"]) < 3: # Limite arbitrário, ajuste se necessário
                    info_atual["Cargo"] = None


        informacoes_documentos.append(info_atual)

    return informacoes_documentos