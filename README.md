# KD Unicode Converter

Kruti Dev 010 (पुराना, non-Unicode) TTF से एक **Unicode देवनागरी फ़ॉन्ट** बनाने वाली Python script।
बने फ़ॉन्ट में Unicode हिंदी पाठ हूबहू Kruti Dev जैसा दिखता है — Word, Notepad, browser सब में।

> **इस repo में कोई फ़ॉन्ट नहीं है।** Kruti Dev की आकृतियाँ उसके मूल स्वामी की हैं।
> आप अपने पास मौजूद Kruti Dev 010 फ़ॉन्ट पर यह script चलाकर अपना फ़ॉन्ट खुद बनाएँ।
> बना फ़ॉन्ट केवल निजी/आंतरिक उपयोग के लिए है — उसे आगे न बाँटें।

## App (सबसे आसान)

1. [Releases](../../releases/latest) से **KD-Unicode-Converter.exe** डाउनलोड करें और चलाएँ (install की ज़रूरत नहीं)।
2. "चुनें…" से अपना Kruti Dev 010 फ़ॉन्ट (.ttf) चुनें; नया फ़ॉन्ट उसी फ़ोल्डर में `<नाम>-Unicode.ttf` बनेगा।
3. **Convert** दबाएँ, फिर "फ़ॉन्ट खोलें (Install)"।

अंग्रेज़ी अक्षरों के लिए Arimo (SIL OFL 1.1) app में साथ आता है; चाहें तो दूसरी Latin TTF चुनें या न जोड़ें।
जो फ़ॉन्ट पहले से Unicode है (जैसे Mangal) उसे app मना कर देता है; जिसके नाम में Kruti न हो उस पर पहले पूछता है।
exe पर digital signature नहीं है — SmartScreen आए तो **More info → Run anyway**।

## कैसे काम करता है

1. हर Unicode अक्षर/मात्रा/संयुक्ताक्षर को Kruti Dev की कुंजी-श्रृंखला से परिभाषित किया गया है (जैसे ख = `[k`, ओ = `vks`)।
2. उन glyphs को अगल-बगल रखकर composite glyph बनता है — मूल outline बदले नहीं जाते।
3. देवनागरी shaping के OpenType नियम (nukt, akhn, rphf, blwf, half, pres, abvs, blws) तालिकाओं से अपने-आप बनते हैं।

## Script से चलाना (Windows, बिना app)

1. Python 3 install करें: <https://www.python.org/downloads/> (install के समय "Add Python to PATH" पर tick)।
2. Command Prompt में एक बार:
   ```
   pip install fonttools
   ```
3. एक फ़ोल्डर में रखें:
   - `KrutiDev010.ttf` — आपका मूल Kruti Dev 010 फ़ॉन्ट
   - `Arimo-Regular.ttf` — अंग्रेज़ी अक्षरों के लिए (वैकल्पिक; [Google Fonts](https://fonts.google.com/specimen/Arimo) से, SIL OFL 1.1)
   - `krutidev_to_unicode_font.py` — यह script
4. उस फ़ोल्डर में चलाएँ:
   ```
   python krutidev_to_unicode_font.py KrutiDev010.ttf KD-Unicode-010.ttf --latin Arimo-Regular.ttf
   ```
5. `KD-Unicode-010.ttf` बन जाएगी (साथ में जाँच के लिए `.fea` फ़ाइल)।

विकल्प:

| विकल्प | काम |
|---|---|
| `--family "नाम"` | फ़ॉन्ट का नाम (default: `KD Unicode 010`) |
| `--latin file.ttf` | अंग्रेज़ी अक्षर इस फ़ॉन्ट से; न दें तो नहीं जुड़ेंगे |

## फ़ॉन्ट install करना

1. Word आदि बंद करें; पुराना "KD Unicode" संस्करण हो तो Settings → Fonts से हटाएँ (मूल Kruti Dev को नहीं)।
2. Restart करें, फिर नई `.ttf` पर right-click → **Install for all users**।
3. Word में Ctrl+A → Ctrl+D → "Latin text" और "Complex scripts" दोनों में `KD Unicode 010` चुनें।
4. Line spacing "Single" या ज़्यादा रखें, वरना रेफ़ (र्) और ि/ी की नोक कट सकती है।

## सुधार / योगदान

कोई संयुक्ताक्षर ग़लत दिखे या नया जोड़ना हो, तो script की `LIGATURES` तालिका में एक पंक्ति जोड़ें/बदलें और फ़ॉन्ट दोबारा बनाएँ।
Kruti Dev 011, 016 आदि की कुंजी-व्यवस्था एक जैसी है, इसलिए script उनसे भी चल सकती है (हर फ़ॉन्ट को परखें)।

## App ख़ुद build करना

```
pip install -r requirements.txt pyinstaller
python kd_unicode_app.py                      # सीधे चलाएँ
```
exe कैसे बनता है, वह `.github/workflows/release.yml` में है (`v*` tag push करने पर GitHub Actions release बनाता है)।

## लाइसेंस

Script और app: MIT ([LICENSE](LICENSE))। साथ आया Arimo फ़ॉन्ट: SIL OFL 1.1 (`Arimo-OFL.txt`)। ये लाइसेंस केवल इस code पर हैं — Kruti Dev फ़ॉन्ट या उससे बने फ़ॉन्ट पर नहीं।
