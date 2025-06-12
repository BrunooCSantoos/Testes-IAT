import cv2
import easyocr
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

def segmentar_imagem(imagem_binarizada_input):
    # This function now uses Connected Component Analysis (CCA) for more robust segmentation.
    # It expects a binary image where characters are white on a black background.

    # Find connected components (blobs) in the image
    # cv2.connectedComponentsWithStats returns:
    # 1. The total number of labels (components)
    # 2. The label image (each pixel given a label corresponding to its component)
    # 3. Stats for each label (left, top, width, height, area)
    # 4. Centroids for each label
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(imagem_binarizada_input, 8, cv2.CV_32S)

    char_boxes = []

    # Iterate through each component (skip label 0, which is the background)
    for i in range(1, num_labels):
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        area = stats[i, cv2.CC_STAT_AREA]

        # Filter components based on size and aspect ratio
        # These values are critical and might need tuning for different CAPTCHAs.
        # For 'E w°F', '°' is very small, while 'E', 'w', 'F' are larger.
        # Adjusted values for captcha 2.png
        min_width = 5  # Reduced to capture thinner parts of characters
        max_width = 80 # Kept generous
        min_height = 10 # Reduced to capture shorter characters like 'Y' or small parts
        max_height = 80 # Kept generous
        min_area = 30 # Reduced significantly to capture smaller characters or parts of characters

        if (min_width < w < max_width and
            min_height < h < max_height and
            min_area < area):
                
            # Optional: Filter based on aspect ratio if needed (e.g., exclude very thin vertical/horizontal lines)
            # aspect_ratio = w / float(h)
            # if 0.1 < aspect_ratio < 10.0: # Example aspect ratio filter
            char_boxes.append((x, y, w, h))

    # Sort the detected character bounding boxes from left to right
    char_boxes = sorted(char_boxes, key=lambda b: b[0]) # Sort by x-coordinate

    return char_boxes


def resolver_captcha_auto(caminho_captcha, idioma=['pt']):
    try:
        print(f"Lendo CAPTCHA do arquivo: {caminho_captcha}")
        imagem_pil = Image.open(caminho_captcha)
        print("Imagem aberta com sucesso usando PIL.")

        imagem_np = np.array(imagem_pil)

        # Handle different image channel formats
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

        # --- Advanced Preprocessing for CAPTCHA 1.png ---

        # 1. Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        imagem_clahe = clahe.apply(imagem_gray)

        # 2. Attempt to remove horizontal grid lines using morphological operations
        # Create a horizontal kernel (e.g., 20x1 to detect horizontal lines)
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1)) 
        # Perform morphological opening to remove thin horizontal lines
        # Opening = Erosion followed by Dilation. This removes small objects from the foreground.
        # This might remove parts of characters if they are thin and horizontal.
        # Consider experimentation here.
        horizontal_lines = cv2.morphologyEx(imagem_clahe, cv2.MORPH_OPEN, kernel_h, iterations=1)
        # Subtract the detected lines from the original image to remove them
        image_no_h_lines = cv2.subtract(imagem_clahe, horizontal_lines)

        # Do the same for vertical lines if present and problematic
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
        vertical_lines = cv2.morphologyEx(image_no_h_lines, cv2.MORPH_OPEN, kernel_v, iterations=1)
        image_no_lines = cv2.subtract(image_no_h_lines, vertical_lines)
        
        # At this point, image_no_lines should have fewer grid lines.

        # 3. Adaptive Thresholding on the image with lines removed (or the original CLAHE if line removal hurts)
        # Using the image after line removal attempt
        imagem_binarizada = cv2.adaptiveThreshold(image_no_lines, 255,
                                                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                    cv2.THRESH_BINARY_INV, 11, 2)

        # 4. Apply a Median Blur to reduce noise (especially useful after binarization)
        imagem_mediana = cv2.medianBlur(imagem_binarizada, 3)

        # --- End Advanced Preprocessing ---

        # Segment characters using the binarized and cleaned image
        # Pass the pre-processed *binary* image to segmentar_imagem
        char_bounding_boxes = segmentar_imagem(imagem_mediana)

        if not char_bounding_boxes:
            print("No individual characters segmented using CCA. Attempting OCR on the whole pre-processed image.")
            img_for_ocr = cv2.cvtColor(imagem_mediana, cv2.COLOR_GRAY2BGR) # Convert to 3-channel for EasyOCR
            caracteres_segmentados_for_ocr = [img_for_ocr]
        else:
            print(f"Imagem pré-processada com sucesso. Caracteres segmentados: {len(char_bounding_boxes)}")
            caracteres_segmentados_for_ocr = []
            for (x, y, w, h) in char_bounding_boxes:
                # Crop the original grayscale image for each segmented character
                # Use imagem_gray (original grayscale) for cropping to preserve detail for OCR
                cropped_char = imagem_gray[y:y+h, x:x+w]
                
                # Pad the cropped character to add some white space around it (improves OCR)
                # Ensure padding color is white (255 for grayscale)
                padded_char = cv2.copyMakeBorder(cropped_char, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=(255))
                
                caracteres_segmentados_for_ocr.append(padded_char)

        # Initialize EasyOCR reader
        reader = easyocr.Reader(idioma)
        print("Leitor EasyOCR inicializado.")

        # Tenta reconhecer o texto em cada caractere segmentado
        resultados_ocr = []
        for i, caractere_imagem_single in enumerate(caracteres_segmentados_for_ocr):
            # Debugging: Save each character image
            # cv2.imwrite(f"debug_char_final_{i}.png", caractere_imagem_single)

            # Use allowlist to guide OCR. Note: EasyOCR might not recognize '°' perfectly.
            # Adding 'º' (masculine ordinal indicator) as an alternative for '°' might help if it's misidentified
            result = reader.readtext(caractere_imagem_single, 
                                     allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789°º', 
                                     detail=0)
            
            if result:
                text_recognized = result[0].strip()
                # Post-OCR Correction for degree symbol (if it's still an issue)
                # This heuristic is based on the character's size relative to others.
                if text_recognized in ['o', 'O', '0', 'º'] and caractere_imagem_single.shape[0] < 15 and caractere_imagem_single.shape[1] < 15:
                    text_recognized = '°' # Force to degree symbol if small and recognized as o/O/0/º

                resultados_ocr.append(text_recognized)
            else:
                resultados_ocr.append("")

        # Join the OCR results
        texto_captcha = "".join(resultados_ocr)
        print(f"Resultado da leitura do OCR: {texto_captcha}")

        # Final post-processing
        texto_captcha = texto_captcha.replace(" ", "")
        texto_captcha = texto_captcha.replace('"', '')
        # Specific replacements based on common CAPTCHA errors
        texto_captcha = texto_captcha.replace('0', 'O') # Often '0' is misread as 'O' or vice-versa
        texto_captcha = texto_captcha.replace('o', 'O') # If case sensitive, depends on expected output
        texto_captcha = texto_captcha.replace('º', 'O') # Replace masculine ordinal indicator with degree symbol
        texto_captcha = texto_captcha.replace('5', 'S')
        texto_captcha = texto_captcha.replace('8', 'B')
        texto_captcha = texto_captcha.replace('4', 'A')
        texto_captcha = texto_captcha.replace('6', 'G')
        texto_captcha = texto_captcha.replace('7', 'T')
        texto_captcha = texto_captcha.replace('2', 'Z')
        texto_captcha = texto_captcha.replace('1', 'I')

        print(f"Texto do CAPTCHA resolvido (final): {texto_captcha}")
        return texto_captcha.upper()

    except Exception as e:
        print(f"Erro ao processar CAPTCHA: {e}")
        return None

# Example usage
if __name__ == "__main__":
    numeros = {
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15"
    }

    for numero in numeros:
        captcha_path = f"S:\\GEAD-DRH\\DIAFI-DRH\\DRH - GESTÃO DE PESSOAS\\APLICATIVOS\\Testes-IAT\\DIOE\\Captchas\\captcha {numero}.png"

        resolved_text = resolver_captcha_auto(captcha_path)

        if resolved_text:
            print(f"\nCAPTCHA FINAL RESOLVIDO: {resolved_text}")
        else:
            print("\nNão foi possível resolver o CAPTCHA.")