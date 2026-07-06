import streamlit as st
import pandas as pd
import io
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

# ==================================================
# KONFIGURASI HALAMAN
# ==================================================

st.set_page_config(
    page_title="Analisis K-Means Obat",
    layout="wide"
)

st.title("📊 Klasterisasi Persediaan Obat")
st.write(
    "Analisis Klasterisasi Persediaan Obat Menggunakan Algoritma K-Means "
    "di Apotek Anugrah Bekasi"
)

# ==================================================
# UPLOAD FILE
# ==================================================

st.subheader("1. Unggah Data Penjualan")

uploaded_file = st.file_uploader(
    "Pilih file Excel (.xlsx) atau CSV",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:

    # ==================================================
    # MEMBACA FILE
    # ==================================================

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success(f"✅ File berhasil dimuat: {uploaded_file.name}")

    df.columns = df.columns.astype(str).str.strip()

    required_cols = [
        'Nama Obat',
        'Tanggal Transaksi',
        'Jumlah Terjual',
        'Total Harga'
    ]

    if all(col in df.columns for col in required_cols):

        # ==================================================
        # DATA AGREGASI
        # ==================================================

        data_agregasi = df.groupby(
            'Nama Obat',
            sort=False
        ).agg({
            'Tanggal Transaksi': 'count',
            'Jumlah Terjual': 'sum',
            'Total Harga': 'sum'
        }).reset_index()

        data_agregasi.columns = [
            'Nama Obat',
            'Frekuensi Transaksi',
            'Volume Penjualan',
            'Nilai Transaksi'
        ]

        # ==================================================
        # RINGKASAN DATASET
        # ==================================================

        st.subheader("2. Ringkasan Dataset")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Transaksi",
            len(df)
        )

        col2.metric(
            "Jumlah Jenis Obat",
            len(data_agregasi)
        )

        col3.metric(
            "Total Unit Terjual",
            int(df['Jumlah Terjual'].sum())
        )

        # ==================================================
        # NORMALISASI
        # ==================================================

        fitur = [
            'Frekuensi Transaksi',
            'Volume Penjualan',
            'Nilai Transaksi'
        ]

        scaler = MinMaxScaler()

        X_scaled = scaler.fit_transform(
            data_agregasi[fitur]
        )

        df_normalized = pd.DataFrame(
            X_scaled,
            columns=fitur
        )

        df_normalized.insert(
            0,
            'Nama Obat',
            data_agregasi['Nama Obat'].values
        )

        # ==================================================
        # K-MEANS
        # ==================================================

        kmeans = KMeans(
            n_clusters=3,
            init='k-means++',
            random_state=42
        )

        df_normalized['Cluster_ID'] = kmeans.fit_predict(
            df_normalized[
                [
                    'Frekuensi Transaksi',
                    'Volume Penjualan',
                    'Nilai Transaksi'
                ]
            ]
        )

        # ==================================================
        # PENAMAAN CLUSTER
        # SAMA PERSIS DENGAN COLAB
        # ==================================================

        centroid = (
            df_normalized
            .groupby('Cluster_ID')
            [
                [
                    'Frekuensi Transaksi',
                    'Volume Penjualan',
                    'Nilai Transaksi'
                ]
            ]
            .mean()
        )

        urutan = (
            centroid['Frekuensi Transaksi']
            .sort_values(ascending=False)
            .index
        )

        mapping_kategori = {
            urutan[0]: 'Fast Moving',
            urutan[1]: 'Medium Moving',
            urutan[2]: 'Slow Moving'
        }

        df_normalized['Kategori'] = (
            df_normalized['Cluster_ID']
            .map(mapping_kategori)
        )

        hasil_akhir = df_normalized.copy()

        # ==================================================
        # DISTRIBUSI CLUSTER
        # ==================================================

        st.subheader("3. Distribusi Hasil Clustering")

        hitung_kategori = (
            hasil_akhir['Kategori']
            .value_counts()
            .reindex(
                [
                    'Fast Moving',
                    'Medium Moving',
                    'Slow Moving'
                ]
            )
            .fillna(0)
            .astype(int)
        )

        df_total = pd.DataFrame({
            'Kategori': hitung_kategori.index,
            'Jumlah Obat': hitung_kategori.values
        })

        st.dataframe(
            df_total,
            use_container_width=True
        )

        # ==================================================
        # GRAFIK DISTRIBUSI
        # ==================================================

        st.subheader("4. Grafik Distribusi Cluster")

        fig, ax = plt.subplots(figsize=(8,4))

        kategori = [
            'Fast Moving',
            'Medium Moving',
            'Slow Moving'
        ]

        jumlah = [
            hitung_kategori.get(k,0)
            for k in kategori
        ]

        bars = ax.bar(kategori, jumlah)

        ax.set_xlabel("Kategori")
        ax.set_ylabel("Jumlah Obat")

        for bar in bars:
            y = bar.get_height()

            ax.text(
                bar.get_x() + bar.get_width()/2,
                y,
                int(y),
                ha='center'
            )

        st.pyplot(fig)

        # ==================================================
        # DATA HASIL CLUSTERING
        # ==================================================

        st.subheader("5. Data Hasil Clustering")

        st.dataframe(
            hasil_akhir[
                [
                    'Nama Obat',
                    'Kategori',
                    'Frekuensi Transaksi',
                    'Volume Penjualan',
                    'Nilai Transaksi'
                ]
            ],
            use_container_width=True,
            height=500
        )

        # ==================================================
        # FILTER
        # ==================================================

        st.subheader("6. Filter Berdasarkan Kategori")

        pilihan = st.selectbox(
            "Pilih Kategori",
            [
                'Fast Moving',
                'Medium Moving',
                'Slow Moving'
            ]
        )

        df_filter = hasil_akhir[
            hasil_akhir['Kategori'] == pilihan
        ]

        st.write(
            f"Jumlah Obat: {len(df_filter)}"
        )

        st.dataframe(
            df_filter,
            use_container_width=True
        )

        # ==================================================
        # DOWNLOAD EXCEL
        # ==================================================

        st.subheader("7. Download Hasil Clustering")

        buffer = io.BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine='openpyxl'
        ) as writer:

            hasil_akhir.to_excel(
                writer,
                sheet_name='Hasil Clustering',
                index=False
            )

            hasil_akhir[
                hasil_akhir['Kategori']
                == 'Fast Moving'
            ].to_excel(
                writer,
                sheet_name='Fast Moving',
                index=False
            )

            hasil_akhir[
                hasil_akhir['Kategori']
                == 'Medium Moving'
            ].to_excel(
                writer,
                sheet_name='Medium Moving',
                index=False
            )

            hasil_akhir[
                hasil_akhir['Kategori']
                == 'Slow Moving'
            ].to_excel(
                writer,
                sheet_name='Slow Moving',
                index=False
            )

        st.download_button(
            label="📥 Download Hasil Clustering Excel",
            data=buffer.getvalue(),
            file_name="Hasil_Clustering_Obat.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:

        st.error(
            "Kolom wajib tidak ditemukan.\n\n"
            "Pastikan file memiliki kolom:\n"
            "- Nama Obat\n"
            "- Tanggal Transaksi\n"
            "- Jumlah Terjual\n"
            "- Total Harga"
        )

        st.write("Kolom yang terdeteksi:")

        st.warning(list(df.columns))

else:

    st.info(
        "Silakan unggah file terlebih dahulu untuk memulai analisis."
    )
