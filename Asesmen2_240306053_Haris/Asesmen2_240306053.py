
"""
ASESMEN MODUL 2 — FUZZY DECISION SYSTEM
Penilaian Risiko Kelelahan Pengemudi
Metode: Mamdani

AND = MIN
Implication = MIN
Aggregation = MAX
Defuzzification = Centroid

Dependensi:
    pip install numpy matplotlib

Jalankan:
    python Asesmen2_Fuzzy_Risiko_Kelelahan.py
"""

import numpy as np
import matplotlib.pyplot as plt
from itertools import product


# ============================================================
# 1. FUNGSI KEANGGOTAAN FUZZY
# ============================================================

def trimf(x, a, b, c):
    """Fungsi keanggotaan segitiga."""
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x, dtype=float)

    if a == b:
        y = np.where(x <= b, 1.0, y)
    else:
        mask = (x > a) & (x < b)
        y = np.where(mask, (x - a) / (b - a), y)

    y = np.where(x == b, 1.0, y)

    if b == c:
        y = np.where(x >= b, 1.0, y)
    else:
        mask = (x > b) & (x < c)
        y = np.where(mask, (c - x) / (c - b), y)

    return np.clip(y, 0.0, 1.0)


def trapmf(x, a, b, c, d):
    """Fungsi keanggotaan trapesium, termasuk left/right shoulder."""
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x, dtype=float)

    # Bagian datar
    y = np.where((x >= b) & (x <= c), 1.0, y)

    # Sisi kiri
    if a == b:
        y = np.where(x <= b, 1.0, y)
    else:
        mask = (x > a) & (x < b)
        y = np.where(mask, (x - a) / (b - a), y)

    # Sisi kanan
    if c == d:
        y = np.where(x >= c, 1.0, y)
    else:
        mask = (x > c) & (x < d)
        y = np.where(mask, (d - x) / (d - c), y)

    return np.clip(y, 0.0, 1.0)


# ============================================================
# 2. DOMAIN DAN HIMPUNAN FUZZY
# Parameter dipertahankan sesuai model Modul 1/laporan.
# ============================================================

INPUTS = {
    "jam": {
        "Singkat": lambda x: trapmf(x, 0, 0, 2, 6),
        "Sedang": lambda x: trimf(x, 4, 8, 12),
        "Lama": lambda x: trapmf(x, 10, 14, 24, 24),
    },
    "istirahat": {
        "Kurang": lambda x: trapmf(x, 0, 0, 1, 3),
        "Cukup": lambda x: trimf(x, 2, 5, 8),
        "Lama": lambda x: trapmf(x, 7, 10, 12, 12),
    },
    "jarak": {
        "Dekat": lambda x: trapmf(x, 0, 0, 100, 300),
        "Sedang": lambda x: trimf(x, 200, 500, 800),
        "Jauh": lambda x: trapmf(x, 600, 850, 1000, 1000),
    },
}

DOMAIN = {
    "jam": (0, 24),
    "istirahat": (0, 12),
    "jarak": (0, 1000),
}

Y = np.linspace(0, 100, 1001)

OUTPUT_MF = {
    "Rendah": lambda y: trapmf(y, 0, 0, 20, 45),
    "Sedang": lambda y: trimf(y, 25, 50, 75),
    "Tinggi": lambda y: trapmf(y, 55, 80, 100, 100),
}


# ============================================================
# 3. BASIS ATURAN FUZZY (3 x 3 x 3 = 27 RULES)
# ============================================================

H_SEV = {"Singkat": 0, "Sedang": 1, "Lama": 2}
R_SEV = {"Kurang": 2, "Cukup": 1, "Lama": 0}
D_SEV = {"Dekat": 0, "Sedang": 1, "Jauh": 2}


def consequent(jam_label, rest_label, distance_label):
    score = (
        H_SEV[jam_label]
        + R_SEV[rest_label]
        + D_SEV[distance_label]
    )

    if score <= 1:
        return "Rendah"
    elif score <= 3:
        return "Sedang"

    return "Tinggi"


RULES = [
    (
        jam_label,
        rest_label,
        distance_label,
        consequent(jam_label, rest_label, distance_label)
    )
    for jam_label, rest_label, distance_label in product(
        INPUTS["jam"],
        INPUTS["istirahat"],
        INPUTS["jarak"]
    )
]


# ============================================================
# 4. FUZZIFIKASI DAN VALIDASI INPUT
# ============================================================

def validate_inputs(jam, istirahat, jarak):
    values = {
        "jam": jam,
        "istirahat": istirahat,
        "jarak": jarak
    }

    converted = {}

    for name, value in values.items():
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"Input {name} harus berupa angka.")

        minimum, maximum = DOMAIN[name]

        if not minimum <= number <= maximum:
            raise ValueError(
                f"Input {name} harus berada pada rentang "
                f"{minimum} sampai {maximum}."
            )

        converted[name] = number

    return (
        converted["jam"],
        converted["istirahat"],
        converted["jarak"]
    )


def fuzzify(value, fuzzy_sets):
    """Menghitung derajat keanggotaan setiap label linguistik."""
    return {
        label: float(np.asarray(function(np.array([value])))[0])
        for label, function in fuzzy_sets.items()
    }


# ============================================================
# 5. MESIN INFERENSI MAMDANI DAN DEFUZZIFIKASI CENTROID
# ============================================================

def infer(jam, istirahat, jarak):
    jam, istirahat, jarak = validate_inputs(
        jam, istirahat, jarak
    )

    # Tahap fuzzifikasi
    mu_jam = fuzzify(jam, INPUTS["jam"])
    mu_istirahat = fuzzify(istirahat, INPUTS["istirahat"])
    mu_jarak = fuzzify(jarak, INPUTS["jarak"])

    # Tahap inferensi
    # AND menggunakan MIN
    # Implikasi menggunakan MIN
    # Agregasi menggunakan MAX
    aggregate = np.zeros_like(Y, dtype=float)
    active_rules = []

    for jam_label, rest_label, distance_label, output_label in RULES:

        alpha = min(
            mu_jam[jam_label],
            mu_istirahat[rest_label],
            mu_jarak[distance_label]
        )

        if alpha > 0:
            output_membership = OUTPUT_MF[output_label](Y)

            implied = np.minimum(
                alpha,
                output_membership
            )

            aggregate = np.maximum(
                aggregate,
                implied
            )

            active_rules.append({
                "jam": jam_label,
                "istirahat": rest_label,
                "jarak": distance_label,
                "output": output_label,
                "alpha": alpha,
            })

    # Defuzzifikasi menggunakan metode centroid
    denominator = np.sum(aggregate)

    if denominator <= 0:
        raise RuntimeError(
            "Tidak ada aturan aktif. Periksa cakupan fungsi keanggotaan."
        )

    crisp_output = float(
        np.sum(Y * aggregate) / denominator
    )

    return crisp_output, aggregate, active_rules


# ============================================================
# 6. KATEGORI HASIL DAN INFORMASI HASIL INFERENSI
# ============================================================

def risk_category(score):
    """Batas kategori pelaporan sesuai laporan proyek."""
    if score < 40:
        return "Rendah"
    elif score < 70:
        return "Sedang"

    return "Tinggi"


def show_result(jam, istirahat, jarak, show_rules=True):
    score, aggregate, active_rules = infer(
        jam, istirahat, jarak
    )

    print("\n========== HASIL KEPUTUSAN FUZZY MAMDANI ==========")
    print(f"Jam kerja       : {jam:.2f} jam")
    print(f"Waktu istirahat : {istirahat:.2f} jam")
    print(f"Jarak tempuh    : {jarak:.2f} km")
    print(f"Skor risiko     : {score:.2f} / 100")
    print(f"Kategori risiko : {risk_category(score)}")

    if show_rules:
        print("\nAturan yang aktif:")

        if not active_rules:
            print("Tidak ada aturan aktif.")
        else:
            for number, rule in enumerate(active_rules, start=1):
                print(
                    f"{number:02d}. IF Jam {rule['jam']} AND "
                    f"Istirahat {rule['istirahat']} AND "
                    f"Jarak {rule['jarak']} "
                    f"THEN Risiko {rule['output']} "
                    f"| alpha = {rule['alpha']:.3f}"
                )

    return score, aggregate, active_rules


# ============================================================
# 7. MENAMPILKAN SELURUH BASIS ATURAN
# ============================================================

def print_rulebase():
    print("\n================ BASIS ATURAN (27 RULES) ================")

    for number, (
        jam_label,
        rest_label,
        distance_label,
        output_label
    ) in enumerate(RULES, start=1):

        print(
            f"R{number:02d}: IF Jam {jam_label} AND "
            f"Istirahat {rest_label} AND Jarak {distance_label} "
            f"THEN Risiko {output_label}"
        )


# ============================================================
# 8. PENGUJIAN LIMA SKENARIO
# ============================================================

def test_scenarios():
    cases = [
        ("Normal/ringan", 3, 8, 100),
        ("Sedang", 6, 5, 250),
        ("Tengah", 8, 5, 500),
        ("Berat", 14, 2, 850),
        ("Ekstrem", 24, 1, 1000),
    ]

    print("\n================ HASIL PENGUJIAN ================")

    print(
        f"{'Kasus':<16}{'Jam':>8}{'Istirahat':>12}"
        f"{'Jarak':>10}{'Skor':>12}{'Kategori':>12}"
    )

    print("-" * 70)

    results = []

    for name, jam, istirahat, jarak in cases:
        score, _, _ = infer(jam, istirahat, jarak)
        category = risk_category(score)

        results.append(
            (name, jam, istirahat, jarak, score, category)
        )

        print(
            f"{name:<16}{jam:>8.1f}{istirahat:>12.1f}"
            f"{jarak:>10.1f}{score:>12.2f}{category:>12}"
        )

    return results


# ============================================================
# 9. VISUALISASI FUNGSI KEANGGOTAAN
# ============================================================

def plot_memberships():
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))

    universes = [
        np.linspace(0, 24, 400),
        np.linspace(0, 12, 300),
        np.linspace(0, 1000, 500),
        Y,
    ]

    groups = [
        INPUTS["jam"],
        INPUTS["istirahat"],
        INPUTS["jarak"],
        OUTPUT_MF,
    ]

    titles = [
        "Jam Kerja (jam)",
        "Waktu Istirahat (jam)",
        "Jarak Tempuh (km)",
        "Risiko (0-100)",
    ]

    for ax, universe, group, title in zip(
        axes, universes, groups, titles
    ):
        for label, function in group.items():
            ax.plot(
                universe,
                function(universe),
                label=label,
                linewidth=2
            )

        ax.set_title(title)
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Derajat keanggotaan")
        ax.set_xlabel("Nilai")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    fig.suptitle(
        "Fungsi Keanggotaan Sistem Risiko Kelelahan Pengemudi",
        fontweight="bold"
    )

    fig.tight_layout()

    fig.savefig(
        "kurva_keanggotaan_asesmen2.png",
        dpi=300,
        bbox_inches="tight"
    )

    # Menampilkan grafik ke layar
    plt.show()

    plt.close(fig)


# ============================================================
# 10. VISUALISASI AGREGASI OUTPUT UNTUK SATU CONTOH INPUT
# ============================================================

def plot_aggregation_example(jam=8, istirahat=5, jarak=500):
    score, aggregate, active_rules = infer(
        jam, istirahat, jarak
    )

    fig, ax = plt.subplots(figsize=(9, 5))

    # Menampilkan fungsi keanggotaan output
    for label, function in OUTPUT_MF.items():
        ax.plot(
            Y,
            function(Y),
            "--",
            linewidth=1.5,
            label=f"Output {label}"
        )

    # Menampilkan hasil agregasi MAX
    ax.fill_between(
        Y,
        0,
        aggregate,
        alpha=0.35,
        label="Hasil agregasi (MAX)"
    )

    ax.plot(
        Y,
        aggregate,
        linewidth=2,
        label="Kurva agregasi"
    )

    # Menampilkan garis centroid
    ax.axvline(
        score,
        linestyle=":",
        linewidth=2,
        label=f"Centroid = {score:.2f}"
    )

    ax.set_title(
        f"Agregasi Output Mamdani "
        f"(Jam={jam}, Istirahat={istirahat}, Jarak={jarak})"
    )

    ax.set_xlabel("Skor risiko")
    ax.set_ylabel("Derajat keanggotaan")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()

    fig.savefig(
        "agregasi_output_mamdani.png",
        dpi=300,
        bbox_inches="tight"
    )

    # Menampilkan grafik ke layar
    plt.show()

    plt.close(fig)


# ============================================================
# 11. DECISION SURFACE 3D
# Jarak tempuh ditetapkan 500 km sebagai irisan dua input.
# ============================================================

def plot_decision_surface():
    jam_range = np.linspace(0, 24, 35)
    rest_range = np.linspace(0, 12, 35)

    J, R = np.meshgrid(
        jam_range,
        rest_range
    )

    fixed_distance = 500
    Z = np.zeros_like(J, dtype=float)

    for row in range(J.shape[0]):
        for col in range(J.shape[1]):
            Z[row, col] = infer(
                J[row, col],
                R[row, col],
                fixed_distance
            )[0]

    fig = plt.figure(figsize=(10, 7))

    ax = fig.add_subplot(
        111,
        projection="3d"
    )

    surface = ax.plot_surface(
        J,
        R,
        Z,
        cmap="viridis",
        edgecolor="none",
        alpha=0.92
    )

    ax.set_xlabel("Jam Kerja (jam)")
    ax.set_ylabel("Waktu Istirahat (jam)")
    ax.set_zlabel("Skor Risiko")

    ax.set_title(
        "Decision Surface Risiko Kelelahan\n"
        "(Jarak Tempuh tetap 500 km)"
    )

    fig.colorbar(
        surface,
        ax=ax,
        shrink=0.6,
        aspect=12,
        label="Skor risiko"
    )

    fig.tight_layout()

    fig.savefig(
        "decision_surface_risiko_kelelahan.png",
        dpi=300,
        bbox_inches="tight"
    )

    # Menampilkan grafik 3D ke layar
    plt.show()

    plt.close(fig)


# ============================================================
# 12. INPUT MANUAL DARI PENGGUNA
# ============================================================

def manual_input():
    print("\n========== INPUT DATA PENGEMUDI ==========")

    print("Masukkan nilai sesuai domain berikut:")
    print("Jam kerja       : 0-24 jam")
    print("Waktu istirahat : 0-12 jam")
    print("Jarak tempuh    : 0-1000 km")

    try:
        jam = float(input("Masukkan jam kerja (jam): "))
        istirahat = float(
            input("Masukkan waktu istirahat (jam): ")
        )
        jarak = float(
            input("Masukkan jarak tempuh (km): ")
        )

        # Menampilkan hasil perhitungan
        show_result(jam, istirahat, jarak)

        # Menampilkan grafik agregasi sesuai input pengguna
        plot_aggregation_example(
            jam,
            istirahat,
            jarak
        )

    except ValueError as error:
        print(f"\nInput tidak valid: {error}")


# ============================================================
# 13. MENU UTAMA PROGRAM
# ============================================================

def main():
    while True:
        print("\n==============================================")
        print(" FUZZY DECISION SYSTEM - RISIKO KELELAHAN")
        print("==============================================")

        print("1. Hitung keputusan dari input pengguna")
        print("2. Jalankan lima skenario pengujian")
        print("3. Tampilkan 27 aturan fuzzy")
        print("4. Buat seluruh grafik")
        print("5. Keluar")

        choice = input("Pilih menu (1-5): ").strip()

        if choice == "1":
            manual_input()

        elif choice == "2":
            test_scenarios()

        elif choice == "3":
            print_rulebase()

        elif choice == "4":
            print("\nSedang membuat grafik...")

            print("\nMenampilkan grafik fungsi keanggotaan...")
            plot_memberships()

            print("\nMenampilkan grafik agregasi Mamdani...")
            plot_aggregation_example()

            print("\nMenampilkan grafik Decision Surface 3D...")
            plot_decision_surface()

            print("\nSemua grafik berhasil disimpan:")
            print("- kurva_keanggotaan_asesmen2.png")
            print("- agregasi_output_mamdani.png")
            print("- decision_surface_risiko_kelelahan.png")

        elif choice == "5":
            print("Program selesai. Terima kasih.")
            break

        else:
            print(
                "Pilihan tidak tersedia. "
                "Masukkan angka 1 sampai 5."
            )


if __name__ == "__main__":
    main()
