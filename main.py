import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# --- Setup ---
st.set_page_config(page_title="Prediksi Pendapatan", page_icon="💼")
st.title("💼 Prediksi Pendapatan")
st.write("Prediksi pendapatan berdasarkan jam kerja dan jumlah klien per minggu.")

# --- Load Dataset ---
url = "https://raw.githubusercontent.com/UdinTarmiji/finance-data/main/data/finance_data.csv"
data = pd.read_csv(url)

# --- Train Model ---
x = data[["jam_kerja", "jumlah_klien"]]
y = data["pendapatan"]
model = LinearRegression()
model.fit(x, y)

# --- Input User ---
st.header("🔢 Masukkan Data")
jam = st.slider("🕒 Jam kerja per minggu:", 0, 100, 40)
klien = st.slider("👥 Jumlah klien:", 0, 20, 4)

# --- Prediksi ---
if st.button("🎯 Prediksi Sekarang"):
    hasil = model.predict([[jam, klien]])
    prediksi = int(hasil[0])
    st.success(f"💵 Prediksi Pendapatan: Rp {prediksi:,}")

    # feedback berdasarkan hasil
    if prediksi >= 10_000_000:
        st.balloons()
        st.write("🔥 Wah pendapatanmu luar biasa!")
    elif prediksi >= 5_000_000:
        st.write("🧠 Kerja cerdas! Pendapatanmu sudah bagus.")
    else:
        st.write("📈 Tetap semangat! Masih bisa ditingkatkan.")

    # Download hasil prediksi
    hasil_df = pd.DataFrame({
        "Jam Kerja": [jam],
        "Jumlah Klien": [klien],
        "Prediksi Pendapatan": [prediksi]
    })
    st.download_button("💾 Download Hasil", hasil_df.to_csv(index=False), "hasil_prediksi.csv")

# --- Lihat Data Pelatihan ---
with st.expander("📊 Lihat data pelatihan"):
    st.dataframe(data)

# --- Upload Data Sendiri ---
st.header("📁 Upload Data Anda (Opsional)")
uploaded = st.file_uploader("Upload file CSV")
if uploaded:
    user_data = pd.read_csv(uploaded)
    st.dataframe(user_data)

# --- Visualisasi Tambahan ---
st.header("📈 Visualisasi")
col1, col2 = st.columns(2)

with col1:
    fig1, ax1 = plt.subplots()
    ax1.scatter(data["jam_kerja"], data["pendapatan"], color='blue')
    ax1.set_xlabel("Jam Kerja")
    ax1.set_ylabel("Pendapatan")
    ax1.set_title("Jam Kerja vs Pendapatan")
    ax1.grid(True)
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots()
    ax2.scatter(data["jumlah_klien"], data["pendapatan"], color='green')
    ax2.set_xlabel("Jumlah Klien")
    ax2.set_ylabel("Pendapatan")
    ax2.set_title("Jumlah Klien vs Pendapatan")
    ax2.grid(True)
    st.pyplot(fig2)

# --- Footer ---
st.markdown("---")
st.caption("Made by Dafiq | Powered by Machine Learning")
