
import numpy as np
import matplotlib.pyplot as plt
from itertools import product


# ==========================================
# 1. FUNGSI KEANGGOTAAN
# ==========================================

def trimf(x, a, b, c):
    """Fungsi keanggotaan segitiga."""
    if x < a or x > c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a) if b != a else 1.0
    return (c - x) / (c - b) if c != b else 1.0


def trapmf(x, a, b, c, d):
    """Fungsi keanggotaan trapesium."""
    if x < a or x > d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if a <= x < b:
        return (x - a) / (b - a) if b != a else 1.0
    if c < x <= d:
        return (d - x) / (d - c) if d != c else 1.0
    return 0.0


def left_shoulder(x, a, b, c):
    """Trapesium bahu kiri."""
    if x <= b:
        return 1.0 if x >= a else 1.0
    if x >= c:
        return 0.0
    return (c - x) / (c - b)


def right_shoulder(x, a, b, c):
    """Trapesium bahu kanan."""
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    return (x - a) / (b - a)


# ==========================================
# 2. ARSITEKTUR FUZZY INFERENCE SYSTEM
# ==========================================

class FuzzyInferenceSystem:

    def __init__(self):
        self.inputs = {}
        self.output = None
        self.rules = []

    def add_input_variable(self, name, universe, mf_dict):
        self.inputs[name] = {
            "universe": universe,
            "mf": mf_dict
        }

    def set_output_variable(self, name, universe, mf_dict):
        self.output = {
            "name": name,
            "universe": universe,
            "mf": mf_dict
        }

    def add_rule(self, rule_tuple):
        # Format:
        # (label_jam, label_istirahat,
        #  label_jarak, label_output)
        self.rules.append(rule_tuple)

    def fuzzify(self, input_values):
        fuzzified = {}

        for name, value in input_values.items():
            if name not in self.inputs:
                raise ValueError(f"Input tidak dikenal: {name}")

            var = self.inputs[name]

            if not np.isfinite(value):
                raise ValueError(f"Input {name} tidak valid.")

            if value < min(var["universe"]) or \
               value > max(var["universe"]):
                raise ValueError(
                    f"{name} di luar domain."
                )

            fuzzified[name] = {
                label: mf(value)
                for label, mf in var["mf"].items()
            }

        return fuzzified

    def compute(self, input_values):

        if self.output is None:
            raise ValueError("Output belum ditentukan.")

        if set(input_values) != set(self.inputs):
            raise ValueError(
                "Input harus sesuai variabel sistem."
            )

        fuzzified = self.fuzzify(input_values)

        universe = self.output["universe"]
        aggregated = np.zeros_like(
            universe, dtype=float
        )

        active_rules = []

        for rule in self.rules:
            jam, istirahat, jarak, hasil = rule

            alpha = min(
                fuzzified["Jam Kerja"][jam],
                fuzzified["Waktu Istirahat"][istirahat],
                fuzzified["Jarak Tempuh"][jarak]
            )

            if alpha <= 0:
                continue

            output_mf = self.output["mf"][hasil]

            # Implikasi Mamdani: MIN
            clipped = np.minimum(
                alpha,
                np.array([output_mf(z) for z in universe])
            )

            # Agregasi: MAX
            aggregated = np.maximum(
                aggregated, clipped
            )

            active_rules.append(
                (rule, alpha)
            )

        # Defuzzifikasi Centroid
        denominator = np.sum(aggregated)

        if denominator == 0:
            raise ValueError(
                "Tidak ada aturan aktif."
            )

        crisp_output = np.sum(
            universe * aggregated
        ) / denominator

        return {
            "fuzzified": fuzzified,
            "active_rules": active_rules,
            "aggregated": aggregated,
            "crisp_output": crisp_output
        }


# ==========================================
# 3. MEMBANGUN SISTEM FUZZY
# ==========================================

fis = FuzzyInferenceSystem()

# Input 1: Jam Kerja (0-16 jam)
fis.add_input_variable(
    "Jam Kerja",
    np.arange(0, 17, 1),
    {
        "Singkat": lambda x: trapmf(x, 0, 0, 2, 6),
        "Sedang": lambda x: trimf(x, 4, 8, 12),
        "Lama": lambda x: trapmf(x, 10, 14, 16, 16)
    }
)

# Input 2: Waktu Istirahat (0-12 jam)
fis.add_input_variable(
    "Waktu Istirahat",
    np.arange(0, 13, 1),
    {
        "Kurang": lambda x: trapmf(x, 0, 0, 1, 3),
        "Cukup": lambda x: trimf(x, 2, 5, 8),
        "Lama": lambda x: trapmf(x, 7, 10, 12, 12)
    }
)

# Input 3: Jarak Tempuh (0-1000 km)
fis.add_input_variable(
    "Jarak Tempuh",
    np.arange(0, 1001, 1),
    {
        "Dekat": lambda x: trapmf(x, 0, 0, 100, 300),
        "Sedang": lambda x: trimf(x, 200, 500, 800),
        "Jauh": lambda x: trapmf(x, 600, 850, 1000, 1000)
    }
)

# Output: Risiko Kelelahan (0-100)
fis.set_output_variable(
    "Risiko Kelelahan",
    np.arange(0, 101, 1),
    {
        "Rendah": lambda z: trapmf(z, 0, 0, 20, 45),
        "Sedang": lambda z: trimf(z, 25, 50, 75),
        "Tinggi": lambda z: trapmf(z, 55, 80, 100, 100)
    }
)


# ==========================================
# 4. BASIS ATURAN 27 RULE
# ==========================================

# Urutan jarak: Dekat, Sedang, Jauh
# Baris: waktu istirahat Kurang, Cukup, Lama

rule_matrix = {
    "Singkat": [
        ["Sedang", "Sedang", "Tinggi"],
        ["Rendah", "Rendah", "Sedang"],
        ["Rendah", "Rendah", "Rendah"]
    ],

    "Sedang": [
        ["Sedang", "Sedang", "Tinggi"],
        ["Rendah", "Sedang", "Sedang"],
        ["Rendah", "Rendah", "Sedang"]
    ],

    "Lama": [
        ["Tinggi", "Tinggi", "Tinggi"],
        ["Sedang", "Sedang", "Tinggi"],
        ["Sedang", "Sedang", "Sedang"]
    ]
}

jam_labels = ["Singkat", "Sedang", "Lama"]
istirahat_labels = ["Kurang", "Cukup", "Lama"]
jarak_labels = ["Dekat", "Sedang", "Jauh"]

for jam, istirahat, jarak in product(
    jam_labels, istirahat_labels, jarak_labels
):
    i = istirahat_labels.index(istirahat)
    j = jarak_labels.index(jarak)

    hasil = rule_matrix[jam][i][j]

    fis.add_rule((jam, istirahat, jarak, hasil))


# ==========================================
# 5. PENGUJIAN SISTEM
# ==========================================

test_cases = [
    {
        "nama": "Kasus 1",
        "input": {
            "Jam Kerja": 3,
            "Waktu Istirahat": 8,
            "Jarak Tempuh": 100
        }
    },
    {
        "nama": "Kasus 2",
        "input": {
            "Jam Kerja": 8,
            "Waktu Istirahat": 5,
            "Jarak Tempuh": 500
        }
    },
    {
        "nama": "Kasus 3",
        "input": {
            "Jam Kerja": 14,
            "Waktu Istirahat": 1,
            "Jarak Tempuh": 850
        }
    }
]

results = []

for case in test_cases:
    result = fis.compute(case["input"])

    score = result["crisp_output"]

    results.append({
        "nama": case["nama"],
        "input": case["input"],
        "result": result
    })

    print("\n", "=" * 45)
    print(case["nama"])
    print("Input:", case["input"])

    print("\nDerajat Keanggotaan:")
    for variable, memberships in result["fuzzified"].items():
        print(variable, memberships)

    print("\nAturan Aktif:")
    for rule, alpha in result["active_rules"]:
        print(rule, "alpha =", round(alpha, 3))

    print("\nSkor Risiko:", round(score, 2))


# ==========================================
# 6. VISUALISASI AGREGASI OUTPUT
# ==========================================

for item in results:
    result = item["result"]
    universe = fis.output["universe"]
    aggregated = result["aggregated"]
    score = result["crisp_output"]

    plt.figure(figsize=(9, 4))
    plt.fill_between(
        universe, aggregated, alpha=0.35,
        label="Agregasi Mamdani"
    )
    plt.plot(universe, aggregated,
             label="Kurva Agregasi")
    plt.axvline(
        score, linestyle="--",
        label=f"Centroid = {score:.2f}"
    )

    plt.title(
        f"{item['nama']} - Risiko Kelelahan"
    )
    plt.xlabel("Skor Risiko (0-100)")
    plt.ylabel("Derajat Keanggotaan")
    plt.ylim(0, 1.05)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
