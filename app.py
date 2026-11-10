"""GF Drop - PC tarafi (Flask). Telefon/Mac/iPhone tarayicidan QR ile baglanir."""
import io, os, sys, json, time, socket, secrets, threading, subprocess, webbrowser
from pathlib import Path
import requests
from flask import Flask, request, jsonify, send_from_directory, redirect, abort, Response
from werkzeug.utils import secure_filename
try:
    import qrcode, qrcode.image.svg
except ImportError:
    qrcode = None

VERSION = "0.1.0"
BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))  # paketlenmis dosyalar
DATA = Path.home() / "GFDrop"
BOX = {"inbox": DATA / "inbox", "outbox": DATA / "outbox"}  # inbox: PC'ye gelen, outbox: PC'nin sundugu
for d in BOX.values():
    d.mkdir(parents=True, exist_ok=True)

# ---- ayarlar (config.json: ~/GFDrop/config.json) ----
CFG = {"port": 8765, "github_repo": "", "require_discord": False,
       "discord": {"client_id": "1569806697210323034", "client_secret": "", "guild_id": "1551586915352969317", "invite": ""}}
CFG_F = DATA / "config.json"
if CFG_F.exists():
    CFG.update(json.loads(CFG_F.read_text("utf-8")))
else:
    CFG_F.write_text(json.dumps(CFG, indent=2), "utf-8")

TOKEN = secrets.token_urlsafe(8)   # QR eslesme anahtari
DEVICES, DISCORD = {}, {"user": None, "verified": False}
HIST_F = DATA / "history.json"
HIST = json.loads(HIST_F.read_text("utf-8")) if HIST_F.exists() else []
app = Flask(__name__, static_folder=str(BASE / "static"), static_url_path="/static")


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1)); ip = s.getsockname()[0]; s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def is_host():
    return request.remote_addr in ("127.0.0.1", "::1")


def log(name, size, direction, secs=0):
    dev = DEVICES.get(request.cookies.get("gfd"), {}).get("name", "PC" if is_host() else "?")
    HIST.insert(0, {"name": name, "size": size, "dir": direction, "dev": dev, "t": int(time.time()),
                    "mbs": round(size / 1048576 / secs, 2) if secs > 0 else 0})
    del HIST[200:]
    HIST_F.write_text(json.dumps(HIST), "utf-8")


@app.before_request
def guard():
    p = request.path
    if p == "/" or p.startswith("/static") or p.startswith("/auth"):
        return
    if not (is_host() or request.cookies.get("gf") == TOKEN):
        return jsonify(error="unauthorized"), 401
    if CFG["require_discord"] and not is_host() and p == "/api/upload" and not DISCORD["verified"]:
        return jsonify(error="discord"), 403


@app.route("/")
def index():
    if request.args.get("t") == TOKEN:  # QR ile gelen cihaz: cerez ver
        r = redirect("/")
        r.set_cookie("gf", TOKEN, max_age=86400 * 30)
        r.set_cookie("gfd", secrets.token_hex(4), max_age=86400 * 30)
        return r
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/info")
def info():
    return jsonify(version=VERSION, host=is_host(), discord=DISCORD, dc_ready=bool(CFG["discord"]["client_id"] and CFG["discord"]["client_secret"]),
                   invite=CFG["discord"]["invite"], require_discord=CFG["require_discord"], qr=bool(qrcode))


@app.route("/api/qr")
def qr():
    if not (is_host() and qrcode):
        abort(404)
    url = f"http://{lan_ip()}:{CFG['port']}/?t={TOKEN}"
    b = io.BytesIO()
    qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10).save(b)
    return Response(b.getvalue(), mimetype="image/svg+xml", headers={"X-Url": url})


@app.route("/api/ping", methods=["POST"])
def ping():  # istemciler 5 sn'de bir yoklar -> gercek baglanti durumu
    did = request.cookies.get("gfd", "host")
    ua = request.headers.get("User-Agent", "")
    kind = "iPhone" if "iPhone" in ua else "Android" if "Android" in ua else "Mac" if "Mac" in ua else "Windows" if "Windows" in ua else "Cihaz"
    DEVICES[did] = {"name": f"{kind} ({request.remote_addr})", "type": kind, "seen": time.time(), "host": is_host()}
    now = time.time()
    return jsonify(devices=[dict(v, id=k, online=now - v["seen"] < 15) for k, v in DEVICES.items() if not v["host"]])


@app.route("/api/repair", methods=["POST"])
def repair():  # tum eslesmeleri sifirla
    global TOKEN
    if not is_host():
        abort(403)
    TOKEN = secrets.token_urlsafe(8)
    DEVICES.clear()
    return jsonify(ok=True)


@app.route("/api/upload", methods=["POST"])
def upload():
    box = BOX["outbox"] if is_host() else BOX["inbox"]  # PC gonderir -> outbox, telefon gonderir -> inbox
    t0, saved = time.time(), []
    for f in request.files.getlist("file"):
        name = secure_filename(f.filename) or "dosya"
        dest, n = box / name, 1
        while dest.exists():
            dest = box / f"{Path(name).stem}_{n}{Path(name).suffix}"; n += 1
        f.save(dest)
        log(dest.name, dest.stat().st_size, "sent" if is_host() else "received", time.time() - t0)
        saved.append(dest.name)
    return jsonify(saved=saved)


@app.route("/api/files")
def files():
    out = {}
    for k, d in BOX.items():
        out[k] = sorted(({"name": p.name, "size": p.stat().st_size, "t": int(p.stat().st_mtime)}
                         for p in d.iterdir() if p.is_file()), key=lambda x: -x["t"])
    return jsonify(out)


@app.route("/files/<box>/<name>")
def get_file(box, name):
    if box not in BOX:
        abort(404)
    if not is_host():
        log(name, (BOX[box] / name).stat().st_size, "downloaded")
    return send_from_directory(BOX[box], name, as_attachment=request.args.get("dl") == "1")


@app.route("/api/files/<box>/<name>", methods=["DELETE"])
def del_file(box, name):
    if not is_host() or box not in BOX:
        abort(403)
    (BOX[box] / secure_filename(name)).unlink(missing_ok=True)
    return jsonify(ok=True)


@app.route("/api/history")
def history():
    return jsonify(HIST)


@app.route("/api/open-folder", methods=["POST"])
def open_folder():
    if not is_host():
        abort(403)
    if os.name == "nt":
        os.startfile(BOX["inbox"])
    return jsonify(ok=True)


# ---- otomatik guncelleme (GitHub Releases) ----
def _ver(s):
    return tuple(int(x) for x in s.lstrip("v").split(".") if x.isdigit())


@app.route("/api/update/check")
def upd_check():
    if not CFG["github_repo"]:
        return jsonify(status="no_repo")
    try:
        r = requests.get(f"https://api.github.com/repos/{CFG['github_repo']}/releases/latest", timeout=8).json()
        asset = next((a for a in r.get("assets", []) if a["name"].lower().endswith(".exe")), None)
        new = _ver(r["tag_name"]) > _ver(VERSION)
        return jsonify(status="new" if new and asset else "latest", latest=r["tag_name"], url=asset and asset["browser_download_url"])
    except Exception as e:
        return jsonify(status="error", msg=str(e)), 200


@app.route("/api/update/apply", methods=["POST"])
def upd_apply():
    if not (is_host() and getattr(sys, "frozen", False)):
        return jsonify(status="only_exe"), 400
    url = request.json.get("url", "")
    if not url.startswith("https://github.com/" + CFG["github_repo"]):
        abort(400)
    new, cur = DATA / "GFDrop_new.exe", sys.executable
    new.write_bytes(requests.get(url, timeout=120).content)
    bat = DATA / "upd.bat"  # eski exe kapaninca yenisiyle degistir, yeniden baslat
    bat.write_text(f'@echo off\ntimeout /t 2 >nul\nmove /y "{new}" "{cur}"\nstart "" "{cur}"\ndel "%~f0"\n')
    subprocess.Popen(["cmd", "/c", str(bat)], creationflags=0x00000008)
    threading.Timer(0.5, lambda: os._exit(0)).start()
    return jsonify(status="restarting")


# ---- Discord dogrulama (OAuth2, sadece PC'de) ----
def _redir():
    return f"http://127.0.0.1:{CFG['port']}/auth/discord/callback"


@app.route("/auth/discord")
def dc_login():
    c = CFG["discord"]
    if not (is_host() and c["client_id"] and c["client_secret"]):
        abort(404)
    return redirect("https://discord.com/oauth2/authorize?response_type=code&scope=identify%20guilds"
                    f"&client_id={c['client_id']}&redirect_uri={_redir()}")


@app.route("/auth/discord/callback")
def dc_cb():
    c = CFG["discord"]
    if not is_host():
        abort(403)
    tok = requests.post("https://discord.com/api/oauth2/token", data={
        "client_id": c["client_id"], "client_secret": c["client_secret"], "grant_type": "authorization_code",
        "code": request.args.get("code"), "redirect_uri": _redir()}, timeout=10).json()
    h = {"Authorization": f"Bearer {tok.get('access_token')}"}
    me = requests.get("https://discord.com/api/users/@me", headers=h, timeout=10).json()
    gs = requests.get("https://discord.com/api/users/@me/guilds", headers=h, timeout=10).json()
    DISCORD.update(user=me.get("username"), verified=any(g["id"] == c["guild_id"] for g in gs))
    return redirect("/")


if __name__ == "__main__":
    port = CFG["port"]
    threading.Thread(target=lambda: app.run("0.0.0.0", port, threaded=True), daemon=True).start()
    time.sleep(1)
    url = f"http://127.0.0.1:{port}"
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if os.name == "nt" and os.path.exists(edge):
        subprocess.Popen([edge, f"--app={url}", "--window-size=1200,780"])  # uygulama penceresi
    else:
        webbrowser.open(url)
    while True:  # Edge uygulama penceresi kapaninca (90 sn ping yok) programdan cik
        time.sleep(5)
        h = DEVICES.get("host")
        if os.name == "nt" and h and time.time() - h["seen"] > 90:
            os._exit(0)
