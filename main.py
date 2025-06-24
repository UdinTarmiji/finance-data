import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="📊 Finance Tracker", page_icon="💰")
st.title("💰 Aplikasi Pencatatan Keuangan & Visualisasi")

# --- Upload CSV ---
st.subheader("📤 Upload File CSV Anda")
uploaded = st.file_uploader("Pilih file CSV", type=["csv"])

# --- Load Data ---
if uploaded:
    df = pd.read_csv(uploaded)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    st.session_state.data = df
else:
    if "data" not in st.session_state:
        st.session_state.data = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran"])

# --- Input Manual ---
st.subheader("📝 Tambahkan Catatan Baru")
with st.form("entry_form"):
    col1, col2 = st.columns(2)
    with col1:
        tgl = st.date_input("Tanggal", value=datetime.today())
        pemasukan = st.number_input("Pemasukan", 0, step=50000)
    with col2:
        waktu = st.time_input("Waktu", value=datetime.now().time())
        pengeluaran = st.number_input("Pengeluaran", 0, step=50000)
    submitted = st.form_submit_button("Tambah")
    if submitted:
        full_datetime = datetime.combine(tgl, waktu)
        new_row = {"tanggal": full_datetime, "pemasukan": pemasukan, "pengeluaran": pengeluaran}
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
        st.success("Data berhasil ditambahkan!")

# --- Tabel Data ---
if not st.session_state.data.empty:
    st.subheader("📄 Data Saat Ini")
    st.dataframe(st.session_state.data.sort_values("tanggal"))

# --- Pilihan Agregasi ---
st.subheader("🕒 Pilih Rentang Waktu Visualisasi")
rentang = st.selectbox("Tampilkan grafik berdasarkan:", ("Jam", "Hari", "Minggu", "Bulan", "Tahun"))

# --- Visualisasi ---
if not st.session_state.data.empty:
    df = st.session_state.data.copy()
    df["tanggal"] = pd.to_datetime(df["tanggal"])

    if rentang == "Jam":
        df["waktu"] = df["tanggal"].dt.hour
        group = df.groupby("waktu")[["pemasukan", "pengeluaran"]].sum()
        xlabel = "Jam (0-23)"
    elif rentang == "Hari":
        df["waktu"] = df["tanggal"].dt.day_name()
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        group = df.groupby("waktu")[["pemasukan", "pengeluaran"]].sum().reindex(order)
        xlabel = "Hari"
    elif rentang == "Minggu":
        df["waktu"] = df["tanggal"].dt.isocalendar().week
        group = df.groupby("waktu")[["pemasukan", "pengeluaran"]].sum()
        xlabel = "Minggu ke-"
    elif rentang == "Bulan":
        df["waktu"] = df["tanggal"].dt.strftime("%B")
        order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        group = df.groupby("waktu")[["pemasukan", "pengeluaran"]].sum().reindex(order)
        xlabel = "Bulan"
    else:
        df["waktu"] = df["tanggal"].dt.year
        group = df.groupby("waktu")[["pemasukan", "pengeluaran"]].sum()
        xlabel = "Tahun"

    # Plot
    st.subheader(f"📈 Grafik Keuangan per {rentang}")
    fig, ax = plt.subplots()
    group.plot(kind="bar", ax=ax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Jumlah (Rp)")
    ax.set_title(f"Pemasukan dan Pengeluaran per {rentang}")
    st.pyplot(fig)

# --- Footer ---
st.markdown("---")
st.caption("Made with 💙 by Dafiq")
