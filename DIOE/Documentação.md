# Estrutura do Projeto
O projeto é modular e organizado nos seguintes arquivos:

- main.py: O ponto de entrada principal da automação, orquestrando o download, leitura, extração e envio de e-mails.

- baixar_e_ler_dioe.py: Responsável por baixar os diários oficiais e iniciar o processo de leitura.

- leitura_portaria.py: Contém funções para extrair e filtrar portarias de arquivos PDF/TXT.

- leitura_decreto.py: Contém funções para extrair e filtrar decretos de arquivos PDF/TXT.

- informacoes.py: Trata da extração e salvamento de informações relevantes em formato CSV e conversão de TXT para PDF.

- expresso_funcoes.py: Fornece funções para interação com o sistema de e-mail Expresso, incluindo login, preenchimento de campos e envio.

- chromedriver_funcoes.py: Lida com o download e a configuração do ChromeDriver, além de obter credenciais de proxy.

- leitor_captcha.py: Implementa a lógica para resolver CAPTCHAs usando OCR.

- gerenciador_email_gui.py: Implementa a interface gráfica do usuário (GUI) para controlar e agendar a automação.

Descrição Detalhada dos Módulos

- main.py
Este módulo é o coração da automação. Ele coordena as chamadas para as outras funções e módulos para executar o fluxo completo:

iniciar(update_status_gui=None, destinatarios_email=None, assunto_email=None, texto_email=None):

Função principal que inicia todo o processo de automação.

Chama baixar_e_ler_dioe.start() para obter os diários.

Utiliza informacoes.extrair_e_salvar_informacoes_dioe() para processar os arquivos TXT gerados e extrair informações.

Prepara o e-mail (assunto, corpo, anexos) utilizando as informações extraídas.

Interage com expresso_funcoes para fazer login, preencher o e-mail e enviá-lo.

Realiza a limpeza de arquivos temporários (PDFs originais, TXTs intermediários, PDFs gerados).

update_status_gui: Callback para atualizar o status na GUI.

destinatarios_email, assunto_email, texto_email: Parâmetros para customizar o e-mail.

- baixar_e_ler_dioe.py
Este módulo lida com o download dos diários oficiais e a coordenação da leitura:

obter_datas_baixadas(caminho_csv): Lê um arquivo CSV para obter as datas dos diários já baixados, evitando downloads duplicados.

adicionar_data_baixada(caminho_csv, data_str): Adiciona uma nova data ao arquivo CSV de diários baixados.

ocultar_arquivo(caminho_csv): Oculta o arquivo CSV (específico para Windows).

start(caminho_diretorio):

Inicia o processo de download do Diário Oficial Eletrônico (DIOE).

Configura o Selenium WebDriver com as opções e preferências necessárias (modo headless, download de PDF).

Navega até a página do DIOE, resolve CAPTCHAs usando leitor_captcha.resolver_captcha().

Preenche a data desejada e tenta baixar o PDF.

Verifica se o PDF foi baixado corretamente.

Chama leitura_portaria.ler() e leitura_decreto.ler() para processar os PDFs baixados e gerar arquivos TXT com portarias e decretos.

Remove os arquivos PDF originais após o processamento.

- leitura_portaria.py
Este módulo é dedicado à extração de portarias de documentos:

extrair_texto_pdf(caminho_pdf, caminho_txt_paginas_filtradas, palavras_chave, matchcase=False): Extrai texto de páginas PDF que contêm pelo menos 3 ocorrências das palavras-chave especificadas e salva em um arquivo TXT temporário.

filtrar_paragrafos_por_palavras_chave(caminho_txt_entrada, caminho_txt_saida, palavras_chave, matchcase=False): Filtra parágrafos de um arquivo TXT que contêm palavras-chave específicas.

extrair_portarias(texto_paragrafos, matchcase=False): Identifica e extrai blocos de texto que correspondem a portarias, usando expressões regulares.

filtrar_portarias(todas_portarias, matchcase=False): Filtra as portarias extraídas com base em palavras-chave adicionais (ex: "designa", "férias", "IAT").

salvar_documentos_em_arquivo(documentos, caminho_arquivo, titulo): Salva os documentos filtrados em um arquivo TXT.

remover_arquivos_temporarios(arquivos_para_remover): Exclui os arquivos temporários gerados durante o processo.

ler(caminho_diretorio): Função principal para o módulo, orquestrando a extração de portarias de PDFs no diretório.

- leitura_decreto.py
Similar ao leitura_portaria.py, mas focado na extração de decretos:

extrair_texto_pdf(...): (Mesma função de leitura_portaria.py)

filtrar_paragrafos_por_palavras_chave(...): (Mesma função de leitura_portaria.py)

extrair_decretos(texto_paragrafos, matchcase=False): Identifica e extrai blocos de texto que correspondem a decretos.

filtrar_decretos(todos_decretos, matchcase=False): Filtra os decretos extraídos com base em palavras-chave (ex: "nomeação", "ampliação de vagas", "SEAP", "IAT").

salvar_documentos_em_arquivo(...): (Mesma função de leitura_portaria.py)

remover_arquivos_temporarios(...): (Mesma função de leitura_portaria.py)

ler(caminho_diretorio): Função principal para o módulo, orquestrando a extração de decretos de PDFs.

- informacoes.py
Responsável por processar os arquivos TXT de portarias/decretos, extrair informações estruturadas, salvar em CSV e converter os TXTs em PDFs:

converter_txt_para_pdf(arquivo_txt, caminho_arquivo_pdf, diario_publicacao): Converte um arquivo TXT para um PDF formatado, incluindo um título com a data de publicação.

extrair_informacoes_bloco(bloco, data_publicacao): Extrai informações específicas (tipo de documento, número, data, nome, situação, etc.) de um bloco de texto (portaria/decreto).

registro_existe(informacoes_extraidas, novo_registro): Verifica se um registro já existe na lista de informações extraídas para evitar duplicatas.

salvar_em_csv(informacoes, caminho_diretorio): Salva as informações extraídas em um arquivo CSV.

extrair_e_salvar_informacoes_dioe(arquivos_txt_gerados, caminho_diretorio, data_publicacao_str):

Itera sobre os arquivos TXT gerados (portarias e decretos).

Para cada arquivo, extrai informações de blocos.

Converte o TXT para PDF.

Salva todas as informações extraídas em um arquivo CSV.

Retorna a lista de caminhos dos PDFs gerados.

- expresso_funcoes.py
Contém funções para interagir com o sistema de e-mail Expresso via Selenium WebDriver:

Variáveis globais: caminho_driver, opcoes_chrome, servico, driver (instância do WebDriver).

email_expresso(login, senha): Navega até a página de login do Expresso e realiza o login.

nova_mensagem(): Clica no botão para criar uma nova mensagem.

adicionar_destinatarios(destinatarios): Preenche o campo "Para" com os destinatários fornecidos.

adicionar_assunto(assunto): Preenche o campo de assunto do e-mail.

anexar_arquivo(caminho_arquivo): Anexa um arquivo ao e-mail.

inserir_texto(texto): Insere o corpo do texto no e-mail (geralmente em um iframe).

adicionar_cco(destinatarios): Adiciona destinatários ao campo CCO (cópia carbono oculta).

assinatura(): Clica para adicionar a assinatura (se houver um botão ou elemento específico para isso).

enviar_email(): Clica no botão de envio do e-mail.

fechar_driver(): Fecha a instância do Selenium WebDriver.

- chromedriver_funcoes.py
Gerencia o ChromeDriver, que é essencial para a automação do navegador:

chromedriver_path: Variável que armazena o caminho do ChromeDriver.

chromedriver_func (classe):

obter_versao_chrome(): Tenta obter a versão do Google Chrome instalada no sistema.

baixar_chromedriver(): Baixa a versão compatível do ChromeDriver com base na versão do Chrome detectada. Inclui tratamento de erros para download, extração e permissões.

obter_credenciais_proxy(): Abre janelas de diálogo (Tkinter) para solicitar nome de usuário e senha do proxy, caso seja necessário.

- leitor_captcha.py
Implementa a lógica para resolver CAPTCHAs de imagem:

segmentar_imagem(imagem_binarizada_input): Segmenta a imagem do CAPTCHA em caracteres individuais usando Análise de Componentes Conectados (CCA).

preprocessar_imagem(caminho_imagem_captcha): Carrega, redimensiona, converte para tons de cinza, binariza e aplica filtros na imagem do CAPTCHA para melhorar a legibilidade.

resolver_captcha(caminho_imagem_captcha):

Orquestra o processo de resolução do CAPTCHA.

Chama preprocessar_imagem para preparar a imagem.

Chama segmentar_imagem para obter caixas delimitadoras de caracteres.

Usa EasyOCR para reconhecer o texto em cada segmento de caractere.

Aplica pós-processamento para corrigir erros comuns de OCR (ex: "0" para "O", "5" para "S").

Remove o arquivo de imagem do CAPTCHA temporário.

- gerenciador_email_gui.py
Fornece a interface gráfica do usuário para interagir com a automação:

GerenciadorEmailApp (classe):

__init__(self, root): Inicializa a janela principal, carrega a configuração (destinatários, assunto, etc.) de um arquivo JSON.

carregar_configuracao() / salvar_configuracao(): Métodos para carregar e salvar as configurações da GUI (destinatários, assunto, corpo do e-mail, agendamento, etc.).

criar_widgets(): Cria e posiciona os elementos da GUI (labels, entries, botões, caixa de texto de status).

iniciar_automacao_thread(): Inicia a automação em uma thread separada para não travar a GUI.

iniciar_automacao(): Chama a função main.iniciar() passando os parâmetros da GUI.

agendar_verificacao_diaria(): Agenda a execução diária da automação em um horário específico usando um loop em uma thread separada.

atualizar_status(mensagem): Atualiza a caixa de texto de status na GUI.

configurar_agendamento(): Abre um diálogo para o usuário definir o horário de agendamento.

ao_fechar_janela(): Gerencia o fechamento da aplicação, garantindo que as threads e o driver do navegador sejam encerrados corretamente.

# Como Executar
Pré-requisitos:

Python 3.x instalado.

Instalar as bibliotecas Python necessárias:

pip install selenium pypdf2 easyocr numpy opencv-python-headless Pillow reportlab requests

Certifique-se de ter o Google Chrome instalado, pois o script depende do ChromeDriver.

Configuração do ChromeDriver:

O script chromedriver_funcoes.py tenta baixar e configurar o ChromeDriver automaticamente.

A variável chromedriver_path em chromedriver_funcoes.py está definida como S:\\GEAD-DRH\\DIAFI-DRH\\DRH - GESTÃO DE PESSOAS\\CONJUNTO DE ATIVIDADES DRH - PLANILHAS\\Selenium\\chromedriver-win64\\chromedriver.exe. Você pode precisar ajustar este caminho ou garantir que a função de download automático esteja funcionando corretamente.

Execução da GUI:

Execute o script gerenciador_email_gui.py:

python gerenciador_email_gui.py

A GUI será exibida, permitindo que você configure os destinatários do e-mail, assunto, texto e agende a automação.

Uso da GUI:

Preencha os campos "E-mails Destinatários", "Assunto do E-mail" e "Texto do E-mail".

Clique em "Iniciar Automação Agora" para executar a automação imediatamente.

Clique em "Configurar Agendamento Diário" para definir um horário para a execução automática todos os dias.

O "Log de Status" mostrará o progresso e quaisquer mensagens de erro.

Fluxo de Operação
Inicialização da GUI: O gerenciador_email_gui.py inicia, carrega as configurações e exibe a interface.

Agendamento/Início Manual:

Se agendado, uma thread de agendamento aguarda o horário definido.

Se iniciado manualmente, uma thread de automação é imediatamente iniciada.

Download do Diário (baixar_e_ler_dioe.py):

O Selenium abre o navegador (em modo headless, se configurado).

Navega até a página do DIOE.

Resolve o CAPTCHA usando leitor_captcha.py (processamento de imagem e OCR).

Seleciona a data e tenta baixar o PDF do diário.

Verifica se o diário para a data atual já foi baixado.

Leitura e Extração (leitura_portaria.py, leitura_decreto.py, informacoes.py):

Os PDFs baixados são processados para extrair texto (PyPDF2).

O texto é filtrado por palavras-chave relevantes.

Portarias e Decretos são identificados e extraídos usando expressões regulares.

As informações extraídas são estruturadas e salvas em um arquivo CSV.

Os arquivos TXT com as portarias/decretos são convertidos em PDFs para serem anexados ao e-mail.

Os PDFs originais do diário e os arquivos TXT intermediários são removidos.

Envio de E-mail (expresso_funcoes.py):

Abre o navegador e navega para o Expresso.

Faz login.

Cria uma nova mensagem, preenche destinatários (Para e CCO), assunto e corpo do e-mail.

Anexa os PDFs gerados contendo as portarias e decretos.

Envia o e-mail.

Limpeza: Remove todos os arquivos temporários gerados (PDFs originais, TXTs, PDFs gerados para anexo) após o envio do e-mail.

Finalização: O driver do navegador é fechado e a thread da automação termina.

# Considerações Importantes
Modo Headless: O expresso_funcoes.py está configurado para --headless, o que significa que o navegador será executado em segundo plano sem uma interface gráfica. Para depuração visual, comente a linha opcoes_chrome.add_argument("--headless").

Caminhos de Arquivo: Certifique-se de que os caminhos de arquivo (especialmente para o ChromeDriver) estão corretos e que o script tem as permissões necessárias para ler/escrever arquivos no diretório de trabalho.

Credenciais: As credenciais do Expresso e do proxy são solicitadas via tkinter.simpledialog.

Robustez do OCR: A leitura de CAPTCHAs é inerentemente frágil e pode falhar com variações na imagem ou complexidade do CAPTCHA. O módulo leitor_captcha.py inclui pré-processamento e pós-processamento para melhorar a precisão.

Tratamento de Erros: O código inclui blocos try-except para lidar com erros comuns durante a automação, mas é importante monitorar o "Log de Status" na GUI para quaisquer problemas.

Agendamento: O agendamento é implementado como um loop em uma thread separada. Se a aplicação for fechada, o agendamento será interrompido.

Proxy: O projeto inclui funções para lidar com proxy, solicitando credenciais ao usuário se necessário.

Padronização de Saída: As informações são salvas em CSVs para fácil análise e os documentos extraídos são convertidos para PDFs para anexos de e-mail.