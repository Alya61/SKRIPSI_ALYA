import streamlit as st
import pandas as pd
import io  # <-- PASTIKAN BARIS INI ADA DI PALING ATAS
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

# Konfigurasi halaman utama
st.set_page_config(page_title="Analisis K-Means Obat", layout="wide")

st.title("📊 KLASTERISASI PERSEDIAAN OBAT")
st.write("Analisis Klasterisasi Persediaan Obat Menggunakan Algoritma K-MEANS di Apotek Anugrah Bekasi")

# --- PROSES UNGGAH FILE ---
st.subheader("Unggah Data Penjualan")
uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) atau CSV data penjualan Anda", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Membaca data sesuai formatnya
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success(f"✅ Berhasil memuat file: {uploaded_file.name}")

    # --- PROSES AGREGASI DATA ---
    try:
        data_agregasi = df.groupby('Nama Obat', sort=False).agg({
            'Tanggal Transaksi': 'count',    
            'Jumlah Terjual': 'sum',         
            'Total Harga': 'sum'             
        }).reset_index()

        data_agregasi.columns = ['Nama Obat', 'Frekuensi Transaksi', 'Volume Penjualan', 'Nilai Transaksi']
    except KeyError as e:
        st.error(f"Kolom tidak ditemukan! Pastikan file memiliki kolom 'Nama Obat', 'Tanggal Transaksi', 'Jumlah Terjual', dan 'Total Harga'.")
        st.stop()

    # --- PROSES NORMALISASI DAN K-MEANS ---
    scaler = MinMaxScaler()
    fitur = ['Frekuensi Transaksi', 'Volume Penjualan', 'Nilai Transaksi']
    X_scaled = scaler.fit_transform(data_agregasi[fitur])
    df_normalized = pd.DataFrame(X_scaled, columns=fitur)
    
    kmeans = KMeans(n_clusters=3, init='k-means++', random_state=42)
    data_agregasi['Cluster_ID'] = kmeans.fit_predict(df_normalized)
    
    # --- PROSES PENAMAAN KATEGORI MOVING ---
    cluster_means = data_agregasi.groupby('Cluster_ID')['Volume Penjualan'].mean().sort_values().index
    mapping_kategori = {
        cluster_means[0]: 'Slow Moving',
        cluster_means[1]: 'Medium Moving',
        cluster_means[2]: 'Fast Moving'
    }
    data_agregasi['Kategori'] = data_agregasi['Cluster_ID'].map(mapping_kategori)
    
    # --- TAMPILAN 1: TOTAL DATA BERDASARKAN KARAKTERISTIK ---
    st.subheader("Total Data Berdasarkan Karakteristik (Kategori)")
    hitung_kategori = data_agregasi['Kategori'].value_counts().reindex(['Slow Moving', 'Medium Moving', 'Fast Moving']).fillna(0).astype(int)
    
    df_total = pd.DataFrame({
        'Karakteristik / Kategori': hitung_kategori.index,
        'Total Jenis Obat': hitung_kategori.values
    })
    st.dataframe(df_total, use_container_width=True)
    
    # --- TAMPILAN 2: VISUALISASI GRAFIK ---
    st.subheader("Visualisasi Grafik Distribusi")
    fig, ax = plt.subplots(figsize=(6, 3))
    kategori_urut = ['Slow Moving', 'Medium Moving', 'Fast Moving']
    jumlah_urut = [hitung_kategori.get(k, 0) for k in kategori_urut]
    
    colors = ['#e74c3c', '#f39c12', '#2ecc71']
    bars = ax.bar(kategori_urut, jumlah_urut, color=colors)
    ax.set_ylabel('Jumlah Jenis Obat')
    
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.1, yval, ha='center', va='bottom', fontweight='bold')
        
    st.pyplot(fig)

  # --- PROSES PEMBENTUKAN STRUKTUR EXCEL ---
        st.subheader("Unduh Hasil Akhir")
        st.write("Unduh data hasil klasterisasi")

        df_fast = data_agregasi[data_agregasi['Kategori'] == 'Fast Moving'][['Nama Obat', 'Frekuensi Transaksi', 'Volume Penjualan', 'Nilai Transaksi']].reset_index(drop=True)
        df_medium = data_agregasi[data_agregasi['Kategori'] == 'Medium Moving'][['Nama Obat', 'Frekuensi Transaksi', 'Volume Penjualan', 'Nilai Transaksi']].reset_index(drop=True)
        df_slow = data_agregasi[data_agregasi['Kategori'] == 'Slow Moving'][['Nama Obat', 'Frekuensi Transaksi', 'Volume Penjualan', 'Nilai Transaksi']].reset_index(drop=True)

        df_fast.columns = ['[FAST] Nama Obat', '[FAST] Frekuensi', '[FAST] Volume', '[FAST] Nilai Transaksi']
        df_medium.columns = ['[MEDIUM] Nama Obat', '[MEDIUM] Frekuensi', '[MEDIUM] Volume', '[MEDIUM] Nilai Transaksi']
        df_slow.columns = ['[SLOW] Nama Obat', '[SLOW] Frekuensi', '[SLOW] Volume', '[SLOW] Nilai Transaksi']

        df_excel_final = pd.concat([df_fast, df_medium, df_slow], axis=1)

        with st.expander("Lihat Preview Struktur Tabel Excel yang Akan Diunduh"):
            st.dataframe(df_excel_final.head(10))

        # KODE BARU: Menggunakan openpyxl (Tanpa xlsxwriter)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_excel_final.to_excel(writer, sheet_name='Grouping Karakteristik Obat', index=False)
        
        excel_data = buffer.getvalue()
        
        st.download_button(
            label="📥 Download Hasil",
            data=excel_data,
            file_name="Hasil_klasterisasi",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
