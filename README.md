# GF Drop — Transfer Without Limits.

Ayni agdaki (ya da internet modunda herhangi bir agdaki) cihazlar arasi dosya aktarimi. PC'de Flask sunucusu + web arayuzu,
telefon/Mac/iPhone tarayicidan QR ile baglanir.

## Yapi
| Yol | Gorev |
|---|---|
| `app.py` | Sunucu: eslesme (QR/token), yukle/indir, gecmis, guncelleme, Discord, tunel, baslangic |
| `static/index.html`, `app.css`, `app.js` | Arayuz (TR/EN sozlugu `app.js` basinda `T` nesnesi) |
| `installer/GFDrop.iss` | Windows kurulum paketi (Inno Setup) |
| `tests/test_smoke.py` | Duman testleri (`pytest -q`) |
| `.github/workflows/build.yml` | Test + exe + Setup + Release |

## Gelistirme
    pip install -r requirements-dev.txt
    python app.py            # pencere acar   |  python app.py --background  # sadece sunucu
    pytest -q
Veri klasoru: `%USERPROFILE%\GFDrop` (degistirmek icin `GFDROP_DATA`). Ayarlar: `config.json` (ornek: `config.example.json`).

## Surum yayinlama (otomatik guncelleme buradan beslenir)
1. `app.py` icinde `VERSION` degerini artir (ornek `0.2.1`).
2. GitHub > Releases > Create new release > etiket `v0.2.1` > Publish.
3. Actions test eder, `GFDrop-Setup.exe` ve `GFDrop.exe` uretip Release'e ekler.
4. Calisan uygulamalar acilista yeni surumu gorur; Ayarlar > "Indir ve yukle" sessizce kurar ve yeniden acar.

## Guvenlik notlari
- Host = yalnizca localhost'tan, proxy basligi olmayan istek. Tunelden gelenler host sayilmaz.
- Cihazlar QR'daki token ile eslesir; Ayarlar > "Eslesmeleri sifirla" token'i yeniler.
- `client_secret` sadece kullanicinin `config.json` dosyasinda durur, depoya konmaz.

## Yol haritasi
Android uygulamasi (WebView + yerel kesif) · tarayicidan indirmede ilerleme · coklu dosya zip · sifreli aktarim · macOS surumu
