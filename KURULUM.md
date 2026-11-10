# GF Drop - Kurulum (telefondan)

## 1) Dosyalari GitHub'a yukle (Termux)
    termux-setup-storage
    pkg install -y git unzip
    cd ~ && unzip /sdcard/Download/gfdrop.zip -d gfdrop && cd gfdrop
    git init && git add -A && git commit -m "GF Drop 0.1.0"
    git branch -M main
    git remote add origin https://github.com/KULLANICI/DEPO.git
    git push -u origin main        # sifre yerine GitHub Token (PAT) yapistirilir

## 2) Logo
static/logo.png olarak ekle (yoksa yazi logo gorunur).

## 3) EXE uret
GitHub > Actions > build-exe > Run workflow  -> Artifacts > GFDrop.exe
(Surum yayini icin:  git tag v0.1.0 && git push origin v0.1.0  -> Releases'e GFDrop.exe girer)

## 4) PC'de ilk calistirma
- GFDrop.exe'yi ac. Guvenlik Duvari sorarsa "ozel aglara" izin ver (yoksa telefon baglanamaz).
- Olusan %USERPROFILE%\GFDrop\config.json icine client_secret, invite, github_repo yaz.

## 5) Discord
discord.com/developers/applications > GF Drop > OAuth2:
Client Secret al, Redirects'e ekle: http://127.0.0.1:8765/auth/discord/callback
