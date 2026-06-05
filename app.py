from flask import Flask, render_template, request, jsonify, session
import random
from kelimeler import KELIME_HAVUZU

app = Flask(__name__)
app.secret_key = "odev_projesi_gizli_key"

def internetten_kelime_sec(harf_sayisi):
    # İsmi fonksiyon hatası vermesin diye eski ismiyle bıraktık ama 
    # artık internete değil, senin hazırladığın yerel kütüphaneye bağlanıyor!
    havuz = KELIME_HAVUZU.get(harf_sayisi, KELIME_HAVUZU[5])
    secilen = random.choice(havuz).upper()
    print(f"--- KÜTÜPHANEDEN BAŞARIYLA ÇEKİLDİ ({harf_sayisi} Harf): {secilen} ---")
    return secilen

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/wordle/<int:harf_sayisi>')
def wordle(harf_sayisi):
    session.pop('wordle_hedef', None)
    session.pop('harf_sayisi', None)
    
    session['harf_sayisi'] = harf_sayisi
    session['wordle_hedef'] = internetten_kelime_sec(harf_sayisi)
    return render_template('wordle.html', harf_sayisi=harf_sayisi)

@app.route('/wordle-kontrol', methods=['POST'])
def wordle_kontrol():
    import unicodedata
    
    data = request.get_json()
    tahmin_ham = data.get('tahmin', '').strip()
    hedef_ham = session.get('wordle_hedef', 'KİTAP').strip()
    harf_sayisi = session.get('harf_sayisi', 5)
    
    # Tarayıcıların gizli karakter oyunlarını bozmak için NFC normalizasyonu yapıyoruz
    def harf_duzelt(metin):
        # Önce küçük i ve ı harflerini sağlama alıyoruz
        metin = metin.replace('ı', 'I').replace('i', 'İ')
        metin = metin.upper()
        
        # EĞER HEDEF KELİMEDE 'İ' VARSA VE TAHMİNDE YANLIŞLIKLA 'I' GİTMİŞSE TOLERANS GÖSTER:
        # Ya da tam tersi durumlar için harfleri normalize etmeden önce birbirine zorla dönüştürüyoruz
        return unicodedata.normalize('NFC', metin)

    tahmin = harf_duzelt(tahmin_ham)
    hedef_kelime = harf_duzelt(hedef_ham) 
# Eğer harf sayıları tutuyor ama tarayıcı İ harfini I yaptıysa tolerans sağla:
    if tahmin != hedef_kelime:
        # Tahmindeki 'I' harflerini, hedef kelimede o pozisyonda 'İ' varsa 'İ'ye dönüştür
        gecici_tahmin = list(tahmin)
        for i in range(min(len(tahmin), len(hedef_kelime))):
            if tahmin[i] == 'I' and hedef_kelime[i] == 'İ':
                gecici_tahmin[i] = 'İ'
        tahmin = "".join(gecici_tahmin)

    
    sonuc = ['absent'] * harf_sayisi
    
    # Hedef kelimedeki harflerin adetlerini say
    harf_sayilari = {}
    for harf in hedef_kelime:
        harf_sayilari[harf] = harf_sayilari.get(harf, 0) + 1

    # 1. TUR: Tam yerine oturan YEŞİL harfler
    for i in range(harf_sayisi):
        if tahmin[i] == hedef_kelime[i]:
            sonuc[i] = 'correct'
            harf_sayilari[tahmin[i]] -= 1

    # 2. TUR: Yeri yanlış ama kelimede olan SARI harfler
    for i in range(harf_sayisi):
        if sonuc[i] != 'correct':
            if tahmin[i] in harf_sayilari and harf_sayilari[tahmin[i]] > 0:
                sonuc[i] = 'present'
                harf_sayilari[tahmin[i]] -= 1

    # Kazanma kontrolü
    kazandi = (tahmin == hedef_kelime)
    
    return jsonify({
        'sonuc': sonuc, 
        'kazandi': kazandi, 
        'dogru_kelime': hedef_kelime
    })

if __name__ == '__main__':
    app.run(debug=True)