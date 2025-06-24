import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt

# --- Setup ---
st.set_page_config(page_title="📊 Finance Tracker", page_icon="💰")
st.title("💰 Finance Visualizer & Analyzer")

# --- Upload CSV ---
st.write("Upload CSV dengan kolom: `tanggal`, `pemasukan`, `pengeluaran`")
uploaded_file = st.file_uploader("Upload file", type=["csv"])

if uploaded_file:
    data = pd.read_csv(uploaded_file)
    data['tanggal'] = pd.to_datetime(data['tanggal'])
    data = data.sort_values(by='tanggal')
    data['saldo'] = data['pemasukan'] - data['pengeluaran']
    data['total_saldo'] = data['saldo'].cumsum()

    # --- Filter by timeframe ---
    st.subheader("📅 Pilih Rentang Waktu")
    time_option = st.selectbox("Lihat berdasarkan:", ["Harian (7 Hari)", "Mingguan (1 Bulan)", "Bulanan (1 Tahun)", "Tahunan"])

    if time_option == "Harian (7 Hari)":
        recent = data[data['tanggal'] > (data['tanggal'].max() - pd.Timedelta(days=7))]
        group_data = recent.groupby(data['tanggal'].dt.date).sum()
        x_label = "Tanggal"
    elif time_option == "Mingguan (1 Bulan)":
        data['minggu'] = data['tanggal'].dt.isocalendar().week
        data['tahun'] = data['tanggal'].dt.year
        group_data = data.groupby(['tahun', 'minggu']).sum(numeric_only=True)
        group_data.index = [f"{y}-W{k}" for y, k in group_data.index]
        x_label = "Minggu"
    elif time_option == "Bulanan (1 Tahun)":
        data['bulan'] = data['tanggal'].dt.month
        data['tahun'] = data['tanggal'].dt.year
        group_data = data.groupby(['tahun', 'bulan']).sum(numeric_only=True)
        group_data.index = [f"{y}-{m:02d}" for y, m in group_data.index]
        x_label = "Bulan"
    else:
        data['tahun'] = data['tanggal'].dt.year
        group_data = data.groupby('tahun').sum(numeric_only=True)
        x_label = "Tahun"

    # --- Plotting ---
    st.subheader("📈 Grafik Saldo")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(group_data.index, group_data['pemasukan'] - group_data['pengeluaran'], color='#4caf50', alpha=0.6)
    ax.set_ylabel("Saldo (Rp)")
    ax.set_xlabel(x_label)
    ax.set_ylim(0, 10_000_000)
    ax.set_yticks(range(0, 10_000_001, 500_000))
    ax.set_title("Visualisasi Keuangan: Sisa Pendapatan")
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # --- Show Table ---
    st.subheader("🧾 Tabel Ringkasan")
    st.dataframe(group_data[['pemasukan', 'pengeluaran']])
