import cv2
import numpy as np

# cv2.CAP_DSHOW proporciona maior estabilidade de captura no Windows
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Erro ao acessar a câmera!")
    exit()

print("Pressione 'q' para fechar a simulação")

while True:
    # 1. Capturar quadro a quadro
    ret, frame = cap.read()
    if not ret:
        print("Não foi possível receber o quadro da câmera")
        break

    # 2. Converter a imagem de BGR para HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 3. Faixa de azul mais tolerante a variações de iluminação e tons
    # Hue: 85 a 140 (cobre do ciano até azul-marinho/arroxeado)
    # Saturation: 40 a 255 (permite áreas com reflexo de luz)
    # Value: 30 a 255 (permite tons de azul mais escuros)
    lower_blue = np.array([85, 40, 30])
    upper_blue = np.array([140, 255, 255])

    # 4. Criar a máscara para isolar a cor azul
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Operações morfológicas suaves para não apagar a caneta fina
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=2)

    # 5. Identificar os contornos do objeto detectado
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 6. Se encontrar algum contorno que atende ao tamanho mínimo
    if len(contours) > 0:
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        # Filtro de área ajustado para 100 (tampa/ponta de caneta à distância)
        if area > 100:
            x, y, w, h = cv2.boundingRect(c)

            # Desenha o retângulo delimitador
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Exibe o rótulo com a área calculada
            cv2.putText(
                frame,
                f"Caneta Detectada (Area: {int(area)})",
                (x, max(y - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

    # 7. Exibir a máscara binária (ajuda a calibrar) e a imagem processada
    cv2.imshow("Mascara (Azul)", mask)
    cv2.imshow("Simulacao da Visao Computacional - Caneta", frame)

    # Pressione 'q' para sair
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Liberação dos recursos FORA do loop
cap.release()
cv2.destroyAllWindows()
