import re
import os
import csv
import glob
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def converter_txt_para_pdf(arquivo_txt, caminho_arquivo_pdf, diario_publicacao):
    # Cria um novo documento PDF
    doc = SimpleDocTemplate(caminho_arquivo_pdf, pagesize=letter)
    
    # Obtém os estilos de parágrafo padrão
    estilo = getSampleStyleSheet()
    
    # Lista para armazenar os elementos (parágrafos, espaços, etc.) que serão adicionados ao PDF
    elementos_pdf = []


    if not os.path.exists(arquivo_txt):
        print(f"Erro: O arquivo TXT '{arquivo_txt}' não foi encontrado e será ignorado.")


    try:
        # Abre o arquivo TXT para leitura
        with open(arquivo_txt, 'r', encoding='utf-8') as f:
            texto = f.read()

        # Adiciona o nome do arquivo como um título ou separador (opcional, para clareza)
        elementos_pdf.append(Paragraph(f"--- Conteúdo de: {diario_publicacao} ---", estilo['h2']))
        elementos_pdf.append(Spacer(1, 0.2 * 10))

        # Divide o texto em parágrafos.
        # Cada linha do TXT se torna um parágrafo no PDF.
        paragrafos = texto.split('\n')
        
        for p in paragrafos:
            if p.strip():  # Adiciona apenas parágrafos que não são vazios
                elementos_pdf.append(Paragraph(p.strip(), estilo['Normal']))
            elementos_pdf.append(Spacer(1, 0.2 * 10)) 
        
    except Exception as e:
        print(f"Ocorreu um erro ao processar o arquivo '{arquivo_txt}': {e}")


    try:
        # Constrói o PDF com base em *todos* os elementos coletados
        doc.build(elementos_pdf)
        print(f"PDF criado com sucesso em: {caminho_arquivo_pdf}")
    except Exception as e:
        print(f"Ocorreu um erro ao gerar o PDF: {e}")

    os.remove(arquivo_txt)

def registro_existe(lista_registros, novo_registro):
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

def limpar_texto(texto):
    if texto is None:
        return "Não Encontrado"

    texto = str(texto) 
    texto = texto.replace('ﬁ', 'fi').replace('ﬀ', 'ff')

    meses_pt = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho", 
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    
    for mes in meses_pt:
        padrao = r'\b' + r'\s*'.join(list(mes)) + r'\b'
        texto = re.sub(padrao, mes, texto, flags=re.IGNORECASE)

    texto = re.sub(r'\s*-\s*', ' - ', texto) 
    texto = re.sub(r'(\d)\s+(\d)', r'\1\2', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    texto = texto.replace(' - ', '-') 

    return texto

def extrair_data_do_nome_arquivo(nome_arquivo):
    match_data = re.search(r'EX_(\d{4}-\d{2}-\d{2})_', nome_arquivo)
    if match_data:
        data_iso = match_data.group(1)
        dia, mes, ano = data_iso.split('-')[2], data_iso.split('-')[1], data_iso.split('-')[0]
        return f"Diário {dia}-{mes}-{ano}"
    return "Não Identificada"

def extrair_orgao_lotacao(conteudo_documento_str):
    match_orgao_iat = re.search(r'INSTITUTO ÁGUA E TERRA', conteudo_documento_str, re.IGNORECASE)
    match_orgao_seap = re.search(r'Secretaria de Estado da Administração e da Previdência – SEAP', conteudo_documento_str, re.IGNORECASE)
    
    if match_orgao_iat:
        return "Instituto Água e Terra - IAT"
    elif match_orgao_seap:
        return "Secretaria de Estado da Administração e da Previdência – SEAP"
    return "Não Encontrado"

def extrair_cargo(conteudo_documento_str):
    match_cargo = re.search(
        r'para\s+exercer(?:em)?\s+' 
        r'(?:em\s+comissão\s+o\s+cargo\s+de|o\s+cargo\s+de|a\s+função\s+de)\s*' 
        r'(.+?)' 
        r'(?=\s*[,.]?\s*(?:-\s+de|no\s+período|por\s+motivo|Lei|do\s+Quadro|Art\.\s*\d+|Curitiba,|\(assinado\s+eletronicamente\)|\s*DECRETA:\s*|\s*PORTARIA:\s*|\s*do\s+titular\s+[A-Z\u00C0-\u00FF\s\-\.\']{3,}|--- FIM D(?:A PORTARIA|O DECRETO)|\Z))',
        conteudo_documento_str, re.IGNORECASE | re.DOTALL
    )
    
    if match_cargo:
        cargo = match_cargo.group(1).strip()
        cargo = re.sub(r'\s+do Quadro Próprio do Poder Executivo – QPPE', '', cargo, flags=re.IGNORECASE).strip()
        cargo = re.sub(r'\s+do Estado do Paraná', '', cargo, flags=re.IGNORECASE).strip()
        cargo = re.sub(r'–\s*Escritório\s*de\s*Guarapuava\s*-\s*ERGUA', '– Escritório de Guarapuava - ERGUA', cargo, flags=re.IGNORECASE).strip()
        cargo = ' '.join(cargo.split())
        return cargo
    return "Não Encontrado"

def analisar_bloco_decreto(conteudo_documento_str, numero_diario="N/A"):
    registro = {
        "Tipo_Documento": "DECRETO",
        "Numero_Documento": "Não Encontrado",
        "Situação": "Não Identificada",
        "Nome": "Não Encontrado",
        "RG": "Não Encontrado",
        "Titular_Ferias_Nome": "N/A",
        "Periodo_Ferias": "N/A",
        "Substituto_Nome": "N/A",
        "Cargo": "Não Encontrado",
        "Orgao_Lotacao": "Não Encontrado",
        "Numero_Diario": numero_diario,
        "Diario_Fonte": "Não Identificada"
    }

    match_decreto = re.search(r'DECRETO Nº\s*([\d.]+)', conteudo_documento_str, re.IGNORECASE)
    if match_decreto:
        registro["Numero_Documento"] = match_decreto.group(1).strip()

    if ("Nomeia, em virtude de habilitação em concurso público" in conteudo_documento_str or 
        "Nomeação de servidores para exercerem cargos" in conteudo_documento_str):
        registro["Situação"] = "Nomeação"
        # Para Decretos de Nomeação, onde os nomes podem estar em anexo
        registro["Nome"] = "Verificar Anexo (Nomes em lista separada)"
    
    registro["Cargo"] = extrair_cargo(conteudo_documento_str)
    registro["Orgao_Lotacao"] = extrair_orgao_lotacao(conteudo_documento_str)

    return {k: limpar_texto(v) for k, v in registro.items()}


def analisar_bloco_portaria(conteudo_documento_str, numero_diario="N/A"):
    registro = {
        "Tipo_Documento": "PORTARIA",
        "Numero_Documento": "Não Encontrado",
        "Situação": "Não Identificada",
        "Nome": "Não Encontrado",
        "RG": "Não Encontrado",
        "Titular_Ferias_Nome": "N/A",
        "Periodo_Ferias": "N/A",
        "Substituto_Nome": "N/A",
        "Cargo": "Não Encontrado",
        "Orgao_Lotacao": "Não Encontrado",
        "Numero_Diario": numero_diario,
        "Diario_Fonte": "Não Identificada"
    }

    match_portaria = re.search(r'PORTARIA Nº\s*([\d.]+)', conteudo_documento_str, re.IGNORECASE)
    if match_portaria:
        registro["Numero_Documento"] = match_portaria.group(1).strip()

    if re.search(r'por\s+motivo\s+de\s+férias', conteudo_documento_str, re.IGNORECASE):
        registro["Situação"] = "Designação (Substituição por Férias)"
        
        # Regex mais flexível para o substituto (nome e RG),
        # permitindo ou não "o/a servidor/servidora"
        match_substituto = re.search(
            r'Designar\s+(?:o|a)?\s*(?:servidor|servidora)?\s*([A-Z\u00C0-\u00FF\s\-\.\']{3,}?),\s+RG\s+nº\s*([\d.xX\s-]+)',
            conteudo_documento_str, re.IGNORECASE | re.DOTALL
        )
        if match_substituto:
            nome_substituto_raw = match_substituto.group(1).strip()
            # Remove "o", "a", "servidor", "servidora" se estiverem colados ao nome
            registro["Substituto_Nome"] = re.sub(r'^(?:o|a)\s+', '', nome_substituto_raw, flags=re.IGNORECASE).strip()
            registro["Substituto_Nome"] = re.sub(r'^(?:servidor|servidora)\s+', '', registro["Substituto_Nome"], flags=re.IGNORECASE).strip()
            registro["Nome"] = registro["Substituto_Nome"] # O campo 'Nome' será o do substituto
            registro["RG"] = match_substituto.group(2).strip()
        
        # Regex para o titular em férias (focando apenas no nome e RG)
        match_titular_ferias = re.search(
            r'férias\s*do\s*titular\s*([A-Z\u00C0-\u00FF\s\-\.\']{3,}?)\s*,\s*RG\s+nº\s*([\d.xX\s-]+)',
            conteudo_documento_str, re.IGNORECASE | re.DOTALL
        )
        if match_titular_ferias:
            nome_titular_ferias_raw = match_titular_ferias.group(1).strip()
            # Limpeza similar para o nome do titular de férias
            registro["Titular_Ferias_Nome"] = re.sub(r'^(?:o|a)\s+', '', nome_titular_ferias_raw, flags=re.IGNORECASE).strip()
            registro["Titular_Ferias_Nome"] = re.sub(r'^(?:servidor|servidora)\s+', '', registro["Titular_Ferias_Nome"], flags=re.IGNORECASE).strip()

        # Regex para o período de férias (buscando o período independentemente)
        match_periodo_ferias = re.search(
            r'(?:no\s+)?período\s+de\s+(.*?)(?=\s*(?:,|\.|Art\.|--- FIM))',
            conteudo_documento_str, re.IGNORECASE | re.DOTALL
        )
        if match_periodo_ferias:
            registro["Periodo_Ferias"] = match_periodo_ferias.group(1).strip()

    # Se não for substituição por férias, verifica a designação geral
    elif re.search(r'Designar\s+(?:o|a)?\s*(?:servidor|servidora)?', conteudo_documento_str, re.IGNORECASE):
        registro["Situação"] = "Designação"
        # Regex para o nome e RG na designação geral (sem ser de férias)
        match_designacao_generico = re.search(
            r'Designar\s+(?:o|a)?\s*(?:servidor|servidora)?\s*([A-Z\u00C0-\u00FF\s\-\.\']{3,}?),\s+RG\s+nº\s*([\d.xX\s-]+)',
            conteudo_documento_str, re.IGNORECASE | re.DOTALL
        )
        if match_designacao_generico:
            nome_raw = match_designacao_generico.group(1).strip()
            # Remove "o", "a", "servidor", "servidora" se estiverem colados ao nome
            registro["Nome"] = re.sub(r'^(?:o|a)\s+', '', nome_raw, flags=re.IGNORECASE).strip()
            registro["Nome"] = re.sub(r'^(?:servidor|servidora)\s+', '', registro["Nome"], flags=re.IGNORECASE).strip()
            registro["RG"] = match_designacao_generico.group(2).strip()
        else: # Fallback se não encontrar o padrão RG completo
            match_designacao_sem_rg = re.search(
                r'Designar\s+(?:o|a)?\s*(?:servidor|servidora)?\s*([A-Z\u00C0-\u00FF\s\-\.\']{3,}?)\s*(?:,|$)',
                conteudo_documento_str, re.IGNORECASE | re.DOTALL
            )
            if match_designacao_sem_rg:
                nome_raw = match_designacao_sem_rg.group(1).strip()
                registro["Nome"] = re.sub(r'^(?:o|a)\s+', '', nome_raw, flags=re.IGNORECASE).strip()
                registro["Nome"] = re.sub(r'^(?:servidor|servidora)\s+', '', registro["Nome"], flags=re.IGNORECASE).strip()
                # RG permanece "Não Encontrado"

    registro["Cargo"] = extrair_cargo(conteudo_documento_str)
    registro["Orgao_Lotacao"] = extrair_orgao_lotacao(conteudo_documento_str)

    return {k: limpar_texto(v) for k, v in registro.items()}


def analisar_bloco_documento(bloco_texto, numero_diario="N/A"):
    match_inicio = re.search(r'--- INÍCIO (PORTARIA|DECRETO)[^-\n]*---', bloco_texto, re.IGNORECASE)
    match_fim = re.search(r'--- FIM (?:PORTARIA|DECRETO)[^-\n]*---', bloco_texto, re.IGNORECASE)

    if not match_inicio or not match_fim:
        print(f"Aviso: Bloco encontrado mas marcadores de início/fim ausentes em um trecho.")
        return None

    tipo_documento_identificado = match_inicio.group(1).upper()
    marcador_inicio = match_inicio.group(0) # Pega o marcador completo
    conteudo_documento_str = bloco_texto[len(marcador_inicio):match_fim.start()].strip()

    if tipo_documento_identificado == "DECRETO":
        return analisar_bloco_decreto(conteudo_documento_str, numero_diario)
    elif tipo_documento_identificado == "PORTARIA":
        return analisar_bloco_portaria(conteudo_documento_str, numero_diario)
    else:
        print(f"Tipo de documento desconhecido: {tipo_documento_identificado}")
        return None

def salvar_em_csv(dados, diretorio, nome_arquivo="informacoes_extraidas.csv"):
    caminho_csv = os.path.join(diretorio, nome_arquivo)
    if dados:
        with open(caminho_csv, 'w', newline='', encoding='utf-8') as csvfile:
            nomes_campos = ["Tipo_Documento", "Numero_Documento", "Situação", "Nome", "RG", "Titular_Ferias_Nome", "Periodo_Ferias", "Substituto_Nome", "Cargo", "Orgao_Lotacao", "Numero_Diario", "Diario_Fonte"]
            writer = csv.DictWriter(csvfile, fieldnames=nomes_campos)
            writer.writeheader()
            writer.writerows(dados)
        print(f"Informações salvas com sucesso em: {caminho_csv}")
    else:
        print("Nenhuma informação foi extraída para salvar no CSV.")

def extrair_e_salvar_informacoes_dioe(caminho_diretorio, arquivos_txt, numero_diario="N/A"):
    print("Iniciando extração de informações dos arquivos TXT...")
    informacoes_extraidas = []
    if len(arquivos_txt) == 1:
        arquivos_txt = arquivos_txt[0]
    
    nomes_arquivos_txt = [f for f in os.listdir(caminho_diretorio) if re.match(r"EX_.*\.txt", f)]

    for nome_arquivo in nomes_arquivos_txt: 
        caminho_arquivo = os.path.join(caminho_diretorio, nome_arquivo)
        print(f"Processando arquivo: {nome_arquivo}")

        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                conteudo_completo = f.read()

            data_publicacao = extrair_data_do_nome_arquivo(nome_arquivo)

            padrao_bloco_completo = re.compile(
                r'(--- INÍCIO (?:PORTARIA|DECRETO)[^-\n]*---.*?'
                r'--- FIM (?:PORTARIA|DECRETO)[^-\n]*---)',
                re.IGNORECASE | re.DOTALL
            )
            
            blocos_completos = padrao_bloco_completo.findall(conteudo_completo)
            
            if not blocos_completos:
                print(f"Nenhum bloco de documento completo encontrado em '{nome_arquivo}'.")
                continue

            for bloco_texto in blocos_completos:
                registro = analisar_bloco_documento(bloco_texto, numero_diario)
                if registro:
                    registro["Diario_Fonte"] = data_publicacao # Atualiza com a data correta
                    if not registro_existe(informacoes_extraidas, registro):
                        informacoes_extraidas.append(registro)
                    else:
                        print(f"Registro duplicado detectado e ignorado: "
                              f"Tipo: {registro['Tipo_Documento']}, "
                              f"Número: {registro['Numero_Documento']}, "
                              f"Nome: {registro['Nome']}, "
                              f"Situação: {registro['Situação']}")

        except Exception as e:
            print(f"Erro ao processar o arquivo '{nome_arquivo}': {e}")
            continue

    salvar_em_csv(informacoes_extraidas, caminho_diretorio)
    txt_para_pdf = os.path.join(caminho_diretorio, arquivos_txt)
    pdf_final = os.path.join(caminho_diretorio, f"{data_publicacao}.pdf")
    converter_txt_para_pdf(txt_para_pdf, pdf_final, data_publicacao)

    return pdf_final

if __name__ == "__main__":
    caminho_diretorio = os.getcwd()
    extrair_e_salvar_informacoes_dioe(caminho_diretorio)