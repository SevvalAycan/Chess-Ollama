import numpy as np
import cv2
import chess
import requests
import random

#Önce satranç tahtamızı oluşturalım
board=np.zeros((800,800,3),dtype="uint8")

def draw_board(img):
    lb = (158, 203, 230)  # light brown
    db = (34, 63, 101)  # dark brown

    for i in range(8):
        for j in range(8):
            # köşeleri belirlemece
            y1, y2 = i * 100, (i + 1) * 100
            x1, x2 = j * 100, (j + 1) * 100

            img[y1:y2,x1:x2] = lb if ( i + j ) % 2 == 0 else db

    for i in range(64):
        x,y = get_pixel_coordinate(i)
        cv2.putText(img,chess.square_name(i), (x+5, y+ 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)

#koordinat bilgisini belirleyelim
def get_pixel_coordinate(index):
    column = index % 8
    row = index // 8

    x = column * 100  #pixel x depends on column
    y = (7-row) * 100 #pixel y - depends on the row, but since itis top to buttom, it's inverted

    return x,y

# taşları yerleştirme fonksiyonu
def place_pieces(background, image_of_pieces, x_center, y_center):
    h,w = image_of_pieces.shape[:2]

    y1, y2 = y_center + 20 , y_center + 20 + h
    x1, x2 = x_center + 20 , x_center + 20 + w

    alpha_piece = image_of_pieces[: , :, 3] / 255.0
    alpha_background = 1.0 - alpha_piece

    for i in range(0,3):
        background[y1:y2,x1:x2,i] = (alpha_piece * image_of_pieces[: , :, i] + alpha_background * background[y1:y2,x1:x2,i])

# beyaz taşlar
b_kale = cv2.imread("images/beyaz_kale.png", cv2.IMREAD_UNCHANGED)
b_at = cv2.imread("images/beyaz_at.png", cv2.IMREAD_UNCHANGED)
b_fil = cv2.imread("images/beyaz_fil.png", cv2.IMREAD_UNCHANGED)
b_vezir = cv2.imread("images/beyaz_vezir.png", cv2.IMREAD_UNCHANGED)
b_sah = cv2.imread("images/beyaz_sah.png", cv2.IMREAD_UNCHANGED)
b_piyon = cv2.imread("images/beyaz_piyon.png", cv2.IMREAD_UNCHANGED)
# siyah taşlar
s_kale = cv2.imread("images/siyah_kale.png", cv2.IMREAD_UNCHANGED)
s_at = cv2.imread("images/siyah_at.png", cv2.IMREAD_UNCHANGED)
s_fil = cv2.imread("images/siyah_fil.png", cv2.IMREAD_UNCHANGED)
s_vezir = cv2.imread("images/siyah_vezir.png", cv2.IMREAD_UNCHANGED)
s_sah = cv2.imread("images/siyah_sah.png", cv2.IMREAD_UNCHANGED)
s_piyon = cv2.imread("images/siyah_piyon.png", cv2.IMREAD_UNCHANGED)
'''
python-chess'te taşlar harf ile tutulurmuş bende görseller ile bu şekilde eşleyeceğim
Beyazlar 
    R - Kale
    N - At
    B - Fil
    Q - Vezir
    K - Şah
    P - Piyon

Siyahlar
    r - Kale
    n - At
    b - Fil
    q - Vezir
    k - Şah
    p - Piyon
'''

# python-chess ile uyumlu sözlük
tas_sozlugu = {
    'R': b_kale, 'N': b_at, 'B': b_fil, 'Q': b_vezir, 'K': b_sah, 'P': b_piyon,
    'r': s_kale, 'n': s_at, 'b': s_fil, 'q': s_vezir, 'k': s_sah, 'p': s_piyon
}


#ollamadan hamle iste
def get_ollama_move(fen):
    url = "http://localhost:11434/api/generate"
    prompt = (f"Sen bir satranç motorusun. Mevcut FEN: {fen}. "
              "SADECE bir sonraki enyi hamleyi UCI formatında (örn: e7e5) yaz. "
              "Asla açıklama yapma, sadece 4 veya 5 karakterlik hamleyi gönder.")
    data = { "model": "llama3", "prompt": prompt,"stream":False , "options":{"temperature":0.2}}
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()['response'].strip()
    except requests.exceptions.Timeout:
        print("[SİSTEM Ollama çok uzun süre düşündü zaman aşımı!")
        return None
    except Exception as e:
        print(e)
        return None

chess_board = chess.Board()

print("-" * 30)
print("SATRANÇ MOTORU BAŞLADI")
print("-" * 30)

while True:
    draw_board(board)

    for i in range(64):
        piece = chess_board.piece_at(i)
        if piece is not None:
            place_pieces(board, tas_sozlugu[piece.symbol()], *get_pixel_coordinate(i))

    if chess_board.is_check():
        cv2.putText(board, "SAH!", (700, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    if chess_board.is_game_over():
        result = chess_board.result()
        message=""

        if result == "1-0":
            message = "TEBRIKLER! Beyaz Kazandı! (Mat)"
        elif result == "0-1":
            message = "OLLAMA KAZANDI! Siyah Kazandı! (Mat)"
        else:
            message = "BERABERE! Oyun bitti."

        cv2.putText(board, "OYUN BITTI", (150, 350), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)
        cv2.putText(board, message, (100, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("chess", board)
        print(f"\n[SİSTEM] {message}")
        print("Çıkmak için OpenCV penceresindeyken bir tuşa basın...")
        cv2.waitKey(0)
        break

    cv2.imshow("chess", board)
    cv2.waitKey(1)

    #ollama sırası mı kontrol et
    if chess_board.turn == chess.BLACK:
        print("\n[BİLGİ] Ollama hamle düşünüyor...")
        ai_move_str = get_ollama_move(chess_board.fen())

        move = None

        if ai_move_str:
            try:
                temp_move = chess.Move.from_uci(ai_move_str)
                if temp_move in chess_board.legal_moves:
                    move = temp_move
                    print(f"[OLLAMA] Hamlesi: {ai_move_str}")
                else:
                    print(f"[UYARI] Ollama geçersiz hamle önerdi ({ai_move_str}).")
            except:
                print("[HATA] Ollama'dan gelen hamle formatı bozuk!")

        if move is None:
            move = random.choice(list(chess_board.legal_moves))
            print(f"[SİSTEM] Otomatik (Rastgele) hamle yapıldı: {move}")

        chess_board.push(move)
        continue

    #kullanıcı hamlesi
    print("\n>>> SIRA SİZDE (Beyazlar)")
    move_input = input("Hamlenizi girin (örn e2e4) veya 'exit': ").lower()

    if move_input == "exit":
        print("Oyun sonlandırıldı")
        break

    try:
        move = chess.Move.from_uci(move_input)
        if move in chess_board.legal_moves:
            chess_board.push(move)
            print(f"[SİSTEM] Hamle: {move_input}")
        else:
            print("[GEÇERSİZ] Bu hamle satranç kurallarına aykırı!")
    except:
        print("[HATA] Yanlış format girdiniz! Örnek: e2e4")


cv2.destroyAllWindows()

