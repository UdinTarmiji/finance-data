import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import random

st.set_page_config(page_title="📊 Finance Tracker", page_icon="💰")

# ------------------ USER LOGIN -------------------
if "username" not in st.session_state:
    st.session_state.username = None

if not st.session_state.username:
    st.title("🔐 Masuk ke Aplikasi Keuangan")
    username_input = st.text_input("Masukkan Username Anda")
    if st.button("Masuk"):
        if username_input.strip() != "":
            st.session_state.username = username_input.strip()
            st.experimental_rerun()
        else:
            st.warning("Nama tidak boleh kosong!")
    st.stop()

username = st.session_state.username
st.title(f"💰 Selamat datang, {username}!")

# ------------------ DATA STORAGE -------------------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["tanggal", "pemasukan", "pengeluaran", "kategori"])

# ------------------ INPUT MANUAL -------------------
st.markdown("### ➕ Tambahkan Data Keuangan Manual")
with st.form("form_manual", clear_on_submit=True):
    tanggal = st.date_input("📅 Tanggal", dt.date.today())
    waktu = st.time_input("🕒 Jam", dt.datetime.now().time())
    pemasukan = st.number_input("📥 Pemasukan", min_value=0, step=50000)
    pengeluaran = st.number_input("📤 Pengeluaran", min_value=0, step=50000)
    kategori = st.text_input("🏷️ Kategori (jika ada)", value="Umum")
    submit = st.form_submit_button("✅ Simpan")

    if submit:
        waktu_lengkap = dt.datetime.combine(tanggal, waktu)
        new_data = {
            "tanggal": waktu_lengkap,
            "pemasukan": pemasukan,
            "pengeluaran": pengeluaran,
            "kategori": kategori if pengeluaran > 0 else "-"
        }
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_data])], ignore_index=True)
        st.success("✅ Data berhasil ditambahkan!")

# ------------------ LOAD DATA -------------------
df = st.session_state.data.copy()
if df.empty:
    st.warning("Belum ada data. Silakan input dulu.")
    st.stop()

df["tanggal"] = pd.to_datetime(df["tanggal"])
df = df.sort_values("tanggal")
df["saldo"] = df["pemasukan"] - df["pengeluaran"]
df["saldo_akumulatif"] = df["saldo"].cumsum()

# ------------------ STATISTIK -------------------
st.markdown("---")
st.metric("💰 Total Saldo", f"Rp {df['saldo_akumulatif'].iloc[-1]:,.0f}")
st.metric("📥 Total Pemasukan", f"Rp {df['pemasukan'].sum():,.0f}")
st.metric("📤 Total Pengeluaran", f"Rp {df['pengeluaran'].sum():,.0f}")

# ------------------ PILIH WAKTU -------------------
periode = st.selectbox("📅 Tampilkan berdasarkan:", ["Harian", "Mingguan", "Bulanan", "Tahunan"])
if periode == "Harian":
    df_grouped = df.groupby(df["tanggal"].dt.date).sum(numeric_only=True)
elif periode == "Mingguan":
    df_grouped = df.resample("W", on="tanggal").sum(numeric_only=True)
elif periode == "Bulanan":
    df_grouped = df.resample("M", on="tanggal").sum(numeric_only=True)
else:
    df_grouped = df.resample("Y", on="tanggal").sum(numeric_only=True)

# ------------------ CHART SALDO -------------------
st.subheader("📈 Grafik Saldo Akumulatif")
fig, ax = plt.subplots()
ax.fill_between(df_grouped.index, df_grouped["saldo"].cumsum(), color='skyblue', alpha=0.5)
ax.plot(df_grouped.index, df_grouped["saldo"].cumsum(), color='blue')
ax.set_ylabel("Saldo (Rp)")
ax.set_title(f"Saldo Akumulatif - {periode}")
ax.set_ylim(0, 10_000_000)
ax.set_yticks(range(0, 10_500_000, 500_000))
ax.grid(True)
st.pyplot(fig)

# ------------------ PIE CHART -------------------
if not df[df["pengeluaran"] > 0].empty:
    st.subheader("📊 Distribusi Pengeluaran per Kategori")
    pie_data = df[df["pengeluaran"] > 0].groupby("kategori")["pengeluaran"].sum()
    colors = ["#%06x" % random.randint(0, 0xFFFFFF) for _ in range(len(pie_data))]
    fig2, ax2 = plt.subplots()
    ax2.pie(pie_data, labels=pie_data.index, autopct="%1.1f%%", startangle=90, colors=colors)
    ax2.axis("equal")
    st.pyplot(fig2)

    st.markdown("### 📋 Detail Pengeluaran")
    for kat, total in pie_data.items():
        st.write(f"🔹 **{kat}**: Rp {total:,.0f}")

# ------------------ TABEL -------------------
with st.expander("📋 Lihat Semua Data"):
    st.dataframe(df.sort_values("tanggal", ascending=False))
