import streamlit as st
import pandas as pd
import io
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt

# =========================
# KONFIGURASI HALAMAN
# =========================

st.set_page_config(
    page_title="Analisis K-Means Obat",
    layout="wide"
)

st.title("📊 Klasterisasi Persediaan Obat")
st.write(
    "Analisis Klasterisasi Persediaan Obat Menggunakan Algoritma K-Means "
    "di Apotek Anugrah Bekasi"
)

# =========================
# UPLOAD FILE
# =========================

st.subheader("1. Unggah Data Penjualan")

uploaded_file = st.file_uploader(
    "Pilih file Excel (.xlsx) atau CSV",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:

    # =========================
    # BACA FILE
    # =========================

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success(f"✅ File berhasil dimuat: {uploaded_file.name}")

    df.columns = df.columns.astype(str).str.strip()

    # =========================
    # VALIDASI KOLOM
    # =========================

    required_cols = [
        'Nama Obat',
        'Tanggal Transaksi',
        'Jumlah Terjual',
        'Total Harga'
    ]

    if all(col in df.columns for col in required_cols):

        # =========================
        # AGREGASI DATA
        # =========================

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

        # =========================
        # RINGKASAN DATASET
        # =========================

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

        # =========================
        # NORMALISASI
        # =========================

        fitur = [
            'Frekuensi Transaksi',
            'Volume Penjualan',
            'Nilai Transaksi'
        ]

        scaler = MinMaxScaler()

        X_scaled = scaler.fit_transform(
            data_agregasi[fitur]
        )

        # =========================
        # K-MEANS
        # =========================

        kmeans = KMeans(
            n_clusters=3,
            init='k-means++',
            random_state=42
        )

        data_agregasi['Cluster_ID'] = kmeans.fit_predict(
            X_scaled
        )

        # =========================
        # LABEL KATEGORI
        # =========================

        cluster_means = (
            data_agregasi
            .groupby('Cluster_ID')['Volume Penjualan']
            .mean()
            .sort_values()
            .index
        )

        mapping_kategori = {
            cluster_means[0]: 'Slow Moving',
            cluster_means[1]: 'Medium Moving',
            cluster_means[2]: 'Fast Moving'
        }

        data_agregasi['Kategori'] = (
            data_agregasi['Cluster_ID']
            .map(mapping_kategori)
        )

        # =========================
        # HASIL AKHIR
        # =========================

        hasil_akhir = data_agregasi.copy()

        hasil_akhir = hasil_akhir[
            [
                'Nama Obat',
                'Frekuensi Transaksi',
                'Volume Penjualan',
                'Nilai Transaksi',
                'Cluster_ID',
                'Kategori'
            ]
        ]

        # =========================
        # DISTRIBUSI CLUSTER
        # =========================

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

        # =========================
        # GRAFIK
        # =========================

        st.subheader("4. Grafik Distribusi Cluster")

        fig, ax = plt.subplots(figsize=(7, 4))

        kategori = [
            'Fast Moving',
            'Medium Moving',
            'Slow Moving'
        ]

        jumlah = [
            hitung_kategori.get(k, 0)
            for k in kategori
        ]

        bars = ax.bar(kategori, jumlah)

        ax.set_ylabel("Jumlah Obat")
        ax.set_xlabel("Kategori")

        for bar in bars:
            yval = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2,
                yval,
                int(yval),
                ha='center'
            )

        st.pyplot(fig)

        # =========================
        # DATA LENGKAP
        # =========================

        st.subheader("5. Data Hasil Clustering Lengkap")

        st.dataframe(
            hasil_akhir,
            use_container_width=True,
            height=500
        )

        # =========================
        # FILTER KATEGORI
        # =========================

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

        # =========================
        # DOWNLOAD EXCEL
        # =========================

        st.subheader("7. Download Hasil Clustering")

        buffer = io.BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine='openpyxl'
        ) as writer:

            hasil_akhir.to_excel(
                writer,
                sheet_name='Semua Hasil',
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
            "Kolom wajib tidak ditemukan. "
            "Pastikan file memiliki kolom: "
            "'Nama Obat', 'Tanggal Transaksi', "
            "'Jumlah Terjual', dan 'Total Harga'."
        )

else:
    st.info(
        "Silakan unggah file terlebih dahulu untuk memulai analisis."
    )
