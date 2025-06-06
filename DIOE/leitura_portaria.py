import re
import glob
import os
from PyPDF2 import PdfReader

caminho_diretorio = os.getcwd()

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
        with open(caminho_txt_entrada, 'r', encoding='utf-8') as f_entrada, open(caminho_txt_saida, 'w', encoding='utf-8') as f_saida:
            conteudo = f_entrada.read()
            paragrafos = conteudo.split('\n')
            
            flags = 0 if matchcase else re.IGNORECASE
            
            for paragrafo in paragrafos:
                if re.match(r'--- Início da Página \d+ ---', paragrafo) or \
                   any(re.search(r'\b' + re.escape(palavra) + r'\b', paragrafo, flags=flags) for palavra in palavras_chave):
                    f_saida.write(paragrafo.strip() + '\n')
    except Exception as e:
        print(f"Erro ao filtrar parágrafos de '{caminho_txt_entrada}': {e}")
        return False
    return True

def extrair_portarias(paragrafos, matchcase=False):
    portarias_encontradas = []
    portaria_atual_linhas = []
    capturando = False
    flags = 0 if matchcase else re.IGNORECASE

    # Padrão para identificar o início de uma portaria.
    # Flexibilizado para capturar "PORTARIA Nº" seguido do número, com ou sem data completa.
    # Adicionado "(?:\bINSTITUTO ÁGUA E TERRA\b\s*)?" para capturar o órgão se ele aparecer logo antes.
    # O foco é no "PORTARIA Nº" como cabeçalho.
    padrao_inicio_portaria = re.compile(
        r'(?:^|\n)\s*(?:INSTITUTO\s+ÁGUA\s+E\s+TERRA\s*|SECRETARIA\s+DE\s+ESTADO.*?|MINISTÉRIO\s+PÚBLICO.*?)?\s*PORTARIA\s+Nº\s*([\d.]+)', 
        flags
    )

    # Padrões para identificar o fim de uma PORTARIA (fim de um bloco administrativo).
    # Prioriza o início de um novo DECRETO ou PORTARIA ou SEÇÃO clara.
    padrao_fim_portaria_bloco = re.compile(
        r'(?:^|\n)(?:'
        r'\bDECRETO Nº\s*[\d.]+|'                          # Início de um novo DECRETO
        r'\bPORTARIA Nº\s*[\d.]+\s*(?:DE\s*\d+\s+DE\s+\w+\s+DE\s+\d{4})?|' # Início de uma nova PORTARIA (com ou sem data)
        r'Despachos do Governador|'                      # Início de seção de despachos do Governador
        r'Despachos do Chefe da Casa Civil|'             # Início de seção de despachos do Chefe da Casa Civil
        r'MINUTA DECRETO|'                               # Outro marcador que pode indicar fim de um documento
        r'RESOLUÇÃO SEFA|'                               # Outro tipo de documento oficial
        r'ATO DO SECRETÁRIO|'                            # Outro tipo de ato
        r'COORDENADORIA DO PROGRAMA ESTADUAL DE SANIDADE ANIMAL|' # Outra seção
        r'DEPARTAMENTO DE TRÂNSITO DO PARANÁ - DETRAN/PR|' # Outra seção
        r'SECRETARIA DA CIÊNCIA, TECNOLOGIA E ENSINO SUPERIOR|' # Outra seção
        r'\Z'                                            # Fim do arquivo (garante que o último seja capturado)
        r')',
        flags
    )

    for i, paragrafo in enumerate(paragrafos):
        if re.match(r'--- Início da Página \d+ ---', paragrafo):
            continue

        match_inicio_portaria = padrao_inicio_portaria.search(paragrafo)
        is_fim_bloco = padrao_fim_portaria_bloco.search(paragrafo)

        if match_inicio_portaria:
            # Se já estava capturando e encontrou um novo início de portaria, finalize o anterior.
            if capturando and portaria_atual_linhas:
                portarias_encontradas.append("\n".join(portaria_atual_linhas).strip())
                portaria_atual_linhas = []
            
            capturando = True
            portaria_atual_linhas.append(paragrafo)
        elif capturando:
            # Se estamos capturando e o parágrafo atual é um delimitador de fim de bloco
            # E não é um novo início de portaria (que já seria tratado pelo 'if match_inicio_portaria').
            if is_fim_bloco and not match_inicio_portaria:
                # Se o delimitador de fim de bloco REALMENTE inicia um novo ato ou seção
                # então o documento atual termina ANTES dessa linha.
                # Esta verificação é crucial para evitar cortar documentos no meio.
                if re.search(r'\bDECRETO Nº\s*[\d.]+|'
                             r'\bPORTARIA Nº\s*[\d.]+\s*(?:DE\s*\d+\s+DE\s+\w+\s+DE\s+\d{4})?|'
                             r'Despachos do Governador|'
                             r'Despachos do Chefe da Casa Civil|'
                             r'MINUTA DECRETO|RESOLUÇÃO SEFA|ATO DO SECRETÁRIO|COORDENADORIA.*?|DEPARTAMENTO.*?|SECRETARIA.*?', 
                             paragrafo, flags):
                    if portaria_atual_linhas:
                        portarias_encontradas.append("\n".join(portaria_atual_linhas).strip())
                        portaria_atual_linhas = []
                        capturando = False 
                else:
                    # Se não é um início de um novo documento/seção claro, continua capturando
                    portaria_atual_linhas.append(paragrafo)
            else:
                portaria_atual_linhas.append(paragrafo)

    if portaria_atual_linhas:
        portarias_encontradas.append("\n".join(portaria_atual_linhas).strip())

    return portarias_encontradas

def filtrar_portarias_designacao_ferias_iat(portarias, matchcase=False):
    portarias_filtradas = []
    
    # Padrão para EXCLUIR portarias que contenham "agente de contratação" ou "pregoeiro"
    padrao_exclusao_agente_contratacao = re.compile(
        r'agente\s+de\s+contratação|\bpregoeiro\b', 
        re.IGNORECASE | re.DOTALL
    )

    for portaria_conteudo in portarias:
        # PRIMEIRO: Verificar se a portaria deve ser EXCLUÍDA
        if padrao_exclusao_agente_contratacao.search(portaria_conteudo):
            print(f"Portaria excluída (agente de contratação/pregoeiro): {portaria_conteudo[:100]}...") # Log para depuração
            continue # Pula esta portaria, não a adiciona à lista de filtradas
        
        # Padrões para identificar Designação (sem ser férias) e Férias, ambos para o IAT
        # A ordem de verificação é importante.
        
        # Padrão para portarias de férias: 'Designar' e 'férias' e 'IAT' no mesmo bloco.
        padrao_ferias_iat = re.compile(
            r'Designar.*?por\s+motivo\s+de\s+férias.*?INSTITUTO\s+ÁGUA\s+E\s+TERRA|\bIAT\b', 
            re.IGNORECASE | re.DOTALL
        )
        
        # Padrão para portarias de designação (geral, que não sejam férias) E para o IAT.
        padrao_designacao_iat = re.compile(
            r'Designar.*?(?:INSTITUTO\s+ÁGUA\s+E\s+TERRA|\bIAT\b)', 
            re.IGNORECASE | re.DOTALL
        )
        
        # Ordem de verificação: Mais específico primeiro para evitar falsos positivos
        if padrao_ferias_iat.search(portaria_conteudo):
            portarias_filtradas.append((portaria_conteudo, "ferias"))
        elif padrao_designacao_iat.search(portaria_conteudo):
            portarias_filtradas.append((portaria_conteudo, "designacao"))
            
    return portarias_filtradas


def salvar_documentos_em_arquivo(documentos_com_tipo, caminho_arquivo_designacao, caminho_arquivo_ferias):
    try:
        with open(caminho_arquivo_designacao, 'w', encoding='utf-8') as f_designacao, \
             open(caminho_arquivo_ferias, 'w', encoding='utf-8') as f_ferias:
            
            for i, (doc_conteudo, tipo_doc) in enumerate(documentos_com_tipo):
                match_numero_portaria = re.search(r'\bPORTARIA Nº\s*([\d.]+)', doc_conteudo, re.IGNORECASE)
                numero = match_numero_portaria.group(1).strip() if match_numero_portaria else "Sem Numero"
                
                if tipo_doc == "designacao":
                    f_designacao.write(f"\n--- INÍCIO DA PORTARIA DE DESIGNAÇÃO IAT {numero} ---\n")
                    f_designacao.write(doc_conteudo.strip() + "\n")
                    f_designacao.write(f"--- FIM DA PORTARIA DE DESIGNAÇÃO IAT {numero} ---\n\n")
                elif tipo_doc == "ferias":
                    f_ferias.write(f"\n--- INÍCIO DA PORTARIA DE FÉRIAS IAT {numero} ---\n")
                    f_ferias.write(doc_conteudo.strip() + "\n")
                    f_ferias.write(f"--- FIM DA PORTARIA DE FÉRIAS IAT {numero} ---\n\n")

        print(f"Portarias de designação salvas em: {caminho_arquivo_designacao}")
        print(f"Portarias de férias salvas em: {caminho_arquivo_ferias}")

    except Exception as e:
        print(f"Erro ao salvar documentos: {e}")

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
    
    padrao_pdf = os.path.join(caminho_diretorio, "*.pdf")
    arquivos_pdf = glob.glob(padrao_pdf)

    palavras_chave_gerais = [
        "PORTARIA Nº", "Designar", "férias", "substituição", "servidor",
        "INSTITUTO ÁGUA E TERRA", "IAT", "cargo", "função", "RG"
    ]

    for arquivo_pdf in arquivos_pdf:
        nome_base = os.path.basename(arquivo_pdf).replace(".pdf", "")
        caminho_txt_paginas_filtradas = os.path.join(caminho_diretorio, f"{nome_base}_portarias_paginas_filtradas.txt")
        caminho_txt_paragrafos_filtrados = os.path.join(caminho_diretorio, f"{nome_base}_portarias_paragrafos_filtrados.txt")
        caminho_txt_portarias_designacao_iat = os.path.join(caminho_diretorio, f"EX_{nome_base}_portarias_designacao_IAT.txt")
        caminho_txt_portarias_ferias_iat = os.path.join(caminho_diretorio, f"EX_{nome_base}_portarias_ferias_IAT.txt")

        if extrair_texto_pdf(arquivo_pdf, caminho_txt_paginas_filtradas, palavras_chave_gerais):
            if filtrar_paragrafos_por_palavras_chave(caminho_txt_paginas_filtradas, caminho_txt_paragrafos_filtrados, palavras_chave_gerais):
                with open(caminho_txt_paragrafos_filtrados, 'r', encoding='utf-8') as f:
                    texto_paragrafos = f.read().split('\n')
                
                matchcase = False
                todas_portarias = extrair_portarias(texto_paragrafos, matchcase)
                
                portarias_filtradas_e_classificadas = filtrar_portarias_designacao_ferias_iat(todas_portarias, matchcase)

                if portarias_filtradas_e_classificadas:
                    salvar_documentos_em_arquivo(
                        portarias_filtradas_e_classificadas, 
                        caminho_txt_portarias_designacao_iat, 
                        caminho_txt_portarias_ferias_iat
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

if __name__ == "__main__":
    print("Este script é um módulo e deve ser executado através de 'main.py'.")