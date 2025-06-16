import re
import glob
import os
from PyPDF2 import PdfReader

def extrair_texto_pdf(caminho_pdf, caminho_txt_paginas_filtradas, palavras_chave, matchcase=False):
    try:
        with open(caminho_pdf, "rb") as arquivo_pdf, open(caminho_txt_paginas_filtradas, "w", encoding="utf-8") as arquivo_txt_saida:
            leitor_pdf = PdfReader(arquivo_pdf)
            for pagina_num, pagina in enumerate(leitor_pdf.pages):
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    flags = 0 if matchcase else re.IGNORECASE
                    num_ocorrencias_chave = sum(1 for palavra in palavras_chave if re.search(r'\b' + re.escape(palavra) + r'\b', texto_pagina, flags=flags))
                    
                    if num_ocorrencias_chave >= 3:
                        # O marcador de início de página é útil para depuração, mas NÃO DEVE ser um delimitador de documento.
                        arquivo_txt_saida.write(f"--- Início da Página {pagina_num + 1} ---\n")
                        arquivo_txt_saida.write(texto_pagina.strip() + "\n\n") # Removido '\f' daqui
            # Adiciona um \f ao final do arquivo para simular o fim de um documento para a última página.
            # Isso é para garantir que o último documento seja capturado se ele não for seguido por um delimitador explícito.
            arquivo_txt_saida.write("\n\f\n") 
    except Exception as e:
        print(f"Erro ao extrair texto do PDF '{caminho_pdf}': {e}")
        return False
    return True

def filtrar_paragrafos_por_palavras_chave(caminho_txt_entrada, caminho_txt_saida, palavras_chave, matchcase=False):
    """
    Filtra parágrafos de um arquivo de texto, capturando blocos que começam com "DECRETO"
    ou contêm palavras-chave, e terminam com a assinatura "Governador do Estado".
    Parágrafos de marcadores de página são sempre incluídos.

    Args:
        caminho_txt_entrada (str): O caminho para o arquivo de texto de entrada.
        caminho_txt_saida (str): O caminho para o arquivo de texto de saída.
        palavras_chave (list): Uma lista de palavras-chave para buscar.
        matchcase (bool): Se True, a busca por palavras-chave e padrões será sensível a maiúsculas/minúsculas.
                         Caso contrário, será insensível (padrão).
    Returns:
        bool: True se o processo de filtragem for bem-sucedido, False caso contrário.
    """
    try:
        with open(caminho_txt_entrada, 'r', encoding='utf-8') as f_entrada:
            conteudo = f_entrada.read()
            # Divide o conteúdo em parágrafos, considerando uma ou mais linhas em branco como separador
            paragrafos = re.split(r'\n\s*\n+', conteudo)
            flags = 0 if matchcase else re.IGNORECASE
            
            # Compila os padrões regex uma única vez para otimização de desempenho
            padrao_marcador_pagina = re.compile(r'--- Início da Página \d+ ---')
            padrao_inicio_decreto = re.compile(r'DECRETO', flags=flags)
            padrao_fim_governador = re.compile(r'Governador\s+do\s+Estado', flags=flags)
            
            # Constrói um padrão regex para buscar qualquer uma das palavras-chave fornecidas como palavra inteira
            padrao_palavras_chave = re.compile(
                r'\b(?:' + '|'.join(re.escape(palavra) for palavra in palavras_chave) + r')\b',
                flags
            )

            # Lista para armazenar todos os blocos de parágrafos filtrados e marcadores de página
            paragrafos_filtrados = []
            # Lista temporária para armazenar as linhas do bloco que está sendo capturado atualmente
            bloco_atual_linhas = []
            # Sinalizador para indicar se estamos atualmente dentro de um bloco de interesse
            capturando = False 

            for paragrafo in paragrafos:
                paragrafo_limpo = paragrafo.strip()
                
                # Critério 1: Verifica se é um marcador de página. Marcadores são sempre incluídos.
                if padrao_marcador_pagina.match(paragrafo_limpo):
                    if capturando and bloco_atual_linhas:
                        # Se um marcador de página for encontrado no meio de um bloco capturado,
                        # finalize o bloco anterior antes de adicionar o marcador.
                        paragrafos_filtrados.append("\n".join(bloco_atual_linhas).strip())
                        bloco_atual_linhas = []
                        capturando = False
                    paragrafos_filtrados.append(paragrafo_limpo) 
                    continue # Pula para o próximo parágrafo

                # Critério 2: Verifica se o parágrafo começa com "DECRETO".
                is_inicio_decreto = padrao_inicio_decreto.search(paragrafo_limpo)
                # Critério 3: Verifica se o parágrafo termina com "Governador do Estado".
                is_fim_governador = padrao_fim_governador.search(paragrafo_limpo)
                # Critério 4: Verifica se o parágrafo contém alguma das palavras-chave fornecidas.
                contains_keywords = padrao_palavras_chave.search(paragrafo_limpo)

                # Define a condição para iniciar um NOVO bloco de interesse.
                # Um novo bloco começa se for um "DECRETO" OU se contiver palavras-chave relevantes.
                is_start_of_new_relevant_block = is_inicio_decreto or contains_keywords

                if is_start_of_new_relevant_block:
                    if capturando and bloco_atual_linhas:
                        # Se já estava capturando um bloco (anterior) e encontrou um novo início de bloco relevante,
                        # finalize o bloco anterior e adicione-o à lista de resultados.
                        paragrafos_filtrados.append("\n".join(bloco_atual_linhas).strip())
                    
                    # Começa um novo bloco com o parágrafo atual
                    bloco_atual_linhas = [paragrafo_limpo] 
                    capturando = True
                elif capturando:
                    # Se estamos capturando um bloco, adicione o parágrafo atual a ele.
                    bloco_atual_linhas.append(paragrafo_limpo)
                    
                    # Se o parágrafo adicionado contém o marcador de fim de bloco ("Governador do Estado"),
                    # finalize o bloco atual.
                    if is_fim_governador:
                        paragrafos_filtrados.append("\n".join(bloco_atual_linhas).strip())
                        bloco_atual_linhas = [] # Limpa para o próximo bloco
                        capturando = False
            
            # Após percorrer todos os parágrafos, verifica se o último bloco ainda estava sendo capturado.
            # Se sim, adiciona-o à lista de resultados.
            if bloco_atual_linhas:
                paragrafos_filtrados.append("\n".join(bloco_atual_linhas).strip())
            
            # Abre o arquivo de saída no modo de escrita e escreve todos os parágrafos filtrados.
            # Cada bloco ou marcador de página é separado por duas quebras de linha para manter a formatação.
            with open(caminho_txt_saida, 'w', encoding='utf-8') as f_saida:
                f_saida.write('\n\n'.join(paragrafos_filtrados))
                    
    except Exception as e:
        # Em caso de qualquer erro durante a execução, imprime a mensagem de erro e retorna False.
        print(f"Erro ao filtrar parágrafos de '{caminho_txt_entrada}': {e}")
        return False
        
    # Se a execução for bem-sucedida, retorna True.
    return True

def extrair_decretos(paragrafos, matchcase=True):
    decretos_encontrados = []
    decreto_atual_linhas = []
    capturando = False
    flags = 0 if matchcase else re.IGNORECASE
    numeros_decretos_existentes = set() # Novo: Armazena os números dos decretos já adicionados

    # Padrão para identificar o início de um decreto
    # Modificado para capturar o número do decreto
    padrao_inicio_decreto = re.compile(
        r'\bDECRETO\s*Nº?\s*(\d+(?:[\.\-]\d+)*)', 
        flags
    )

    # Padrão para identificar o fim de um DECRETO (fim de um bloco administrativo)
    padrao_fim_decreto_bloco = re.compile(
        r'\bGovernador do Estado\b',
        flags
    )

    for i, paragrafo in enumerate(paragrafos):
        # Ignora marcadores de página ao processar documentos
        if re.match(r'--- Início da Página \d+ ---', paragrafo):
            continue

        is_inicio_decreto = padrao_inicio_decreto.search(paragrafo)
        is_fim_bloco = padrao_fim_decreto_bloco.search(paragrafo)

        if is_inicio_decreto:
            # Extrai o número do decreto
            numero_decreto = is_inicio_decreto.group(1)

            if capturando and decreto_atual_linhas:
                # Se já estava capturando e encontrou um novo decreto,
                # finalize o anterior antes de começar um novo (se não for duplicado).
                finalizado_decreto = "\n".join(decreto_atual_linhas).strip()
                # Verifica duplicata para o decreto que estava sendo capturado anteriormente, se houver
                match_numero_anterior = padrao_inicio_decreto.search(finalizado_decreto)
                if match_numero_anterior:
                    num_anterior = match_numero_anterior.group(1)
                    if num_anterior not in numeros_decretos_existentes:
                        decretos_encontrados.append(finalizado_decreto)
                        numeros_decretos_existentes.add(num_anterior)

            # Inicia um novo decreto se o número não for um duplicado
            if numero_decreto not in numeros_decretos_existentes:
                decreto_atual_linhas = [paragrafo] # Começa um novo decreto com o parágrafo atual
                capturando = True
            else:
                # Se for um número duplicado, não inicia a captura para este decreto
                capturando = False # Garante que não continuemos capturando para esta duplicata
                decreto_atual_linhas = [] # Limpa as linhas atuais
        elif capturando:
            # Se estamos capturando, adicione o parágrafo atual ao decreto
            decreto_atual_linhas.append(paragrafo)
            
            # Se o parágrafo adicionado contém o marcador de fim de bloco,
            # finalize o decreto atual.
            if is_fim_bloco:
                finalizado_decreto = "\n".join(decreto_atual_linhas).strip()
                # Extrai o número do decreto a ser adicionado
                match_numero = padrao_inicio_decreto.search(finalizado_decreto)
                if match_numero:
                    numero_decreto_finalizado = match_numero.group(1)
                    if numero_decreto_finalizado not in numeros_decretos_existentes:
                        decretos_encontrados.append(finalizado_decreto)
                        numeros_decretos_existentes.add(numero_decreto_finalizado) # Adiciona ao conjunto de números existentes
                
                decreto_atual_linhas = [] # Limpa para o próximo decreto
                capturando = False
                
    # Adiciona o último decreto se ainda estiver capturando ao final do loop
    if decreto_atual_linhas:
        finalizado_decreto = "\n".join(decreto_atual_linhas).strip()
        match_numero = padrao_inicio_decreto.search(finalizado_decreto)
        if match_numero:
            numero_decreto_finalizado = match_numero.group(1)
            if numero_decreto_finalizado not in numeros_decretos_existentes:
                decretos_encontrados.append(finalizado_decreto)
                numeros_decretos_existentes.add(numero_decreto_finalizado)

    return decretos_encontrados

def filtrar_decretos(decretos, matchcase=False):
    decretos_filtrados = []
    # Define as flags para a expressão regular, considerando a sensibilidade a maiúsculas/minúsculas.
    flags = 0 if matchcase else re.IGNORECASE
    
    # Padrões nomeação SEAP
    padrao_inicio_decreto = re.compile(r'DECRETO', flags)
    padrao_nomeacao = re.compile(r'Nomeia|Nomeação', flags)
    padrao_orgao_seap = re.compile(r'Secretaria\s+de\s+Estado\s+da\s+Administração\s+e\s+da\s+Previdência|SEAP', flags)
    padrao_qppe = re.compile(r'QPPE', flags)
    padrao_orgao_iat = re.compile(r'INSTITUTO\s+ÁGUA\s+E\s+TERRA|\bIAT\b', flags)
    # Novo padrão para verificar a frase "Governador do Estado"
    padrao_fim = re.compile(r'Governador\s+do\s+Estado', flags)
    
    # Itera sobre os decretos usando índices
    for i in range(len(decretos)):
        decreto_atual_conteudo = decretos[i].strip() # Pega o conteúdo do decreto atual
        
        # Primeiro critério: O decreto atual DEVE começar com "DECRETO"
        if not padrao_inicio_decreto.search(decreto_atual_conteudo):
            continue # Se não começar com "DECRETO", pula para o próximo decreto
        
        # Filtros de nomeação SEAP
        is_nomeacao = bool(padrao_nomeacao.search(decreto_atual_conteudo))
        is_seap = bool(padrao_orgao_seap.search(decreto_atual_conteudo))
        is_qppe = bool(padrao_qppe.search(decreto_atual_conteudo))
        is_iat = bool(padrao_orgao_iat.search(decreto_atual_conteudo))
        is_governador_do_estado = bool(padrao_fim.search(decreto_atual_conteudo)) # Nova verificação
        
        # Se todos os critérios forem atendidos pela janela, adiciona o *decreto atual* à lista filtrada
        if is_nomeacao and ((is_seap and is_qppe) or is_iat) and is_governador_do_estado:
            decretos_filtrados.append(decreto_atual_conteudo)

    return decretos_filtrados

def salvar_documentos_em_arquivo(decretos, caminho_arquivo, titulo_secao):
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            for i, decreto in enumerate(decretos):
                # Tenta identificar o número do decreto para incluir no marcador
                match_numero = re.search(r'\bDECRETO Nº\s*([\d.]+)', decreto, re.IGNORECASE)
                numero = match_numero.group(1).strip() if match_numero else "Sem Numero"
                
                f.write(f"\n--- INÍCIO {titulo_secao} {numero} ---\n")
                f.write(decreto.strip() + "\n")
                f.write(f"--- FIM {titulo_secao} {numero} ---\n\n")
        print(f"Decretos salvos em: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao salvar decretos em '{caminho_arquivo}': {e}")

    return caminho_arquivo

def remover_arquivos_temporarios(arquivos):
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            try:
                os.remove(arquivo)
                print(f"Arquivo temporário removido: {arquivo}")
            except Exception as e:
                print(f"Erro ao remover arquivo temporário '{arquivo}': {e}")

def ler(caminho_diretorio):
    print("Iniciando leitura de decretos...")
    
    matchcase = True

    padrao_pdf = os.path.join(caminho_diretorio, "EX*.pdf")
    arquivos_pdf = glob.glob(padrao_pdf)
    arquivo_decretos = None

    palavras_chave_gerais = [
        "DECRETO", "Nomeação", "Nomeia", 
        "QPPE", "Art. 1",
        "Secretaria de Estado da Administração e da Previdência - SEAP", "INSTITUTO ÁGUA E TERRA", "IAT",
    ]
    
    for arquivo_pdf in arquivos_pdf:
        nome_base = os.path.basename(arquivo_pdf).replace(".pdf", "")
        caminho_txt_paginas_filtradas = os.path.join(caminho_diretorio, f"{nome_base}_decretos_paginas_filtradas.txt")
        caminho_txt_paragrafos_filtrados = os.path.join(caminho_diretorio, f"{nome_base}_decretos_paragrafos_filtrados.txt")
        caminho_txt_decretos = os.path.join(caminho_diretorio, f"{nome_base}_decretos.txt")
        
        print("Separando páginas...")
        if extrair_texto_pdf(arquivo_pdf, caminho_txt_paginas_filtradas, palavras_chave_gerais, matchcase):
            print("Separando parágrafos...")
            if filtrar_paragrafos_por_palavras_chave(caminho_txt_paginas_filtradas, caminho_txt_paragrafos_filtrados, palavras_chave_gerais, matchcase):
                with open(caminho_txt_paragrafos_filtrados, 'r', encoding='utf-8') as f:
                    texto_paragrafos = f.read().split('\n')
                
                
                todos_decretos = extrair_decretos(texto_paragrafos, matchcase)
                
                decretos_final = filtrar_decretos(todos_decretos, matchcase)

                if decretos_final:
                    arquivo_decretos = salvar_documentos_em_arquivo(decretos_final, caminho_txt_decretos, "DECRETO") # Título mais genérico
                else:
                    print(f"Nenhum decreto de nomeação ou ampliação de vagas referente à SEAP ou IAT encontrado para salvar em '{caminho_txt_decretos}'.")
            else:
                print(f"Falha ao filtrar parágrafos de '{caminho_txt_paginas_filtradas}'.")
        else:
            print(f"Falha ao extrair texto do PDF '{arquivo_pdf}'.")
        
        arquivos_para_remover = [
            caminho_txt_paginas_filtradas,
            caminho_txt_paragrafos_filtrados
        ]
        remover_arquivos_temporarios(arquivos_para_remover)

        return arquivo_decretos

if __name__ == "__main__":
    caminho = "S:\\GEAD-DRH\\DIAFI-DRH\\DRH - GESTÃO DE PESSOAS\\APLICATIVOS\\Testes-IAT\\"
    ler(caminho)