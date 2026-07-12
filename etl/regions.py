"""Tunisia governorate gazetteer + region resolution.

Single source of truth for the 24 governorates: canonical slug, French and
Arabic names, and a list of aliases (name variants + major cities/delegations)
used to detect which region an article is about.

`geojson_id` is the ISO 3166-2 code used to join map features to slugs.
"""
import re
import unicodedata

# slug -> metadata
GOVERNORATES = {
    "tunis":       {"fr": "Tunis",        "ar": "تونس",       "geojson_id": "TN-11",
                    "aliases": ["tunis", "تونس", "la marsa", "le bardo", "carthage", "goulette", "kram", "sidi bou said"]},
    "ariana":      {"fr": "Ariana",       "ar": "أريانة",     "geojson_id": "TN-12",
                    "aliases": ["ariana", "أريانة", "raoued", "ettadhamen", "soukra", "kalaat el andalous"]},
    "ben-arous":   {"fr": "Ben Arous",    "ar": "بن عروس",    "geojson_id": "TN-13",
                    "aliases": ["ben arous", "بن عروس", "rades", "hammam lif", "megrine", "ezzahra", "mornag", "mourouj"]},
    "manouba":     {"fr": "Manouba",      "ar": "منوبة",      "geojson_id": "TN-14",
                    "aliases": ["manouba", "la manouba", "منوبة", "denden", "oued ellil", "tebourba", "djedeida"]},
    "nabeul":      {"fr": "Nabeul",       "ar": "نابل",       "geojson_id": "TN-21",
                    "aliases": ["nabeul", "نابل", "hammamet", "kelibia", "korba", "menzel temime", "dar chaabane", "beni khalled", "soliman"]},
    "zaghouan":    {"fr": "Zaghouan",     "ar": "زغوان",      "geojson_id": "TN-22",
                    "aliases": ["zaghouan", "زغوان", "el fahs", "bir mcherga", "nadhour", "zriba"]},
    "bizerte":     {"fr": "Bizerte",      "ar": "بنزرت",      "geojson_id": "TN-23",
                    "aliases": ["bizerte", "بنزرت", "menzel bourguiba", "mateur", "ras jebel", "sejnane", "menzel jemil", "tinja"]},
    "beja":        {"fr": "Béja",         "ar": "باجة",       "geojson_id": "TN-31",
                    "aliases": ["beja", "béja", "باجة", "medjez el bab", "testour", "nefza", "goubellat", "teboursouk"]},
    "jendouba":    {"fr": "Jendouba",     "ar": "جندوبة",     "geojson_id": "TN-32",
                    "aliases": ["jendouba", "جندوبة", "tabarka", "ain draham", "bou salem", "fernana", "ghardimaou"]},
    "kef":         {"fr": "Le Kef",       "ar": "الكاف",      "geojson_id": "TN-33",
                    "aliases": ["le kef", "el kef", "الكاف", "kef", "dahmani", "tajerouine", "nebeur", "sers", "jerissa"]},
    "siliana":     {"fr": "Siliana",      "ar": "سليانة",     "geojson_id": "TN-34",
                    "aliases": ["siliana", "سليانة", "makthar", "bou arada", "gaafour", "el krib", "bargou"]},
    "sousse":      {"fr": "Sousse",       "ar": "سوسة",       "geojson_id": "TN-51",
                    "aliases": ["sousse", "سوسة", "msaken", "kalaa kebira", "hammam sousse", "akouda", "enfidha", "kondar", "sidi bou ali"]},
    "monastir":    {"fr": "Monastir",     "ar": "المنستير",   "geojson_id": "TN-52",
                    "aliases": ["monastir", "المنستير", "moknine", "ksar hellal", "jemmal", "sahline", "bekalta", "teboulba", "ksibet el mediouni"]},
    "mahdia":      {"fr": "Mahdia",       "ar": "المهدية",    "geojson_id": "TN-53",
                    "aliases": ["mahdia", "المهدية", "ksour essef", "chebba", "el jem", "sidi alouane", "bou merdes", "melloulech"]},
    "sfax":        {"fr": "Sfax",         "ar": "صفاقس",      "geojson_id": "TN-61",
                    "aliases": ["sfax", "صفاقس", "sakiet ezzit", "sakiet eddaier", "thyna", "kerkennah", "jebeniana", "el hencha", "mahres", "agareb"]},
    "kairouan":    {"fr": "Kairouan",     "ar": "القيروان",   "geojson_id": "TN-41",
                    "aliases": ["kairouan", "القيروان", "haffouz", "sbikha", "oueslatia", "bou hajla", "chebika", "nasrallah"]},
    "kasserine":   {"fr": "Kasserine",    "ar": "القصرين",    "geojson_id": "TN-42",
                    "aliases": ["kasserine", "القصرين", "sbeitla", "feriana", "thala", "foussana", "sbiba", "majel bel abbes"]},
    "sidi-bouzid": {"fr": "Sidi Bouzid",  "ar": "سيدي بوزيد", "geojson_id": "TN-43",
                    "aliases": ["sidi bouzid", "سيدي بوزيد", "regueb", "menzel bouzaiane", "meknassy", "jelma", "bir el hafey", "sidi ali ben aoun"]},
    "gabes":       {"fr": "Gabès",        "ar": "قابس",       "geojson_id": "TN-71",
                    "aliases": ["gabes", "gabès", "قابس", "el hamma", "mareth", "matmata", "ghannouch", "metouia", "menzel habib"]},
    "medenine":    {"fr": "Médenine",     "ar": "مدنين",      "geojson_id": "TN-82",
                    "aliases": ["medenine", "médenine", "مدنين", "djerba", "jerba", "houmt souk", "midoun", "ben gardane", "zarzis", "beni khedache"]},
    "tataouine":   {"fr": "Tataouine",    "ar": "تطاوين",     "geojson_id": "TN-83",
                    "aliases": ["tataouine", "تطاوين", "ghomrassen", "remada", "bir lahmar", "dhehiba", "smar"]},
    "gafsa":       {"fr": "Gafsa",        "ar": "قفصة",       "geojson_id": "TN-72",
                    "aliases": ["gafsa", "قفصة", "metlaoui", "redeyef", "moulares", "el guettar", "sened", "belkhir", "mdhilla"]},
    "tozeur":      {"fr": "Tozeur",       "ar": "توزر",       "geojson_id": "TN-73",
                    "aliases": ["tozeur", "توزر", "nefta", "degache", "tameghza", "hazoua"]},
    "kebili":      {"fr": "Kébili",       "ar": "قبلي",       "geojson_id": "TN-74",
                    "aliases": ["kebili", "kébili", "قبلي", "douz", "souk lahad", "faouar", "el golaa"]},
}

SLUGS = tuple(GOVERNORATES.keys())


def normalize(text: str) -> str:
    """Lowercase, strip diacritics/accents, collapse whitespace.

    Latin accents are removed (é→e); Arabic letters are preserved (their
    combining marks — tashkil — are dropped, which is what we want).
    """
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", stripped).strip()


# Precomputed alias -> slug, normalized, longest-first so multi-word
# place names match before shorter substrings.
def _build_alias_index():
    pairs = []
    for slug, meta in GOVERNORATES.items():
        for alias in meta["aliases"]:
            pairs.append((normalize(alias), slug))
    # longest alias first
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


ALIAS_INDEX = _build_alias_index()


def region_label(slug: str | None) -> str:
    """Human label for a slug (French), or the national bucket label."""
    if slug is None:
        return "National / non localisé"
    meta = GOVERNORATES.get(slug)
    return meta["fr"] if meta else slug


# ── Tagging ────────────────────────────────────────────────────────────────

def _score_regions(title: str, content: str) -> dict[str, int]:
    """Weighted hit counts per governorate. Title hits weigh 3×."""
    title_n = normalize(title or "")
    body_n = normalize(content or "")
    scores: dict[str, int] = {}
    for alias_n, slug in ALIAS_INDEX:
        pattern = r"(?<!\w)" + re.escape(alias_n) + r"(?!\w)"
        t = len(re.findall(pattern, title_n))
        b = len(re.findall(pattern, body_n))
        if t or b:
            scores[slug] = scores.get(slug, 0) + t * 3 + b
    return scores


def tag_region_gazetteer(title: str, content: str = "") -> str | None:
    """Tier 1: deterministic gazetteer match. None if no/ambiguous winner."""
    scores = _score_regions(title, content)
    if not scores:
        return None
    best = max(scores.values())
    winners = [s for s, v in scores.items() if v == best]
    return winners[0] if len(winners) == 1 else None


def tag_region_llm(title: str, content: str = "") -> str | None:
    """Tier 2: LLM disambiguation, validated against the slug set."""
    from etl.llm import complete, FAST_MODEL
    prompt = (
        "Article de presse tunisien. Quel gouvernorat concerne-t-il "
        f"principalement ? Réponds par UN SEUL slug parmi : {', '.join(SLUGS)}, "
        "ou 'national' si aucun ou si ce n'est pas clair.\n\n"
        f"Titre : {title}\n{(content or '')[:800]}\n\nSlug :"
    )
    try:
        out = complete(user=prompt, max_tokens=12, model=FAST_MODEL)
    except Exception:
        return None
    slug = normalize(out).replace(" ", "-")
    return slug if slug in GOVERNORATES else None


def tag_region(title: str, content: str = "", use_llm: bool = True) -> str | None:
    """Resolve an article's region: gazetteer first, LLM fallback."""
    slug = tag_region_gazetteer(title, content)
    if slug:
        return slug
    if use_llm:
        return tag_region_llm(title, content)
    return None
