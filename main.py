import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import os
import base64
import json
import requests

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Finance Tracker", page_icon="💰")
st.title("💰 Aplikasi Analisis Keuangan Harian")

# --- Fungsi Simpan ke GitHub ---
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

# --- Login/Register ---
if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.username:
    st.markdown("### 🔐 Masuk untuk Melanjutkan")
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user_path = f"data/{username}/data.csv"
            if os.path.exists(user_path):
                st.session_state.username = username
            else:
                st.error("User tidak ditemukan. Silakan register terlebih dahulu.")

    with tab2:
        new_user = st.text_input("Buat Username Baru")
        if st.button("Register") and new_user:
            folder_path = f"data/{new_user}"
            os.makedirs(folder_path, exist_ok=True)
            pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"]).to_csv(os.path.join(folder_path, "data.csv"), index=False)
            st.success("Berhasil daftar! Silakan login.")

    st.stop()

user_folder = f"data/{st.session_state.username}"
os.makedirs(user_folder, exist_ok=True)
user_csv_path = os.path.join(user_folder, "data.csv")

if os.path.exists(user_csv_path):
    df = pd.read_csv(user_csv_path, parse_dates=["tanggal"])
else:
    df = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

# --- Input Data ---
st.markdown("## ➕ Input Data Keuangan")
with st.form("input_form"):
    tanggal = st.date_input("Tanggal", value=dt.date.today())
    waktu = st.time_input("Waktu", value=dt.datetime.now().time())
    pemasukan = st.number_input("Pemasukan (Rp)", min_value=0, step=50000)
    pengeluaran = st.number_input("Pengeluaran (Rp)", min_value=0, step=50000)
    kategori = st.text_input("Kategori", value="Umum")
    submit = st.form_submit_button("Simpan")

    if submit:
        waktu_lengkap = dt.datetime.combine(tanggal, waktu)
        df = pd.concat([df, pd.DataFrame.from_records([{
            "tanggal": waktu_lengkap,
            "pemasukan": pemasukan,
            "pengeluaran": pengeluaran,
            "kategori": kategori if pengeluaran > 0 else "-"
        }])], ignore_index=True)
        df.to_csv(user_csv_path, index=False)
        simpan_ke_github(df, f"data/{st.session_state.username}/data.csv")
        st.experimental_rerun()

# --- Ringkasan ---
df = df.sort_values("tanggal")
df["saldo"] = df["pemasukan"].cumsum() - df["pengeluaran"].cumsum()

st.metric("💰 Saldo", f"Rp {df['saldo'].iloc[-1]:,.0f}" if not df.empty else "Rp 0")
st.metric("📈 Total Pemasukan", f"Rp {df['pemasukan'].sum():,.0f}")
st.metric("📉 Total Pengeluaran", f"Rp {df['pengeluaran'].sum():,.0f}")

# --- Grafik Saldo ---
st.markdown("## 📈 Grafik Saldo")
fig, ax = plt.subplots()
ax.plot(df["tanggal"], df["saldo"], color="blue")
ax.set_title("Perkembangan Saldo")
ax.set_ylabel("Saldo (Rp)")
ax.grid(True)
st.pyplot(fig)

# --- Pie Chart ---
if not df[df["pengeluaran"] > 0].empty:
    st.markdown("## 📊 Persentase Pengeluaran per Kategori")
    kategori_pengeluaran = df[df["pengeluaran"] > 0].groupby("kategori")["pengeluaran"].sum()
    warna = ["#%06x" % random.randint(0, 0xFFFFFF) for _ in range(len(kategori_pengeluaran))]
    fig2, ax2 = plt.subplots()
    ax2.pie(kategori_pengeluaran, labels=kategori_pengeluaran.index, autopct="%1.1f%%", colors=warna)
    ax2.axis("equal")
    st.pyplot(fig2)
    for k, v in kategori_pengeluaran.items():
        st.write(f"🔹 {k}: Rp {v:,.0f}")

# --- Dataframe ---
st.markdown("---")
st.markdown("### 📋 Histori Keuangan")
st.dataframe(df.sort_values("tanggal", ascending=False))

# --- Footer ---
st.markdown("""
---
Made by [Dafiq](https://instagram.com/dafiqelhaq) | Powered by Machine Learning  
📧 [Email](mailto:dafiqelhaq11@gmail.com) | 📱 [WhatsApp](https://wa.me/6281224280846)
""")
