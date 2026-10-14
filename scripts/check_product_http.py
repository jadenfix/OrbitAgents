import json, os, secrets, socket, subprocess, sys, tempfile, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
r = Path(__file__).resolve().parents[1]
evidence = Path(os.getenv("ORBIT_EVIDENCE_DIR", str(r / "artifacts/product-browser")))
evidence.mkdir(exist_ok=True)


def port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Fixture(BaseHTTPRequestHandler):
    def do_POST(self):
        q = json.loads(self.rfile.read(int(self.headers["Content-Length"]))).get("q")
        self.send_response(503 if q == "outage" else 200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        listing = {
            "id": "http-contract-fixture",
            "title": "HTTP contract fixture",
            "address": "Fixture address",
            "city": "Denver",
            "price": 1200,
            "beds": 2,
            "baths": 1,
            "location": {"lat": 39.7, "lon": -104.9},
            "property_type": "apartment",
            "amenities": [],
            "images": [],
            "date_added": "2026-10-14",
        }
        self.wfile.write(
            json.dumps(
                {
                    "query": q,
                    "listings": [] if q == "empty" else [listing],
                    "total": 0 if q == "empty" else 1,
                    "limit": 20,
                    "parse_time_ms": 1,
                    "search_time_ms": 2,
                    "total_time_ms": 3,
                }
            ).encode()
        )

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
threading.Thread(target=server.serve_forever, daemon=True).start()
processes = []
logs = []
try:
    with tempfile.TemporaryDirectory() as tmp:
        auth, gateway, front = port(), port(), port()
        env = {k: v for k, v in os.environ.items() if not k.lower().endswith("proxy")}
        env.update(
            DATABASE_URL=f"sqlite:///{tmp}/auth.sqlite",
            JWT_SECRET=secrets.token_urlsafe(48),
            RATE_LIMIT_ENABLED="false",
            AUTH_SERVICE_URL=f"http://127.0.0.1:{auth}",
            QUERY_SERVICE_URL=f"http://127.0.0.1:{server.server_port}",
            API_GATEWAY_URL=f"http://127.0.0.1:{gateway}",
        )

        def start(args, cwd, name):
            log = open(evidence / f"{name}.log", "w")
            logs.append(log)
            p = subprocess.Popen(args, cwd=cwd, env=env, stdout=log, stderr=log)
            processes.append(p)
            return p

        start(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(auth),
            ],
            r / "services/auth",
            "auth",
        )
        start(
            [
                sys.executable,
                "-m",
                "flask",
                "--app",
                "api.index",
                "run",
                "--host",
                "127.0.0.1",
                "--port",
                str(gateway),
            ],
            r,
            "gateway",
        )
        start(
            [
                "node",
                "node_modules/vite/bin/vite.js",
                str(r / "frontend"),
                "--host",
                "127.0.0.1",
                "--port",
                str(front),
                "--strictPort",
            ],
            r / "frontend",
            "frontend",
        )
        for url in [
            f"http://127.0.0.1:{auth}/healthz",
            f"http://127.0.0.1:{gateway}/api/health",
            f"http://127.0.0.1:{front}/index.html",
        ]:
            for _ in range(150):
                try:
                    opener.open(url, timeout=1).close()
                    break
                except Exception as error:
                    if _ == 149:
                        print(url, repr(error))
                    time.sleep(0.1)
            else:
                raise RuntimeError("Startup failed; inspect local logs")
        credentials = {
            "email": "browser-proof@example.com",
            "password": "Aa9!" + secrets.token_urlsafe(28),
        }
        req = urllib.request.Request(
            f"http://127.0.0.1:{gateway}/api/auth/register",
            data=json.dumps(credentials).encode(),
            headers={"Content-Type": "application/json"},
        )
        with opener.open(req) as resp:
            assert resp.status == 201
        env.update(
            ORBIT_FRONTEND=f"http://127.0.0.1:{front}",
            ORBIT_EMAIL=credentials["email"],
            ORBIT_PASSWORD=credentials["password"],
            ORBIT_EVIDENCE=str(evidence),
        )
        result = subprocess.run(
            ["node", str(r / "scripts/check_product_browser.cjs")],
            env=env,
            text=True,
            capture_output=True,
            timeout=150,
        )
        print(result.stdout)
        print(result.stderr)
        result.check_returncode()
        (evidence / "browser-receipt.json").write_text(
            json.dumps(
                [
                    json.loads(x)
                    for x in result.stdout.splitlines()
                    if x.startswith("{")
                ],
                indent=2,
            )
        )
finally:
    for p in reversed(processes):
        p.terminate()
        p.wait(timeout=10)
    for l in logs:
        l.close()
    server.shutdown()
    server.server_close()
