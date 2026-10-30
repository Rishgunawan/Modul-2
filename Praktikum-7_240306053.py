import numpy as np
import matplotlib.pyplot as plt

def trimf(x, params):
    """Fungsi keanggotaan segitiga [a, b, c]"""
    a, b, c = params
    y = np.zeros_like(x, dtype=float)
    idx1 = (x > a) & (x <= b)
    if np.any(idx1) and b != a:
        y[idx1] = (x[idx1] - a) / (b - a)
    idx2 = (x > b) & (x < c)
    if np.any(idx2) and c != b:
        y[idx2] = (c - x[idx2]) / (c - b)
    return np.clip(y, 0.0, 1.0)

def trapmf(x, params):
    """Fungsi keanggotaan trapesium [a, b, c, d]"""
    a, b, c, d = params
    y = np.zeros_like(x, dtype=float)
    idx1 = (x > a) & (x <= b)
    if np.any(idx1) and b != a:
        y[idx1] = (x[idx1] - a) / (b - a)
    idx2 = (x >= b) & (x <= c)
    y[idx2] = 1.0
    idx3 = (x > c) & (x < d)
    if np.any(idx3) and d != c:
        y[idx3] = (d - x[idx3]) / (d - c)
    return np.clip(y, 0.0, 1.0)


class DriverFatigueFIS:
    def __init__(self):
        # Domain semesta pembicaraan
        self.x_jam = np.linspace(0, 12, 300)       # 0 - 12 jam
        self.x_ist = np.linspace(0, 4, 300)        # 0 - 4 jam
        self.x_jarak = np.linspace(0, 500, 300)    # 0 - 500 km
        self.z_risiko = np.linspace(0, 100, 500)   # 0 - 100 %

        self._build_membership_functions()
        self._build_27_rules()

    def _build_membership_functions(self):
        # Jam Kerja
        self.mf_jam = {
            "Singkat": trapmf(self.x_jam, [0, 0, 2, 5]),
            "Sedang": trimf(self.x_jam, [3, 6, 9]),
            "Lama": trapmf(self.x_jam, [7, 10, 12, 12])
        }
        # Waktu Istirahat
        self.mf_ist = {
            "Kurang": trapmf(self.x_ist, [0, 0, 0.5, 1.5]),
            "Cukup": trimf(self.x_ist, [1.0, 2.0, 3.0]),
            "Lama": trapmf(self.x_ist, [2.5, 3.5, 4.0, 4.0])
        }
        # Jarak Tempuh
        self.mf_jarak = {
            "Dekat": trapmf(self.x_jarak, [0, 0, 50, 150]),
            "Sedang": trimf(self.x_jarak, [100, 250, 400]),
            "Jauh": trapmf(self.x_jarak, [300, 425, 500, 500])
        }
        # Output: Risiko Kelelahan
        self.mf_risiko = {
            "Rendah": trapmf(self.z_risiko, [0, 0, 20, 45]),
            "Sedang": trimf(self.z_risiko, [35, 50, 65]),
            "Tinggi": trapmf(self.z_risiko, [55, 80, 100, 100])
        }

    def _build_27_rules(self):
        labels_jam = ["Singkat", "Sedang", "Lama"]
        labels_ist = ["Kurang", "Cukup", "Lama"]
        labels_jarak = ["Dekat", "Sedang", "Jauh"]
        skor_j = {"Singkat": 0, "Sedang": 1, "Lama": 2}
        skor_i = {"Kurang": 2, "Cukup": 1, "Lama": 0}
        skor_d = {"Dekat": 0, "Sedang": 1, "Jauh": 2}

        self.rules = []
        r_id = 1
        for j in labels_jam:
            for i in labels_ist:
                for d in labels_jarak:
                    skor = skor_j[j] + skor_i[i] + skor_d[d]
                    cons = "Rendah" if skor <= 2 else ("Sedang" if skor <= 4 else "Tinggi")
                    self.rules.append({
                        "id": f"R{r_id}",
                        "antecedent": {"Jam Kerja": j, "Istirahat": i, "Jarak": d},
                        "consequent": cons
                    })
                    r_id += 1

    def compute(self, val_jam, val_ist, val_jarak):
        # 1. Fuzzifikasi
        f_j = {k: float(np.interp(val_jam, self.x_jam, v)) for k, v in self.mf_jam.items()}
        f_i = {k: float(np.interp(val_ist, self.x_ist, v)) for k, v in self.mf_ist.items()}
        f_d = {k: float(np.interp(val_jarak, self.x_jarak, v)) for k, v in self.mf_jarak.items()}

        # 2. Implikasi
        imp_rendah = np.zeros_like(self.z_risiko)
        imp_sedang = np.zeros_like(self.z_risiko)
        imp_tinggi = np.zeros_like(self.z_risiko)

        firing_rules = []
        for r in self.rules:
            alpha = min(f_j[r["antecedent"]["Jam Kerja"]],
                        f_i[r["antecedent"]["Istirahat"]],
                        f_d[r["antecedent"]["Jarak"]])
            if alpha > 0:
                firing_rules.append((r["id"], r["consequent"], alpha))
                if r["consequent"] == "Rendah":
                    imp_rendah = np.maximum(imp_rendah, np.minimum(alpha, self.mf_risiko["Rendah"]))
                elif r["consequent"] == "Sedang":
                    imp_sedang = np.maximum(imp_sedang, np.minimum(alpha, self.mf_risiko["Sedang"]))
                elif r["consequent"] == "Tinggi":
                    imp_tinggi = np.maximum(imp_tinggi, np.minimum(alpha, self.mf_risiko["Tinggi"]))

        # 3. Agregasi (Max)
        agregasi = np.maximum(imp_rendah, np.maximum(imp_sedang, imp_tinggi))

        # 4. Defuzzifikasi Centroid
        total_mu = np.sum(agregasi)
        z_crisp = np.sum(self.z_risiko * agregasi) / total_mu if total_mu > 0 else 0.0

        return z_crisp, agregasi, firing_rules


# ==========================================================
# SIMULASI & PENGUJIAN 3 KASUS
# ==========================================================
fis = DriverFatigueFIS()

kasus_list = [
    {"nama": "Kasus 1 (Aman)", "jam": 2.0, "ist": 3.0, "jarak": 50},
    {"nama": "Kasus 2 (Sedang)", "jam": 6.0, "ist": 1.5, "jarak": 200},
    {"nama": "Kasus 3 (Bahaya)", "jam": 10.0, "ist": 0.5, "jarak": 400}
]

print("=" * 75)
print("HASIL EKSEKUSI PIPELINE FIS — PENILAIAN RISIKO KELELAHAN PENGEMUDI")
print("=" * 75)

for k in kasus_list:
    z_out, agg, active_r = fis.compute(k["jam"], k["ist"], k["jarak"])
    print(f"\n[{k['nama']}]")
    print(f"Input  : Jam Kerja = {k['jam']}j | Istirahat = {k['ist']}j | Jarak = {k['jarak']}km")
    print(f"Output : Persentase Risiko Kelelahan = {z_out:.2f}%")
    print(f"Aturan Aktif ({len(active_r)} aturan):")
    for r_id, cons, a in active_r:
        print(f"   - {r_id:<4} : Risiko {cons:<8} | alpha = {a:.2f}")

# Plot Kasus 3 (Bahaya)
z_out, agg, _ = fis.compute(10.0, 0.5, 400)
plt.figure(figsize=(10, 5))
plt.plot(fis.z_risiko, fis.mf_risiko["Rendah"], 'g--', label='MF Rendah', alpha=0.5)
plt.plot(fis.z_risiko, fis.mf_risiko["Sedang"], 'b--', label='MF Sedang', alpha=0.5)
plt.plot(fis.z_risiko, fis.mf_risiko["Tinggi"], 'r--', label='MF Tinggi', alpha=0.5)
plt.fill_between(fis.z_risiko, 0, agg, color='purple', alpha=0.35, label='Area Agregasi Fuzzy')
plt.plot(fis.z_risiko, agg, color='purple', linewidth=2.5)
plt.axvline(x=z_out, color='black', linewidth=2.5, linestyle='-', label=f'Crisp Output (Centroid = {z_out:.2f}%)')
plt.scatter([z_out], [0], color='black', s=80, zorder=6)
plt.title('Pipeline FIS: Agregasi Konklusi dan Defuzzifikasi Centroid', fontweight='bold')
plt.xlabel('Tingkat Risiko Kelelahan (%)')
plt.ylabel('Derajat Keanggotaan μ(z)')
plt.ylim(-0.05, 1.05)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(loc='upper left')
plt.tight_layout()
plt.savefig('pipeline_fis_agregasi_defuzzifikasi.png', dpi=300)
plt.show()
