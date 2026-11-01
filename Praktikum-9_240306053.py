#implementasi perhitungan sugeno
import numpy as np

def hitung_sugeno(alphas, z_values):
    alphas = np.asarray(alphas, dtype=float)
    z_values = np.asarray(z_values, dtype=float)

    total = np.sum(alphas)

    if total <= 0:
        raise ValueError("Total aktivasi aturan harus lebih dari 0.")

    if len(alphas) != len(z_values):
        raise ValueError("Jumlah data tidak sama.")

    return np.sum(alphas * z_values) / total


# Contoh simulasi
alphas = [0.2, 0.4, 0.2, 0.6]

# Sugeno Orde 0
z0 = [20, 50, 50, 80]
hasil0 = hitung_sugeno(alphas, z0)

# Sugeno Orde 1
J, I, D = 8, 5, 500

z1 = [
    0.8*J - 2*I + 0.01*D + 10,
    0.7*J - 1.5*I + 0.01*D + 15,
    0.9*J - 2*I + 0.008*D + 12,
    0.8*J - 1.8*I + 0.01*D + 20
]

hasil1 = hitung_sugeno(alphas, z1)

print("Sugeno Orde 0:", round(hasil0, 3))
print("Sugeno Orde 1:", round(hasil1, 3))
#implementasi perhitungan sukamoto
def monoton_naik(alpha, a=0, b=100):
    return a + alpha * (b - a)

def monoton_turun(alpha, a=0, b=100):
    return b - alpha * (b - a)

def hitung_tsukamoto(alphas, arah):
    z_values = []

    for alpha, jenis in zip(alphas, arah):
        if jenis == "naik":
            z = monoton_naik(alpha)
        elif jenis == "turun":
            z = monoton_turun(alpha)
        else:
            raise ValueError("Jenis konsekuen tidak valid.")

        z_values.append(z)

    hasil = hitung_sugeno(alphas, z_values)
    return hasil, z_values


alphas = [0.2, 0.4, 0.2, 0.6]
arah = ["turun", "naik", "turun", "naik"]

hasil, nilai_aturan = hitung_tsukamoto(alphas, arah)

print("Nilai konsekuen:", nilai_aturan)
print("Hasil Tsukamoto:", round(hasil, 3))

