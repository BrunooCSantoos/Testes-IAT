import re
import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def converter_txt_para_pdf(arquivos_txt, caminho_arquivo_pdf):
    # Cria um novo documento PDF
    doc = SimpleDocTemplate(caminho_arquivo_pdf, pagesize=letter)
    
    # Obtém os estilos de parágrafo padrão
    estilo = getSampleStyleSheet()
    
    # Lista para armazenar os elementos (parágrafos, espaços, etc.) que serão adicionados ao PDF
    arquivo = []

    for arquivo_txt in arquivos_txt:
        if not os.path.exists(arquivo_txt):
            print(f"Erro: O arquivo TXT '{arquivo_txt}' não foi encontrado e será ignorado.")
            continue # Pula para o próximo arquivo se este não for encontrado

        try:
            # Abre o arquivo TXT para leitura
            with open(arquivo_txt, 'r', encoding='utf-8') as f:
                texto = f.read()

            # Adiciona o nome do arquivo como um título ou separador (opcional, para clareza)
            arquivo.append(Paragraph(f"--- Conteúdo de: {os.path.basename(arquivo_txt)} ---", estilo['h2']))
            arquivo.append(Spacer(1, 0.2 * 10))

            # Divide o texto em parágrafos. Cada linha do TXT se torna um parágrafo no PDF.
            paragrafos = texto.split('\n')
            
            for p in paragrafos:
                if p.strip():  # Adiciona apenas parágrafos que não são vazios
                    arquivo.append(Paragraph(p.strip(), estilo['Normal']))
                arquivo.append(Spacer(1, 0.2 * 10)) # Espaço após cada parágrafo

        except Exception as e:
            print(f"Ocorreu um erro ao processar o arquivo '{arquivo_txt}': {e}")
            continue # Continua para o próximo arquivo mesmo que um erro ocorra

    try:
        # Constrói o PDF com base em *todos* os elementos coletados
        doc.build(arquivo)
        print(f"PDF criado com sucesso em: {caminho_arquivo_pdf}")
    except Exception as e:
        print(f"Ocorreu um erro ao gerar o PDF: {e}")

def registro_existe(lista_registros, novo_registro):
    """
    Verifica se um registro (dicionário) já existe na lista.
    Considera um registro como duplicado se a combinação de Tipo_Documento,
    Numero_Documento, Nome e Situação for idêntica a um registro existente.
    Isso é crucial para evitar duplicatas quando a mesma portaria/decreto
    é processada de diferentes arquivos TXT (por exemplo, portaria de designação
    que também é de férias).
    """
    chaves_comparacao = ["Tipo_Documento", "Numero_Documento", "Nome", "Situação"]
    
    for registro_existente in lista_registros:
        match = True
        for chave in chaves_comparacao:
            # Verifica se a chave existe em ambos e se os valores são idênticos
            if chave in novo_registro and chave in registro_existente and \
               novo_registro[chave] != registro_existente[chave]:
                match = False
                break
            # Se a chave existe em um mas não no outro (e é uma chave de comparação),
            # não consideramos match para evitar falsos positivos com dados ausentes.
            if (chave in novo_registro and chave not in registro_existente) or \
               (chave not in novo_registro and chave in registro_existente):
                match = False
                break
        if match:
            return True
    return False

def extrair_e_salvar_informacoes_dioe(caminho_diretorio):
    print("Iniciando extração de informações dos arquivos TXT...")
    informacoes_extraidas = []
    
    # Padrão para encontrar os arquivos TXT gerados
    padrao_arquivos = os.path.join(caminho_diretorio, "EX_*.txt")
    arquivos_txt = [f for f in os.listdir(caminho_diretorio) if re.match(r"EX_.*\.txt", f)]

    for nome_arquivo in arquivos_txt:
        caminho_arquivo = os.path.join(caminho_diretorio, nome_arquivo)
        print(f"Processando arquivo: {nome_arquivo}")

        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                conteudo_completo = f.read()

            # Extrair a data do nome do arquivo
            match_data = re.search(r'EX_(\d{4}-\d{2}-\d{2})_', nome_arquivo)
            data_publicacao = "Não Identificada"
            if match_data:
                data_iso = match_data.group(1)
                dia, mes, ano = data_iso.split('-')[2], data_iso.split('-')[1], data_iso.split('-')[0]
                data_publicacao = f"Diário {dia}-{mes}-{ano}"

            # Regex para encontrar todos os blocos de documentos (portarias ou decretos)
            # Captura o marcador de início, o conteúdo do documento e o marcador de fim.
            # Usa DOTALL para pegar quebras de linha dentro do conteúdo.
            documento_blocos = re.findall(
                r'(--- INÍCIO D(?:A PORTARIA|O DECRETO)[^-\n]*---\s*)(.*?)(?=\s*--- FIM D(?:A PORTARIA|O DECRETO)[^-\n]*---|\Z)',
                conteudo_completo, re.IGNORECASE | re.DOTALL
            )
            
            if not documento_blocos:
                print(f"Nenhum bloco de documento encontrado em '{nome_arquivo}'.")
                continue # Pula para o próximo arquivo se não encontrar documentos

            for inicio_marcador, conteudo_documento_str in documento_blocos:
                # Reinicializa as variáveis para cada documento individual
                nome = "Não Encontrado"
                rg = "Não Encontrado"
                situacao = "Não Identificada"
                cargo = "Não Encontrado"
                orgao_lotacao = "Não Encontrado"
                tipo_documento = "Não Encontrado"
                numero_documento = "Não Encontrado"
                substituto_nome = "N/A"
                titular_ferias_nome = "N/A"
                periodo_ferias = "N/A"
                
                # Tentar identificar o Órgão/Lotação primeiro, pois é um bom indicador
                match_orgao_iat = re.search(r'INSTITUTO ÁGUA E TERRA', conteudo_documento_str, re.IGNORECASE)
                match_orgao_seap = re.search(r'Secretaria de Estado da Administração e da Previdência – SEAP', conteudo_documento_str, re.IGNORECASE)
                
                if match_orgao_iat:
                    orgao_lotacao = "Instituto Água e Terra - IAT"
                elif match_orgao_seap:
                    orgao_lotacao = "Secretaria de Estado da Administração e da Previdência – SEAP"
                
                # --- Extração de Tipo e Número do Documento ---
                match_decreto = re.search(r'DECRETO Nº\s*([\d.]+)', conteudo_documento_str, re.IGNORECASE)
                match_portaria = re.search(r'PORTARIA Nº\s*([\d.]+)', conteudo_documento_str, re.IGNORECASE)

                if match_decreto:
                    tipo_documento = "DECRETO"
                    numero_documento = match_decreto.group(1).strip()
                elif match_portaria:
                    tipo_documento = "PORTARIA"
                    numero_documento = match_portaria.group(1).strip()


                # --- Extração de Situação e detalhes de Férias/Designação ---
                if "DECRETO Nº" in conteudo_documento_str and ("Nomeia, em virtude de habilitação em concurso público" in conteudo_documento_str or "Nomeação de servidores para exercerem cargos" in conteudo_documento_str):
                    situacao = "Nomeação"
                elif "PORTARIA Nº" in conteudo_documento_str:
                    # Priorizar a detecção de "Designação (Substituição por Férias)"
                    if re.search(r'férias', conteudo_documento_str, re.IGNORECASE):
                        situacao = "Designação (Substituição por Férias)"
                        
                        # Regex mais flexível para o substituto (nome e RG), permitindo ou não "o/a servidor/servidora"
                        match_substituto = re.search(
                            r'Designar\s+(?:o|a)?\s*(?:servidor|servidora)?\s*([A-Z\u00C0-\u00FF\s]+?),\s+RG\s+nº\s*([\d.xX-]+)',
                            conteudo_documento_str, re.IGNORECASE | re.DOTALL
                        )
                        if match_substituto:
                            substituto_nome_raw = match_substituto.group(1).strip()
                            # Remove "o", "a", "servidor", "servidora" se estiverem colados ao nome
                            substituto_nome = re.sub(r'^(?:o|a)\s+', '', substituto_nome_raw, flags=re.IGNORECASE).strip()
                            substituto_nome = re.sub(r'^(?:servidor|servidora)\s+', '', substituto_nome, flags=re.IGNORECASE).strip()
                            
                            nome = substituto_nome # O campo 'Nome' será o do substituto
                            rg = match_substituto.group(2).strip()
                        
                        # Regex para o titular em férias (focando apenas no nome e RG)
                        match_titular_ferias = re.search(
                            r'férias\s*do\s*titular\s*([A-Z\u00C0-\u00FF\s]+?)\s*,\s*RG\s+nº\s*[\d.xX-]+',
                            conteudo_documento_str, re.IGNORECASE | re.DOTALL
                        )
                        if match_titular_ferias:
                            titular_ferias_name_raw = match_titular_ferias.group(1).strip()
                            # Limpeza similar para o nome do titular de férias
                            titular_ferias_nome = re.sub(r'^(?:o|a)\s+', '', titular_ferias_name_raw, flags=re.IGNORECASE).strip()
                            titular_ferias_nome = re.sub(r'^(?:servidor|servidora)\s+', '', titular_ferias_nome, flags=re.IGNORECASE).strip()

                        # Regex para o período de férias (buscando o período independentemente)
                        match_periodo_ferias = re.search(
                            r'(?:no\s+)?período\s+de\s+(\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+\d{4}\s+a\s+\d{1,2}\s+de\s+[a-zA-ZçÇ]+\s+de\s+\d{4})',
                            conteudo_documento_str, re.IGNORECASE | re.DOTALL
                        )
                        if match_periodo_ferias:
                            periodo_ferias = match_periodo_ferias.group(1).strip()

                    # Se não for substituição por férias, verifica a designação geral
                    elif re.search(r'Designar\s+(?:o|a)?\s*(?:servidor|servidora)?', conteudo_documento_str, re.IGNORECASE):
                        situacao = "Designação"
                        # Regex para o nome e RG na designação geral (sem ser de férias)
                        match_designacao_generico = re.search(
                            r'Designar\s+(?:o|a)?\s*(?:servidor|servidora)?\s*([A-Z\u00C0-\u00FF\s]+?),\s+RG\s+nº\s*([\d.xX-]+)',
                            conteudo_documento_str, re.IGNORECASE | re.DOTALL
                        )
                        if match_designacao_generico:
                            name_raw = match_designacao_generico.group(1).strip()
                            # Remove "o", "a", "servidor", "servidora" se estiverem colados ao nome
                            nome = re.sub(r'^(?:o|a)\s+', '', name_raw, flags=re.IGNORECASE).strip()
                            nome = re.sub(r'^(?:servidor|servidora)\s+', '', nome, flags=re.IGNORECASE).strip()
                            rg = match_designacao_generico.group(2).strip()
                        else: # Fallback se não encontrar o padrão RG completo
                            match_designacao_sem_rg = re.search(
                                r'Designar\s+(?:o|a)?\s*(?:servidor|servidora)?\s*([A-Z\u00C0-\u00FF\s]+?)\s*(?:,|$)',
                                conteudo_documento_str, re.IGNORECASE | re.DOTALL
                            )
                            if match_designacao_sem_rg:
                                name_raw = match_designacao_sem_rg.group(1).strip()
                                nome = re.sub(r'^(?:o|a)\s+', '', name_raw, flags=re.IGNORECASE).strip()
                                nome = re.sub(r'^(?:servidor|servidora)\s+', '', nome, flags=re.IGNORECASE).strip()
                                # RG permanece "Não Encontrado"

                # --- Extração de Cargo/Função (Regex aprimorada para limitar a captura) ---
                match_cargo = re.search(
                    r'para\s+exercer(?:em)?\s+' # "para exercer" ou "para exercerem"
                    r'(?:em\s+comissão\s+o\s+cargo\s+de|o\s+cargo\s+de|a\s+função\s+de)\s*' # Formas de introdução
                    r'(.+?)' # Captura o nome do cargo/função (não-guloso)
                    r'(?=\s*[,.]?\s*(?:-\s+de|no\s+período|por\s+motivo|Lei|do\s+Quadro|Art\.\s*\d+|Curitiba,|\(assinado\s+eletronicamente\)|\s*DECRETA:\s*|\s*PORTARIA:\s*|--- FIM D(?:A PORTARIA|O DECRETO)|\Z))',
                    # Novos delimitadores de parada no lookahead:
                    # - 'Art.\s*\d+': Início de um novo artigo (ex: Art. 1º)
                    # - 'Curitiba,': Início da linha de assinatura de decretos/portarias
                    # - '\(assinado\s+eletronicamente\)': Marcador de assinatura eletrônica
                    # - '\s*DECRETA:\s*': Se o documento contém múltiplos decretos/portarias, pode ser o início do próximo
                    # - '\s*PORTARIA:\s*': O mesmo para portarias
                    conteudo_documento_str, re.IGNORECASE | re.DOTALL
                )
                
                if match_cargo:
                    cargo = match_cargo.group(1).strip()
                    # Limpeza adicional para remover texto irrelevante que pode ser capturado
                    cargo = re.sub(r'\s+do Quadro Próprio do Poder Executivo – QPPE', '', cargo, flags=re.IGNORECASE).strip()
                    cargo = re.sub(r'\s+do Estado do Paraná', '', cargo, flags=re.IGNORECASE).strip()
                    # Ajuste para "Escritório de Guarapuava - ERGUA" que pode vir com espaços estranhos
                    cargo = re.sub(r'–\s*Escritório\s*de\s*Guarapuava\s*-\s*ERGUA', '– Escritório de Guarapuava - ERGUA', cargo, flags=re.IGNORECASE).strip()
                    # Remover quebras de linha e espaços extras, normalizando para um único espaço
                    cargo = ' '.join(cargo.split())
                else:
                    cargo = "Não Encontrado"

                # Para Decretos de Nomeação, onde os nomes podem estar em anexo
                if situacao == "Nomeação" and nome == "Não Encontrado":
                    nome = "Verificar Anexo (Nomes em lista separada)"
                
                novo_registro = {
                    "Tipo_Documento": tipo_documento,
                    "Numero_Documento": numero_documento,
                    "Nome": nome,
                    "RG": rg,
                    "Situação": situacao,
                    "Cargo": cargo,
                    "Orgao_Lotacao": orgao_lotacao,
                    "Diario_Fonte": data_publicacao,
                    "Substituto_Nome": substituto_nome,
                    "Titular_Ferias_Nome": titular_ferias_nome,
                    "Periodo_Ferias": periodo_ferias
                }

                # Prevenção de duplicidade
                if not registro_existe(informacoes_extraidas, novo_registro):
                    informacoes_extraidas.append(novo_registro)
                else:
                    # Imprime qual registro duplicado foi ignorado e por quê
                    print(f"Registro duplicado detectado e ignorado: "
                          f"Tipo: {novo_registro['Tipo_Documento']}, "
                          f"Número: {novo_registro['Numero_Documento']}, "
                          f"Nome: {novo_registro['Nome']}, "
                          f"Situação: {novo_registro['Situação']}")

        except Exception as e:
            print(f"Erro ao processar o arquivo '{nome_arquivo}': {e}")
            continue

    # --- Salvar em CSV ---
    nome_csv = "informacoes_extraidas.csv"
    caminho_csv = os.path.join(caminho_diretorio, nome_csv)
    
    if informacoes_extraidas:
        with open(caminho_csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Tipo_Documento", "Numero_Documento", "Nome", "RG", "Situação", "Cargo", "Orgao_Lotacao", "Diario_Fonte", "Substituto_Nome", "Titular_Ferias_Nome", "Periodo_Ferias"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(informacoes_extraidas)
        print(f"Informações salvas com sucesso em: {caminho_csv}")
    else:
        print("Nenhuma informação foi extraída para salvar no CSV.")

    # --- Salvar em TXT formatado para PDF ---
    nome_txt_formatado = "informacoes_formatadas_para_pdf.txt"
    caminho_txt_formatado = os.path.join(caminho_diretorio, nome_txt_formatado)

    if informacoes_extraidas:
        with open(caminho_txt_formatado, 'w', encoding='utf-8') as txtfile:
            txtfile.write("--- INFORMAÇÕES EXTRAÍDAS DO DIÁRIO OFICIAL ---\n\n")
            for i, info in enumerate(informacoes_extraidas):
                txtfile.write(f"Registro {i+1}:\n")
                txtfile.write(f"  Tipo Documento: {info['Tipo_Documento']}\n")
                txtfile.write(f"  Número Documento: {info['Numero_Documento']}\n")
                txtfile.write(f"  Nome: {info['Nome']}\n")
                txtfile.write(f"  RG: {info['RG']}\n")
                txtfile.write(f"  Situação: {info['Situação']}\n")
                txtfile.write(f"  Cargo: {info['Cargo']}\n")
                txtfile.write(f"  Órgão/Lotação: {info['Orgao_Lotacao']}\n")
                if info['Substituto_Nome'] != "N/A":
                    txtfile.write(f"  Substituto: {info['Substituto_Nome']}\n")
                if info['Titular_Ferias_Nome'] != "N/A":
                    txtfile.write(f"  Titular de Férias: {info['Titular_Ferias_Nome']}\n")
                if info['Periodo_Ferias'] != "N/A":
                    txtfile.write(f"  Período de Férias: {info['Periodo_Ferias']}\n")
                txtfile.write(f"  Diário Fonte: {info['Diario_Fonte']}\n")
                txtfile.write("-" * 40 + "\n\n")
        print(f"Informações formatadas salvas para PDF em: {caminho_txt_formatado}")
    else:
        print("Nenhuma informação para formatar e salvar em TXT para PDF.")