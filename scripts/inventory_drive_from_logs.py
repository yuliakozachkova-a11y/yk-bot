"""
Extract Drive file IDs from gdown logs (from the previous download attempt).
Build catalog in DB without storing local copies.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot import drive

# Folder mapping (parent folder name → simplified label)
FOLDER_MAP = {
    "03-06 Козачкова Юля": "03-06_KozachkovaYulia",
    "Юля": "Yulia",
    "Фотосессии 2017": "Fotosessii2017",
}

# Hard-skip personal folders by name keyword
SKIP_KEYWORDS = [
    "Семья", "Семья 2015", "Семья 2016", "Семья 2017", "Семья 2019",
    "Семья 2021", "Семья 2025",
    "Свадьба", "Свадьба",
    "Беременность", "беременность",
    "ДР Давид", "Давид",
    "ДР 34",
    "Аеротруба",
    "Родители",
    "Оцифровка",
    "Новая папка",  # contents not clear, treat as personal-default
]


# Direct from gdown log dump: (file_id, filename, parent_folder)
ENTRIES = [
    # === folder "03-06 Козачкова Юля" — ивент с её фотографиями на стенде ===
    ("10wrx1WOS9xOu0-NTvRVb8YNGm9pd09Ta", "IMG_7280.jpg", "03-06 Козачкова Юля"),
    ("1Ap685SuIzdEI6HDwLJQPBpCCaTRRjVHs", "IMG_7284.jpg", "03-06 Козачкова Юля"),
    ("1vhHoIWaAk4k_w7vg-jOEFPxs30CWSkFT", "IMG_7285.jpg", "03-06 Козачкова Юля"),
    ("10LrVmXOxxE_8o9iQD7L_gqoGqO6eHW24", "IMG_7287.jpg", "03-06 Козачкова Юля"),
    ("1CBwBZ4IYJ-PNI0-k9KWAjvePfA5QRWeq", "IMG_7289.jpg", "03-06 Козачкова Юля"),
    ("1kyIeTQbVOBx-oABE9AoonW0NvQu7OQ1V", "IMG_7294.jpg", "03-06 Козачкова Юля"),
    ("1-uwl88WZdPS1C8K9WKAraZljvx5Pxtd0", "IMG_7300.jpg", "03-06 Козачкова Юля"),
    ("1JSHs-RXclLPjcrPfKplx4GjSqO1PZQ6e", "IMG_7303.jpg", "03-06 Козачкова Юля"),
    ("1lhDjlDFA7CNNdofeN9ydnDNR7x0lDxeu", "IMG_7312.jpg", "03-06 Козачкова Юля"),
    ("1918QmJqDe6Ol9bZKzRZijx5fofeyX7K7", "IMG_7317.jpg", "03-06 Козачкова Юля"),
    ("18a5DmlSAMZ5eiuRjUtyTKZZ_mAzrslp7", "IMG_7320.jpg", "03-06 Козачкова Юля"),
    ("1YnEi7AEvH-m9TMFth_FggV4DUlASXEGE", "IMG_7324.jpg", "03-06 Козачкова Юля"),
    ("1SGnd50NY7qnywNmoecO2aSMLQKMUIXE8", "IMG_7330.jpg", "03-06 Козачкова Юля"),
    ("12y8gD-eSwMKJlXVFAAAVJKNjZZMtosX6", "IMG_7334.jpg", "03-06 Козачкова Юля"),
    ("1KHpuHVGH0-b11BnLo9F6rnRZJhdnSLAQ", "IMG_7341.jpg", "03-06 Козачкова Юля"),
    ("1gNrOIG742XQo2agsegUMXEFzEXOGzp7E", "IMG_7342.jpg", "03-06 Козачкова Юля"),
    ("1gSEhsVPESSPy8py_jah6NMHBTJTcanGE", "IMG_7347.jpg", "03-06 Козачкова Юля"),
    ("10FmzwSfZ14HDapJnHd73K9vk0zXlJkBT", "IMG_7365.jpg", "03-06 Козачкова Юля"),
    ("1rMR9Yk_bDwq0nl4Cz7Qijw0qEj70n7cD", "IMG_7371.jpg", "03-06 Козачкова Юля"),
    ("1WhYmVG32KnXfD9P7SJCoD0z1AKzQLwqv", "IMG_7374.jpg", "03-06 Козачкова Юля"),
    ("1SIrQi-X2uKhFeiraBnOzLIqqSNTbG9bv", "IMG_7376.jpg", "03-06 Козачкова Юля"),
    ("1nIzOZHru9oc5SLDYWxcCMV4EEe6M61EN", "IMG_7383.jpg", "03-06 Козачкова Юля"),
    ("1Gu_fPG5gG4BMfrayFhyt7PGYKjPlBk59", "IMG_7385.jpg", "03-06 Козачкова Юля"),
    ("13z0gSiq3J9Sy5Rscbv_hhAoqmWnyjXMA", "IMG_7388.jpg", "03-06 Козачкова Юля"),
    ("1J_pGuPUNjbfQ_pHy34oIedEJpwGrxY6b", "IMG_7391.jpg", "03-06 Козачкова Юля"),
    ("1HcXPHR2dBYHlAsUEgDI5KQI2FQBl5g4a", "IMG_7393.jpg", "03-06 Козачкова Юля"),
    ("1tKbC2mE4DWY3mCXbn9ft4s5zVouh2AYi", "IMG_7395.jpg", "03-06 Козачкова Юля"),
    ("1aCgvrUQkcUt2LLCEYxrxlCfvzPr5zo3R", "IMG_7397.jpg", "03-06 Козачкова Юля"),
    ("1andiGvlNR5YzQvyxOdbT2hjkXBhf41Zd", "IMG_7399.jpg", "03-06 Козачкова Юля"),
    ("1r9yhJYnTjSaugqDijroh0R9JmOtPpy1Q", "IMG_7401.jpg", "03-06 Козачкова Юля"),
    ("10rVvloU_X3O5uGdIn0LYNLLqlNb2e2qj", "IMG_7403.jpg", "03-06 Козачкова Юля"),
    ("1sMHiz_rVsDayJAx3ni5-0O6PugxdZOFN", "IMG_7405.jpg", "03-06 Козачкова Юля"),
    ("1VhwO2jcDc8XUshSCo2QS4fB2AJxas-sA", "IMG_7407.jpg", "03-06 Козачкова Юля"),
    ("1irXqAr4gVofT4P_pf6uIB-dVkxkjuYJb", "IMG_7410.jpg", "03-06 Козачкова Юля"),
    ("1OmkyAN-ewEiexuLbE0cajrAYdd_ubnP1", "IMG_7414.jpg", "03-06 Козачкова Юля"),
    ("189dKKX_mDwHRY_IKjkNy7mSkETgCHpMc", "IMG_7416.jpg", "03-06 Козачкова Юля"),
    ("1bxOqodAuNPhtHfYMy-sDHQA9m-o-azMI", "IMG_7419.jpg", "03-06 Козачкова Юля"),
    ("1MFfMMPFFH4Ze6dbEnUMvfWzOXdmwz3B1", "IMG_7421.jpg", "03-06 Козачкова Юля"),
    ("12RA0mhmAK-RIzoZzcrRiOaq17e0mlQo7", "IMG_7423.jpg", "03-06 Козачкова Юля"),
    ("1ToGHo38w1ckCYbFL-LcmNz42gOB2xMq5", "IMG_7426.jpg", "03-06 Козачкова Юля"),
    ("1_ryqUY3EbfeBce9OrTKm5l5dDOqc0OAG", "IMG_7427.jpg", "03-06 Козачкова Юля"),
    ("1DD-y2JuonUDK-5uh9JkXe5i3UbXPvA7Y", "IMG_7428.jpg", "03-06 Козачкова Юля"),
    ("13VhAq_R3OcDQDowYpGqrawmgRoHYkvZV", "IMG_7430.jpg", "03-06 Козачкова Юля"),
    ("1jKRfsRTZGbFoqXtpm8H1vwVfdEk9snPS", "IMG_7431.jpg", "03-06 Козачкова Юля"),
    ("1JU-Wa7SgDeT1x9W-fixIcmv-xMb35sVX", "IMG_7432.jpg", "03-06 Козачкова Юля"),
    ("14oaAFJJn6SiJRvL-X8bNAXeSkRM-JVp5", "IMG_7434.jpg", "03-06 Козачкова Юля"),
    ("14VCw8pdJ4jgwgB0WvlR48Nn6Jcf72RqW", "IMG_7439.jpg", "03-06 Козачкова Юля"),
    ("1NzaEu8wX7pRLSSOejEpmPUxtsStihpwo", "IMG_7441.jpg", "03-06 Козачкова Юля"),
    ("1XrNLYZEBSHoCszVsWbSIm-fdnY70akUu", "IMG_7442.jpg", "03-06 Козачкова Юля"),
    ("1xp4DuqRXGipMF7T9a9o_IU7iWLCH2IyX", "IMG_7448.jpg", "03-06 Козачкова Юля"),

    # === folder "Юля" — смешанная (есть личные, отметим, потом отфильтрую визуально) ===
    ("1QRPA0oXsmv9UYVIRLa2UfXcKmTiFagTY", "1.jpg", "Юля"),
    ("1jCedfa7NWjuspSqSnNSBW5fyUkOCC6BG", "CZ6B3490.jpg", "Юля"),
    ("1vI75ifIwW431Zi8coqvCwQq2tGVoS_cR", "CZ6B7316.jpg", "Юля"),
    ("12FRKb2kJNvBOgQ9tuCy_EDcoO5Ms6KQz", "CZ6B7471.JPG", "Юля"),
    ("1T2qoM3FVqrWh9wrkjyJq2qithSfTSCxY", "CZ6B7475.JPG", "Юля"),
    ("1-lvSrbMHQd722sSfk07Y_V_yMQpf3BiR", "DM7A2403.jpg", "Юля"),
    ("1qNX0Rdx-TjjQ-mNHvz4hyi3NfTkIymT4", "DM7A8448.jpg", "Юля"),
    ("1xz0SVVFU2SzDsPL-bQeJ-05Vq-pDp-n7", "DM7A8453.jpg", "Юля"),
    ("1CKJLepuE7SvyRkt9T4YanPrcPnytMzmG", "DM7A8848.jpg", "Юля"),
    ("1GrcsbKXLaVTfe7d5dA7msHZNAoGrKBrt", "DSC_0673.JPG", "Юля"),
    ("1XHErL3xAFZQ08wU1mO6PbbX6oo76MZpj", "DSC_7906.JPG", "Юля"),
]


def main():
    drive.ensure_table()

    inserted, skipped = 0, 0
    for file_id, name, folder in ENTRIES:
        if any(k.lower() in folder.lower() for k in SKIP_KEYWORDS):
            skipped += 1
            continue
        if drive.add_photo(file_id, name, folder):
            inserted += 1

    print(f"✅ Inserted: {inserted}, skipped (personal folders): {skipped}")
    print(f"   Total in catalog: {len(ENTRIES) - skipped}")


if __name__ == "__main__":
    main()
