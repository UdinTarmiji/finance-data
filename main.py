import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Keuangan Harian", page_icon="💰")
st.title("📊 Aplikasi Catatan Keuangan")

# Session state untuk menyimpan data
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran"])

# --- Form Input ---
with st.form("input_form"):
    st.subheader("➕ Tambah Catatan Keuangan")

    today = datetime.date.today()
    tanggal = st.date_input("Tanggal", today)
    waktu = st.time_input("Waktu", datetime.datetime.now().time())
    pemasukan = st.number_input("Pemasukan (Rp)", 0)
    pengeluaran = st.number_input("Pengeluaran (Rp)", 0)

    submitted = st.form_submit_button("Simpan")

    if submitted:
        datetime_str = datetime.datetime.combine(tanggal, waktu)
        new_row = {"tanggal": datetime_str, "pemasukan": pemasukan, "pengeluaran": pengeluaran}
        st.session_state.data.loc[len(st.session_state.data)] = new_row
        st.success("✅ Data berhasil disimpan!")

# --- Upload CSV (optional) ---
st.sidebar.subheader("📁 Upload Data dari CSV")
uploaded_file = st.sidebar.file_uploader("Pilih file CSV", type=["csv"])
if uploaded_file:
    uploaded_data = pd.read_csv(uploaded_file)
    st.session_state.data = pd.concat([st.session_state.data, uploaded_data], ignore_index=True)
    st.success("📥 Data dari CSV berhasil dimuat!")

# --- Tampilkan Tabel ---
st.subheader("📋 Riwayat Keuangan")
st.dataframe(st.session_state.data.sort_values("tanggal", ascending=False))

# --- Visualisasi ---
if not st.session_state.data.empty:
    st.subheader("📈 Grafik Keuangan")

    df = st.session_state.data.copy()
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    df = df.sort_values("tanggal")

    fig, ax = plt.subplots()
    ax.plot(df["tanggal"], df["pemasukan"], label="Pemasukan", marker="o", color="green")
    ax.plot(df["tanggal"], df["pengeluaran"], label="Pengeluaran", marker="x", color="red")
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Jumlah (Rp)")
    ax.set_title("Pemasukan vs Pengeluaran")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
else:
    st.info("Belum ada data untuk divisualisasikan.")

# --- Footer ---
st.markdown("---")
st.caption("Dibuat oleh Dafiq 💻 | Powered by Streamlit")
