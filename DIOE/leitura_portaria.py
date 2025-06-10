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
            
            for paragrafo in paragrafos:
                # Remove espaços em branco do início e fim do parágrafo para uma correspondência precisa.
                paragrafo_limpo = paragrafo.strip()
                
                # Critério 1: Verifica se é um marcador de página.
                is_page_marker = re.match(r'--- Início da Página \d+ ---', paragrafo_limpo)
                
                # Critério 2: Verifica se o parágrafo começa com "DECRETO".
                starts_with_portaria = re.match(r'PORTARIA', paragrafo_limpo, flags=flags)
                
                # Critério 3: Verifica se o parágrafo termina com "Governador do Estado".
                # Usa \s*$ para considerar espaços em branco opcionais antes do fim da linha.
                ends_with = re.search(r'Diretor\s*-\s*Presidente do Instituto Água e Terra', paragrafo_limpo, flags=flags)
                
                # Critério 4: Verifica se o parágrafo contém alguma das palavras-chave fornecidas.
                # A \b garante que a palavra seja correspondida como uma palavra inteira.
                contains_keywords = any(re.search(r'\b' + re.escape(palavra) + r'\b', paragrafo_limpo, flags=flags) 
                                        for palavra in palavras_chave)
                
                # Inclui o parágrafo se qualquer um dos critérios for verdadeiro:
                # É um marcador de página OU (começa com DECRETO E termina com Governador do Estado) OU contém palavras-chave.
                if is_page_marker or \
                   (starts_with_portaria and ends_with) or \
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

def extrair_portarias(paragrafos, matchcase=False):
    portarias_encontradas = []
    portaria_atual_linhas = []
    capturando = False
    flags = 0 if matchcase else re.IGNORECASE
    fim_bloco_count = 0 # Contador para as ocorrências do padrão de fim de bloco

    # Padrão para identificar o início de uma portaria
    padrao_inicio_portaria = re.compile(
        r'\bPORTARIA\b', 
        flags
    )

    # Padrão para identificar o fim de uma PORTARIA (fim de um bloco administrativo)
    padrao_fim_portaria_bloco = re.compile(
        r'\bDiretor\s*-\s*Presidente do Instituto Água e Terra\b',
        flags
    )

    for i, paragrafo in enumerate(paragrafos):
        # Ignora marcadores de página ao processar documentos
        if re.match(r'--- Início da Página \d+ ---', paragrafo):
            continue

        is_inicio_portaria = padrao_inicio_portaria.search(paragrafo)
        is_fim_bloco = padrao_fim_portaria_bloco.search(paragrafo)

        if is_inicio_portaria:
            if capturando and portaria_atual_linhas:
                # Se já estava capturando e encontrou um novo início de portaria,
                # finalize a portaria anterior (mesmo que o segundo delimitador não tenha sido encontrado).
                # Isso é importante para evitar portarias "perdidas" se o padrão de fim não se repetir.
                portarias_encontradas.append("\n".join(portaria_atual_linhas).strip())
            portaria_atual_linhas = [paragrafo] # Começa uma nova portaria com o parágrafo atual
            capturando = True
            fim_bloco_count = 0 # Reseta o contador para a nova portaria
        elif capturando:
            # Se estamos capturando, adicione o parágrafo atual à portaria
            portaria_atual_linhas.append(paragrafo)
            
            # Se o parágrafo adicionado contém o marcador de fim de bloco
            if is_fim_bloco:
                fim_bloco_count += 1 # Incrementa o contador
                
                # Se esta é a segunda ocorrência do marcador de fim de bloco,
                # finalize a portaria atual.
                if fim_bloco_count == 2:
                    portarias_encontradas.append("\n".join(portaria_atual_linhas).strip())
                    portaria_atual_linhas = [] # Limpa para a próxima portaria
                    capturando = False
                    fim_bloco_count = 0 # Reseta o contador
                
    # Adiciona a última portaria se ainda estiver capturando ao final do loop
    # Isso pode ocorrer se o segundo delimitador não foi encontrado até o final do documento.
    if portaria_atual_linhas:
        portarias_encontradas.append("\n".join(portaria_atual_linhas).strip())

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
    padrao_fim = re.compile(r'Diretor\s*-\s*Presidente do Instituto Água e Terra', flags)
    
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
            for i, decreto in enumerate(documentos):
                # Tenta identificar o número do decreto para incluir no marcador
                match_numero = re.search(r'\bPORTARIA Nº\s*([\d.]+)', decreto, re.IGNORECASE)
                numero = match_numero.group(1).strip() if match_numero else "Sem Numero"
                
                f.write(f"\n--- INÍCIO {titulo_secao} {numero} ---\n")
                f.write(decreto.strip() + "\n")
                f.write(f"--- FIM {titulo_secao} {numero} ---\n\n")
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
    print("Iniciando leitura de portarias...")
    
    padrao_pdf = os.path.join(caminho_diretorio, "EX*.pdf")
    arquivos_pdf = glob.glob(padrao_pdf)

    palavras_chave_gerais = [
        "PORTARIA Nº", "Designar", "férias",
        "INSTITUTO ÁGUA E TERRA", "IAT"
    ]

    for arquivo_pdf in arquivos_pdf:
        nome_base = os.path.basename(arquivo_pdf).replace(".pdf", "")
        caminho_txt_paginas_filtradas = os.path.join(caminho_diretorio, f"{nome_base}_portarias_paginas_filtradas.txt")
        caminho_txt_paragrafos_filtrados = os.path.join(caminho_diretorio, f"{nome_base}_portarias_paragrafos_filtrados.txt")
        caminho_txt_portarias_designacao_iat = os.path.join(caminho_diretorio, f"{nome_base}_portarias.txt")

        print("Separando páginas...")
        if extrair_texto_pdf(arquivo_pdf, caminho_txt_paginas_filtradas, palavras_chave_gerais):
            print("Separando parágrafos...")
            if filtrar_paragrafos_por_palavras_chave(caminho_txt_paginas_filtradas, caminho_txt_paragrafos_filtrados, palavras_chave_gerais):
                with open(caminho_txt_paragrafos_filtrados, 'r', encoding='utf-8') as f:
                    texto_paragrafos = f.read().split('\n')
                
                matchcase = True
                todas_portarias = extrair_portarias(texto_paragrafos, matchcase)
                
                portarias_filtradas_e_classificadas = filtrar_portarias_designacao_ferias_iat(todas_portarias, matchcase)

                if portarias_filtradas_e_classificadas:
                    salvar_documentos_em_arquivo(
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

if __name__ == "__main__":
    caminho = "S:\\GEAD-DRH\\DIAFI-DRH\\DRH - GESTÃO DE PESSOAS\\APLICATIVOS\\Testes-IAT\\"
    ler(caminho)