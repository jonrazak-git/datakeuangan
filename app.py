import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image
import pytesseract
import datetime

# --- KONFIGURASI GOOGLE SHEETS ---
# Mendefinisikan scope dan kredensial (Ganti 'credentials.json' dengan file Anda)

# KODE BARU
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# Mengambil data dari secrets.toml
credentials_dict = dict(st.secrets["gcp_service_account"])
CREDS = Credentials.from_service_account_info(credentials_dict, scopes=SCOPE)
client = gspread.authorize(CREDS)

# Buka spreadsheet dan worksheet pertama
SHEET_ID = "Sheet1" 
sheet = client.open_by_key(SHEET_ID).sheet1

# --- FUNGSI BANTUAN ---
def simpan_data(tanggal, tipe, kategori, nominal, keterangan):
    # Menyimpan baris baru ke Google Sheet
    sheet.append_row([str(tanggal), tipe, kategori, nominal, keterangan])
    st.success("Data berhasil disimpan ke Google Sheets!")

def ambil_data():
    # Mengambil data dari GSheet menjadi Pandas DataFrame
    data = sheet.get_all_records()
    if data:
        df = pd.DataFrame(data)
        # Pastikan kolom Nominal berupa angka
        df['Nominal'] = pd.to_numeric(df['Nominal'], errors='coerce')
        return df
    return pd.DataFrame()

# --- ANTARMUKA PENGGUNA (UI) STREAMLIT ---
st.set_page_config(page_title="Pencatatan Keuangan Pribadi", layout="wide")
st.title("💸 Aplikasi Keuangan Pribadi")

# Membuat Tab Navigasi
tab1, tab2, tab3 = st.tabs(["Catat Manual", "Upload Struk (OCR)", "Analisis Keuangan"])

# TAB 1: PENCATATAN MANUAL
with tab1:
    st.subheader("Input Pemasukan & Pengeluaran")
    with st.form("form_pencatatan"):
        tanggal = st.date_input("Tanggal", datetime.date.today())
        tipe = st.selectbox("Tipe Transaksi", ["Pengeluaran", "Pemasukan"])
        kategori = st.selectbox("Kategori", ["Makanan", "Transportasi", "Tagihan", "Gaji", "Investasi", "Lainnya"])
        nominal = st.number_input("Nominal (Rp)", min_value=0)
        keterangan = st.text_input("Keterangan Tambahan")
        
        submitted = st.form_submit_button("Simpan Data")
        if submitted:
            simpan_data(tanggal, tipe, kategori, nominal, keterangan)

# TAB 2: PEMBACAAN STRUK (OCR)
with tab2:
    st.subheader("Otomatisasi dari Foto Struk")
    uploaded_file = st.file_uploader("Upload foto struk atau kwitansi (JPG/PNG)", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Struk yang diupload', width=300)
        
        if st.button("Ekstrak Teks dari Struk"):
            with st.spinner('Membaca teks...'):
                # Proses OCR menggunakan Tesseract
                extracted_text = pytesseract.image_to_string(image)
                st.text_area("Hasil Ekstraksi Teks (Edit jika ada kesalahan):", extracted_text, height=150)
                
                # Catatan: Untuk sistem yang lebih canggih di dunia nyata, 
                # teks ini diproses dengan Regex (Regular Expression) atau LLM 
                # untuk secara otomatis menemukan angka "Total" dan memindahkannya ke form.
                st.info("Fitur ekstraksi berhasil. Anda dapat menyalin total nominal dari teks di atas dan memasukkannya ke tab 'Catat Manual'.")

# TAB 3: ANALISIS KEUANGAN
with tab3:
    st.subheader("Dashboard Analisis")
    df = ambil_data()
    
    if not df.empty:
        # Metrik Utama
        total_pemasukan = df[df['Tipe'] == 'Pemasukan']['Nominal'].sum()
        total_pengeluaran = df[df['Tipe'] == 'Pengeluaran']['Nominal'].sum()
        saldo = total_pemasukan - total_pengeluaran
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
        col2.metric("Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")
        col3.metric("Saldo Saat Ini", f"Rp {saldo:,.0f}")
        
        st.divider()
        
        # Grafik Pengeluaran Berdasarkan Kategori
        st.write("**Pengeluaran Berdasarkan Kategori**")
        df_pengeluaran = df[df['Tipe'] == 'Pengeluaran']
        if not df_pengeluaran.empty:
            kategori_group = df_pengeluaran.groupby('Kategori')['Nominal'].sum().reset_index()
            st.bar_chart(kategori_group.set_index('Kategori'))
            
        st.write("**Tabel Data Mentah**")
        st.dataframe(df)
    else:
        st.warning("Belum ada data keuangan di Google Sheets Anda.")
