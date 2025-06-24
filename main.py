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

# --- USERNAME LOGIN PAGE ---
if "username" not in st.session_state:
    st.session_state.username = ""
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    mode = st.radio("Pilih Mode:", ["Login", "Register"])
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    if st.button("Login/Register"):
        st.session_state.username = username_input
        st.session_state.logged_in = True
        st.rerun()
    st.stop()

# --- User Directory Setup ---
user_folder = f"data/{st.session_state.username}"
os.makedirs(user_folder, exist_ok=True)
user_csv_path = os.path.join(user_folder, "data.csv")

if "manual_data" not in st.session_state:
    if os.path.exists(user_csv_path):
        st.session_state.manual_data = pd.read_csv(user_csv_path, parse_dates=["tanggal"])
    else:
        st.session_state.manual_data = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

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
            simpan_ke_github(st.session_state.manual_data, f"data/{st.session_state.username}/data.csv")
            st.success("✅ Data berhasil ditambahkan!")
            st.session_state.show_form = False

# --- Load and Filter Data ---
if st.session_state.manual_data.empty:
    st.warning("📎 Silakan input data keuangan terlebih dahulu.")
    st.stop()

df = st.session_state.manual_data.copy()
df["tanggal"] = pd.to_datetime(df["tanggal"])
df = df.sort_values("tanggal")
df["saldo"] = df["pemasukan"].cumsum() - df["pengeluaran"].cumsum()

# --- Filters ---
st.sidebar.header("🔍 Filter")
start_date = st.sidebar.date_input("Mulai Tanggal", value=dt.date.today() - dt.timedelta(days=30))
end_date = st.sidebar.date_input("Sampai Tanggal", value=dt.date.today())
kategori_filter = st.sidebar.multiselect("Pilih Kategori", options=sorted(df["kategori"].unique()))

if start_date and end_date:
    df = df[(df["tanggal"] >= pd.to_datetime(start_date)) & (df["tanggal"] <= pd.to_datetime(end_date))]
if kategori_filter:
    df = df[df["kategori"].isin(kategori_filter)]

# --- Summary Metrics ---
total_pemasukan = df["pemasukan"].sum()
total_pengeluaran = df["pengeluaran"].sum()
total_saldo = total_pemasukan - total_pengeluaran

st.metric("💰 Total Saldo", f"Rp {total_saldo:,.0f}")
st.metric("📥 Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
st.metric("📤 Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")

# --- Grafik Saldo Akumulatif ---
st.markdown("## 📊 Grafik Saldo Akumulatif")
periode = st.selectbox("Tampilkan berdasarkan:", ["Harian", "Mingguan", "Bulanan", "Tahunan"])
tipe_grafik = st.radio("Jenis Visualisasi:", ["Gunung (Area Chart)", "Diagram (Line Chart)"])
y_max_option = st.selectbox("Batas Maksimum Y:", ["1Jt (lonjakan 100rb)", "10Jt (lonjakan 500rb)", "100Jt (lonjakan 5jt)", "1M (lonjakan 50jt)", "10M (lonjakan 500jt)"])

df.set_index("tanggal", inplace=True)
if periode == "Harian":
    df_grouped = df.resample("D").sum(numeric_only=True)
elif periode == "Mingguan":
    df_grouped = df.resample("W").sum(numeric_only=True)
elif periode == "Bulanan":
    df_grouped = df.resample("M").sum(numeric_only=True)
else:
    df_grouped = df.resample("Y").sum(numeric_only=True)

df_grouped["saldo"] = df_grouped["pemasukan"].cumsum() - df_grouped["pengeluaran"].cumsum()

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

# --- Pie Chart ---
if "kategori" in df.columns and not df[df["pengeluaran"] > 0].empty:
    st.markdown("## 🥧 Distribusi Pengeluaran per Kategori")
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
    st.dataframe(df.reset_index().sort_values("tanggal", ascending=False))

# --- Unduh Data ---
st.download_button("📤 Unduh CSV", data=df.reset_index().to_csv(index=False).encode(), file_name="keuangan.csv", mime="text/csv")

# --- Footer ---
st.markdown("""
---
Made by [Dafiq](https://instagram.com/dafiqelhaq) | Powered by Machine Learning

[📧 Email](mailto:dafiqelhaq11@gmail.com) | [📱 WhatsApp](https://wa.me/6281224280846)
""")
