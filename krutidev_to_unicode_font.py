#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
krutidev_to_unicode_font.py
===========================
Kruti Dev 010 (legacy, non-Unicode) TTF की आकृतियों से एक Unicode देवनागरी
फ़ॉन्ट बनाता है, ताकि Unicode हिंदी पाठ हूबहू Kruti Dev जैसा दिखे।

सिद्धांत (सामान्य नियम, किसी एक शब्द के लिए विशेष जुगाड़ नहीं):
  1. हर Unicode अक्षर/मात्रा/संयुक्ताक्षर को Kruti Dev की "कुंजी-श्रृंखला"
     (जैसे ख = "[k", ओ = "vks") से परिभाषित किया गया है।
  2. उस श्रृंखला के glyphs को अगल-बगल रखकर एक composite glyph बनता है
     (मूल outline को छुआ नहीं जाता, इसलिए दिखावट हूबहू रहती है)।
  3. देवनागरी shaping के OpenType नियम (nukt, akhn, rphf, blwf, half, pres,
     abvs, blws) अपने-आप तालिकाओं से बनते हैं।

-------------------------------------------------------------------------------
यह फ़ाइल क्या है
-------------------------------------------------------------------------------
यह वह Python script है जिसने Kruti Dev 010 से "KD Unicode 010" फ़ॉन्ट बनाया।
रोज़ टाइप करने के लिए इसकी ज़रूरत नहीं — केवल बनी हुई .ttf install करें।
इसे भविष्य के लिए रखें:
  * फ़ॉन्ट में सुधार: कोई संयुक्ताक्षर ग़लत दिखे या नया जोड़ना हो, तो नीचे
    की LIGATURES तालिका में एक पंक्ति जोड़/बदलकर फ़ॉन्ट दोबारा बनाएँ।
  * दूसरे Kruti फ़ॉन्टों से बनाना: Kruti Dev 011 (bold), 016 आदि की
    कुंजी-व्यवस्था एक जैसी है, इसलिए यही script उनसे भी Unicode फ़ॉन्ट
    बना सकती है (हर नए फ़ॉन्ट को परखना ज़रूरी है)।

-------------------------------------------------------------------------------
चलाने का तरीका (Windows)
-------------------------------------------------------------------------------
1. Python install करें: https://www.python.org/downloads/
   (install के समय "Add Python to PATH" पर tick लगाएँ)
2. Command Prompt खोलें और एक बार चलाएँ:
       pip install fonttools
3. ये तीन फ़ाइलें एक ही फ़ोल्डर में रखें:
       KrutiDev010.ttf              (मूल Kruti Dev फ़ॉन्ट)
       Arimo-Regular.ttf            (अंग्रेज़ी अक्षरों के लिए, OFL लाइसेंस)
       krutidev_to_unicode_font.py  (यह script)
4. उस फ़ोल्डर में Command Prompt खोलें (फ़ोल्डर के address bar में cmd
   लिखकर Enter) और चलाएँ:
       python krutidev_to_unicode_font.py KrutiDev010.ttf KD-Unicode-010.ttf --latin Arimo-Regular.ttf
5. उसी फ़ोल्डर में KD-Unicode-010.ttf बन जाएगी, साथ में .fea फ़ाइल
   (OpenType नियम, केवल जाँच के लिए)।

अन्य विकल्प:
    --family "कोई नाम"   फ़ॉन्ट का नाम बदलें (default: "KD Unicode 010")
    --latin  file.ttf    अंग्रेज़ी अक्षर/चिह्न इस फ़ॉन्ट से लें; न दें तो
                         अंग्रेज़ी अक्षर नहीं जुड़ेंगे

-------------------------------------------------------------------------------
नया फ़ॉन्ट install करना (Windows)
-------------------------------------------------------------------------------
1. Word, Notepad आदि सभी प्रोग्राम बंद करें।
2. पुराना संस्करण हटाएँ: Settings → Personalization → Fonts → "KD" खोजें →
   फ़ॉन्ट पर क्लिक → Uninstall।  (मूल "Kruti Dev 010" को न हटाएँ।)
3. कंप्यूटर restart करें (Windows का font cache साफ़ होता है)।
4. नई .ttf पर right-click → "Install for all users"।
5. Word में: Ctrl+A → Ctrl+D → "Latin text" और "Complex scripts" दोनों
   खानों में "KD Unicode 010" चुनें।
6. Line spacing: Paragraph → Before/After 0 pt, Line spacing "Single"।
   Single से कम (Multiple < 1 या बहुत कम Exactly) करने पर रेफ़ (र्) और
   ि/ी की ऊपरी नोक कट जाती है।

-------------------------------------------------------------------------------
आवश्यकता और सूचना
-------------------------------------------------------------------------------
आवश्यकता:  Python 3, pip install fonttools
सूचना: Kruti Dev की आकृतियाँ उसके मूल स्वामी की हैं। बना फ़ॉन्ट केवल
निजी/आंतरिक उपयोग के लिए रखें, सार्वजनिक वितरण न करें। अंग्रेज़ी अक्षर
Arimo (SIL Open Font License 1.1) से लिए जाते हैं।
"""

import argparse
import copy
import sys

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent

# ---------------------------------------------------------------------------
# 1. तालिकाएँ : Unicode  ->  Kruti Dev 010 कुंजी-श्रृंखला
# ---------------------------------------------------------------------------

# (अक्षर, glyph-नाम, पूर्ण रूप, आधा रूप या None)
CONSONANTS = [
    ("क", "ka", "d", "D"),
    ("ख", "kha", "[k", "["),
    ("ग", "ga", "x", "X"),
    ("घ", "gha", "Ä", "?"),
    ("ङ", "nga", "³", None),
    ("च", "ca", "p", "P"),
    ("छ", "cha", "N", None),
    ("ज", "ja", "t", "T"),
    ("झ", "jha", ">", "÷"),
    ("ञ", "nya", "´", None),
    ("ट", "tta", "V", None),
    ("ठ", "ttha", "B", None),
    ("ड", "dda", "M", None),
    ("ढ", "ddha", "<", None),
    ("ण", "nna", ".k", "."),
    ("त", "ta", "r", "R"),
    ("थ", "tha", "Fk", "F"),
    ("द", "da", "n", None),
    ("ध", "dha", "/k", "/"),
    ("न", "na", "u", "U"),
    ("प", "pa", "i", "I"),
    ("फ", "pha", "Q", "¶"),
    ("ब", "ba", "c", "C"),
    ("भ", "bha", "Ò", "H"),
    ("म", "ma", "e", "E"),
    ("य", "ya", ";", "¸"),
    ("र", "ra", "j", None),
    ("ल", "la", "y", "Y"),
    ("ळ", "lla", "G", None),
    ("व", "va", "o", "O"),
    ("श", "sha", "'k", "'"),
    ("ष", "ssa", '"k', '"'),
    ("स", "sa", "l", "L"),
    ("ह", "ha", "g", "º"),
]

# जिन व्यंजनों में दाईं खड़ी पाई नहीं है: इनके बाद ्य और ्र का अलग रूप लगता है
NO_STEM = {"nga", "cha", "tta", "ttha", "dda", "ddha", "da", "ha", "lla"}

# पहले से बने नुक्ता वाले Unicode अक्षर -> आधार व्यंजन
NUKTA_PRECOMPOSED = {
    0x0929: "na", 0x0931: "ra", 0x0934: "lla",
    0x0958: "ka", 0x0959: "kha", 0x095A: "ga", 0x095B: "ja",
    0x095C: "dda", 0x095D: "ddha", 0x095E: "pha", 0x095F: "ya",
}

# स्वर, मात्राएँ, चिह्न, अंक, विराम : (अक्षर, glyph-नाम, Kruti श्रृंखला)
SIGNS = [
    ("अ", "a_ind", "v"), ("आ", "aa_ind", "vk"), ("इ", "i_ind", "b"),
    ("ई", "ii_ind", "Ã"), ("उ", "u_ind", "m"), ("ऊ", "uu_ind", "Å"),
    ("ऋ", "vocr_ind", "_"), ("ऍ", "ecandra_ind", ",W"), ("ए", "e_ind", ","),
    ("ऐ", "ai_ind", ",s"), ("ऑ", "ocandra_ind", "v‚"), ("ओ", "o_ind", "vks"),
    ("औ", "au_ind", "vkS"),
    ("ा", "aaMatra", "k"), ("ि", "iMatra", "f"), ("ी", "iiMatra", "h"),
    ("ु", "uMatra", "q"), ("ू", "uuMatra", "w"), ("ृ", "vocrMatra", "`"),
    ("ॅ", "ecandraMatra", "W"), ("े", "eMatra", "s"), ("ै", "aiMatra", "S"),
    ("ॉ", "ocandraMatra", "‚"), ("ो", "oMatra", "¨"), ("ौ", "auMatra", "©"),
    ("्", "virama", "~"), ("़", "nukta", "+"), ("ं", "anusvara", "a"),
    ("ँ", "candrabindu", "¡"), ("ः", "visarga", "%"), ("ऽ", "avagraha", "·"),
    ("।", "danda", "A"), ("॥", "dbldanda", "AA"), ("॰", "abbrev", "ñ"),
    ("०", "zero_deva", "å"), ("१", "one_deva", "ƒ"), ("२", "two_deva", "„"),
    ("३", "three_deva", "…"), ("४", "four_deva", "†"), ("५", "five_deva", "‡"),
    ("६", "six_deva", "ˆ"), ("७", "seven_deva", "‰"), ("८", "eight_deva", "Š"),
    ("९", "nine_deva", "‹"),
    # सामान्य विराम-चिह्न (Kruti Dev में ये दूसरी कुंजियों पर हैं)
    ("0", "zero", "0"), ("1", "one", "1"), ("2", "two", "2"), ("3", "three", "3"),
    ("4", "four", "4"), ("5", "five", "5"), ("6", "six", "6"), ("7", "seven", "7"),
    ("8", "eight", "8"), ("9", "nine", "9"),
    ("!", "exclam", "!"), ("+", "plus", "$"), ("-", "hyphen", "&"),
    ("‐", "hyphen2", "&"), (".", "period", "-"), ("/", "slash", "@"),
    (":", "colon", "%"), (";", "semicolon", "("), ("?", "question", "\\"),
    (",", "comma", "]"), ("(", "parenleft", "¼"), (")", "parenright", "½"),
    ("=", "equal", "¾"), ("{", "braceleft", "¿"), ("}", "braceright", "À"),
    ("‘", "quoteleft", "^"), ("’", "quoteright", "*"), ("'", "quotesingle", "*"),
    ("“", "quotedblleft", "Þ"), ("”", "quotedblright", "ß"), ('"', "quotedbl", "ß"),
    ("÷", "divide", "»"), ("•", "bullet", "Û"),
]

# विशेष रूप (संदर्भ-नियमों में प्रयोग)
SPECIAL = {
    "reph": "Z",            # र् (ऊपर)
    "rakar": "z",           # ्र (पाई वाले व्यंजन के नीचे)
    "rakar.round": "ª",     # ्र (ट ड छ आदि के नीचे)
    "ya.post": "î",         # ्य (ट्य ड्य छ्य आदि)
    "ii_anusvara": "È",     # ीं
    "reph_anusvara": "±",   # र्ं
}

# संयुक्ताक्षर : (Unicode, पूर्ण रूप, आधा रूप या None, feature)
LIGATURES = [
    ("क्ष", "{k", "{", "akhn"),
    ("ज्ञ", "K", None, "akhn"),
    ("त्र", "=", "«", "akhn"),
    ("श्र", "J", None, "akhn"),
    ("स्त्र", "ó", None, "pres"),
    ("क्क", "ô", None, "pres"),
    ("क्त", "ä", None, "pres"),
    ("क्र", "Ø", None, "pres"),
    ("त्त", "Ùk", "Ù", "pres"),
    ("न्न", "é", "™", "pres"),
    ("द्द", "í", None, "pres"),
    ("द्ध", ")", None, "pres"),
    ("द्य", "|", None, "pres"),
    ("द्व", "}", None, "pres"),
    ("द्र", "æ", None, "pres"),
    ("द्म", "ù", None, "pres"),
    ("ट्ट", "ê", None, "pres"),
    ("ट्ठ", "ë", None, "pres"),
    ("ड्ड", "ì", None, "pres"),
    ("ड्ढ", "ï", None, "pres"),
    ("ह्न", "à", None, "pres"),
    ("ह्य", "á", None, "pres"),
    ("ह्म", "ã", None, "pres"),
    ("ह्र", "ºz", None, "pres"),
    ("प्र", "ç", None, "pres"),
    ("फ्र", "Ý", None, "pres"),
    ("रु", "#", None, "blws"),
    ("रू", ":", None, "blws"),
    ("कृ", "Ñ", None, "blws"),
    ("दृ", "–", None, "blws"),
    ("हृ", "â", None, "blws"),
]

VERSION = 1.3

FEATURE_ORDER = ["nukt", "akhn", "rphf", "blwf", "half", "pres", "abvs", "blws"]

# ---------------------------------------------------------------------------
# 2. सहायक
# ---------------------------------------------------------------------------

CONS_BY_CHAR = {c: n for c, n, _, _ in CONSONANTS}
SIGN_BY_CHAR = {c: n for c, n, _ in SIGNS}
HAS_HALF = {n for _, n, _, h in CONSONANTS if h}


def nukta_seq(seq):
    """नुक्ता: पहले glyph के ठीक बाद '+' (जैसे ख़ = '[+k')."""
    return seq[0] + "+" + seq[1:]


def lig_name(ustr):
    parts = []
    for ch in ustr:
        if ch in CONS_BY_CHAR:
            parts.append(CONS_BY_CHAR[ch])
        elif ch in SIGN_BY_CHAR and ch != "्":
            parts.append(SIGN_BY_CHAR[ch])
    return "lig_" + "_".join(parts)


def stage_glyphs(ustr, akhn_map, half_last=False):
    """
    किसी Unicode संयुक्ताक्षर के लिए वह glyph-क्रम लौटाता है जो 'pres' चरण
    तक (akhn, blwf, half के बाद) shaping engine में मौजूद होगा।
    """
    s = ustr
    # akhn संयुक्ताक्षर पहले
    for u, name in sorted(akhn_map.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(u, "\x00" + name + "\x00")
    toks = []
    for part in s.split("\x00"):
        if part.startswith("lig_"):
            toks.append(part)
        else:
            toks.extend(part)
    out = []
    i = 0
    while i < len(toks):
        t = toks[i]
        name = CONS_BY_CHAR.get(t, t if t.startswith("lig_") else SIGN_BY_CHAR.get(t))
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if nxt == "्" and i + 2 < len(toks):
            after = toks[i + 2]
            if after == "र" and i + 3 == len(toks):
                out += [name, "rakar"]
                i += 3
                continue
            if name in HAS_HALF or name + ".half" in HALF_LIG:
                out.append(name + ".half")
            else:
                out += [name, "virama"]
            i += 2
            continue
        out.append(name)
        i += 1
    if half_last:
        out[-1] = out[-1] + ".half"
    return out


HALF_LIG = set()  # akhn संयुक्ताक्षर जिनका आधा रूप है (build में भरा जाता है)


# ---------------------------------------------------------------------------
# 3. फ़ॉन्ट निर्माण
# ---------------------------------------------------------------------------

LATIN_RANGES = [(0x0021, 0x007E), (0x00A1, 0x00FF), (0x2010, 0x203A),
                (0x20A0, 0x20CF), (0x2116, 0x2116), (0x2122, 0x2122), (0x2190, 0x2193),
                (0x2212, 0x2212), (0x00B0, 0x00B0)]


def import_latin(path, src, glyphs, metrics, order, cmap):
    """
    Latin फ़ॉन्ट (जैसे Arimo, OFL) के वे वर्ण जोड़ता है जो Kruti में नहीं हैं।
    आकार का सामान्य नियम: Latin '0' की ऊँचाई = Kruti '0' की ऊँचाई।
    Kruti के अपने अंक/विराम-चिह्न (जो पहले से cmap में हैं) नहीं बदले जाते।
    """
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.pens.transformPen import TransformPen

    lat = TTFont(path)
    if "fvar" in lat:
        from fontTools.varLib import instancer
        lat = instancer.instantiateVariableFont(lat, {"wght": 400})
    lgs, lcm = lat.getGlyphSet(), lat.getBestCmap()
    sgs, scm = src.getGlyphSet(), src.getBestCmap()

    def height(gs, gname):
        bp = BoundsPen(gs); gs[gname].draw(bp)
        return bp.bounds[3] - bp.bounds[1]

    scale = height(sgs, scm[ord("0")]) / height(lgs, lcm[ord("0")])
    lhm = lat["hmtx"]
    done = {}
    for lo, hi in LATIN_RANGES:
        for code in range(lo, hi + 1):
            if code in cmap or code not in lcm:
                continue
            lname = lcm[code]
            gname = "lat." + lname
            if gname not in done:
                rec = DecomposingRecordingPen(lgs)
                lgs[lname].draw(rec)
                pen = TTGlyphPen(None)
                rec.replay(TransformPen(pen, (scale, 0, 0, scale, 0, 0)))
                glyphs[gname] = pen.glyph()
                metrics[gname] = (int(round(lhm[lname][0] * scale)), 0)
                order.append(gname)
                done[gname] = True
            cmap[code] = gname
    print("Latin जोड़े: %d वर्ण (scale %.3f) — %s" % (len(done), scale, path))


def build(src_path, out_path, family, latin_path=None):
    src = TTFont(src_path)
    scmap = src.getBestCmap()
    sglyf = src["glyf"]
    shmtx = src["hmtx"]

    def kd(ch):
        """Kruti कुंजी -> मूल glyph का नया (आंतरिक) नाम"""
        code = ord(ch)
        if code not in scmap:
            raise KeyError("Kruti Dev फ़ॉन्ट में यह कुंजी नहीं: %r" % ch)
        return "kd." + scmap[code]

    # 3.1 मूल glyphs 'kd.' नाम से (components के आधार)
    glyphs, metrics = {}, {}
    order = [".notdef", "space", "uni00A0", "uni200C", "uni200D", "uni25CC"]
    nd = copy.deepcopy(sglyf[".notdef"]) if ".notdef" in sglyf else Glyph()
    glyphs[".notdef"] = nd
    metrics[".notdef"] = shmtx[".notdef"] if ".notdef" in shmtx.metrics else (500, 0)
    space_adv = shmtx[scmap[0x20]][0]
    for n, adv in (("space", space_adv), ("uni00A0", space_adv),
                   ("uni200C", 0), ("uni200D", 0)):
        glyphs[n] = Glyph()
        metrics[n] = (adv, 0)

    # बिंदीदार वृत्त (◌) — अकेली मात्रा दिखाने के लिए
    import math
    pen = TTGlyphPen(None)
    for k in range(12):
        a = 2 * math.pi * k / 12
        cx, cy, r = 260 + 190 * math.cos(a), 330 + 190 * math.sin(a), 22
        pen.moveTo((cx - r, cy - r)); pen.lineTo((cx - r, cy + r))
        pen.lineTo((cx + r, cy + r)); pen.lineTo((cx + r, cy - r)); pen.closePath()
    glyphs["uni25CC"] = pen.glyph()
    metrics["uni25CC"] = (520, 0)

    for gname in src.getGlyphOrder():
        if gname == ".notdef":
            continue
        g = copy.deepcopy(sglyf[gname])
        if g.isComposite():
            for c in g.components:
                c.glyphName = "kd." + c.glyphName
        glyphs["kd." + gname] = g
        metrics["kd." + gname] = shmtx[gname]
        order.append("kd." + gname)

    adv_of = lambda gname: metrics[gname][0]

    def composite(seq):
        g = Glyph()
        g.numberOfContours = -1
        g.components = []
        x = 0
        for ch in seq:
            base = kd(ch)
            c = GlyphComponent()
            c.glyphName = base
            c.x, c.y = x, 0
            c.flags = 0x0004  # ROUND_XY_TO_GRID
            g.components.append(c)
            x += adv_of(base)
        return g, x

    roles = {}  # role-glyph name -> Kruti श्रृंखला

    def add_role(name, seq):
        if name in roles:
            return
        roles[name] = seq
        g, adv = composite(seq)
        glyphs[name] = g
        metrics[name] = (adv, 0)
        order.append(name)

    cmap = {0x20: "space", 0xA0: "uni00A0", 0x200C: "uni200C",
            0x200D: "uni200D", 0x25CC: "uni25CC"}

    for ch, name, full, half in CONSONANTS:
        add_role(name, full)
        cmap[ord(ch)] = name
        add_role(name + ".nukta", nukta_seq(full))
        if half:
            add_role(name + ".half", half)
            add_role(name + ".nukta.half", half + "+")
    for code, base in NUKTA_PRECOMPOSED.items():
        cmap[code] = base + ".nukta"

    for ch, name, seq in SIGNS:
        add_role(name, seq)
        cmap[ord(ch)] = name

    for name, seq in SPECIAL.items():
        add_role(name, seq)

    # डैश: Kruti Dev के '&' (डैश) glyph से; em dash उसे क्षैतिज रूप से खींचकर
    for code, name, sx in ((0x2013, "endash", 1.0), (0x2014, "emdash", 1.8),
                           (0x2212, "minus", 1.0)):
        base = kd("&")
        g = Glyph(); g.numberOfContours = -1
        c = GlyphComponent(); c.glyphName = base; c.x = c.y = 0; c.flags = 0x0004
        if sx != 1.0:
            c.transform = [[sx, 0], [0, 1]]
        g.components = [c]
        glyphs[name] = g
        metrics[name] = (int(round(adv_of(base) * sx)), 0)
        order.append(name)
        cmap[code] = name

    # अंग्रेज़ी (Latin) अक्षर व चिह्न: दूसरे फ़ॉन्ट से, Kruti अंकों की ऊँचाई पर
    if latin_path:
        import_latin(latin_path, src, glyphs, metrics, order, cmap)

    akhn_map = {}
    for u, full, half, feat in LIGATURES:
        n = lig_name(u)
        add_role(n, full)
        if half:
            add_role(n + ".half", half)
        if feat == "akhn":
            akhn_map[u] = n
            if half:
                HALF_LIG.add(n)

    # 3.2 OpenType नियम (.fea) — तालिकाओं से अपने-आप
    fea = {f: [] for f in FEATURE_ORDER}
    for ch, name, full, half in CONSONANTS:
        fea["nukt"].append("sub %s nukta by %s.nukta;" % (name, name))
        if half:
            fea["half"].append("sub %s virama by %s.half;" % (name, name))
            fea["half"].append("sub %s.nukta virama by %s.nukta.half;" % (name, name))
    fea["rphf"].append("sub ra virama by reph;")
    fea["blwf"].append("sub virama ra by rakar;")

    pres_rules = []
    for u, full, half, feat in LIGATURES:
        n = lig_name(u)
        if feat == "akhn":
            src_seq = [CONS_BY_CHAR.get(c, "virama") for c in u]
            fea["akhn"].append("sub %s by %s;" % (" ".join(src_seq), n))
            if half:
                fea["half"].append("sub %s virama by %s.half;" % (n, n))
            continue
        variants = [(n, full, stage_glyphs(u, akhn_map))]
        if half:
            variants.append((n + ".half", half, stage_glyphs(u, akhn_map, half_last=True)))
        # नियम A: नुक्ता वाला पहला व्यंजन (फ़्र, ज़्य ...) — '+' पहले glyph के बाद
        first = CONS_BY_CHAR.get(u[0])
        if first in set(NUKTA_PRECOMPOSED.values()):
            for vn, vseq, st in list(variants):
                st2 = list(st)
                st2[0] = st2[0].replace(first, first + ".nukta", 1)
                add_role(vn + ".nukta", nukta_seq(vseq))
                variants.append((vn + ".nukta", None, st2))
        for vn, vseq, st in variants:
            pres_rules.append((len(st), "sub %s by %s;" % (" ".join(st), vn), feat))
            # नियम B: जिस संयुक्ताक्षर में दृश्य हलंत है (द्व, द्ध, ट्ट ...), वहाँ
            # shaping engine ि को हलंत के बाद रखता है -> ि सहित पूरा रूप
            if "virama" in st:
                v = len(st) - 1 - st[::-1].index("virama")
                sti = st[:v + 1] + ["iMatra"] + st[v + 1:]
                add_role(vn + ".i", "f" + roles[vn])
                pres_rules.append((len(sti), "sub %s by %s.i;" % (" ".join(sti), vn), feat))
    # लंबे संयुक्ताक्षर पहले
    for _, rule, feat in sorted(pres_rules, key=lambda r: -r[0]):
        fea[feat].append(rule)

    fea["abvs"].append("sub iiMatra anusvara by ii_anusvara;")
    fea["abvs"].append("sub reph anusvara by reph_anusvara;")

    nostem = " ".join(sorted(NO_STEM | {n + ".nukta" for n in NO_STEM}))
    lines = [
        "languagesystem dev2 dflt;",
        "languagesystem deva dflt;",
        "@NOSTEM = [%s];" % nostem,
        "lookup YAPOST { sub virama ya by ya.post; } YAPOST;",
        "lookup RKRRND { sub rakar by rakar.round; } RKRRND;",
    ]
    # GDEF: शून्य-चौड़ाई वाले चिह्न (मात्रा/बिंदु/रेफ़/रकार) = MARK, संयुक्ताक्षर = LIGATURE
    mark_g, lig_g, base_g = [], [], []
    for name, seq in roles.items():
        w = sum(adv_of(kd(ch)) for ch in seq)
        if w < 20:
            mark_g.append(name)
        elif name.startswith("lig_"):
            lig_g.append(name)
        else:
            base_g.append(name)
    lines.append("table GDEF { GlyphClassDef [%s], [%s], [%s], ; } GDEF;"
                 % (" ".join(base_g), " ".join(lig_g), " ".join(mark_g)))
    for f in FEATURE_ORDER:
        body = list(fea[f])
        if f == "pres":
            body = ["lookup PRESLIG {"] + body + ["} PRESLIG;",
                    "sub @NOSTEM virama' lookup YAPOST ya';",
                    "sub @NOSTEM rakar' lookup RKRRND;"]
        if body:
            lines.append("feature %s {" % f)
            lines += ["    " + b for b in body]
            lines.append("} %s;" % f)
    # न्यूनतम GPOS (शून्य-मान): Windows-अनुकूल फ़ॉन्टों जैसी संरचना
    lines.append("feature dist { pos virama 0; } dist;")
    fea_text = "\n".join(lines) + "\n"

    # 3.3 फ़ॉन्ट जोड़ना
    fb = FontBuilder(src["head"].unitsPerEm, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    gt = fb.font["glyf"]
    hm = {}
    for gname in order:
        g = gt[gname]
        g.recalcBounds(gt)
        hm[gname] = (metrics[gname][0], getattr(g, "xMin", 0) if g.numberOfContours else 0)
    fb.setupHorizontalMetrics(hm)
    sh = src["hhea"]
    fb.setupHorizontalHeader(ascent=sh.ascent, descent=sh.descent, lineGap=sh.lineGap)
    ps = family.replace(" ", "") + "-Regular"
    fb.setupNameTable({
        "familyName": family,
        "styleName": "Regular",
        "uniqueFontIdentifier": ps + ";personal-conversion",
        "fullName": family + " Regular",
        "psName": ps,
        "version": "Version %.3f" % VERSION,
        "description": "Unicode conversion of Kruti Dev 010 glyphs. "
                       "Personal/internal use only; not for redistribution. "
                       "Latin glyphs (if present) from Arimo, SIL Open Font License 1.1.",
    })
    so = src["OS/2"]
    fb.setupOS2(
        version=4,
        sTypoAscender=sh.ascent, sTypoDescender=sh.descent, sTypoLineGap=sh.lineGap,
        usWinAscent=so.usWinAscent, usWinDescent=so.usWinDescent,
        achVendID="KDUC", fsType=0, usWeightClass=400, fsSelection=0x40,
        ulUnicodeRange1=(1 << 0) | (1 << 1) | (1 << 15) | (1 << 31),  # Latin, Latin-1, Devanagari, Gen. Punct.
        ulUnicodeRange2=(1 << 1),  # Currency symbols
        ulCodePageRange1=1,
        sxHeight=500, sCapHeight=700, panose=so.panose,
    )
    fb.setupPost()
    # TrueType hinting कार्यक्रम मूल से
    for tag in ("fpgm", "prep", "cvt ", "gasp"):
        if tag in src:
            fb.font[tag] = copy.deepcopy(src[tag])
    fb.font["head"].fontRevision = VERSION

    addOpenTypeFeaturesFromString(fb.font, fea_text)
    # खाली DSIG: इसके बिना MS Office (Word) OpenType नियम नहीं लगाता
    dsig = newTable("DSIG")
    dsig.ulVersion, dsig.usFlag, dsig.usNumSigs = 1, 0, 0
    dsig.signatureRecords = []
    fb.font["DSIG"] = dsig

    mp, smp = fb.font["maxp"], src["maxp"]
    mp.recalc(fb.font)
    # TrueType hinting के लिए आवश्यक maxp मान मूल फ़ॉन्ट से
    for attr in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs",
                 "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions"):
        if hasattr(smp, attr):
            setattr(mp, attr, max(getattr(smp, attr), getattr(mp, attr, 0) or 0))
    fb.save(out_path)
    with open(out_path + ".fea", "w", encoding="utf-8") as fh:
        fh.write(fea_text)
    print("बन गया: %s  (%d glyphs, %d Unicode वर्ण)" % (out_path, len(order), len(cmap)))


def main():
    # Windows console (cp1252 आदि) में हिंदी print पर crash न हो
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Kruti Dev 010 -> Unicode फ़ॉन्ट")
    ap.add_argument("src", help="मूल Kruti Dev 010 TTF")
    ap.add_argument("out", help="बनने वाली Unicode TTF")
    ap.add_argument("--family", default="KD Unicode 010")
    ap.add_argument("--latin", default=None,
                    help="अंग्रेज़ी अक्षरों के लिए Latin TTF (जैसे Arimo-Regular.ttf, OFL)")
    a = ap.parse_args()
    build(a.src, a.out, a.family, a.latin)


if __name__ == "__main__":
    sys.exit(main())
