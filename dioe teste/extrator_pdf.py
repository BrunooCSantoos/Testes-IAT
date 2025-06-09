import PyPDF2
import re
import os

def extrair_texto_pdf(caminho_pdf):
    """
    Extrai todo o texto de um PDF, página por página.
    Retorna uma lista onde cada elemento é o texto de uma página.
    """
    textos = []
    try:
        with open(caminho_pdf, 'rb') as arquivo:
            leitor = PyPDF2.PdfReader(arquivo)
            for num_pagina in range(len(leitor.pages)):
                pagina = leitor.pages[num_pagina]
                textos.append(pagina.extract_text())
    except Exception as e:
        print(f"Erro ao extrair texto do PDF: {e}")
        return None
    return textos

def identificar_e_salvar_paginas_relevantes(todos_textos_paginas, diretorio_saida="paginas_relevantes", palavras_chave_relevantes=None):
    """
    Identifica páginas relevantes e salva seu texto em arquivos TXT.
    A relevância é definida por palavras-chave que indicam portarias/decretos.
    """
    if not os.path.exists(diretorio_saida):
        os.makedirs(diretorio_saida)

    info_paginas_relevantes = []
    
    for i, texto_pagina in enumerate(todos_textos_paginas):
        num_pagina = i + 1
        e_relevante = False

        if palavras_chave_relevantes:
            for palavra_chave in palavras_chave_relevantes:
                if re.search(r'\b' + re.escape(palavra_chave) + r'\b', texto_pagina, re.IGNORECASE):
                    e_relevante = True
                    break
        
        if e_relevante:
            nome_arquivo = os.path.join(diretorio_saida, f"pagina_relevante_{num_pagina}.txt")
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                f.write(texto_pagina)
            print(f"Página {num_pagina} identificada como relevante e salva em {nome_arquivo}")
            info_paginas_relevantes.append((num_pagina, nome_arquivo))
    
    return info_paginas_relevantes