"""Hizli duman testleri: pytest -q"""
import importlib.util, io, os, pathlib, pytest

HOST, PHONE = {"REMOTE_ADDR": "127.0.0.1"}, {"REMOTE_ADDR": "192.168.1.9"}


@pytest.fixture(scope="module")
def mod(tmp_path_factory):
    os.environ["GFDROP_DATA"] = str(tmp_path_factory.mktemp("data"))  # gercek klasore dokunma
    spec = importlib.util.spec_from_file_location("gfapp", pathlib.Path(__file__).parent.parent / "app.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_host_info(mod):
    assert mod.app.test_client().get("/api/info", environ_overrides=HOST).json["host"] is True


def test_phone_needs_pairing(mod):
    assert mod.app.test_client().get("/api/files", environ_overrides=PHONE).status_code == 401


def test_pair_then_upload(mod):
    c = mod.app.test_client()
    assert c.get("/?t=" + mod.TOKEN, environ_overrides=PHONE).status_code == 302
    r = c.post("/api/upload", data={"file": (io.BytesIO(b"hi"), "a.txt")}, environ_overrides=PHONE)
    assert r.json["saved"] == ["a.txt"]


def test_tunnel_requests_are_not_host(mod):  # internet modu: Cloudflare basligi olan istek yetkisiz
    r = mod.app.test_client().get("/api/files", environ_overrides=HOST, headers={"Cf-Connecting-Ip": "1.1.1.1"})
    assert r.status_code == 401


def test_path_traversal_blocked(mod):
    assert mod.app.test_client().get("/files/inbox/..%2Fconfig.json", environ_overrides=HOST).status_code == 404
