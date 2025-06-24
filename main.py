import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import random

st.set_page_config(page_title="📊 Finance Tracker", page_icon="💰")
st.title("💰 Aplikasi Analisis Keuangan Harian")

# --- Inisialisasi Manual Data ---
if "manual_data" not in st.session_state:
    st.session_state.manual_data = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

# --- Tombol Input Manual ---
if st.button("➕ Input Data Keuangan Manual"):
    with st.container():
        st.markdown("### Tambahkan Data Baru")
        with st.form("form_input_manual", clear_on_submit=True):
            tanggal = st.date_input("📅 Tanggal", dt.date.today())
            waktu = st.time_input("🕒 Waktu", dt.datetime.now().time())
            pemasukan = st.number_input("📥 Pemasukan (Rp)", min_value=0, step=50000)
            pengeluaran = st.number_input("📤 Pengeluaran (Rp)", min_value=0, step=50000)
            kategori = st.text_input("🏷️ Kategori Pengeluaran", value="Umum")
            simpan = st.form_submit_button("✅ Simpan")
            if simpan:
                waktu_komplit = dt.datetime.combine(tanggal, waktu)
                st.session_state.manual_data = pd.concat([
                    st.session_state.manual_data,
                    pd.DataFrame({
                        "tanggal": [waktu_komplit],
                        "pemasukan": [pemasukan],
                        "pengeluaran": [pengeluaran],
                        "kategori": [kategori if pengeluaran > 0 else "-"]
                    })
                ], ignore_index=True)
                st.success("✅ Data berhasil ditambahkan!")

# --- Upload CSV ---
st.sidebar.header("📤 Upload CSV")
uploaded_file = st.sidebar.file_uploader("Unggah file CSV Anda", type=["csv"])

# --- Load Data ---
if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["tanggal"])
elif not st.session_state.manual_data.empty:
    df = st.session_state.manual_data.copy()
else:
    st.warning("📎 Silakan upload file CSV atau input data manual terlebih dahulu.")
    st.stop()

# --- Preprocessing ---
df["tanggal"] = pd.to_datetime(df["tanggal"])
df = df.sort_values("tanggal")
df["saldo"] = df["pemasukan"] - df["pengeluaran"]

# --- Statistik Total ---
total_pemasukan = df["pemasukan"].sum()
total_pengeluaran = df["pengeluaran"].sum()
total_saldo = total_pemasukan - total_pengeluaran

st.markdown("---")
st.metric("💰 Total Saldo", f"Rp {total_saldo:,.0f}")
st.metric("📥 Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
st.metric("📤 Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")

# --- Pilihan Waktu ---
waktu = st.selectbox("Tampilkan berdasarkan:", ["Harian", "Mingguan", "Bulanan", "Tahunan"])

# --- Grup Data ---
if waktu == "Harian":
    df_grouped = df.groupby(df["tanggal"].dt.date).sum(numeric_only=True)
elif waktu == "Mingguan":
    df_grouped = df.resample("W", on="tanggal").sum(numeric_only=True)
elif waktu == "Bulanan":
    df_grouped = df.resample("M", on="tanggal").sum(numeric_only=True)
elif waktu == "Tahunan":
    df_grouped = df.resample("Y", on="tanggal").sum(numeric_only=True)

# --- Visualisasi Gunung ---
st.subheader("📈 Grafik Saldo Akumulatif")
fig, ax = plt.subplots(figsize=(10, 4))
ax.fill_between(df_grouped.index, df_grouped["saldo"].cumsum(), color="skyblue", alpha=0.5, label="Saldo")
ax.plot(df_grouped.index, df_grouped["saldo"].cumsum(), color="blue")
ax.set_title(f"Saldo {waktu}")
ax.set_ylabel("Saldo (Rp)")
ax.set_ylim(0, 10_000_000)
ax.set_yticks(range(0, 10_500_000, 500_000))
ax.grid(True, linestyle='--', alpha=0.3)
ax.legend()
st.pyplot(fig)

# --- Visualisasi Kategori Pie ---
if "kategori" in df.columns and not df[df["pengeluaran"] > 0].empty:
    st.subheader("📊 Distribusi Pengeluaran berdasarkan Kategori")
    kategori_data = df[df["pengeluaran"] > 0].groupby("kategori")["pengeluaran"].sum()
    warna = ["#%06x" % random.randint(0, 0xFFFFFF) for _ in range(len(kategori_data))]
    fig2, ax2 = plt.subplots()
    ax2.pie(kategori_data, labels=kategori_data.index, autopct="%1.1f%%", startangle=90, colors=warna)
    ax2.axis("equal")
    st.pyplot(fig2)

    st.markdown("### 📋 Detail Pengeluaran per Kategori")
    for kategori, total in kategori_data.items():
        st.write(f"🔹 **{kategori}**: Rp {total:,.0f}")

# --- Tabel Data ---
with st.expander("📋 Lihat Data Lengkap"):
    st.dataframe(df.sort_values("tanggal", ascending=False))
