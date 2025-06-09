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
    try:
        with open(caminho_txt_entrada, 'r', encoding='utf-8') as f_entrada, \
             open(caminho_txt_saida, 'w', encoding='utf-8') as f_saida:
            
            conteudo = f_entrada.read()
            paragrafos = re.split(r'\n\s*\n+', conteudo)
            flags = 0 if matchcase else re.IGNORECASE
            
            for paragrafo in paragrafos:
                # Remove espaços em branco do início e fim do parágrafo para uma correspondência precisa.
                paragrafo_limpo = paragrafo.strip()
                
                # Critério 1: Verifica se é um marcador de página.
                is_page_marker = re.match(r'--- Início da Página \d+ ---', paragrafo_limpo)
                
                # Critério 2: Verifica se o parágrafo começa com "DECRETO".
                starts_with_decreto = re.match(r'^DECRETO', paragrafo_limpo, flags=flags)
                
                # Critério 3: Verifica se o parágrafo termina com "Governador do Estado".
                # Usa \s*$ para considerar espaços em branco opcionais antes do fim da linha.
                ends_with_governador = re.search(r'Governador do Estado\s*$', paragrafo_limpo, flags=flags)
                
                # Critério 4: Verifica se o parágrafo contém alguma das palavras-chave fornecidas.
                # A \b garante que a palavra seja correspondida como uma palavra inteira.
                contains_keywords = any(re.search(r'\b' + re.escape(palavra) + r'\b', paragrafo_limpo, flags=flags) 
                                        for palavra in palavras_chave)
                
                # Inclui o parágrafo se qualquer um dos critérios for verdadeiro:
                # É um marcador de página OU (começa com DECRETO E termina com Governador do Estado) OU contém palavras-chave.
                if is_page_marker or \
                   (starts_with_decreto and ends_with_governador) or \
                   contains_keywords:
                    # Escreve o parágrafo limpo no arquivo de saída, adicionando uma linha em branco
                    # para manter a separação dos parágrafos no arquivo de saída.
                    f_saida.write("\n\n" + paragrafo_limpo + '\n\n')
                    
    except Exception as e:
        # Em caso de erro, imprime a mensagem de erro e retorna False.
        print(f"Erro ao filtrar parágrafos de '{caminho_txt_entrada}': {e}")
        return False
        
    # Se a execução for bem-sucedida, retorna True.
    return True

def extrair_decretos(paragrafos, matchcase=False):
    decretos_encontrados = []
    decreto_atual_linhas = []
    capturando = False
    flags = 0 if matchcase else re.IGNORECASE

    # Padrão para identificar o início de um decreto, capturando o número
    padrao_inicio_decreto = re.compile(
        r'\bDECRETO\b', 
        flags
    )

    # Padrões para identificar o fim de um DECRETO (fim de um bloco administrativo)
    # Não inclui "Início da Página" como delimitador de fim de documento.
    padrao_fim_decreto_bloco = re.compile(
        r'(?:\bGovernador do Estado\b)',
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
    # Define as flags para a expressão regular, considerando a sensibilidade a maiúsculas/minúsculas.
    flags = 0 if matchcase else re.IGNORECASE
    
    # Compila os padrões regex para eficiência
    padrao_inicio_decreto = re.compile(r'DECRETO', flags)
    padrao_nomeacao = re.compile(r'Nomeia|Nomeação', flags)
    padrao_orgao_seap = re.compile(r'Secretaria\s+de\s+Estado\s+da\s+Administração\s+e\s+da\s+Previdência\s*-\s*SEAP', flags)
    padrao_orgao_iat = re.compile(r'INSTITUTO\s+ÁGUA\s+E\s+TERRA|\bIAT\b', flags)
    # Novo padrão para verificar a frase "Governador do Estado"
    padrao_governador_estado = re.compile(r'Governador\s+do\s+Estado', flags)
    
    # Itera sobre os decretos usando índices
    for i in range(len(decretos)):
        current_decreto_conteudo = decretos[i].strip() # Pega o conteúdo do decreto atual
        
        # Primeiro critério: O decreto atual DEVE começar com "DECRETO"
        if not padrao_inicio_decreto.search(current_decreto_conteudo):
            continue # Se não começar com "DECRETO", pula para o próximo decreto
        
        # Realiza a busca dos padrões na string
        is_nomeacao = bool(padrao_nomeacao.search(current_decreto_conteudo))
        is_seap = bool(padrao_orgao_seap.search(current_decreto_conteudo))
        is_iat = bool(padrao_orgao_iat.search(current_decreto_conteudo))
        is_governador_do_estado = bool(padrao_governador_estado.search(current_decreto_conteudo)) # Nova verificação
        
        # Se todos os critérios forem atendidos pela janela, adiciona o *decreto atual* à lista filtrada
        if is_nomeacao and (is_seap or is_iat) or is_governador_do_estado:
            decretos_filtrados.append(current_decreto_conteudo)

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
    
    padrao_pdf = os.path.join(caminho_diretorio, "EX*.pdf")
    arquivos_pdf = glob.glob(padrao_pdf)

    palavras_chave_gerais = [
        "DECRETO", "Nomeação", "Nomeia", 
        "Secretaria de Estado da Administração e da Previdência - SEAP", "INSTITUTO ÁGUA E TERRA", "IAT",
    ]
    
    for arquivo_pdf in arquivos_pdf:
        nome_base = os.path.basename(arquivo_pdf).replace(".pdf", "")
        caminho_txt_paginas_filtradas = os.path.join(caminho_diretorio, f"{nome_base}_decretos_paginas_filtradas.txt")
        caminho_txt_paragrafos_filtrados = os.path.join(caminho_diretorio, f"{nome_base}_decretos_paragrafos_filtrados.txt")
        caminho_txt_decretos_nomeacao_orgao = os.path.join(caminho_diretorio, f"EX_{nome_base}_decretos_nomeacao_SEAP_IAT.txt")
        
        print("Separando páginas...")
        if extrair_texto_pdf(arquivo_pdf, caminho_txt_paginas_filtradas, palavras_chave_gerais):
            print("Separando parágrafos...")
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
        #remover_arquivos_temporarios(arquivos_para_remover)

if __name__ == "__main__":
    caminho = "S:\\GEAD-DRH\\DIAFI-DRH\\DRH - GESTÃO DE PESSOAS\\APLICATIVOS\\Testes-IAT\\"
    ler(caminho)