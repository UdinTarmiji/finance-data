#main.py (Final Chart Fix)

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
st.title("💰 Finance Tracker")

#--- GitHub Save Function ---

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

--- USERNAME LOGIN ---

st.sidebar.header("🔐 Login Pengguna") if "username" not in st.session_state: st.session_state.username = ""

username = st.sidebar.text_input("Masukkan Username") if username: st.session_state.username = username else: st.stop()

user_folder = f"data/{st.session_state.username}" os.makedirs(user_folder, exist_ok=True) user_csv_path = os.path.join(user_folder, "data.csv")

if os.path.exists(user_csv_path): df = pd.read_csv(user_csv_path, parse_dates=["tanggal"]) else: df = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

--- Input Data ---

st.markdown("## ➕ Tambah Data Baru") with st.expander("Input Data Manual"): with st.form("input_data"): tanggal = st.date_input("📅 Tanggal", dt.date.today()) pemasukan = st.number_input("⬆️ Pemasukan (Rp)", min_value=0) pengeluaran = st.number_input("⬇️ Pengeluaran (Rp)", min_value=0) kategori = st.text_input("🏷️ Kategori", value="Umum") submit = st.form_submit_button("💾 Simpan")

if submit:
        new_row = pd.DataFrame({
            "tanggal": [tanggal],
            "pemasukan": [pemasukan],
            "pengeluaran": [pengeluaran],
            "kategori": [kategori if pengeluaran > 0 else "-"]
        })
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(user_csv_path, index=False)
        simpan_ke_github(df, f"data/{st.session_state.username}/data.csv")
# main.py (Final Version - Stable & Complete)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import random
import os
import base64
import json
import requests

# --- CONFIG ---
st.set_page_config(page_title="Finance Tracker", page_icon="💰")
st.title("💰 Finance Tracker")

# --- GITHUB SAVE FUNCTION ---
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

# --- LOGIN USERNAME ---
st.sidebar.header("🔐 Login Pengguna")
username = st.sidebar.text_input("Masukkan Username")
if username:
    st.session_state.username = username
else:
    st.stop()

# --- PATH FILE USER ---
user_folder = f"data/{username}"
os.makedirs(user_folder, exist_ok=True)
user_csv_path = os.path.join(user_folder, "data.csv")

# --- LOAD DATA ---
if os.path.exists(user_csv_path):
    df = pd.read_csv(user_csv_path, parse_dates=["tanggal"], dayfirst=True)
else:
    df = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

# --- INPUT DATA ---
st.markdown("## ➕ Tambah Data Baru")
with st.expander("Input Data Manual"):
    with st.form("input_data"):
        tanggal = st.date_input("📅 Tanggal", dt.date.today())
        pemasukan = st.number_input("⬆️ Pemasukan (Rp)", min_value=0)
        pengeluaran = st.number_input("⬇️ Pengeluaran (Rp)", min_value=0)
        kategori = st.text_input("🏷️ Kategori", value="Umum")
        submit = st.form_submit_button("💾 Simpan")

        if submit:
            new_row = pd.DataFrame({
                "tanggal": [tanggal],
                "pemasukan": [pemasukan],
                "pengeluaran": [pengeluaran],
                "kategori": [kategori if pengeluaran > 0 else "-"]
            })
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(user_csv_path, index=False)
            simpan_ke_github(df, f"data/{username}/data.csv")
            st.success("✅ Data berhasil ditambahkan!")

# --- PREPROCESSING ---
df = df.dropna(subset=["tanggal"])
df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")
df["pemasukan"] = pd.to_numeric(df["pemasukan"], errors="coerce").fillna(0)
df["pengeluaran"] = pd.to_numeric(df["pengeluaran"], errors="coerce").fillna(0)
df = df.sort_values("tanggal")
df["saldo"] = df["pemasukan"].cumsum() - df["pengeluaran"].cumsum()

# --- RINGKASAN ---
st.markdown("## 📊 Ringkasan")
st.metric("💰 Total Saldo", f"Rp {df['saldo'].iloc[-1] if not df.empty else 0:,.0f}")
st.metric("📈 Total Pemasukan", f"Rp {df['pemasukan'].sum():,.0f}")
st.metric("📉 Total Pengeluaran", f"Rp {df['pengeluaran'].sum():,.0f}")

# --- CHART ---
st.markdown("## 📅 Grafik Saldo")
periode = st.selectbox("Pilih Periode", ["Harian", "Mingguan", "Bulanan", "Tahunan"])
chart_type = st.radio("Tipe Grafik", ["Line Chart", "Area Chart"])

resample_map = {"Harian": "D", "Mingguan": "W", "Bulanan": "M", "Tahunan": "Y"}
df_chart = df.set_index("tanggal").resample(resample_map[periode]).sum(numeric_only=True)
df_chart["saldo"] = df_chart["pemasukan"].cumsum() - df_chart["pengeluaran"].cumsum()

if not df_chart.empty and df_chart["saldo"].notnull().any():
    fig, ax = plt.subplots(figsize=(10, 4))
    if chart_type == "Line Chart":
        ax.plot(df_chart.index, df_chart["saldo"], color="blue", linewidth=2)
    else:
        ax.fill_between(df_chart.index, df_chart["saldo"], color="skyblue", alpha=0.5)
        ax.plot(df_chart.index, df_chart["saldo"], color="blue", linewidth=1.5)
    ax.set_ylabel("Saldo (Rp)")
    ax.set_title(f"Perkembangan Saldo - {periode}")
    ax.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig)
else:
    st.warning("Tidak ada data yang cukup untuk ditampilkan sebagai grafik.")

# --- PIE CHART ---
st.markdown("## 🧁 Persentase Pengeluaran per Kategori")
if not df[df["pengeluaran"] > 0].empty:
    kategori_data = df[df["pengeluaran"] > 0].groupby("kategori")["pengeluaran"].sum()
    warna = ["#%06x" % random.randint(0, 0xFFFFFF) for _ in kategori_data]
    fig2, ax2 = plt.subplots()
    ax2.pie(kategori_data, labels=kategori_data.index, autopct="%1.1f%%", startangle=90, colors=warna)
    ax2.axis("equal")
    st.pyplot(fig2)
    st.markdown("### 💡 Detail Kategori")
    for kategori, nominal in kategori_data.items():
        st.write(f"🔹 {kategori}: Rp {nominal:,.0f}")

# --- HISTORY ---
with st.expander("📄 Lihat Data & Edit/Hapus"):
    st.dataframe(df.sort_values("tanggal", ascending=False))

    if st.button("✏️ Edit / Hapus Transaksi"):
        idx_list = list(df.index)
        selected_index = st.selectbox("Pilih Index Transaksi", idx_list)
        selected_row = df.loc[selected_index]

        with st.form("edit_form"):
            new_tanggal = st.date_input("Tanggal", selected_row["tanggal"].date())
            new_pemasukan = st.number_input("Pemasukan", value=int(selected_row["pemasukan"]))
            new_pengeluaran = st.number_input("Pengeluaran", value=int(selected_row["pengeluaran"]))
            new_kategori = st.text_input("Kategori", value=selected_row["kategori"])
            save = st.form_submit_button("💾 Simpan Perubahan")
            delete = st.form_submit_button("🗑️ Hapus")

            if save:
                df.at[selected_index, "tanggal"] = new_tanggal
                df.at[selected_index, "pemasukan"] = new_pemasukan
                df.at[selected_index, "pengeluaran"] = new_pengeluaran
                df.at[selected_index, "kategori"] = new_kategori
                df.to_csv(user_csv_path, index=False)
                simpan_ke_github(df, f"data/{username}/data.csv")
                st.success("✅ Data berhasil diperbarui!")

            if delete:
                df = df.drop(index=selected_index).reset_index(drop=True)
                df.to_csv(user_csv_path, index=False)
                simpan_ke_github(df, f"data/{username}/data.csv")
                st.success("🗑️ Data berhasil dihapus!")

# --- DOWNLOAD ---
st.download_button("📥 Unduh CSV", df.to_csv(index=False).encode(), "keuangan.csv")

# --- FOOTER ---
st.markdown("""
---
Made by Dafiq | Powered by Machine Learning  
[📱 WhatsApp](https://wa.me/6281224280846) | [📧 Email](mailto:dafiqelhaq11@gmail.com) | [📷 Instagram](https://instagram.com/dafiqelhaq)
""")

