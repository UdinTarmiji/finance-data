import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import os
import json
import requests
import base64
import random

st.set_page_config(page_title="Finance Tracker", page_icon="💰")
st.title("💰 Finance Tracker")

# --- GitHub Save Function ---
def simpan_ke_github(df, path):
    csv_data = df.to_csv(index=False)
    token = st.secrets["github_token"]
    owner = st.secrets["repo_owner"]
    repo = st.secrets["repo_name"]

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    get_response = requests.get(url, headers=headers)
    sha = get_response.json().get("sha", None)

    payload = {
        "message": "update data.csv",
        "content": base64.b64encode(csv_data.encode()).decode(),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, headers=headers, data=json.dumps(payload))
    if response.status_code in [200, 201]:
        st.success("✅ Data berhasil disimpan ke GitHub")
    else:
        st.error("❌ Gagal menyimpan ke GitHub")
        st.write(response.json())

# --- USERNAME LOGIN ---
st.sidebar.header("🔐 Login")
username = st.sidebar.text_input("Masukkan Username")
if not username:
    st.stop()

st.session_state.username = username
data_path = f"data/{username}/data.csv"
os.makedirs(os.path.dirname(data_path), exist_ok=True)

# --- Load CSV ---
if os.path.exists(data_path):
    df = pd.read_csv(data_path)
else:
    df = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

# --- Input Data ---
st.markdown("## ➕ Tambah Data Baru")
with st.expander("Input Data Manual"):
    with st.form("form_input"):
        tgl = st.date_input("📅 Tanggal", dt.date.today())
        masuk = st.number_input("⬆️ Pemasukan", min_value=0)
        keluar = st.number_input("⬇️ Pengeluaran", min_value=0)
        kategori = st.text_input("🏷️ Kategori", value="Umum")
        submit = st.form_submit_button("💾 Simpan")

        if submit:
            new_data = pd.DataFrame({
                "tanggal": [tgl.strftime("%Y-%m-%d")],
                "pemasukan": [masuk],
                "pengeluaran": [keluar],
                "kategori": [kategori if keluar > 0 else "-"]
            })
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(data_path, index=False)
            simpan_ke_github(df, data_path)
            st.success("✅ Data berhasil ditambahkan")

# --- Preprocessing Data ---
df["tanggal"] = pd.to_datetime(df["tanggal"].astype(str), errors="coerce")
df = df.dropna(subset=["tanggal"])
df = df.sort_values("tanggal")
df["pemasukan"] = pd.to_numeric(df["pemasukan"], errors="coerce").fillna(0)
df["pengeluaran"] = pd.to_numeric(df["pengeluaran"], errors="coerce").fillna(0)
df["saldo"] = df["pemasukan"].cumsum() - df["pengeluaran"].cumsum()

# --- Ringkasan ---
st.markdown("## 📊 Ringkasan")
st.metric("💰 Total Saldo", f"Rp {df['saldo'].iloc[-1]:,.0f}" if not df.empty else "Rp 0")
st.metric("📈 Total Pemasukan", f"Rp {df['pemasukan'].sum():,.0f}")
st.metric("📉 Total Pengeluaran", f"Rp {df['pengeluaran'].sum():,.0f}")

# --- Grafik Saldo ---
st.markdown("## 📈 Grafik Saldo")
periode = st.selectbox("Pilih Periode", ["Harian", "Mingguan", "Bulanan", "Tahunan"])
chart_type = st.radio("Tipe Grafik", ["Line Chart", "Area Chart"])

resample_map = {"Harian": "D", "Mingguan": "W", "Bulanan": "M", "Tahunan": "Y"}
df_chart = df.set_index("tanggal").resample(resample_map[periode]).sum(numeric_only=True)
df_chart["saldo"] = df_chart["pemasukan"].cumsum() - df_chart["pengeluaran"].cumsum()

fig, ax = plt.subplots(figsize=(10, 4))
if chart_type == "Line Chart":
    ax.plot(df_chart.index, df_chart["saldo"], color="blue", linewidth=2)
else:
    ax.fill_between(df_chart.index, df_chart["saldo"], color="skyblue", alpha=0.4)
    ax.plot(df_chart.index, df_chart["saldo"], color="blue", linewidth=2)

ax.set_ylabel("Saldo (Rp)")
ax.set_title(f"Perkembangan Saldo - {periode}")
ax.grid(True)
st.pyplot(fig)

# --- Pie Chart ---
st.markdown("## 🧁 Persentase Pengeluaran per Kategori")
df_pengeluaran = df[df["pengeluaran"] > 0]
if not df_pengeluaran.empty:
    kategori_data = df_pengeluaran.groupby("kategori")["pengeluaran"].sum()
    warna = ["#%06x" % random.randint(0, 0xFFFFFF) for _ in kategori_data]
    fig2, ax2 = plt.subplots()
    ax2.pie(kategori_data, labels=kategori_data.index, autopct="%1.1f%%", startangle=90, colors=warna)
    ax2.axis("equal")
    st.pyplot(fig2)

# --- Tabel & Edit Hapus ---
with st.expander("📄 Lihat Data Lengkap"):
    st.dataframe(df[["tanggal", "pemasukan", "pengeluaran", "kategori", "saldo"]])

    if st.button("✏️ Edit / Hapus Transaksi"):
        idx_list = list(df.index)
        selected_idx = st.selectbox("Pilih Index Transaksi", idx_list)

        selected = df.loc[selected_idx]
        st.write("Transaksi Terpilih:", selected)

        with st.form("edit_form"):
            tgl_baru = st.date_input("Tanggal", selected["tanggal"].date())
            masuk_baru = st.number_input("Pemasukan", value=int(selected["pemasukan"]))
            keluar_baru = st.number_input("Pengeluaran", value=int(selected["pengeluaran"]))
            kategori_baru = st.text_input("Kategori", value=selected["kategori"])
            simpan = st.form_submit_button("💾 Simpan Perubahan")
            hapus = st.form_submit_button("🗑️ Hapus")

            if simpan:
                df.at[selected_idx, "tanggal"] = tgl_baru.strftime("%Y-%m-%d")
                df.at[selected_idx, "pemasukan"] = masuk_baru
                df.at[selected_idx, "pengeluaran"] = keluar_baru
                df.at[selected_idx, "kategori"] = kategori_baru
                df.to_csv(data_path, index=False)
                simpan_ke_github(df, data_path)
                st.success("✅ Data berhasil diperbarui")

            if hapus:
                df = df.drop(index=selected_idx).reset_index(drop=True)
                df.to_csv(data_path, index=False)
                simpan_ke_github(df, data_path)
                st.success("🗑️ Data berhasil dihapus")

# --- Unduh CSV ---
st.download_button("📥 Unduh CSV", df.to_csv(index=False).encode(), "keuangan.csv")

# --- Footer ---
st.markdown("""
---
Made by Dafiq | Powered by Machine Learning  
📱 [WhatsApp](https://wa.me/6281224280846) | 📧 [Email](mailto:dafiqelhaq11@gmail.com) | 📷 [Instagram](https://instagram.com/dafiqelhaq)
""")
