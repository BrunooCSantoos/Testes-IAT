import os
import cv2
import easyocr
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

def segmentar_imagem(imagem_binarizada_input):
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(imagem_binarizada_input, 8, cv2.CV_32S)

    caixas_de_caracteres = []

    # Iterate through each component (skip label 0, which is the background)
    for i in range(1, num_labels):
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]

        min_largura = 5 
        max_largura = 80 
        min_altura = 10
        max_altura = 80 
        min_area = 30 

        if (min_largura < w < max_largura and
            min_altura < h < max_altura and
            min_area < area):

            caixas_de_caracteres.append((x, y, w, h))

    caixas_de_caracteres = sorted(caixas_de_caracteres, key=lambda b: b[0])

    return caixas_de_caracteres

def resolver_captcha_auto(caminho_captcha, idioma=['pt']):
    try:
        print(f"Lendo CAPTCHA do arquivo: {caminho_captcha}")
        imagem_pil = Image.open(caminho_captcha)
        print("Imagem aberta com sucesso usando PIL.")

        imagem_np = np.array(imagem_pil)

        if len(imagem_np.shape) == 3:
            if imagem_pil.mode == 'RGB':
                imagem_np = cv2.cvtColor(imagem_np, cv2.COLOR_RGB2BGR)
            elif imagem_pil.mode == 'RGBA':
                imagem_np = cv2.cvtColor(imagem_np, cv2.COLOR_RGBA2BGR)
            imagem_gray = cv2.cvtColor(imagem_np, cv2.COLOR_BGR2GRAY)
        elif len(imagem_np.shape) == 2:
            imagem_gray = imagem_np
        else:
            raise ValueError("Unsupported image format: image must have 1, 3, or 4 channels.")

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        imagem_clahe = clahe.apply(imagem_gray)

        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1)) 

        horizontal_lines = cv2.morphologyEx(imagem_clahe, cv2.MORPH_OPEN, kernel_h, iterations=1)

        image_no_h_lines = cv2.subtract(imagem_clahe, horizontal_lines)

        # Do the same for vertical lines if present and problematic
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
        vertical_lines = cv2.morphologyEx(image_no_h_lines, cv2.MORPH_OPEN, kernel_v, iterations=1)
        image_no_lines = cv2.subtract(image_no_h_lines, vertical_lines)

        imagem_binarizada = cv2.adaptiveThreshold(image_no_lines, 255,
                                                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                    cv2.THRESH_BINARY_INV, 11, 2)

        imagem_mediana = cv2.medianBlur(imagem_binarizada, 3)

        char_bounding_boxes = segmentar_imagem(imagem_mediana)

        if not char_bounding_boxes:
            print("No individual characters segmented using CCA. Attempting OCR on the whole pre-processed image.")
            img_for_ocr = cv2.cvtColor(imagem_mediana, cv2.COLOR_GRAY2BGR) # Convert to 3-channel for EasyOCR
            caracteres_segmentados_for_ocr = [img_for_ocr]
        else:
            print(f"Imagem pré-processada com sucesso. Caracteres segmentados: {len(char_bounding_boxes)}")
            caracteres_segmentados_for_ocr = []
            for (x, y, w, h) in char_bounding_boxes:
                cropped_char = imagem_gray[y:y+h, x:x+w]
                
                padded_char = cv2.copyMakeBorder(cropped_char, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=(255))
                
                caracteres_segmentados_for_ocr.append(padded_char)

        reader = easyocr.Reader(idioma)
        print("Leitor EasyOCR inicializado.")

        resultados_ocr = []
        for i, caractere_imagem_single in enumerate(caracteres_segmentados_for_ocr):

            resultado = reader.readtext(caractere_imagem_single, 
                                     allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789°º', 
                                     detail=0)
            
            if resultado:
                texto_reconhecido = resultado[0].strip()

                if texto_reconhecido in ['o', 'O', '0', 'º'] and caractere_imagem_single.shape[0] < 15 and caractere_imagem_single.shape[1] < 15:
                    texto_reconhecido = '°'

                resultados_ocr.append(texto_reconhecido)
            else:
                resultados_ocr.append("")

        texto_captcha = "".join(resultados_ocr)
        print(f"Resultado da leitura do OCR: {texto_captcha}")

        texto_captcha = texto_captcha.replace(" ", "")
        texto_captcha = texto_captcha.replace('"', '')
        
        texto_captcha = texto_captcha.replace('0', 'O')
        texto_captcha = texto_captcha.replace('º', 'O')
        texto_captcha = texto_captcha.replace('5', 'S')
        texto_captcha = texto_captcha.replace('8', 'B')
        texto_captcha = texto_captcha.replace('3', 'B')
        texto_captcha = texto_captcha.replace('4', 'A')
        texto_captcha = texto_captcha.replace('6', 'G')
        texto_captcha = texto_captcha.replace('7', 'T')
        texto_captcha = texto_captcha.replace('2', 'Z')
        texto_captcha = texto_captcha.replace('1', 'I')

        print(f"Texto do CAPTCHA resolvido (final): {texto_captcha}")
        os.remove(caminho_captcha)
        return texto_captcha.upper()

    except Exception as e:
        print(f"Erro ao processar CAPTCHA: {e}")
        os.remove(caminho_captcha)
        return None