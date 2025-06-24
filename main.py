main.py (Final Chart Fix)

import streamlit as st import pandas as pd import matplotlib.pyplot as plt import datetime as dt import random import os import base64 import json import requests

st.set_page_config(page_title="Finance Tracker", page_icon="💰") st.title("💰 Finance Tracker")

--- GitHub Save Function ---

def simpan_ke_github(dataframe, filepath): csv_content = dataframe.to_csv(index=False) token = st.secrets["github_token"] owner = st.secrets["repo_owner"] repo = st.secrets["repo_name"]

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
        st.success("✅ Data berhasil ditambahkan!")

--- Hitung Saldo ---

df = df.dropna(subset=["tanggal"]) df["tanggal"] = pd.to_datetime(df["tanggal"]) df["pemasukan"] = pd.to_numeric(df["pemasukan"], errors="coerce").fillna(0) df["pengeluaran"] = pd.to_numeric(df["pengeluaran"], errors="coerce").fillna(0) df = df.sort_values("tanggal") df["saldo"] = df["pemasukan"].cumsum() - df["pengeluaran"].cumsum()

--- Ringkasan ---

st.markdown("## 📊 Ringkasan") total_pemasukan = df["pemasukan"].sum() total_pengeluaran = df["pengeluaran"].sum() total_saldo = total_pemasukan - total_pengeluaran st.metric("💰 Total Saldo", f"Rp {total_saldo:,.0f}") st.metric("📈 Total Pemasukan", f"Rp {total_pemasukan:,.0f}") st.metric("📉 Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")

--- Pilih Periode & Chart ---

st.markdown("## 📅 Grafik Saldo") periode = st.selectbox("Pilih Periode", ["Harian", "Mingguan", "Bulanan", "Tahunan"]) chart_type = st.radio("Tipe Grafik", ["Line Chart", "Area Chart"])

resample_map = {"Harian": "D", "Mingguan": "W", "Bulanan": "M", "Tahunan": "Y"} df_chart = df.copy() df_chart = df_chart.sort_values("tanggal") df_chart.set_index("tanggal", inplace=True) df_chart = df_chart.resample(resample_map[periode]).sum(numeric_only=True) df_chart["saldo"] = df_chart["pemasukan"].cumsum() - df_chart["pengeluaran"].cumsum()

fig, ax = plt.subplots(figsize=(12, 5)) if chart_type == "Line Chart": ax.plot(df_chart.index, df_chart["saldo"], color="blue", linewidth=2.5) else: ax.fill_between(df_chart.index, df_chart["saldo"], color='skyblue', alpha=0.4) ax.plot(df_chart.index, df_chart["saldo"], color="blue", linewidth=2.5)

ax.set_ylabel("Saldo (Rp)") ax.set_title(f"Perkembangan Saldo - {periode}") ax.grid(True, linestyle="--", alpha=0.6) fig.autofmt_xdate() st.pyplot(fig)

--- Pie Chart ---

st.markdown("## 🧁 Persentase Pengeluaran per Kategori") if not df[df["pengeluaran"] > 0].empty: kategori_data = df[df["pengeluaran"] > 0].groupby("kategori")["pengeluaran"].sum() warna = ["#%06x" % random.randint(0, 0xFFFFFF) for _ in kategori_data] fig2, ax2 = plt.subplots() ax2.pie(kategori_data, labels=kategori_data.index, autopct="%1.1f%%", startangle=90, colors=warna) ax2.axis("equal") st.pyplot(fig2) st.markdown("### 💡 Detail Kategori") for kategori, nominal in kategori_data.items(): st.write(f"🔹 {kategori}: Rp {nominal:,.0f}")

--- Tabel & Unduh ---

with st.expander("📄 Lihat Data Lengkap"): st.dataframe(df.sort_values("tanggal", ascending=False))

st.download_button("📥 Unduh CSV", df.to_csv(index=False).encode(), "keuangan.csv")

--- Footer ---

st.markdown("""

Made by Dafiq | Powered by Machine Learning
📱 WhatsApp | 📧 Email | 📷 Instagram
""")

