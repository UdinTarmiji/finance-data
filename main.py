import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import random
import os
import base64
import json
import requests

st.set_page_config(page_title="Finance Tracker", page_icon="💰")
st.title("💰 Aplikasi Analisis Keuangan Harian")

# --- GitHub Save Function ---
def simpan_ke_github(dataframe, filepath):
    csv_content = dataframe.to_csv(index=False)
    token = st.secrets["github_token"]
    owner = st.secrets["repo_owner"]
    repo = st.secrets["repo_name"]

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filepath}"
    headers = {"Authorization": f"token {token}"}
    get_resp = requests.get(url, headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

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

# --- USER LOGIN / REGISTER ---
if "username" not in st.session_state:
    st.session_state.username = ""
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_option = st.radio("Login/Register", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Masuk")

    if login_button and username and password:
        st.session_state.username = username
        st.session_state.logged_in = True
        st.experimental_rerun()
    st.stop()

# --- User Path Setup ---
user_folder = f"data/{st.session_state.username}"
os.makedirs(user_folder, exist_ok=True)
user_csv_path = os.path.join(user_folder, "data.csv")

# --- Load Data ---
if os.path.exists(user_csv_path):
    df_manual = pd.read_csv(user_csv_path, parse_dates=["tanggal"])
else:
    df_manual = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

# --- Input Manual ---
st.markdown("## ➕ Input Data Keuangan Manual")
with st.expander("📝 Tambah Data Keuangan"):
    tanggal = st.date_input("Tanggal", dt.date.today())
    waktu = st.time_input("Waktu", dt.datetime.now().time())
    pemasukan = st.number_input("Pemasukan (Rp)", min_value=0, step=50000)
    pengeluaran = st.number_input("Pengeluaran (Rp)", min_value=0, step=50000)
    kategori = st.text_input("Kategori Pengeluaran", value="Umum")
    simpan = st.button("✅ Simpan")
    if simpan:
        waktu_komplit = dt.datetime.combine(tanggal, waktu)
        new_data = pd.DataFrame({
            "tanggal": [waktu_komplit],
            "pemasukan": [pemasukan],
            "pengeluaran": [pengeluaran],
            "kategori": [kategori if pengeluaran > 0 else "-"]
        })
        df_manual = pd.concat([df_manual, new_data], ignore_index=True)
        df_manual.to_csv(user_csv_path, index=False)
        simpan_ke_github(df_manual, f"data/{st.session_state.username}/data.csv")
        st.success("✅ Data berhasil ditambahkan!")
        st.experimental_rerun()

# --- Filter Sidebar ---
df = df_manual.copy()
df["tanggal"] = pd.to_datetime(df["tanggal"])
df = df.sort_values("tanggal")

st.sidebar.header("🔍 Filter Data")
start = st.sidebar.date_input("Dari Tanggal", dt.date.today() - dt.timedelta(days=30))
end = st.sidebar.date_input("Sampai Tanggal", dt.date.today())
kategori_filter = st.sidebar.multiselect("Kategori", df["kategori"].unique())

if kategori_filter:
    df = df[df["kategori"].isin(kategori_filter)]
df = df[(df["tanggal"] >= pd.to_datetime(start)) & (df["tanggal"] <= pd.to_datetime(end))]

if df.empty:
    st.warning("Tidak ada data ditemukan!")
    st.stop()

# --- Analisis ---
df["saldo"] = df["pemasukan"].cumsum() - df["pengeluaran"].cumsum()
total_pemasukan = df["pemasukan"].sum()
total_pengeluaran = df["pengeluaran"].sum()
total_saldo = total_pemasukan - total_pengeluaran

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Saldo", f"Rp {total_saldo:,.0f}")
col2.metric("📈 Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
col3.metric("📉 Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")

# --- Grafik Saldo ---
st.markdown("### 📊 Grafik Saldo")
periode = st.selectbox("Periode", ["Harian", "Mingguan", "Bulanan", "Tahunan"])
mode = st.radio("Tipe Grafik", ["Line", "Area"])

df = df.set_index("tanggal")
if periode == "Harian":
    grouped = df.resample("D").sum()
elif periode == "Mingguan":
    grouped = df.resample("W").sum()
elif periode == "Bulanan":
    grouped = df.resample("M").sum()
else:
    grouped = df.resample("Y").sum()

grouped["saldo"] = grouped["pemasukan"].cumsum() - grouped["pengeluaran"].cumsum()

fig, ax = plt.subplots()
if mode == "Area":
    ax.fill_between(grouped.index, grouped["saldo"], alpha=0.4, color="skyblue")
ax.plot(grouped.index, grouped["saldo"], marker='o', color="green")
ax.set_ylabel("Saldo (Rp)")
ax.grid(True)
ax.set_title(f"Grafik Saldo {periode}")
st.pyplot(fig)

# --- Pie Chart ---
if not df[df["pengeluaran"] > 0].empty:
    st.markdown("### 📊 Distribusi Pengeluaran")
    kategori_sum = df[df["pengeluaran"] > 0].groupby("kategori")["pengeluaran"].sum()
    colors = ["#%06x" % random.randint(0, 0xFFFFFF) for _ in range(len(kategori_sum))]
    fig2, ax2 = plt.subplots()
    ax2.pie(kategori_sum, labels=kategori_sum.index, autopct="%1.1f%%", startangle=90, colors=colors)
    ax2.axis("equal")
    st.pyplot(fig2)
    st.markdown("#### Rincian Pengeluaran:")
    for k, v in kategori_sum.items():
        st.write(f"🔹 {k}: Rp {v:,.0f}")

# --- Tabel Data ---
st.markdown("### 📋 History Data")
st.dataframe(df.reset_index().sort_values("tanggal", ascending=False))

# --- Download ---
st.download_button("📥 Unduh CSV", df.reset_index().to_csv(index=False), file_name="keuangan.csv")

# --- Footer ---
st.markdown("""
---
Made by [Dafiq](https://instagram.com/dafiqelhaq) | Powered by Machine Learning  
📧 [Email](mailto:dafiqelhaq11@gmail.com) | [WhatsApp](https://wa.me/6281224280846)
""")
