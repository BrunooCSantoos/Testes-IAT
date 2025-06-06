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
    try:
        with open(caminho_txt_entrada, 'r', encoding='utf-8') as f_entrada, open(caminho_txt_saida, 'w', encoding='utf-8') as f_saida:
            conteudo = f_entrada.read()
            # Ajuste aqui para dividir por '\n\n' para considerar blocos de parágrafos,
            # mas ainda processar cada linha individualmente dentro das funções de extração.
            # O importante é que a função `extrair_decretos` receba linhas.
            paragrafos = conteudo.split('\n') 
            
            flags = 0 if matchcase else re.IGNORECASE
            
            for paragrafo in paragrafos:
                # Se o parágrafo é um marcador de página ou contém palavras-chave relevantes
                if re.match(r'--- Início da Página \d+ ---', paragrafo) or \
                   any(re.search(r'\b' + re.escape(palavra) + r'\b', paragrafo, flags=flags) for palavra in palavras_chave):
                    f_saida.write(paragrafo.strip() + '\n')
    except Exception as e:
        print(f"Erro ao filtrar parágrafos de '{caminho_txt_entrada}': {e}")
        return False
    return True

def extrair_decretos(paragrafos, matchcase=False):
    decretos_encontrados = []
    decreto_atual_linhas = []
    capturando = False
    flags = 0 if matchcase else re.IGNORECASE

    # Padrão para identificar o início de um decreto, capturando o número
    padrao_inicio_decreto = re.compile(r'\bDECRETO Nº\s*([\d.]+)', flags)

    # Padrões para identificar o fim de um DECRETO (fim de um bloco administrativo)
    # Não inclui "Início da Página" como delimitador de fim de documento.
    padrao_fim_decreto_bloco = re.compile(
        r'(?:^|\n)(?:'
        r'\bDECRETO Nº\s*[\d.]+|'              # Início de um novo DECRETO
        r'\bPORTARIA Nº\s*[\d.]+|'             # Início de uma nova PORTARIA
        r'Despachos do Governador|'          # Início de seção de despachos do Governador
        r'Despachos do Chefe da Casa Civil|' # Início de seção de despachos do Chefe da Casa Civil
        r'MINUTA DECRETO|'                   # Outro marcador que pode indicar fim de um documento
        r'RESOLUÇÃO SEFA|'                   # Outro tipo de documento oficial
        r'ATO DO SECRETÁRIO|'                # Outro tipo de ato
        r'COORDENADORIA DO PROGRAMA ESTADUAL DE SANIDADE ANIMAL|' # Outra seção
        r'DEPARTAMENTO DE TRÂNSITO DO PARANÁ - DETRAN/PR|' # Outra seção
        r'SECRETARIA DA CIÊNCIA, TECNOLOGIA E ENSINO SUPERIOR|' # Outra seção
        r'\Z'                                # Fim do arquivo (garante que o último seja capturado)
        r')',
        flags
    )

    for i, paragrafo in enumerate(paragrafos):
        # Ignora marcadores de página ao processar documentos
        if re.match(r'--- Início da Página \d+ ---', paragrafo):
            continue

        is_inicio_decreto = padrao_inicio_decreto.search(paragrafo)
        is_fim_bloco = padrao_fim_decreto_bloco.search(paragrafo)

        if is_inicio_decreto:
            if capturando and decreto_atual_linhas:
                # Se já estava capturando e encontrou um novo decreto,
                # finalize o anterior e comece um novo.
                decretos_encontrados.append("\n".join(decreto_atual_linhas).strip())
                decreto_atual_linhas = [] # Limpa para o novo documento
            capturando = True
            decreto_atual_linhas.append(paragrafo)
        elif capturando:
            # Se estamos capturando e encontramos um delimitador de fim de bloco/seção
            # que NÃO é um novo decreto (já tratado acima).
            if is_fim_bloco and not is_inicio_decreto:
                # Verifica se o delimitador é realmente o fim de um decreto e não parte dele.
                # Se o parágrafo atual é um delimitador e não é o início de um novo DECRETO/PORTARIA,
                # então o documento atual termina antes dele.
                decretos_encontrados.append("\n".join(decreto_atual_linhas).strip())
                decreto_atual_linhas = []
                capturando = False
                
                # Se o parágrafo atual é o início de outro tipo de documento (Portaria)
                # ou uma nova seção que deve ser ignorada, ele não deve ser adicionado ao decreto atual.
                # A próxima iteração ou outra função de extração tratará disso.
                
            else:
                decreto_atual_linhas.append(paragrafo)

    # Adiciona o último decreto se ainda estiver capturando ao final do loop
    if decreto_atual_linhas:
        decretos_encontrados.append("\n".join(decreto_atual_linhas).strip())

    return decretos_encontrados

def filtrar_decretos_de_nomeacao_por_orgao(decretos, matchcase=False):
    decretos_filtrados = []
    flags = 0 if matchcase else re.IGNORECASE
    
    padrao_nomeacao = re.compile(r'Nomeia,\s+em\s+virtude\s+de\s+habilitação\s+em\s+concurso\s+público|Nomeação\s+de\s+servidores|Nomeação\s+para\s+o\s+cargo', flags)
    padrao_orgao_seap = re.compile(r'Secretaria\s+de\s+Estado\s+da\s+Administração\s+e\s+da\s+Previdência\s*–\s*SEAP', flags)
    padrao_orgao_iat = re.compile(r'INSTITUTO\s+ÁGUA\s+E\s+TERRA|\bIAT\b', flags)
    
    # Adicionado padrão para verificar se o decreto é de ampliação de vagas
    # Este padrão deve capturar "ampliação de X vagas"
    padrao_ampliacao_vagas = re.compile(r'AUTORIZO\s*,\s*nos\s+termos\s+do\s+art\.\s*\d+º,\s*§\d+º,\s*do\s+Decreto\s*nº\s*[\d.]+/[\d]{4},\s*a\s+ampliação\s+de\s*(\d+)\s*\((\w+)\)\s*vagas', flags)
    
    for decreto_conteudo in decretos:
        is_nomeacao = bool(padrao_nomeacao.search(decreto_conteudo))
        is_seap = bool(padrao_orgao_seap.search(decreto_conteudo))
        is_iat = bool(padrao_orgao_iat.search(decreto_conteudo))
        
        match_ampliacao = padrao_ampliacao_vagas.search(decreto_conteudo)

        if is_nomeacao and (is_seap or is_iat):
            decretos_filtrados.append(decreto_conteudo)
        elif match_ampliacao: # Se for um decreto de ampliação de vagas, adicione também
            decretos_filtrados.append(decreto_conteudo)

    return decretos_filtrados

def salvar_decretos_em_arquivo(decretos, caminho_arquivo, titulo_secao="DECRETO"):
    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            for i, decreto in enumerate(decretos):
                # Tenta identificar o número do decreto para incluir no marcador
                match_numero = re.search(r'\bDECRETO Nº\s*([\d.]+)', decreto, re.IGNORECASE)
                numero = match_numero.group(1).strip() if match_numero else "Sem Numero"
                
                # Para decretos de ampliação de vagas, podemos adicionar uma identificação extra
                identificacao_extra = ""
                if "ampliação de" in decreto.lower() and "vagas" in decreto.lower():
                    identificacao_extra = " (Ampliação de Vagas)"
                
                f.write(f"\n--- INÍCIO DO {titulo_secao} {numero}{identificacao_extra} ---\n")
                f.write(decreto.strip() + "\n")
                f.write(f"--- FIM DO {titulo_secao} {numero}{identificacao_extra} ---\n\n")
        print(f"Decretos salvos em: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao salvar decretos em '{caminho_arquivo}': {e}")

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
    
    padrao_pdf = os.path.join(caminho_diretorio, "*.pdf")
    arquivos_pdf = glob.glob(padrao_pdf)

    palavras_chave_gerais = [
        "DECRETO Nº", "Nomeação", "servidores", "cargo", "Quadro Próprio do Poder Executivo",
        "Secretaria de Estado da Administração e da Previdência – SEAP", "INSTITUTO ÁGUA E TERRA", "IAT",
        "concurso público", "ampliação de vagas" # Adicionado para capturar decretos de ampliação
    ]
    
    for arquivo_pdf in arquivos_pdf:
        nome_base = os.path.basename(arquivo_pdf).replace(".pdf", "")
        caminho_txt_paginas_filtradas = os.path.join(caminho_diretorio, f"{nome_base}_decretos_paginas_filtradas.txt")
        caminho_txt_paragrafos_filtrados = os.path.join(caminho_diretorio, f"{nome_base}_decretos_paragrafos_filtrados.txt")
        caminho_txt_decretos_nomeacao_orgao = os.path.join(caminho_diretorio, f"EX_{nome_base}_decretos_nomeacao_SEAP_IAT.txt")
        
        if extrair_texto_pdf(arquivo_pdf, caminho_txt_paginas_filtradas, palavras_chave_gerais):
            if filtrar_paragrafos_por_palavras_chave(caminho_txt_paginas_filtradas, caminho_txt_paragrafos_filtrados, palavras_chave_gerais):
                with open(caminho_txt_paragrafos_filtrados, 'r', encoding='utf-8') as f:
                    texto_paragrafos = f.read().split('\n')
                
                matchcase = False
                todos_decretos = extrair_decretos(texto_paragrafos, matchcase)
                
                decretos_nomeacao_orgao_final = filtrar_decretos_de_nomeacao_por_orgao(todos_decretos, matchcase)

                if decretos_nomeacao_orgao_final:
                    salvar_decretos_em_arquivo(decretos_nomeacao_orgao_final, caminho_txt_decretos_nomeacao_orgao, titulo_secao="DECRETO") # Título mais genérico
                else:
                    print(f"Nenhum decreto de nomeação ou ampliação de vagas referente à SEAP ou IAT encontrado para salvar em '{caminho_txt_decretos_nomeacao_orgao}'.")
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