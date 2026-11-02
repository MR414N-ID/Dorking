#!/usr/bin/env python3
"""Dork Finder - generate query dork + scrape hasil (link).
Pakai : python dorking.py
Butuh : pip install requests beautifulsoup4 pyperclip
BY. MR414N-ID
"""
import sys
import os
import time
import shutil
import webbrowser
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}

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
    print(C["d"] + "Dork Finder  •  Search + Scrape".center(cols) + C["x"])
    print(C["d"] + ("─" * min(cols, 44)).center(cols) + C["x"])
    print()


# ===== DATA =====

REGION_ALIASES = {
    "bandung":    ["bandung", "bdg", "jabar", "jawa barat"],
    "jakarta":    ["jakarta", "jkt", "dki"],
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
    "sosmed":      {"label": "Sosial Media",   "sites": ["instagram.com", "facebook.com", "tiktok.com", "threads.net"]},
    "sosmed_x":    {"label": "Twitter/X",       "sites": ["twitter.com", "x.com"]},
    "marketplace": {"label": "Marketplace",     "sites": ["shopee.co.id", "tokopedia.com", "bukalapak.com", "olx.co.id"]},
    "forum":       {"label": "Forum/Komunitas", "sites": ["kaskus.co.id", "kompasiana.com", "quora.com"]},
    "berita":      {"label": "Berita/Penipuan", "keywords": ["penipuan", "tipu", "laporan", "korban"]},
    "dokumen":     {"label": "Dokumen",         "filetypes": ["pdf", "docx", "xlsx"]},
    "pekerjaan":   {"label": "Profesional",     "sites": ["linkedin.com", "github.com"]},
    "lokal":       {"label": "Lokal (butuh lokasi)", "needs_location": True},
}


# ===== QUERY BUILDER =====

def phone_variants(nomor):
    n = nomor.strip().replace("-", "").replace(" ", "").replace(".", "")
    variants = [n]
    if n.startswith("0"):
        variants += ["+62" + n[1:], "62" + n[1:]]
    elif n.startswith("+62"):
        variants += ["0" + n[3:], "62" + n[3:]]
    elif n.startswith("62"):
        variants += ["0" + n[2:], "+" + n]
    seen, out = set(), []
    for v in variants:
        if v and v not in seen:
            seen.add(v); out.append(v)
    return out


def build_term(fields):
    parts = []
    if fields.get("nama"):
        parts.append(f'"{fields["nama"]}"')
    if fields.get("username"):
        parts.append(f'"{fields["username"].lstrip("@")}"')
    if fields.get("email"):
        parts.append(f'"{fields["email"]}"')
    if fields.get("nomor"):
        pv = phone_variants(fields["nomor"])
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
    lokasi_term = build_location_term(fields.get("lokasi"))
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
            for site in ["olx.co.id", "shopee.co.id"]:
                queries.append((label, f"{base} {lokasi_term} site:{site}"))
    return queries


# ===== SCRAPER =====

def search_ddg(query, max_results=15):
    """Scrape DuckDuckGo HTML endpoint."""
    try:
        r = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "kl": "id-id"},
            headers=HEADERS, timeout=20,
        )
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results, seen = [], set()
        for a in soup.select("a.result__a"):
            href = a.get("href", "")
            if href.startswith("//duckduckgo.com/l/"):
                qs = parse_qs(urlparse("https:" + href).query)
                href = unquote(qs.get("uddg", [""])[0])
            if not href.startswith("http") or href in seen:
                continue
            seen.add(href)
            title = a.get_text(" ", strip=True)
            snippet = ""
            parent = a.find_parent("div", class_="result")
            if parent:
                sn = parent.select_one(".result__snippet")
                if sn:
                    snippet = sn.get_text(" ", strip=True)[:160]
            results.append({"title": title, "url": href, "snippet": snippet})
            if len(results) >= max_results:
                break
        return results
    except Exception:
        return []


def search_bing(query, max_results=15):
    try:
        r = requests.get(
            "https://www.bing.com/search",
            params={"q": query},
            headers=HEADERS, timeout=20,
        )
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        results, seen = [], set()
        for li in soup.select("li.b_algo"):
            a = li.select_one("h2 a")
            if not a:
                continue
            href = a.get("href", "")
            if not href.startswith("http") or href in seen:
                continue
            seen.add(href)
            title = a.get_text(" ", strip=True)
            sn = li.select_one(".b_caption p")
            snippet = sn.get_text(" ", strip=True)[:160] if sn else ""
            results.append({"title": title, "url": href, "snippet": snippet})
            if len(results) >= max_results:
                break
        return results
    except Exception:
        return []


def jalankan_dorking(queries, engine, delay=2.0):
    semua = []
    for i, (label, q) in enumerate(queries, 1):
        print(f"\n{C['d']}[{i}/{len(queries)}] {label}{C['x']}")
        print(f"{C['d']}   Query: {q}{C['x']}")
        if engine == "ddg":
            results = search_ddg(q)
        else:
            results = search_bing(q)
        if results:
            print(f"{C['g']}   → {len(results)} hasil{C['x']}")
            for r in results:
                print(f"     {C['y']}•{C['x']} {C['w']}{r['title'][:70]}{C['x']}")
                print(f"       {C['c']}{r['url']}{C['x']}")
                if r.get("snippet"):
                    print(f"       {C['d']}{r['snippet']}{C['x']}")
        else:
            print(f"{C['r']}   → 0 hasil (kemungkinan diblokir atau kosong){C['x']}")
        semua.append({"label": label, "query": q, "results": results})
        if i < len(queries):
            time.sleep(delay)
    return semua


def ringkasan_dan_simpan(semua, label_file):
    cols = shutil.get_terminal_size((50, 20)).columns
    garis = "=" * min(cols, 50)
    total = sum(len(x["results"]) for x in semua)
    unik = set()
    for x in semua:
        for r in x["results"]:
            unik.add(r["url"])

    print(f"\n{C['c']}{garis}{C['x']}")
    print(f"{C['g']}{C['B']}RINGKASAN{C['x']}")
    print(f"{C['c']}{garis}{C['x']}")
    print(f"{C['y']}Total hasil    : {C['w']}{total}{C['x']}")
    print(f"{C['y']}URL unik       : {C['w']}{len(unik)}{C['x']}")
    print(f"{C['c']}{garis}{C['x']}")

    # URL unik untuk dilihat
    if unik:
        print(f"\n{C['g']}{C['B']}SEMUA URL UNIK (yang belum pernah lihat, prioritas){C['x']}")
        for i, url in enumerate(sorted(unik), 1):
            print(f"{C['y']}{i:2}.{C['x']} {C['c']}{url}{C['x']}")

    fname = f"dork_hasil_{label_file}.txt"
    with open(fname, "w", encoding="utf-8") as fh:
        for x in semua:
            fh.write(f"\n{'=' * 50}\n[{x['label']}] {x['query']}\n{'=' * 50}\n")
            if not x["results"]:
                fh.write("(tidak ada hasil)\n")
            for r in x["results"]:
                fh.write(f"- {r['title']}\n  {r['url']}\n")
                if r.get("snippet"):
                    fh.write(f"  {r['snippet']}\n")
    print(f"\n{C['g']}[+] Hasil lengkap disimpan di {fname}{C['x']}")

    # Opsi buka URL tertentu
    if unik:
        try:
            pilih = input(f"\n{C['y']}[?] Buka URL nomor berapa? (1,2 / all / skip) >> {C['x']}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if not pilih or pilih == "skip":
            return
        urls = sorted(unik)
        if pilih == "all":
            for url in urls:
                webbrowser.open(url)
                time.sleep(0.3)
        else:
            for part in pilih.replace(",", " ").split():
                try:
                    idx = int(part) - 1
                    if 0 <= idx < len(urls):
                        webbrowser.open(urls[idx])
                        time.sleep(0.3)
                except ValueError:
                    pass


# ===== UI =====

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
    print(f"{C['y']}[1]{C['x']} DuckDuckGo {C['d']}(stabil){C['x']}")
    print(f"{C['y']}[2]{C['x']} Bing {C['d']}(kadang diblokir){C['x']}")
    try:
        c = input(f"{C['g']}[?] Pilih (default: 1) >> {C['x']}").strip()
    except (EOFError, KeyboardInterrupt):
        return "ddg"
    return "bing" if c == "2" else "ddg"


def input_fields():
    print(f"\n{C['c']}{C['B']}INPUT TARGET{C['x']}")
    print(f"{C['d']}(kosongkan yang tidak ada — minimal 1 dari nama/username/email/nomor){C['x']}\n")
    try:
        return {
            "nama":     input(f"{C['y']}Nama      >> {C['x']}").strip(),
            "username": input(f"{C['y']}Username  >> {C['x']}").strip(),
            "email":    input(f"{C['y']}Email     >> {C['x']}").strip(),
            "nomor":    input(f"{C['y']}Nomor HP  >> {C['x']}").strip(),
            "lokasi":   input(f"{C['y']}Lokasi    >> {C['x']}").strip(),
        }
    except (EOFError, KeyboardInterrupt):
        return None


def mode_single():
    fields = input_fields()
    if not fields:
        return
    if not any(fields[k] for k in ["nama", "username", "email", "nomor"]):
        print(f"{C['r']}[!] Minimal isi 1 dari: nama / username / email / nomor.{C['x']}")
        return

    categories = pilih_kategori()
    if not categories:
        return
    engine = pilih_mesin()

    queries = generate_queries(fields, categories)
    if not queries:
        print(f"{C['r']}[!] Tidak ada query dihasilkan.{C['x']}")
        return

    print(f"\n{C['y']}[*] Target : {build_term(fields)}{C['x']}")
    if fields.get("lokasi"):
        print(f"{C['y']}[*] Lokasi : {fields['lokasi']}{C['x']}")
    print(f"{C['y']}[*] Mesin  : {engine.upper()}{C['x']}")
    print(f"{C['y']}[*] Query  : {len(queries)} siap dijalankan{C['x']}")
    print(f"{C['d']}(estimasi waktu: ~{len(queries) * 2} detik){C['x']}")

    label_file = (fields["username"] or fields["nama"] or fields["email"] or fields["nomor"] or "target")
    label_file = label_file.replace(" ", "_").replace("@", "").lower()

    semua = jalankan_dorking(queries, engine)
    ringkasan_dan_simpan(semua, label_file)


def mode_batch():
    print(f"\n{C['c']}{C['B']}MODE BATCH{C['x']}")
    print(f"{C['d']}Format: nama|username|email|nomor|lokasi  (kosongkan yang tidak ada){C['x']}")
    print(f"{C['d']}Contoh: Budi Santoso|budisantoso88||081234|Bandung{C['x']}\n")
    try:
        path = input(f"{C['g']}[?] Nama file >> {C['x']}").strip()
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
    engine = pilih_mesin()

    for i, line in enumerate(lines, 1):
        parts = [p.strip() for p in line.split("|")]
        while len(parts) < 5:
            parts.append("")
        fields = {
            "nama": parts[0], "username": parts[1],
            "email": parts[2], "nomor": parts[3], "lokasi": parts[4],
        }
        print(f"\n{C['c']}{'=' * 50}{C['x']}")
        print(f"{C['g']}{C['B']}TARGET [{i}/{len(lines)}]{C['x']}")
        print(f"{C['y']}{build_term(fields)}{C['x']}")
        queries = generate_queries(fields, categories)
        if not queries:
            print(f"{C['r']}(skip — tidak ada query){C['x']}")
            continue
        label = (fields["username"] or fields["nama"] or f"target_{i}").replace(" ", "_").replace("@", "").lower()
        semua = jalankan_dorking(queries, engine)
        ringkasan_dan_simpan(semua, label)


def tampilkan_menu():
    print(f"{C['y']}[1]{C['x']} Cari target (1 orang)")
    print(f"{C['y']}[2]{C['x']} Batch (banyak target dari file)")
    print(f"{C['y']}[q]{C['x']} Keluar")


def main():
    banner()
    while True:
        print(f"\n{C['c']}{C['B']}MENU UTAMA{C['x']}")
        tampilkan_menu()
        try:
            pilih = input(f"\n{C['g']}[?] Pilih >> {C['x']}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(); break
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
