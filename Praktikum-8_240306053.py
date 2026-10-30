import numpy as np
import matplotlib.pyplot as plt
import skfuzzy as fuzz

# 1. SEMESTA OUTPUT
z = np.linspace(0, 100, 1000)

# 2. FUNGSI KEANGGOTAAN RISIKO
rendah = fuzz.trapmf(z, [0, 0, 20, 45])
sedang = fuzz.trimf(z, [25, 50, 75])
tinggi = fuzz.trapmf(z, [55, 80, 100, 100])

# 3. KEKUATAN AKTIVASI SIMULASI
alpha_rendah = 0.3
alpha_sedang = 0.7
alpha_tinggi = 0.5

# 4. IMPLIKASI MIN
imp_rendah = np.fmin(alpha_rendah, rendah)
imp_sedang = np.fmin(alpha_sedang, sedang)
imp_tinggi = np.fmin(alpha_tinggi, tinggi)

# 5. AGREGASI MAX
agregasi = np.fmax(
    imp_rendah,
    np.fmax(imp_sedang, imp_tinggi)
)

# 6. DEFUZZIFIKASI
metode = ["centroid", "bisector", "mom", "som", "lom"]
hasil = {}

for m in metode:
    hasil[m] = fuzz.defuzz(z, agregasi, m)

# 7. MENAMPILKAN HASIL
print("=" * 50)
print("HASIL KOMPARASI DEFUZZIFIKASI")
print("=" * 50)

for m, nilai in hasil.items():
    print(f"{m.upper():10s}: {nilai:.3f}")

# 8. VISUALISASI
plt.figure(figsize=(11, 6))

plt.plot(z, agregasi, linewidth=2,
         label="Kurva Agregasi")
plt.fill_between(z, agregasi, alpha=0.3)

for metode, nilai in hasil.items():
    plt.axvline(
        nilai,
        linestyle="--",
        label=f"{metode.upper()} = {nilai:.2f}"
    )

plt.title("Komparasi Metode Defuzzifikasi Mamdani")
plt.xlabel("Skor Risiko Kelelahan")
plt.ylabel("Derajat Keanggotaan")
plt.xlim(0, 100)
plt.ylim(0, 1.05)
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig("komparasi_metode_defuzzifikasi.png", dpi=300)
plt.show()
