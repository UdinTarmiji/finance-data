import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import random
import os

st.set_page_config(page_title="📊 Finance Tracker", page_icon="💰")
st.title("📊 Finance Tracker")

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
if st.button("Input Data Keuangan", type="primary"):
    st.session_state.show_form = True

if st.session_state.get("show_form"):
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
            st.session_state.manual_data = pd.concat([st.session_state.manual_data, new_data], ignore_index=True)
            st.session_state.manual_data.to_csv(user_csv_path, index=False)
            st.success("✅ Data berhasil ditambahkan!")
            st.session_state.show_form = False

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

if df.empty:
    st.warning("📎 Data masih kosong. Silakan input data terlebih dahulu.")
    st.stop()

# --- Preprocessing ---
df["tanggal"] = pd.to_datetime(df["tanggal"])
df = df.sort_values("tanggal")
df["saldo"] = df["pemasukan"].cumsum() - df["pengeluaran"].cumsum()

# --- Statistik Total ---
total_pemasukan = df["pemasukan"].sum()
total_pengeluaran = df["pengeluaran"].sum()
total_saldo = total_pemasukan - total_pengeluaran

st.markdown("---")
st.metric("💰 Total Saldo", f"Rp {total_saldo:,.0f}")
st.metric("📥 Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
st.metric("📤 Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")

# --- Pilihan Waktu ---
st.markdown("## 📅 Pilih Periode dan Tipe Grafik")
periode = st.selectbox("Tampilkan berdasarkan:", ["Harian", "Mingguan", "Bulanan", "Tahunan"])
tipe_grafik = st.radio("Jenis Visualisasi Saldo:", ["Gunung (Area Chart)", "Diagram (Line Chart)"])
y_max_option = st.selectbox("Batas Maksimum Y (Rp):", ["1Jt (lonjakan 100rb)", "10Jt (lonjakan 500rb)", "100Jt (lonjakan 5jt)", "1M (lonjakan 50jt)", "10M (lonjakan 500jt)"])

# --- Grup Data ---
df.set_index("tanggal", inplace=True)
if periode == "Harian":
    df_grouped = df.resample("D").sum(numeric_only=True)
elif periode == "Mingguan":
    df_grouped = df.resample("W").sum(numeric_only=True)
elif periode == "Bulanan":
    df_grouped = df.resample("M").sum(numeric_only=True)
else:
    df_grouped = df.resample("Y").sum(numeric_only=True)

if df_grouped.empty or "pemasukan" not in df_grouped or "pengeluaran" not in df_grouped:
    st.info("Grafik belum tersedia karena belum ada data pemasukan/pengeluaran.")
else:
    df_grouped["saldo"] = df_grouped["pemasukan"].cumsum() - df_grouped["pengeluaran"].cumsum()

    # --- Grafik Saldo ---
    st.subheader("📈 Grafik Saldo Akumulatif")
    fig, ax = plt.subplots(figsize=(10, 4))

    if tipe_grafik == "Gunung (Area Chart)":
        ax.fill_between(df_grouped.index, df_grouped["saldo"], color="skyblue", alpha=0.5)
        ax.plot(df_grouped.index, df_grouped["saldo"], color="blue")
    else:
        ax.plot(df_grouped.index, df_grouped["saldo"], color="green", linewidth=2)

    limits = {
        "1Jt (lonjakan 100rb)": (1_000_000, 100_000),
        "10Jt (lonjakan 500rb)": (10_000_000, 500_000),
        "100Jt (lonjakan 5jt)": (100_000_000, 5_000_000),
        "1M (lonjakan 50jt)": (1_000_000_000, 50_000_000),
        "10M (lonjakan 500jt)": (10_000_000_000, 500_000_000)
    }
    y_max, y_step = limits[y_max_option]
    ax.set_ylim(0, y_max)
    ax.set_yticks(range(0, y_max + y_step, y_step))
    ax.set_title(f"Saldo {periode}")
    ax.set_ylabel("Saldo (Rp)")
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
    st.dataframe(df.sort_index(ascending=False).reset_index())

# --- Footer ---
st.markdown("---")
st.markdown("Made by Dafiq | Powered by Machine Learning")
st.markdown("📱 [WhatsApp](https://wa.me/6281224280846) | 📸 [Instagram](https://instagram.com/dafiqelhaq) | 📧 [Email](mailto:dafiqelhaq11@gmail.com)")
