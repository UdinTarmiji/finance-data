import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import random
import os
import base64
import json
import requests

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Finance Tracker", page_icon="💰")
st.title("💰 Finance Tracker")

# --- Fungsi Simpan ke GitHub ---
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

# --- Login dengan Username ---
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.username:
    st.session_state.username = st.text_input("Masukkan Username untuk Memulai:")
    if not st.session_state.username:
        st.stop()

user_folder = f"data/{st.session_state.username}"
os.makedirs(user_folder, exist_ok=True)
user_csv_path = os.path.join(user_folder, "data.csv")

# --- Load Data CSV ---
if os.path.exists(user_csv_path):
    df = pd.read_csv(user_csv_path, parse_dates=["tanggal"])
else:
    df = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

# --- Input Data Manual ---
st.markdown("## ➕ Input Data Keuangan")
with st.form("form_input", clear_on_submit=True):
    tanggal = st.date_input("🗓️ Tanggal", dt.date.today())
    waktu = st.time_input("🕒 Waktu", dt.datetime.now().time())
    pemasukan = st.number_input("📥 Pemasukan (Rp)", min_value=0, step=50000)
    pengeluaran = st.number_input("📤 Pengeluaran (Rp)", min_value=0, step=50000)
    kategori = st.text_input("🏷️ Kategori", value="Umum")
    submit = st.form_submit_button("✅ Simpan")

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

# --- Konversi dan Perhitungan ---
df["tanggal"] = pd.to_datetime(df["tanggal"])
df = df.sort_values("tanggal")
df["pemasukan"] = pd.to_numeric(df["pemasukan"], errors="coerce").fillna(0)
df["pengeluaran"] = pd.to_numeric(df["pengeluaran"], errors="coerce").fillna(0)
df["saldo"] = df["pemasukan"].cumsum() - df["pengeluaran"].cumsum()

# --- Ringkasan Keuangan ---
st.markdown("---")
st.metric("💰 Total Saldo", f"Rp {df['saldo'].iloc[-1]:,.0f}" if not df.empty else "Rp 0")
st.metric("📈 Total Pemasukan", f"Rp {df['pemasukan'].sum():,.0f}")
st.metric("📉 Total Pengeluaran", f"Rp {df['pengeluaran'].sum():,.0f}")

# --- Grafik Saldo Akumulatif ---
st.subheader("📈 Grafik Saldo")
periode = st.selectbox("Pilih Periode", ["Harian", "Mingguan", "Bulanan", "Tahunan"])
tipe_grafik = st.radio("Tipe Grafik", ["Area", "Line"])

if not df.empty:
    df.set_index("tanggal", inplace=True)
    rule = {"Harian": "D", "Mingguan": "W", "Bulanan": "M", "Tahunan": "Y"}[periode]
    df_grouped = df.resample(rule).sum(numeric_only=True)
    df_grouped["saldo"] = df_grouped["pemasukan"].cumsum() - df_grouped["pengeluaran"].cumsum()

    fig, ax = plt.subplots(figsize=(10, 4))
    if tipe_grafik == "Area":
        ax.fill_between(df_grouped.index, df_grouped["saldo"], color="skyblue", alpha=0.5)
    ax.plot(df_grouped.index, df_grouped["saldo"], color="blue")
    ax.set_title(f"Saldo Akumulatif ({periode})")
    ax.set_ylabel("Saldo (Rp)")
    ax.grid(True)
    st.pyplot(fig)

    df.reset_index(inplace=True)

# --- Pie Chart Kategori ---
st.subheader("📊 Distribusi Pengeluaran")
kategori_data = df[df["pengeluaran"] > 0].groupby("kategori")["pengeluaran"].sum()
if not kategori_data.empty:
    fig2, ax2 = plt.subplots()
    colors = ["#%06x" % random.randint(0, 0xFFFFFF) for _ in kategori_data]
    ax2.pie(kategori_data, labels=kategori_data.index, autopct="%1.1f%%", colors=colors, startangle=90)
    ax2.axis("equal")
    st.pyplot(fig2)

    st.markdown("### 📋 Rincian Pengeluaran per Kategori")
    for kategori, total in kategori_data.items():
        st.write(f"🔹 **{kategori}**: Rp {total:,.0f}")

# --- Dataframe ---
with st.expander("📄 Lihat Data Lengkap"):
    st.dataframe(df.sort_values("tanggal", ascending=False))

# --- Footer ---
st.markdown("""
---
Made by [Dafiq](https://instagram.com/dafiqelhaq) | Powered by Machine Learning  
📧 [Email](mailto:dafiqelhaq11@gmail.com) | 📱 [WhatsApp](https://wa.me/6281224280846)
""")
