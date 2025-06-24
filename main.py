# main.py (Versi Lengkap - Stabil, Aman, dan Fitur Tambahan)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import random
import os
import base64
import json
import requests
from io import BytesIO

st.set_page_config(page_title="Finance Tracker", page_icon="💰", layout="wide")
st.title("💰 Finance Tracker")

# --- GitHub Save Function ---
def simpan_ke_github(dataframe, filepath):
    csv_content = dataframe.to_csv(index=False, encoding="utf-8-sig")
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

# --- USER LOGIN ---
st.sidebar.header("🔐 Login Pengguna")
if "username" not in st.session_state:
    st.session_state.username = ""

username = st.sidebar.text_input("Masukkan Username")
password = st.sidebar.text_input("Password", type="password")
login = st.sidebar.button("Login")

if login:
    if username and password:  # Simple validation only
        st.session_state.username = username
    else:
        st.sidebar.error("Username dan Password wajib diisi")

if not st.session_state.username:
    st.stop()

user_folder = f"data/{st.session_state.username}"
os.makedirs(user_folder, exist_ok=True)
user_csv_path = os.path.join(user_folder, "data.csv")

if os.path.exists(user_csv_path):
    df = pd.read_csv(user_csv_path, encoding="utf-8-sig")
else:
    df = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

# --- Input Data ---
st.markdown("## ➕ Tambah Data Baru")
with st.expander("Input Data Manual"):
    with st.form("input_data"):
        tanggal = st.date_input("🗕️ Tanggal", dt.date.today())
        pemasukan = st.number_input("⬆️ Pemasukan (Rp)", min_value=0)
        pengeluaran = st.number_input("⬇️ Pengeluaran (Rp)", min_value=0)
        kategori = st.text_input("🏷️ Kategori", value="Umum")
        submit = st.form_submit_button("💾 Simpan")

        if submit:
            new_row = pd.DataFrame({
                "tanggal": [str(tanggal)],
                "pemasukan": [pemasukan],
                "pengeluaran": [pengeluaran],
                "kategori": [kategori if pengeluaran > 0 else "-"]
            })
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(user_csv_path, index=False, encoding="utf-8-sig")
            simpan_ke_github(df, f"data/{st.session_state.username}/data.csv")
            st.success("✅ Data berhasil ditambahkan!")

# --- Proses Data ---
df = df.dropna(subset=["tanggal"])
df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")
df = df.dropna(subset=["tanggal"])
df = df.sort_values("tanggal")
df["pemasukan"] = pd.to_numeric(df["pemasukan"], errors="coerce").fillna(0)
df["pengeluaran"] = pd.to_numeric(df["pengeluaran"], errors="coerce").fillna(0)
df["saldo"] = df["pemasukan"].cumsum() - df["pengeluaran"].cumsum()

# --- Filter Data ---
st.sidebar.header("📆 Filter Data")
tgl_awal = st.sidebar.date_input("Tanggal Awal", df["tanggal"].min().date() if not df.empty else dt.date.today())
tgl_akhir = st.sidebar.date_input("Tanggal Akhir", df["tanggal"].max().date() if not df.empty else dt.date.today())
df_filtered = df[(df["tanggal"] >= pd.to_datetime(tgl_awal)) & (df["tanggal"] <= pd.to_datetime(tgl_akhir))]

# --- Ringkasan ---
st.markdown("## 📊 Ringkasan")
if not df_filtered.empty:
    st.metric("💰 Total Saldo", f"Rp {df_filtered['saldo'].iloc[-1]:,.0f}")
    st.metric("📈 Total Pemasukan", f"Rp {df_filtered['pemasukan'].sum():,.0f}")
    st.metric("📉 Total Pengeluaran", f"Rp {df_filtered['pengeluaran'].sum():,.0f}")
else:
    st.warning("Tidak ada data pada rentang tanggal tersebut.")

# --- Grafik Saldo ---
st.markdown("## 🗓️ Grafik Saldo")
periode = st.selectbox("Pilih Periode", ["Harian", "Mingguan", "Bulanan", "Tahunan"])
chart_type = st.radio("Tipe Grafik", ["Line Chart", "Area Chart"], horizontal=True)

resample_map = {"Harian": "D", "Mingguan": "W", "Bulanan": "M", "Tahunan": "Y"}
df_chart = df_filtered.set_index("tanggal").resample(resample_map[periode]).sum(numeric_only=True)
df_chart["saldo"] = df_chart["pemasukan"].cumsum() - df_chart["pengeluaran"].cumsum()

fig, ax = plt.subplots(figsize=(12, 5))
if chart_type == "Line Chart":
    ax.plot(df_chart.index, df_chart["saldo"], linewidth=3, color="blue")
else:
    ax.fill_between(df_chart.index, df_chart["saldo"], color="skyblue", alpha=0.5)
    ax.plot(df_chart.index, df_chart["saldo"], linewidth=3, color="blue")

ax.set_ylabel("Saldo (Rp)")
ax.set_title(f"Perkembangan Saldo - {periode}")
ax.grid(True, linestyle="--", alpha=0.5)
st.pyplot(fig)

# --- Pie Chart Pengeluaran ---
st.markdown("## 🡝 Persentase Pengeluaran per Kategori")
df_expense = df_filtered[df_filtered["pengeluaran"] > 0]
if not df_expense.empty:
    kategori_data = df_expense.groupby("kategori")["pengeluaran"].sum()
    warna = ["#%06x" % random.randint(0, 0xFFFFFF) for _ in kategori_data]
    fig2, ax2 = plt.subplots()
    wedges, texts, autotexts = ax2.pie(kategori_data, labels=kategori_data.index,
                                       autopct="%1.1f%%", colors=warna, startangle=90)
    for autotext in autotexts:
        autotext.set_color("white")
    ax2.axis("equal")
    st.pyplot(fig2)
    st.markdown("### 💡 Detail Kategori")
    for kategori, nominal in kategori_data.items():
        st.write(f"🔹 {kategori}: Rp {nominal:,.0f}")

# --- History & Edit ---
with st.expander("📄 Lihat Riwayat Transaksi"):
    st.dataframe(df_filtered.sort_values("tanggal", ascending=False))
    if st.button("✏️ Edit / Hapus Transaksi"):
        idx_list = list(df_filtered.index)
        selected_index = st.selectbox("Pilih Index", idx_list)
        selected_row = df_filtered.loc[selected_index]

        with st.form("edit_form"):
            new_tanggal = st.date_input("Tanggal", selected_row["tanggal"].date())
            new_pemasukan = st.number_input("Pemasukan", value=int(selected_row["pemasukan"]))
            new_pengeluaran = st.number_input("Pengeluaran", value=int(selected_row["pengeluaran"]))
            new_kategori = st.text_input("Kategori", value=selected_row["kategori"])
            simpan = st.form_submit_button("💾 Simpan")
            hapus = st.form_submit_button("🗑️ Hapus")

            if simpan:
                df.at[selected_index, "tanggal"] = str(new_tanggal)
                df.at[selected_index, "pemasukan"] = new_pemasukan
                df.at[selected_index, "pengeluaran"] = new_pengeluaran
                df.at[selected_index, "kategori"] = new_kategori
                df.to_csv(user_csv_path, index=False, encoding="utf-8-sig")
                simpan_ke_github(df, f"data/{st.session_state.username}/data.csv")
                st.success("✅ Data berhasil diperbarui!")

            if hapus:
                df = df.drop(index=selected_index).reset_index(drop=True)
                df.to_csv(user_csv_path, index=False, encoding="utf-8-sig")
                simpan_ke_github(df, f"data/{st.session_state.username}/data.csv")
                st.success("🗑️ Data berhasil dihapus!")

# --- Export ke Excel ---
st.markdown("## 📥 Unduh Data")
if st.button("⬇️ Unduh sebagai Excel"):
    output = BytesIO()
    df.to_excel(output, index=False, engine="xlsxwriter")
    st.download_button("📥 Klik untuk Unduh", data=output.getvalue(), file_name="finance_data.xlsx")

# --- Footer ---
st.markdown("""
---
Made by Dafiq | Powered by Machine Learning  
[📱 WhatsApp](https://wa.me/6281224280846) | [📧 Email](mailto:dafiqelhaq11@gmail.com) | [📷 Instagram](https://instagram.com/dafiqelhaq)
""")
