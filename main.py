import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Setup Page ---
st.set_page_config(page_title="Analis Keuangan", page_icon="📊")
st.title("📊Analis Keuangan")
st.write("Analisis pemasukan dan pengeluaran perusahaan dengan bantuan program sederhana.")

# --- Load Dataset ---
url = "https://raw.githubusercontent.com/UdinTarmiji/finance-data/main/data/finance_data.csv"
data = pd.read_csv(url)

# --- Proses Data ---
data["profit"] = data["pemasukan"] - data["pengeluaran"]
total_income = data["pemasukan"].sum()
total_expense = data["pengeluaran"].sum()
total_profit = data["profit"].sum()
average_profit = data["profit"].mean()

# --- Tampilkan Ringkasan ---
st.header("📄 Ringkasan Keuangan")
st.metric("Total Pemasukan", f"Rp {total_income:,.0f}")
st.metric("Total Pengeluaran", f"Rp {total_expense:,.0f}")
st.metric("Total Profit", f"Rp {total_profit:,.0f}")
st.metric("Rata-rata Profit Harian", f"Rp {average_profit:,.0f}")

# --- Grafik ---
st.header("📈 Grafik Keuangan")
fig, ax = plt.subplots()
ax.plot(data["tanggal"], data["pemasukan"], label="Pemasukan", marker="o")
ax.plot(data["tanggal"], data["pengeluaran"], label="Pengeluaran", marker="o")
ax.plot(data["tanggal"], data["profit"], label="Profit", linestyle="--", color="green")
ax.set_xlabel("Tanggal")
ax.set_ylabel("Rupiah")
ax.set_title("Tren Keuangan")
ax.legend()
ax.grid(True)
plt.xticks(rotation=45)
st.pyplot(fig)

# --- Analisis AI Sederhana ---
st.header("💬 Analisis")
if total_profit > 5_000_000:
    st.success("Performa keuangan sangat baik! 🚀")
elif total_profit > 0:
    st.info("Keuangan sehat, tetap dipantau. 👍")
else:
    st.warning("Pengeluaran lebih besar dari pemasukan! ⚠️")

# --- Lihat Data ---
with st.expander("🔍 Lihat Tabel Data"):
    st.dataframe(data)

# --- Footer ---
st.markdown("---")
st.caption("Made by Dafiq")
