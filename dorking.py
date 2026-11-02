#!/usr/bin/env python3
"""Dork Generator - buat query dork OSINT (nama/username/email/nomor/lokasi).
Pakai : python dorking.py
Butuh : pip install pyperclip   (opsional, buat fitur salin)
BY. MR414N-ID
"""
import sys
import os
import time
import shutil
import webbrowser
from urllib.parse import quote_plus

C = {
    "r": "\033[91m", "g": "\033[92m", "y": "\033[93m", "b": "\033[94m",
    "m": "\033[95m", "c": "\033[96m", "w": "\033[97m", "d": "\033[90m",
    "x": "\033[0m", "B": "\033[1m",
}

FONT = {
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #"],
    "R": ["#### ", "#   #", "#### ", "#  # ", "#   #"],
    "4": ["#  # ", "#  # ", "#####", "   # ", "   # "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", " ### "],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #"],
    "-": ["     ", "     ", " ### ", "     ", "     "],
    "I": ["###", " # ", " # ", " # ", "###"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#### "],
}

TUX = [
    "      .--.      ",
    "     |o_o |     ",
    "     |:_/ |     ",
    "    //   \\ \\    ",
    "   (|     | )   ",
    "  /'\\_   _/`\\   ",
    "  \\___)=(___/   ",
]


def blok(teks):
    baris = [""] * 5
    for ch in teks:
        for i in range(5):
            baris[i] += FONT[ch][i].replace("#", "█") + " "
    return baris


def banner():
    os.system("clear")
    cols = shutil.get_terminal_size((50, 20)).columns
    print()
    for line in TUX:
        print(C["y"] + C["B"] + line.center(cols) + C["x"])
        time.sleep(0.05)
    print()
    teks = ["MR414N-ID"]
    if sum(len(FONT[c][0]) + 1 for c in teks[0]) > cols:
        teks = ["MR414N", "-ID"]
    warna = ["r", "y", "g", "c", "m"]
    for t in teks:
        for i, row in enumerate(blok(t)):
            print(C[warna[i % len(warna)]] + C["B"] + row.center(cols) + C["x"])
            time.sleep(0.05)
    print()
    print(C["c"] + C["B"] + "BY. MR414N-ID".center(cols) + C["x"])
    print(C["d"] + "Dork Generator  •  OSINT Indonesia".center(cols) + C["x"])
    print(C["d"] + ("─" * min(cols, 44)).center(cols) + C["x"])
    print()


# ===== DATA =====

REGION_ALIASES = {
    "bandung":    ["bandung", "bdg", "jabar", "jawa barat"],
    "jakarta":    ["jakarta", "jkt", "dki", "jakarta pusat", "jakarta selatan"],
    "surabaya":   ["surabaya", "sby", "jatim", "jawa timur"],
    "yogyakarta": ["yogyakarta", "jogja", "yogya", "diy"],
    "semarang":   ["semarang", "smg"],
    "medan":      ["medan", "mdn"],
    "makassar":   ["makassar", "mks", "ujungpandang"],
    "palembang":  ["palembang", "plg"],
    "denpasar":   ["denpasar", "bali", "dps"],
    "malang":     ["malang", "mlg"],
    "solo":       ["solo", "surakarta", "skt"],
    "bogor":      ["bogor", "bgr"],
    "depok":      ["depok", "dpk"],
    "tangerang":  ["tangerang", "tgr"],
    "bekasi":     ["bekasi", "bks"],
}

CATEGORIES = {
    "sosmed": {
        "label": "Sosial Media",
        "sites": ["instagram.com", "facebook.com", "tiktok.com", "threads.net"],
    },
    "sosmed_x": {
        "label": "Twitter/X",
        "sites": ["twitter.com", "x.com"],
    },
    "marketplace": {
        "label": "Marketplace",
        "sites": ["shopee.co.id", "tokopedia.com", "bukalapak.com", "olx.co.id", "lazada.co.id"],
    },
    "forum": {
        "label": "Forum/Komunitas",
        "sites": ["kaskus.co.id", "kompasiana.com", "quora.com", "reddit.com"],
    },
    "berita": {
        "label": "Berita/Kasus Penipuan",
        "keywords": ["penipuan", "tipu", "laporan", "modus", "korban", "penipu"],
    },
    "dokumen": {
        "label": "Dokumen Bocor/Publik",
        "filetypes": ["pdf", "docx", "xlsx", "txt"],
    },
    "pekerjaan": {
        "label": "Profesional",
        "sites": ["linkedin.com", "github.com", "gitlab.com"],
    },
    "lokal": {
        "label": "Lokal Indonesia (butuh lokasi)",
        "needs_location": True,
    },
}

SEARCH_ENGINES = {
    "google": "https://www.google.com/search?q={}",
    "bing": "https://www.bing.com/search?q={}",
    "duckduckgo": "https://duckduckgo.com/?q={}",
    "yandex": "https://yandex.com/search/?text={}",
}


# ===== QUERY BUILDER =====

def phone_variants(nomor):
    n = nomor.strip().replace("-", "").replace(" ", "").replace(".", "")
    variants = [n]
    if n.startswith("0"):
        variants.append("+62" + n[1:])
        variants.append("62" + n[1:])
    elif n.startswith("+62"):
        variants.append("0" + n[3:])
        variants.append("62" + n[3:])
    elif n.startswith("62"):
        variants.append("0" + n[2:])
        variants.append("+" + n)
    # dedupe while preserving order
    seen = set()
    out = []
    for v in variants:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def build_term(fields):
    """Gabung semua field terisi jadi 1 query-term."""
    parts = []
    nama = fields.get("nama", "").strip()
    username = fields.get("username", "").strip().lstrip("@")
    email = fields.get("email", "").strip()
    nomor = fields.get("nomor", "").strip()

    if nama:
        parts.append(f'"{nama}"')
    if username:
        parts.append(f'"{username}"')
    if email:
        parts.append(f'"{email}"')
    if nomor:
        pv = phone_variants(nomor)
        if len(pv) == 1:
            parts.append(f'"{pv[0]}"')
        else:
            parts.append("(" + " OR ".join(f'"{v}"' for v in pv) + ")")

    return " ".join(parts)


def build_location_term(lokasi):
    if not lokasi:
        return ""
    lok = lokasi.lower().strip()
    aliases = REGION_ALIASES.get(lok, [lok])
    if len(aliases) == 1:
        return f'"{aliases[0]}"'
    return "(" + " OR ".join(f'"{a}"' for a in aliases) + ")"


def generate_queries(fields, categories):
    base = build_term(fields)
    if not base:
        return []
    lokasi_term = build_location_term(fields.get("lokasi", ""))

    queries = []
    for key in categories:
        cat = CATEGORIES[key]
        label = cat["label"]

        if "sites" in cat:
            for site in cat["sites"]:
                q = f"{base} site:{site}"
                if lokasi_term:
                    q += f" {lokasi_term}"
                queries.append((label, q))

        elif "keywords" in cat:
            kw = " OR ".join(cat["keywords"])
            q = f"{base} ({kw})"
            if lokasi_term:
                q += f" {lokasi_term}"
            queries.append((label, q))

        elif "filetypes" in cat:
            for ft in cat["filetypes"]:
                q = f"{base} filetype:{ft}"
                if lokasi_term:
                    q += f" {lokasi_term}"
                queries.append((label, q))

        elif cat.get("needs_location"):
            if not lokasi_term:
                continue
            queries.append((label, f"{base} {lokasi_term} (toko OR jasa OR umkm OR penipuan)"))
            for site in ["olx.co.id", "shopee.co.id", "kaskus.co.id"]:
                queries.append((label, f"{base} {lokasi_term} site:{site}"))

    return queries


# ===== UI =====

def tampilkan_queries(queries):
    cols = shutil.get_terminal_size((50, 20)).columns
    garis = "=" * min(cols, 50)
    print(f"\n{C['c']}{garis}{C['x']}")
    print(f"{C['g']}{C['B']} {len(queries)} QUERY DORK DIBUAT{C['x']}")
    print(f"{C['c']}{garis}{C['x']}\n")
    for i, (label, q) in enumerate(queries, 1):
        print(f"{C['y']}{i:2}.{C['x']} {C['d']}[{label}]{C['x']}")
        print(f"    {C['w']}{q}{C['x']}")
    print()


def buka_query(q, mesin):
    url = SEARCH_ENGINES[mesin].format(quote_plus(q))
    webbrowser.open(url)


def eksekusi(queries, mesin, target_label):
    try:
        choice = input(
            f"{C['g']}[?] Buka nomor (1,2,3 / all / salin / simpan / skip) >> {C['x']}"
        ).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    if not choice or choice == "skip":
        return

    if choice == "all":
        print(f"{C['y']}[*] Membuka {len(queries)} tab di browser...{C['x']}")
        for i, (_, q) in enumerate(queries, 1):
            buka_query(q, mesin)
            print(f"{C['d']}   [{i}/{len(queries)}] {q}{C['x']}")
            time.sleep(0.4)
        return

    if choice == "salin":
        text = "\n".join(f"{i}. {q}" for i, (_, q) in enumerate(queries, 1))
        try:
            import pyperclip
            pyperclip.copy(text)
            print(f"{C['g']}[+] {len(queries)} query disalin ke clipboard.{C['x']}")
        except ImportError:
            print(f"{C['r']}[!] pyperclip belum terinstall. Jalankan: pip install pyperclip{C['x']}")
            print(text)
        return

    if choice == "simpan":
        fname = f"dork_{target_label}.txt"
        with open(fname, "w", encoding="utf-8") as fh:
            for i, (label, q) in enumerate(queries, 1):
                fh.write(f"{i}. [{label}] {q}\n")
        print(f"{C['g']}[+] Disimpan di {fname}{C['x']}")
        return

    indices = []
    for part in choice.replace(",", " ").split():
        try:
            idx = int(part) - 1
            if 0 <= idx < len(queries):
                indices.append(idx)
        except ValueError:
            pass

    for i in indices:
        label, q = queries[i]
        buka_query(q, mesin)
        print(f"{C['g']}[+] [{label}] {q}{C['x']}")
        time.sleep(0.4)


def pilih_kategori():
    print(f"\n{C['c']}{C['B']}PILIH KATEGORI{C['x']}")
    print(f"{C['y']}[all]{C['x']} semua kategori")
    keys = list(CATEGORIES.keys())
    for i, k in enumerate(keys, 1):
        print(f"{C['y']}[{i}]{C['x']} {CATEGORIES[k]['label']}")

    try:
        c = input(f"\n{C['g']}[?] Pilih (all / 1,2,3) >> {C['x']}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return None

    if not c or c == "all":
        return keys
    chosen = []
    for part in c.replace(",", " ").split():
        try:
            idx = int(part) - 1
            if 0 <= idx < len(keys):
                chosen.append(keys[idx])
        except ValueError:
            pass
    return chosen or keys


def pilih_mesin():
    print(f"\n{C['c']}{C['B']}MESIN PENCARI{C['x']}")
    engines = ["google", "bing", "duckduckgo", "yandex"]
    labels = ["Google", "Bing", "DuckDuckGo", "Yandex"]
    for i, l in enumerate(labels, 1):
        print(f"{C['y']}[{i}]{C['x']} {l}")
    try:
        c = input(f"{C['g']}[?] Pilih (default: 1) >> {C['x']}").strip()
    except (EOFError, KeyboardInterrupt):
        return "google"
    if c.isdigit() and 1 <= int(c) <= len(engines):
        return engines[int(c) - 1]
    return "google"


# ===== MODES =====

def mode_single():
    print(f"\n{C['c']}{C['B']}INPUT TARGET{C['x']}")
    print(f"{C['d']}(kosongkan yang tidak ada — minimal 1 dari nama/username/email/nomor){C['x']}\n")
    fields = {}
    try:
        fields["nama"]     = input(f"{C['y']}Nama      >> {C['x']}").strip()
        fields["username"] = input(f"{C['y']}Username  >> {C['x']}").strip()
        fields["email"]    = input(f"{C['y']}Email     >> {C['x']}").strip()
        fields["nomor"]    = input(f"{C['y']}Nomor HP  >> {C['x']}").strip()
        fields["lokasi"]   = input(f"{C['y']}Lokasi    >> {C['x']}").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not any(fields[k] for k in ["nama", "username", "email", "nomor"]):
        print(f"{C['r']}[!] Minimal isi 1 dari: nama / username / email / nomor.{C['x']}")
        return

    categories = pilih_kategori()
    if not categories:
        return

    mesin = pilih_mesin()

    queries = generate_queries(fields, categories)
    if not queries:
        print(f"{C['r']}[!] Tidak ada query dihasilkan. Cek input.{C['x']}")
        return

    print(f"\n{C['y']}[*] Target : {build_term(fields)}{C['x']}")
    if fields.get("lokasi"):
        print(f"{C['y']}[*] Lokasi : {fields['lokasi']}{C['x']}")
    print(f"{C['y']}[*] Mesin  : {mesin.upper()}{C['x']}")

    tampilkan_queries(queries)

    label_file = (fields.get("username") or fields.get("nama") or
                  fields.get("email") or fields.get("nomor") or "target")
    label_file = label_file.replace(" ", "_").replace("@", "").lower()

    eksekusi(queries, mesin, label_file)


def mode_batch():
    print(f"\n{C['c']}{C['B']}MODE BATCH{C['x']}")
    print(f"{C['d']}Format baris: nama|username|email|nomor|lokasi  (kosongkan yang tidak ada){C['x']}")
    print(f"{C['d']}Contoh: Budi Santoso|budisantoso88||081234|Bandung{C['x']}\n")

    try:
        path = input(f"{C['g']}[?] Nama file (contoh: target.txt) >> {C['x']}").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not path or not os.path.exists(path):
        print(f"{C['r']}[!] File tidak ditemukan: {path}{C['x']}")
        return

    with open(path, "r", encoding="utf-8") as fh:
        lines = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]

    if not lines:
        print(f"{C['r']}[!] File kosong.{C['x']}")
        return

    categories = pilih_kategori()
    if not categories:
        return
    mesin = pilih_mesin()

    for i, line in enumerate(lines, 1):
        parts = [p.strip() for p in line.split("|")]
        while len(parts) < 5:
            parts.append("")
        fields = {
            "nama": parts[0], "username": parts[1],
            "email": parts[2], "nomor": parts[3], "lokasi": parts[4],
        }
        print(f"\n{C['c']}{'=' * 44}{C['x']}")
        print(f"{C['g']}{C['B']}TARGET [{i}/{len(lines)}]{C['x']}")
        print(f"{C['y']}{build_term(fields)}{C['x']}")
        if fields["lokasi"]:
            print(f"{C['d']}Lokasi: {fields['lokasi']}{C['x']}")
        queries = generate_queries(fields, categories)
        tampilkan_queries(queries)
        label = (fields["username"] or fields["nama"] or f"target_{i}").replace(" ", "_").replace("@", "").lower()
        eksekusi(queries, mesin, label)


# ===== MAIN =====

def tampilkan_menu():
    print(f"{C['y']}[1]{C['x']} Generate dork {C['d']}(1 target){C['x']}")
    print(f"{C['y']}[2]{C['x']} Batch {C['d']}(banyak target dari file .txt){C['x']}")
    print(f"{C['y']}[q]{C['x']} Keluar")


def main():
    banner()
    while True:
        print(f"\n{C['c']}{C['B']}MENU UTAMA{C['x']}")
        tampilkan_menu()
        try:
            pilih = input(f"\n{C['g']}[?] Pilih >> {C['x']}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if pilih in ("q", "quit", "exit"):
            break
        elif pilih == "1":
            mode_single()
        elif pilih == "2":
            mode_batch()
        else:
            print(f"{C['r']}Pilihan tidak valid.{C['x']}")

    print(C["c"] + "\nTerima kasih!  —  BY. MR414N-ID" + C["x"])


if __name__ == "__main__":
    main()
