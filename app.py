import streamlit as st
import pandas as pd
import io
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

# Konfigurasi halaman utama
st.set_page_config(page_title="Analisis K-Means Obat", layout="wide")

st.title("📊 Klasterisasi Persediaan Obat")
st.write("Analisis Klasterisasi Persediaan Obat Menggunakan Algoritma K-MEANS di Apotek Anugrah Bekasi.")

# --- PROSES UNGGAH FILE ---
st.subheader("1. Unggah Data Penjualan")
uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) atau CSV data penjualan Anda", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Membaca data sesuai formatnya
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success(f"✅ Berhasil memuat file: {uploaded_file.name}")
    
    # Membersihkan nama kolom dari spasi tidak sengaja di awal/akhir
    df.columns = df.columns.astype(str).str.strip()

    # --- PROSES AGREGASI DATA ---
    # Definisikan nama kolom yang dicari
    kolom_nama_obat = 'Nama Obat'
    kolom_tanggal = 'Tanggal Transaksi'
    kolom_terjual = 'Jumlah Terjual'
    kolom_total_harga = 'Total Harga'

    # Validasi apakah kolom-kolom di atas ada di file yang diupload
    fitur_ada = [kolom_nama_obat in df.columns, kolom_tanggal in df.columns, kolom_terjual in df.columns, kolom_total_harga in df.columns]
    
    if all(fitur_ada):
        try:
            data_agregasi = df.groupby(kolom_nama_obat, sort=False).agg({
                kolom_tanggal: 'count',    
                kolom_terjual: 'sum',         
                kolom_total_harga: 'sum'             
            }).reset_index()

            data_agregasi.columns = ['Nama Obat', 'Frekuensi Transaksi', 'Volume Penjualan', 'Nilai Transaksi']
        except Exception as e:
            st.error(f"Gagal melakukan agregasi data. Error: {e}")
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
        st.subheader("2. Total Data Berdasarkan Karakteristik (Kategori)")
        hitung_kategori = data_agregasi['Kategori'].value_counts().reindex(['Slow Moving', 'Medium Moving', 'Fast Moving']).fillna(0).astype(int)
        
        df_total = pd.DataFrame({
            'Karakteristik / Kategori': hitung_kategori.index,
            'Total Jenis Obat': hitung_kategori.values
        })
        st.dataframe(df_total, use_container_width=True)
        
        # --- TAMPILAN 2: VISUALISASI GRAFIK ---
        st.subheader("3. Visualisasi Grafik Distribusi")
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

        # --- TAMPILAN 3: GROUPING DETAIL OBAT ---
        st.subheader("4. Grouping Detail Obat Sesuai Kategori")
        pilihan_kategori = st.selectbox("Pilih Kategori Obat untuk Dilihat di Web:", ['Slow Moving', 'Medium Moving', 'Fast Moving'])
        
        df_filtered = data_agregasi[data_agregasi['Kategori'] == pilihan_kategori][['Nama Obat', 'Frekuensi Transaksi', 'Volume Penjualan', 'Nilai Transaksi']].reset_index(drop=True)
        st.write(f"### Daftar Obat Berkategori: **{pilihan_kategori}** ({len(df_filtered)} obat)")
        st.dataframe(df_filtered, use_container_width=True)

        # --- PROSES PEMBENTUKAN STRUKTUR EXCEL ---
        st.subheader("5. Unduh Hasil Akhir")
        st.write("Unduh data hasil clustering yang sudah dikelompokkan berdasarkan kategori karakteristik obat:")

        df_fast = data_agregasi[data_agregasi['Kategori'] == 'Fast Moving'][['Nama Obat', 'Frekuensi Transaksi', 'Volume Penjualan', 'Nilai Transaksi']].reset_index(drop=True)
        df_medium = data_agregasi[data_agregasi['Kategori'] == 'Medium Moving'][['Nama Obat', 'Frekuensi Transaksi', 'Volume Penjualan', 'Nilai Transaksi']].reset_index(drop=True)
        df_slow = data_agregasi[data_agregasi['Kategori'] == 'Slow Moving'][['Nama Obat', 'Frekuensi Transaksi', 'Volume Penjualan', 'Nilai Transaksi']].reset_index(drop=True)

        # Penamaan kolom horizontal
        df_fast.columns = ['[FAST] Nama Obat', '[FAST] Frekuensi', '[FAST] Volume', '[FAST] Nilai Transaksi']
        df_medium.columns = ['[MEDIUM] Nama Obat', '[MEDIUM] Frekuensi', '[MEDIUM] Volume', '[MEDIUM] Nilai Transaksi']
        df_slow.columns = ['[SLOW] Nama Obat', '[SLOW] Frekuensi', '[SLOW] Volume', '[SLOW] Nilai Transaksi']

        # Gabungkan secara horizontal
        df_excel_final = pd.concat([df_fast, df_medium, df_slow], axis=1)

        with st.expander("Lihat Preview Struktur Tabel Excel yang Akan Diunduh"):
            st.dataframe(df_excel_final.head(10))

        # Proses penyimpanan ke buffer memory untuk didownload
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_excel_final.to_excel(writer, sheet_name='Grouping Karakteristik Obat', index=False)
        
        excel_data = buffer.getvalue()

        st.download_button(
            label="📥 Download Tabel Karakteristik Obat (Excel)",
            data=excel_data,
            file_name="Tabel_Karakteristik_Obat_KMeans.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        # Menampilkan pesan edukatif jika nama kolom di Excel user tidak sesuai kriteria script
        st.error("❌ Waduh! Kolom yang dibutuhkan tidak ditemukan di dalam file Excel Anda.")
        st.write("Aplikasi ini membutuhkan kolom: **'Nama Obat'**, **'Tanggal Transaksi'**, **'Jumlah Terjual'**, dan **'Total Harga'**.")
        st.write("Berikut adalah daftar nama kolom asli yang terdeteksi di file Anda sekarang (Silakan sesuaikan huruf besar/kecilnya):")
        st.warning(list(df.columns))

else:
    st.info("💡 Silakan unggah file dataset terlebih dahulu pada menu di atas untuk memulai analisis.")
