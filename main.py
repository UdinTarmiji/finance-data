import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import random
import os
import base64
import json
import requests

# Konfigurasi dasar
st.set_page_config(page_title="Finance Tracker", page_icon="💰", layout="wide")
st.title("💰 Finance Tracker")

# Fungsi simpan ke GitHub
def simpan_ke_github(dataframe, filepath):
    csv_content = dataframe.to_csv(index=False)
    token = st.secrets["github_token"]
    owner = st.secrets["repo_owner"]
    repo = st.secrets["repo_name"]

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filepath}"
    headers = {"Authorization": f"token {token}"}
    get_resp = requests.get(url, headers=headers)
    sha = get_resp.json()["sha"] if get_resp.status_code == 200 else None

    payload = {
        "message": "update data.csv",
        "content": base64.b64encode(csv_content.encode()).decode(),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        st.success("✅ Data berhasil disimpan ke GitHub!")
    else:
        st.error("❌ Gagal menyimpan ke GitHub")
        st.write(response.json())

# --- Halaman Login/Register ---
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.username:
    st.header("🔐 Masuk atau Daftar")
    opsi = st.radio("Pilih Aksi:", ["Login", "Register"])
    username_input = st.text_input("Username")
    if st.button("Lanjut") and username_input:
        st.session_state.username = username_input
        st.experimental_rerun()
    st.stop()

# Path penyimpanan lokal dan Github
user_folder = f"data/{st.session_state.username}"
os.makedirs(user_folder, exist_ok=True)
user_csv_path = os.path.join(user_folder, "data.csv")

# Load Data
if os.path.exists(user_csv_path):
    df = pd.read_csv(user_csv_path, parse_dates=["tanggal"])
else:
    df = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

# --- Input Manual ---
st.markdown("## ➕ Input Data Keuangan")
with st.expander("📝 Tambahkan Data Manual"):
    with st.form("form_input"): 
        tanggal = st.date_input("Tanggal", dt.date.today())
        waktu = st.time_input("Waktu", dt.datetime.now().time())
        pemasukan = st.number_input("Pemasukan", min_value=0, step=1000)
        pengeluaran = st.number_input("Pengeluaran", min_value=0, step=1000)
        kategori = st.text_input("Kategori", value="Umum")
        submit = st.form_submit_button("Simpan")
        if submit:
            waktu_komplit = dt.datetime.combine(tanggal, waktu)
            new_data = pd.DataFrame({
                "tanggal": [waktu_komplit],
                "pemasukan": [pemasukan],
                "pengeluaran": [pengeluaran],
                "kategori": [kategori if pengeluaran > 0 else "-"]
            })
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(user_csv_path, index=False)
            simpan_ke_github(df, f"data/{st.session_state.username}/data.csv")
            st.success("Data berhasil ditambahkan!")
            st.experimental_rerun()

# Filter Data
st.sidebar.header("Filter")
start = st.sidebar.date_input("Dari", value=dt.date.today() - dt.timedelta(days=30))
end = st.sidebar.date_input("Sampai", value=dt.date.today())
kategori_filter = st.sidebar.multiselect("Kategori", options=sorted(df["kategori"].unique()))

if start and end:
    df = df[(df["tanggal"] >= pd.to_datetime(start)) & (df["tanggal"] <= pd.to_datetime(end))]
if kategori_filter:
    df = df[df["kategori"].isin(kategori_filter)]

# Analisis dan Visualisasi
df["tanggal"] = pd.to_datetime(df["tanggal"])
df["pemasukan"] = pd.to_numeric(df["pemasukan"], errors="coerce").fillna(0)
df["pengeluaran"] = pd.to_numeric(df["pengeluaran"], errors="coerce").fillna(0)
df = df.sort_values("tanggal")
df["saldo"] = df["pemasukan"].cumsum() - df["pengeluaran"].cumsum()

st.metric("💰 Total Saldo", f"Rp {df['saldo'].iloc[-1]:,.0f}" if not df.empty else "Rp 0")
st.metric("📈 Total Pemasukan", f"Rp {df['pemasukan'].sum():,.0f}")
st.metric("📉 Total Pengeluaran", f"Rp {df['pengeluaran'].sum():,.0f}")

# Grafik Saldo
st.subheader("📊 Grafik Saldo")
periode = st.selectbox("Periode Grafik", ["Harian", "Mingguan", "Bulanan", "Tahunan"])
resample_map = {"Harian": "D", "Mingguan": "W", "Bulanan": "M", "Tahunan": "Y"}
df.set_index("tanggal", inplace=True)
df_grouped = df.resample(resample_map[periode]).sum(numeric_only=True)
df_grouped["saldo"] = df_grouped["pemasukan"].cumsum() - df_grouped["pengeluaran"].cumsum()

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df_grouped.index, df_grouped["saldo"], label="Saldo", color="blue")
ax.set_title("Perkembangan Saldo")
ax.set_ylabel("Saldo (Rp)")
ax.grid(True)
st.pyplot(fig)

# Pie Chart
st.subheader("📌 Persentase Pengeluaran per Kategori")
kategori_pengeluaran = df[df["pengeluaran"] > 0].groupby("kategori")["pengeluaran"].sum()
if not kategori_pengeluaran.empty:
    fig2, ax2 = plt.subplots()
    ax2.pie(kategori_pengeluaran, labels=kategori_pengeluaran.index, autopct="%1.1f%%", colors=["#%06x" % random.randint(0, 0xFFFFFF) for _ in range(len(kategori_pengeluaran))])
    ax2.axis("equal")
    st.pyplot(fig2)

    for k, v in kategori_pengeluaran.items():
        st.write(f"🔹 {k}: Rp {v:,.0f}")
else:
    st.info("Belum ada data pengeluaran.")

# Tabel
st.subheader("📋 Riwayat Transaksi")
st.dataframe(df.reset_index().sort_values("tanggal", ascending=False))

# Export
st.download_button("📥 Unduh CSV", data=df.reset_index().to_csv(index=False).encode(), file_name="riwayat_keuangan.csv", mime="text/csv")

# Footer
st.markdown("""
---
Made by Dafiq | Powered by Machine Learning  
📧 [Email](mailto:dafiqelhaq11@gmail.com) | 📱 [WhatsApp](https://wa.me/6281224280846) | 📸 [Instagram](https://instagram.com/dafiqelhaq)
""")
