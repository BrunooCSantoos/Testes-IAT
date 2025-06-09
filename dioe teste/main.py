import os
# Importa as funções dos módulos
from extrator_pdf import extrair_texto_pdf, identificar_e_salvar_paginas_relevantes
from analisador_texto import extrair_paragrafos_relevantes, extrair_informacoes_chave
from gerador_saida import criar_csv_a_partir_dados, criar_pdf_resumo

def main():
    """
    Função principal para orquestrar o processamento do documento.
    """
    caminho_documento_pdf = "EX_2024-12-06.pdf" # Substitua pelo caminho do seu arquivo PDF

    if not os.path.exists(caminho_documento_pdf):
        print(f"Erro: O arquivo PDF '{caminho_documento_pdf}' não foi encontrado.")
        print("Por favor, certifique-se de que o PDF está na mesma pasta que o script ou forneça o caminho completo.")
        return

    print(f"Iniciando o processamento do documento: {caminho_documento_pdf}")
    
    # 1. Extrair todo o texto do PDF
    todos_textos_paginas = extrair_texto_pdf(caminho_documento_pdf)
    if not todos_textos_paginas:
        print("Não foi possível extrair texto do PDF. Abortando.")
        return

    # --- Configurações de Relevância ---
    # Palavras-chave para identificar páginas que contêm Portarias/Decretos
    palavras_chave_paginas_relevantes = ["PORTARIA Nº", "DECRETO Nº", "NOMEAR", "EXONERAR", "DESIGNAR"]
    
    # Palavras-chave para parágrafos relevantes (podem ser mais genéricas)
    palavras_chave_paragrafos_relevantes = [
        "PORTARIA", "DECRETO", "NOMEAR", "EXONERAR", "DESIGNAR", "DISPENSAR",
        "servidor", "cargo", "função", "matrícula", "CPF", "CNPJ", "processo administrativo",
        "Diário OFICIAL Executivo", "Art. 1º", "Art. 2º" # Adicionando termos mais gerais e de artigo
    ]

    # 2. Identificar e salvar páginas relevantes (baseado em palavras-chave de Portaria/Decreto)
    print("\n--- Etapa 1: Identificando e salvando páginas relevantes ---")
    informacoes_paginas_relevantes = identificar_e_salvar_paginas_relevantes(
        todos_textos_paginas,
        palavras_chave_relevantes=palavras_chave_paginas_relevantes
    )
    
    # 3. Separar parágrafos relevantes usando janela deslizante
    print("\n--- Etapa 2: Extraindo parágrafos relevantes com janela deslizante ---")
    if palavras_chave_paragrafos_relevantes:
        extrair_paragrafos_relevantes(todos_textos_paginas, palavras_chave_paragrafos_relevantes)
    else:
        print("Nenhuma palavra-chave para parágrafos relevantes fornecida. Pulando a extração de parágrafos.")

    # 4. Extrair informações chave de TODOS os documentos (portarias/decretos)
    print("\n--- Etapa 3: Extraindo informações chave de todos os documentos ---")
    # Agora, extrair_informacoes_chave retorna uma LISTA de dicionários
    lista_informacoes_chave = extrair_informacoes_chave(todos_textos_paginas)
    
    if lista_informacoes_chave:
        print(f"Total de {len(lista_informacoes_chave)} documentos (Portarias/Decretos) encontrados.")
        for i, info_doc in enumerate(lista_informacoes_chave):
            print(f"\n--- Detalhes do Documento {i+1} ---")
            for k, v in info_doc.items():
                print(f"  {k}: {v}")
    else:
        print("Nenhum documento (Portaria/Decreto) com informações chave pôde ser extraído.")


    # 5. Gerar CSV
    print("\n--- Etapa 4: Gerando arquivo CSV ---")
    criar_csv_a_partir_dados(lista_informacoes_chave) # Passa a lista de dicionários

    # 6. Gerar PDF para e-mail
    print("\n--- Etapa 5: Gerando PDF de resumo para e-mail ---")
    criar_pdf_resumo(lista_informacoes_chave) # Passa a lista de dicionários
    
    print("\nProcessamento concluído.")

if __name__ == "__main__":
    main()