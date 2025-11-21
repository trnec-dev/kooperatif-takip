import streamlit as st
import pandas as pd
from datetime import date, datetime

# --- AYARLAR ---
BASLANGIC_TARIHI = date(2025, 5, 19)
YILLIK_FAIZ_ORANI = 0.24
SENE_GUNU = 365

st.set_page_config(page_title="Yakacity Kooperatif Faiz Takip", layout="wide")

# --- BAŞLIK ---
st.title("🏠 Yakacity Kooperatif Üye Borç ve Faiz Hesaplama Sistemi")
st.markdown(f"**Başlangıç Tarihi:** {BASLANGIC_TARIHI.strftime('%d.%m.%Y')} | **Yıllık Faiz:** %{YILLIK_FAIZ_ORANI*100}")

# --- YAN MENÜ (VERİ GİRİŞİ) ---
st.sidebar.header("Üye İşlemleri")

# 1. Üye Bilgileri
uye_adi = st.sidebar.text_input("Üye Adı Soyadı", "Ahmet Yılmaz")
baslangic_borcu = st.sidebar.number_input("Ana Borç Tutarı (TL)", value=123250.0, step=1000.0)

# 2. Ödemeler
st.sidebar.subheader("Ödeme Girişi")
odeme_sayisi = st.sidebar.number_input("Kaç adet ödeme yapıldı?", min_value=0, value=1, step=1)

odemeler = []
if odeme_sayisi > 0:
    for i in range(odeme_sayisi):
        c1, c2 = st.sidebar.columns(2)
        tarih = c1.date_input(f"{i+1}. Ödeme Tarihi", value=BASLANGIC_TARIHI)
        tutar = c2.number_input(f"{i+1}. Ödeme Tutarı", value=0.0, step=1000.0)
        if tutar > 0:
            odemeler.append({"Tarih": tarih, "Tutar": tutar, "Tur": "Ödeme"})

# Sorgulama Tarihi (Bugün)
sorgu_tarihi = st.sidebar.date_input("Hesap Kesim Tarihi (Bugün)", value=date.today())

# --- HESAPLAMA MOTORU ---
def hesapla(baslangic_borcu, odemeler, sorgu_tarihi):
    # Hareketleri birleştir ve sırala
    hareketler = [{"Tarih": BASLANGIC_TARIHI, "Tutar": 0, "Tur": "Başlangıç"}] + odemeler
    df = pd.DataFrame(hareketler)
    df['Tarih'] = pd.to_datetime(df['Tarih']).dt.date
    df = df.sort_values(by="Tarih")
    
    sonuclar = []
    bakiye = baslangic_borcu
    onceki_tarih = BASLANGIC_TARIHI
    toplam_faiz = 0
    
    # İlk satır (Başlangıç)
    sonuclar.append({
        "Tarih": BASLANGIC_TARIHI,
        "Açıklama": "Dönem Başı Borcu",
        "Gün": 0,
        "Faiz": 0.0,
        "İşlem": 0.0,
        "Kalan Bakiye": bakiye
    })

    # Ödemeleri İşle
    for index, row in df.iterrows():
        if row["Tur"] == "Başlangıç": continue
        if row["Tarih"] > sorgu_tarihi: continue # Gelecek ödemeleri yoksay
        
        islem_tarihi = row["Tarih"]
        gun_farki = (islem_tarihi - onceki_tarih).days
        
        # Faiz Hesabı: Bakiye * 0.24 * Gün / 365
        isleyen_faiz = (bakiye * YILLIK_FAIZ_ORANI * gun_farki) / SENE_GUNU
        toplam_faiz += isleyen_faiz
        
        # Bakiyeyi Güncelle (Önce faizi ekle, sonra ödemeyi düş)
        bakiye = bakiye + isleyen_faiz - row["Tutar"]
        
        sonuclar.append({
            "Tarih": islem_tarihi,
            "Açıklama": "Ödeme Yapıldı",
            "Gün": gun_farki,
            "Faiz": round(isleyen_faiz, 2),
            "İşlem": row["Tutar"] * -1,
            "Kalan Bakiye": round(bakiye, 2)
        })
        onceki_tarih = islem_tarihi

    # Son İşlemden Bugüne Kadar Olan Kısım
    gun_farki_son = (sorgu_tarihi - onceki_tarih).days
    if gun_farki_son > 0:
        son_faiz = (bakiye * YILLIK_FAIZ_ORANI * gun_farki_son) / SENE_GUNU
        toplam_faiz += son_faiz
        bakiye += son_faiz
        
        sonuclar.append({
            "Tarih": sorgu_tarihi,
            "Açıklama": "BUGÜN (Güncel Durum)",
            "Gün": gun_farki_son,
            "Faiz": round(son_faiz, 2),
            "İşlem": 0.0,
            "Kalan Bakiye": round(bakiye, 2)
        })

    return pd.DataFrame(sonuclar), bakiye, toplam_faiz

# --- EKRANA YAZDIRMA ---
if st.button("HESAPLA") or True: # Otomatik çalışsın
    df_sonuc, son_bakiye, top_faiz = hesapla(baslangic_borcu, odemeler, sorgu_tarihi)
    
    # Kartlar
    col1, col2, col3 = st.columns(3)
    col1.metric("Başlangıç Borcu", f"{baslangic_borcu:,.2f} TL")
    col2.metric("Toplam İşleyen Faiz", f"{top_faiz:,.2f} TL", delta_color="inverse")
    col3.metric("ŞU AN ÖDENMESİ GEREKEN", f"{son_bakiye:,.2f} TL", delta_color="inverse")
    
    st.divider()
    
    # Tablo
    st.subheader(f"📂 {uye_adi} - Hesap Ekstresi")
    
    # Tabloyu formatla
    st.dataframe(
        df_sonuc.style.format({
            "Faiz": "{:,.2f} TL",
            "İşlem": "{:,.2f} TL",
            "Kalan Bakiye": "{:,.2f} TL"
        }),
        use_container_width=True,
        height=400
    )
    

    st.warning(f"⚠️ Not: Hesaplamalar {sorgu_tarihi.strftime('%d.%m.%Y')} tarihi baz alınarak yapılmıştır. Yarın ödeme yapılırsa rakam değişecektir.")
