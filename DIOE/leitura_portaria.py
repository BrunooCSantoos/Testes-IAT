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
                        arquivo_txt_saida.write(f"--- Início da Página {pagina_num + 1} ---\n")
                        arquivo_txt_saida.write(texto_pagina.strip() + "\n\n") 
            arquivo_txt_saida.write("\n\f\n") 
    except Exception as e:
        print(f"Erro ao extrair texto do PDF '{caminho_pdf}': {e}")
        return False
    return True

def filtrar_paragrafos_por_palavras_chave(caminho_txt_entrada, caminho_txt_saida, palavras_chave, matchcase=False):
    try:
        with open(caminho_txt_entrada, 'r', encoding='utf-8') as f_entrada, \
             open(caminho_txt_saida, 'w', encoding='utf-8') as f_saida:
            
            conteudo = f_entrada.read()
            paragrafos = re.split(r'\n\s*\n+', conteudo)
            flags = 0 if matchcase else re.IGNORECASE
            
            # Compila os padrões regex uma vez para melhor desempenho
            padrao_marcador_pagina = re.compile(r'--- Início da Página \d+ ---')
            padrao_inicio_portaria = re.compile(r'PORTARIA', flags=flags)
            padrao_fim_bloco_administrativo = re.compile(r'Diretor\s*-\s*Presidente\s+do\s+Instituto\s+Água\s+e\s+Terra', flags=flags)
            
            # Constrói o padrão para qualquer palavra-chave
            padrao_palavras_chave = re.compile(
                r'\b(?:' + '|'.join(re.escape(palavra) for palavra in palavras_chave) + r')\b',
                flags
            )

            # Variáveis para a lógica de captura
            capturando_bloco = False
            bloco_atual_linhas = []

            for paragrafo in paragrafos:
                paragrafo_limpo = paragrafo.strip()
                
                # Ignora marcadores de página
                if padrao_marcador_pagina.match(paragrafo_limpo):
                    continue

                is_inicio_portaria = padrao_inicio_portaria.search(paragrafo_limpo)
                is_fim_bloco_administrativo = padrao_fim_bloco_administrativo.search(paragrafo_limpo)
                contains_keywords = padrao_palavras_chave.search(paragrafo_limpo)

                # Lógica de início de um novo bloco de interesse
                # Um bloco começa se for uma "PORTARIA" OU se contiver qualquer palavra-chave
                # Se for o início de uma nova PORTARIA e já estamos capturando, finaliza o bloco anterior.
                if is_inicio_portaria:
                    if capturando_bloco and bloco_atual_linhas:
                        f_saida.write("\n".join(bloco_atual_linhas) + '\n\n')
                    bloco_atual_linhas = [paragrafo_limpo] # Começa um novo bloco
                    capturando_bloco = True
                elif contains_keywords and not capturando_bloco:
                    # Se contiver palavras-chave e não estamos capturando, inicie a captura.
                    # Isso captura blocos que não começam explicitamente com "PORTARIA" mas são relevantes.
                    bloco_atual_linhas = [paragrafo_limpo]
                    capturando_bloco = True
                elif capturando_bloco:
                    # Se estamos capturando, adicione o parágrafo atual ao bloco
                    bloco_atual_linhas.append(paragrafo_limpo)
                    
                    # Se o parágrafo atual contém o marcador de fim de bloco administrativo,
                    # e estamos no final de um bloco lógico (como uma portaria), finaliza a captura.
                    # Aqui, a lógica de "dois Diretor-Presidente" é específica da extrair_portarias.
                    # Para a filtragem geral, um único 'fim_bloco_administrativo' pode ser o suficiente para terminar o bloco atual.
                    if is_fim_bloco_administrativo:
                        f_saida.write("\n".join(bloco_atual_linhas) + '\n\n')
                        bloco_atual_linhas = [] # Limpa para o próximo bloco
                        capturando_bloco = False
            
            # Adiciona o último bloco se ainda estiver capturando ao final do loop
            if bloco_atual_linhas:
                f_saida.write("\n".join(bloco_atual_linhas) + '\n\n')
                    
    except Exception as e:
        print(f"Erro ao filtrar parágrafos de '{caminho_txt_entrada}': {e}")
        return False
        
    return True

def extrair_portarias(paragrafos, matchcase=False):
    portarias_encontradas = []
    portaria_atual_linhas = []
    capturando = False
    flags = 0 if matchcase else re.IGNORECASE
    fim_bloco_count = 0 # Contador para as ocorrências do padrão de fim de bloco
    numeros_portarias_existentes = set() # Novo: Armazena os números das portarias já adicionadas

    # Padrão para identificar o início de uma portaria
    padrao_inicio_portaria = re.compile(
        r'\bPORTARIA\s*Nº?\s*(\d+)', # Modificado para capturar o número da portaria
        flags
    )

    # Padrão para identificar o fim de uma PORTARIA (fim de um bloco administrativo)
    padrao_fim_portaria_bloco = re.compile(
        r'\bDiretor\s*-\s*Presidente\s+do\s+Instituto\s+Água\s+e\s+Terra\b',
        flags
    )

    for i, paragrafo in enumerate(paragrafos):
        # Ignora marcadores de página ao processar documentos
        if re.match(r'--- Início da Página \d+ ---', paragrafo):
            continue

        is_inicio_portaria = padrao_inicio_portaria.search(paragrafo)
        is_fim_bloco = padrao_fim_portaria_bloco.search(paragrafo)

        if is_inicio_portaria:
            # Extrai o número da portaria
            numero_portaria = is_inicio_portaria.group(1)

            if capturando and portaria_atual_linhas:
                # Se já estava capturando e encontrou um novo início de portaria,
                # finalize a portaria anterior (mesmo que o segundo delimitador não tenha sido encontrado).
                # Isso é importante para evitar portarias "perdidas" se o padrão de fim não se repetir.
                finalized_portaria = "\n".join(portaria_atual_linhas).strip()
                # Verifica duplicata antes de adicionar (para a portaria anterior)
                # Esta verificação é um pouco redundante aqui se o fluxo principal já faz a verificação,
                # mas serve como um "fail-safe" caso a lógica de fim de bloco seja mais complexa.
                # No entanto, a principal verificação de duplicidade ocorrerá quando a portaria for "fechada" abaixo.
                
            # Inicia uma nova portaria se o número não for um duplicado
            if numero_portaria not in numeros_portarias_existentes:
                portaria_atual_linhas = [paragrafo] # Começa uma nova portaria com o parágrafo atual
                capturando = True
                fim_bloco_count = 0 # Reseta o contador para a nova portaria
            else:
                # Se for um número duplicado, não inicia a captura para esta portaria
                capturando = False # Garante que não continuemos capturando para esta duplicata
                portaria_atual_linhas = [] # Limpa as linhas atuais
        elif capturando:
            # Se estamos capturando, adicione o parágrafo atual à portaria
            portaria_atual_linhas.append(paragrafo)
            
            # Se o parágrafo adicionado contém o marcador de fim de bloco
            if is_fim_bloco:
                fim_bloco_count += 1 # Incrementa o contador
                
                # Se esta é a segunda ocorrência do marcador de fim de bloco,
                # finalize a portaria atual.
                if fim_bloco_count == 2:
                    finalized_portaria = "\n".join(portaria_atual_linhas).strip()
                    # Extrai o número da portaria a ser adicionada
                    match_numero = padrao_inicio_portaria.search(finalized_portaria)
                    if match_numero:
                        numero_portaria_finalizada = match_numero.group(1)
                        if numero_portaria_finalizada not in numeros_portarias_existentes:
                            portarias_encontradas.append(finalized_portaria)
                            numeros_portarias_existentes.add(numero_portaria_finalizada) # Adiciona ao conjunto de números existentes
                    
                    portaria_atual_linhas = [] # Limpa para a próxima portaria
                    capturando = False
                    fim_bloco_count = 0 # Reseta o contador
                
    # Adiciona a última portaria se ainda estiver capturando ao final do loop
    # Isso pode ocorrer se o segundo delimitador não foi encontrado até o final do documento.
    if portaria_atual_linhas:
        finalized_portaria = "\n".join(portaria_atual_linhas).strip()
        match_numero = padrao_inicio_portaria.search(finalized_portaria)
        if match_numero:
            numero_portaria_finalizada = match_numero.group(1)
            if numero_portaria_finalizada not in numeros_portarias_existentes:
                portarias_encontradas.append(finalized_portaria)
                numeros_portarias_existentes.add(numero_portaria_finalizada)

    return portarias_encontradas

def filtrar_portarias_designacao_ferias_iat(portarias, matchcase=True):
    portarias_filtrados = []
    # Define as flags para a expressão regular, considerando a sensibilidade a maiúsculas/minúsculas.
    flags = 0 if matchcase else re.IGNORECASE
    
    # Compila os padrões regex para eficiência
    padrao_inicio_portaria = re.compile(r'PORTARIA', flags)
    padrao_designacao = re.compile(r'Designar|Designação|Designa', flags)
    padrao_ferias = re.compile(r'férias', flags)
    # Novo padrão para verificar a frase "Governador do Estado"
    padrao_fim = re.compile(r'Diretor\s*-\s*Presidente\s+do\s+Instituto\s+Água\s+e\s+Terra', flags)
    
    # Itera sobre os decretos usando índices
    for i in range(len(portarias)):
        current_portaria_conteudo = portarias[i].strip() # Pega o conteúdo do decreto atual
        
        # Primeiro critério: O decreto atual DEVE começar com "DECRETO"
        if not padrao_inicio_portaria.search(current_portaria_conteudo):
            continue # Se não começar com "DECRETO", pula para o próximo decreto
        
        # Realiza a busca dos padrões na string concatenada da janela
        is_designacao = bool(padrao_designacao.search(current_portaria_conteudo))
        is_ferias = bool(padrao_ferias.search(current_portaria_conteudo))
        is_governador_do_estado = bool(padrao_fim.search(current_portaria_conteudo)) # Nova verificação
        
        # Se todos os critérios forem atendidos pela janela, adiciona o *decreto atual* à lista filtrada
        if is_designacao and is_ferias and is_governador_do_estado:
            portarias_filtrados.append(current_portaria_conteudo)

    return portarias_filtrados

def salvar_documentos_em_arquivo(documentos, caminho_arquivo, titulo_secao):
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            for i, portaria in enumerate(documentos):
                # Tenta identificar o número do decreto para incluir no marcador
                match_numero = re.search(r'\bPORTARIA Nº\s*([\d.]+)', portaria, re.IGNORECASE)
                numero = match_numero.group(1).strip() if match_numero else "Sem Numero"
                
                f.write(f"\n--- INÍCIO {titulo_secao} {numero} ---\n")
                f.write(portaria.strip() + "\n")
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
    print("Iniciando leitura de portarias...")

    matchcase = True
    
    padrao_pdf = os.path.join(caminho_diretorio, "EX*.pdf")
    arquivos_pdf = glob.glob(padrao_pdf)
    arquivo_portarias = None

    palavras_chave_gerais = [
        "PORTARIA Nº", "Portaria" "Designar", "férias",
        "INSTITUTO ÁGUA E TERRA", "IAT"
    ]

    for arquivo_pdf in arquivos_pdf:
        nome_base = os.path.basename(arquivo_pdf).replace(".pdf", "")
        caminho_txt_paginas_filtradas = os.path.join(caminho_diretorio, f"{nome_base}_portarias_paginas_filtradas.txt")
        caminho_txt_paragrafos_filtrados = os.path.join(caminho_diretorio, f"{nome_base}_portarias_paragrafos_filtrados.txt")
        caminho_txt_portarias_designacao_iat = os.path.join(caminho_diretorio, f"{nome_base}_portarias.txt")

        print("Separando páginas...")
        if extrair_texto_pdf(arquivo_pdf, caminho_txt_paginas_filtradas, palavras_chave_gerais, matchcase):
            print("Separando parágrafos...")
            if filtrar_paragrafos_por_palavras_chave(caminho_txt_paginas_filtradas, caminho_txt_paragrafos_filtrados, palavras_chave_gerais, matchcase):
                with open(caminho_txt_paragrafos_filtrados, 'r', encoding='utf-8') as f:
                    texto_paragrafos = f.read().split('\n')
                
                todas_portarias = extrair_portarias(texto_paragrafos, matchcase)
                
                portarias_filtradas_e_classificadas = filtrar_portarias_designacao_ferias_iat(todas_portarias, matchcase)

                if portarias_filtradas_e_classificadas:
                    arquivo_portarias = salvar_documentos_em_arquivo(
                        portarias_filtradas_e_classificadas, 
                        caminho_txt_portarias_designacao_iat, 
                        "PORTARIA"
                    )
                else:
                    print(f"Nenhuma portaria de designação ou férias referente ao IAT encontrada para salvar para '{nome_base}'.")

            else:
                print(f"Falha ao filtrar parágrafos de '{caminho_txt_paginas_filtradas}'.")
        else:
            print(f"Falha ao extrair texto do PDF '{arquivo_pdf}'.")
        
        arquivos_para_remover = [
            caminho_txt_paginas_filtradas,
            caminho_txt_paragrafos_filtrados
        ]
        remover_arquivos_temporarios(arquivos_para_remover)
        
        return arquivo_portarias

if __name__ == "__main__":
    caminho = "S:\\GEAD-DRH\\DIAFI-DRH\\DRH - GESTÃO DE PESSOAS\\APLICATIVOS\\Testes-IAT\\"
    ler(caminho)