"""Profil karakter & gaya konten bersama untuk IP animasi Denn & Miki."""

from __future__ import annotations

# Ubah profil di bawah kapan saja; perubahan otomatis dipakai oleh Agent konten (Agent 1, 2, dst.).
CHARACTER_PROFILE: dict[str, str] = {
    "nama_duo": "Denn & Miki",
    "sifat_denn": "Agak santai, sarkas, polos di saat tertentu, tapi diam-diam suka overthinking hal sepele.",
    "sifat_miki": "Lebih heboh, logis, cepat bereaksi, dan suka nyeletuk jujur tanpa filter.",
    "relasi": "Sahabat karib / duo tongkrongan yang sering nongkrong dan ngomentari kejadian sehari-hari.",
    "gaya_humor": (
        "Slice of life relatable anak muda Indonesia, sedikit absurd atau ironis, "
        "dialog singkat dan natural ala bahasa sehari-hari."
    ),
    "format_konten": "Animasi storytelling vertikal durasi 30-60 detik untuk TikTok, IG Reels, dan YouTube Shorts.",
}

# Profil jasa pembuatan website UMKM (dipakai bersama oleh Agent 3 & Agent 5).
# Silakan sesuaikan nama brand, keunggulan, dan kisaran harga Anda di sini.
WEB_SERVICE_PROFILE: dict[str, str] = {
    "nama_layanan": "Jasa Pembuatan Website UMKM Lokal",
    "fokus_layanan": (
        "Website profil usaha, katalog produk/menu online, tombol order langsung ke WhatsApp, "
        "dan tampilan ramah HP (mobile-friendly) yang membantu usaha terlihat lebih profesional di Google."
    ),
    "keunggulan": (
        "Desain modern & ringan dibuka di HP, harga ramah UMKM, proses cepat, "
        "dan bisa dibuatkan contoh konsep/demo halaman depan dulu agar pemilik usaha punya gambaran jelas."
    ),
    "gaya_komunikasi": (
        "Ramah, sopan, membumi (tanpa jargon teknis IT yang bikin bingung pemilik UMKM), "
        "personal, dan tidak terkesan spam atau memaksa."
    ),
}
