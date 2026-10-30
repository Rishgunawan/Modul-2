
# ==========================================================
# PRAKTIKUM 6 - FUZZY RULE DAN KNOWLEDGE BASE
# PENILAIAN RISIKO KELELAHAN PENGEMUDI
# ==========================================================

class FuzzyRule:
    def __init__(self, rule_id, antecedent, consequent):
        self.rule_id = rule_id
        self.antecedent = antecedent
        self.consequent = consequent
        self.operator = "AND"

    def hitung_firing_strength(self, data):
        derajat = []

        for variabel, label in self.antecedent.items():
            nilai = data[variabel].get(label, 0.0)
            derajat.append(nilai)

        if not derajat:
            return 0.0

        # AND menggunakan Zadeh Min
        return min(derajat)

    def __str__(self):
        syarat = " AND ".join(
            f"{v} is {l}"
            for v, l in self.antecedent.items()
        )
        return (
            f"[{self.rule_id}] IF {syarat} "
            f"THEN Risiko is {self.consequent}"
        )


# ==========================================================
# 1. BASIS PENGETAHUAN
# ==========================================================

label_jam = ["Singkat", "Sedang", "Lama"]
label_istirahat = ["Kurang", "Cukup", "Lama"]
label_jarak = ["Dekat", "Sedang", "Jauh"]

skor_jam = {
    "Singkat": 0,
    "Sedang": 1,
    "Lama": 2
}

skor_istirahat = {
    "Kurang": 2,
    "Cukup": 1,
    "Lama": 0
}

skor_jarak = {
    "Dekat": 0,
    "Sedang": 1,
    "Jauh": 2
}


def tentukan_risiko(skor):
    if skor <= 2:
        return "Rendah"
    elif skor <= 4:
        return "Sedang"
    else:
        return "Tinggi"


# ==========================================================
# 2. PEMBENTUKAN 27 ATURAN
# ==========================================================

rule_base = []
nomor = 1

for jam in label_jam:
    for istirahat in label_istirahat:
        for jarak in label_jarak:

            skor = (
                skor_jam[jam]
                + skor_istirahat[istirahat]
                + skor_jarak[jarak]
            )

            risiko = tentukan_risiko(skor)

            rule = FuzzyRule(
                f"R{nomor}",
                {
                    "Jam Kerja": jam,
                    "Istirahat": istirahat,
                    "Jarak": jarak
                },
                risiko
            )

            rule_base.append(rule)
            nomor += 1


# ==========================================================
# 3. DATA INPUT CONTOH HASIL FUZZIFIKASI
# ==========================================================

data_input = {
    "Jam Kerja": {
        "Singkat": 0.0,
        "Sedang": 0.4,
        "Lama": 0.6
    },
    "Istirahat": {
        "Kurang": 0.7,
        "Cukup": 0.3,
        "Lama": 0.0
    },
    "Jarak": {
        "Dekat": 0.0,
        "Sedang": 0.4,
        "Jauh": 0.6
    }
}


# ==========================================================
# 4. EVALUASI ATURAN
# ==========================================================

print("=" * 78)
print("EVALUASI BASIS ATURAN FUZZY")
print("PENILAIAN RISIKO KELELAHAN PENGEMUDI")
print("=" * 78)

aturan_aktif = []

for rule in rule_base:
    alpha = rule.hitung_firing_strength(data_input)

    status = "AKTIF" if alpha > 0 else "NONAKTIF"

    print(
        f"{rule} | "
        f"Alpha = {alpha:.2f} | {status}"
    )

    if alpha > 0:
        aturan_aktif.append(
            (rule.rule_id, rule.consequent, alpha)
        )


# ==========================================================
# 5. RINGKASAN
# ==========================================================

print("\n" + "=" * 78)
print("RINGKASAN ATURAN AKTIF")
print("=" * 78)

for rule_id, risiko, alpha in aturan_aktif:
    print(
        f"{rule_id:<4} Risiko = {risiko:<8} "
        f"Alpha = {alpha:.2f}"
    )

print("\nJumlah aturan       :", len(rule_base))
print("Aturan aktif        :", len(aturan_aktif))
print("Aturan nonaktif     :", len(rule_base) - len(aturan_aktif))
