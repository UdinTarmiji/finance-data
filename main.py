import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import random
import os

st.set_page_config(page_title="📊 Finance Tracker", page_icon="💰")
st.title("💰 Aplikasi Analisis Keuangan Harian")

# --- USERNAME LOGIN PAGE ---
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.username:
    st.session_state.username = st.text_input("Masukkan Username untuk Memulai:")
    if not st.session_state.username:
        st.stop()

# Buat folder user jika belum ada
user_folder = f"data/{st.session_state.username}"
os.makedirs(user_folder, exist_ok=True)
user_csv_path = os.path.join(user_folder, "data.csv")

# --- Inisialisasi Manual Data ---
if "manual_data" not in st.session_state:
    if os.path.exists(user_csv_path):
        st.session_state.manual_data = pd.read_csv(user_csv_path, parse_dates=["tanggal"])
    else:
        st.session_state.manual_data = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

# --- Tombol Input Manual ---
st.markdown("## ➕ Input Data Keuangan Manual")
if st.button("Input Data Keuangan"):
    st.session_state.show_modal = True

if st.session_state.get("show_modal"):
    with st.form("form_input_manual", clear_on_submit=True):
        tanggal = st.date_input("📅 Tanggal", dt.date.today())
        waktu = st.time_input("🕒 Waktu", dt.datetime.now().time())
        pemasukan = st.number_input("📥 Pemasukan (Rp)", min_value=0, step=50000)
        pengeluaran = st.number_input("📤 Pengeluaran (Rp)", min_value=0, step=50000)
        kategori = st.text_input("🏷️ Kategori Pengeluaran", value="Umum")
        simpan = st.form_submit_button("✅ Simpan")
        if simpan:
            waktu_komplit = dt.datetime.combine(tanggal, waktu)
            new_data = pd.DataFrame({
                "tanggal": [waktu_komplit],
                "pemasukan": [pemasukan],
                "pengeluaran": [pengeluaran],
                "kategori": [kategori if pengeluaran > 0 else "-"]
            })
            st.session_state.manual_data = pd.concat([
                st.session_state.manual_data,
                new_data
            ], ignore_index=True)
            st.session_state.manual_data.to_csv(user_csv_path, index=False)
            st.success("✅ Data berhasil ditambahkan!")
            st.session_state.show_modal = False

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
periode = st.selectbox("Tampilkan berdasarkan:", ["Harian", "Mingguan", "Bulanan", "Tahunan"])

# --- Grup Data ---
if periode == "Harian":
    df_grouped = df.groupby(df["tanggal"].dt.date).sum(numeric_only=True)
else:
    rule = {"Mingguan": "W", "Bulanan": "M", "Tahunan": "Y"}[periode]
    df_grouped = df.resample(rule, on="tanggal").sum(numeric_only=True)

df_grouped["saldo"] = df_grouped["pemasukan"] - df_grouped["pengeluaran"]

# --- Visualisasi Gunung ---
st.subheader("📈 Grafik Saldo Akumulatif")
fig, ax = plt.subplots(figsize=(10, 4))
ax.fill_between(df_grouped.index, df_grouped["saldo"].cumsum(), color="skyblue", alpha=0.5)
ax.plot(df_grouped.index, df_grouped["saldo"].cumsum(), color="blue")
ax.set_title(f"Saldo {periode}")
ax.set_ylabel("Saldo (Rp)")
ax.set_ylim(0, 10_000_000)
ax.set_yticks(range(0, 10_500_000, 500_000))
ax.grid(True, linestyle='--', alpha=0.3)
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
