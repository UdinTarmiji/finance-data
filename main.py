import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# --- Setup halaman ---
st.set_page_config(page_title="Prediksi Keuangan", page_icon="💰")

st.title("📈 Prediksi Pemasukan Berdasarkan Pengeluaran")
st.write("Aplikasi ini memprediksi pemasukan harian berdasarkan pengeluaran menggunakan model Machine Learning sederhana.")

# --- Load Dataset dari GitHub ---
url = "https://raw.githubusercontent.com/UdinTarmiji/finance-data/main/data/finance_data.csv"
data = pd.read_csv(url)

# --- Model Training ---
x = data[["pengeluaran"]]
y = data["pemasukan"]
model = LinearRegression()
model.fit(x, y)

# --- Input User ---
st.header("🔢 Masukkan Pengeluaran Harian")
user_pengeluaran = st.number_input("Masukkan nominal pengeluaran (Rp):", min_value=0, step=10000)

# --- History Prediksi ---
if "history" not in st.session_state:
    st.session_state.history = []

if st.button("🎯 Prediksi"):
    hasil = model.predict([[user_pengeluaran]])
    prediksi = int(hasil[0])
    st.success(f"💸 Prediksi pemasukan: Rp {prediksi:,}")
    
    # Simpan ke history
    st.session_state.history.append({"pengeluaran": user_pengeluaran, "pemasukan": prediksi})

    # Feedback
    if prediksi > user_pengeluaran:
        st.write("✅ Potensi untung, pemasukan lebih besar dari pengeluaran.")
    else:
        st.write("⚠️ Hati-hati! Bisa jadi defisit.")

# --- Riwayat Prediksi ---
if st.session_state.history:
    st.subheader("📂 Riwayat Prediksi")
    history_df = pd.DataFrame(st.session_state.history)
    st.dataframe(history_df)

    # Visualisasi History
    st.subheader("📊 Grafik Riwayat Prediksi")
    fig1, ax1 = plt.subplots()
    ax1.plot(history_df["pengeluaran"], history_df["pemasukan"], marker='o', linestyle='-')
    ax1.set_xlabel("Pengeluaran (Rp)")
    ax1.set_ylabel("Pemasukan (Rp)")
    ax1.set_title("Riwayat Prediksi Pengeluaran vs Pemasukan")
    st.pyplot(fig1)

# --- Visualisasi Dataset Asli ---
st.subheader("📉 Visualisasi Dataset Asli")
fig2, ax2 = plt.subplots()
ax2.scatter(data["pengeluaran"], data["pemasukan"], color='blue', label="Data asli")
ax2.plot(data["pengeluaran"], model.predict(data[["pengeluaran"]]), color='red', label="Model prediksi")
ax2.set_xlabel("Pengeluaran")
ax2.set_ylabel("Pemasukan")
ax2.set_title("Data Asli & Garis Prediksi")
ax2.grid(True)
ax2.legend()
st.pyplot(fig2)

# --- Footer ---
st.markdown("---")
st.caption("Dibuat oleh Dafiq • Powered by Machine Learning & Streamlit")
