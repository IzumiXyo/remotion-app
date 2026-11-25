#!/usr/bin/env python3
"""Client Kaggle API minimal (stdlib only) untuk push/pantau/unduh notebook.

Token baru Kaggle berupa string dan disimpan di ~/.kaggle/access_token,
atau lewat environment KAGGLE_API_TOKEN.
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "https://api.kaggle.com/v1"
KERNELS_SERVICE = "kernels.KernelsApiService"
CONFIG_DIR = Path(os.environ.get("KAGGLE_CONFIG_DIR", Path.home() / ".kaggle"))


def _read_token():
    token = os.environ.get("KAGGLE_API_TOKEN", "").strip()
    if token:
        return token
    path = CONFIG_DIR / "access_token"
    if path.exists():
        token = path.read_text().strip()
        if token:
            return token
    return None


def _read_legacy():
    path = CONFIG_DIR / "kaggle.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    raw = f"{data['username']}:{data['key']}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def auth_header():
    token = _read_token()
    if token:
        return "Bearer " + token
    legacy = _read_legacy()
    if legacy:
        return legacy
    raise SystemExit(
        "Token Kaggle tidak ditemukan.\n"
        "Simpan token ke ~/.kaggle/access_token atau set KAGGLE_API_TOKEN."
    )


def api_call(method, payload, service=KERNELS_SERVICE):
    url = f"{API_BASE}/{service}/{method}"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": auth_header(),
            "Content-Type": "application/json",
            "User-Agent": "remotion-kaggle-client/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"Kaggle API error HTTP {exc.code}: {detail[:1500]}") from exc


def whoami():
    token = _read_token()
    if not token:
        return {"auth": "basic", "username": None}
    data = api_call(
        "IntrospectToken", {"token": token}, service="security.OAuthService"
    )
    return {"auth": "bearer", "active": data.get("active"), "username": data.get("username")}


def prepare_notebook(path):
    nb = json.loads(Path(path).read_text())
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            if isinstance(cell.get("source"), list):
                cell["source"] = "".join(cell["source"])
    return json.dumps(nb)


def push(notebook, slug, title, gpu=True, internet=True, timeout_seconds=32400):
    payload = {
        "slug": slug,
        "newTitle": title,
        "text": prepare_notebook(notebook),
        "language": "python",
        "kernelType": "notebook",
        "isPrivate": True,
        "enableGpu": gpu,
        "enableTpu": False,
        "enableInternet": internet,
        "datasetDataSources": [],
        "competitionDataSources": [],
        "kernelDataSources": [],
        "modelDataSources": [],
        "categoryIds": [],
        "machineShape": "NvidiaTeslaT4",
        "kernelExecutionType": "SAVE_AND_RUN_ALL",
        "sessionTimeoutSeconds": timeout_seconds,
    }
    return api_call("SaveKernel", payload)


def status(owner, slug):
    data = api_call(
        "GetKernelSessionStatus", {"userName": owner, "kernelSlug": slug}
    )
    # Server menghilangkan field default, jadi {} berarti masih QUEUED.
    if not data:
        return {"status": "QUEUED"}
    return data


def list_output(owner, slug, page_size=50):
    return api_call(
        "ListKernelSessionOutput",
        {"userName": owner, "kernelSlug": slug, "pageSize": page_size},
    )


def wait(owner, slug, interval=20, max_wait=7200):
    started = time.time()
    last = None
    while True:
        data = status(owner, slug)
        state = data.get("status", "UNKNOWN")
        if state != last:
            print(f"[{int(time.time() - started):4d}s] {state}", flush=True)
            last = state
        if state == "COMPLETE":
            return data
        if state in ("ERROR", "CANCEL_ACKNOWLEDGED"):
            raise SystemExit(
                f"Run berhenti: {state}\n{data.get('failureMessage', '')}"
            )
        if time.time() - started > max_wait:
            raise SystemExit("Batas waktu tunggu habis.")
        time.sleep(interval)


def download_output(owner, slug, dest):
    data = list_output(owner, slug)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    log = data.get("log")
    if log:
        (dest / f"{slug}.log").write_text(log)
        print(f"log   → {dest / (slug + '.log')}")

    files = data.get("files") or []
    if not files:
        print("Tidak ada file output (mungkin run belum selesai).")
    for item in files:
        name = item.get("fileName") or "output.bin"
        url = item.get("url")
        target = dest / Path(name).name
        print(f"unduh → {target}")
        with urllib.request.urlopen(url, timeout=600) as resp:
            target.write_bytes(resp.read())
    return dest


def parse_slug(value):
    if "/" not in value:
        raise SystemExit("Slug harus berbentuk owner/kernel-slug")
    return value.split("/", 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami")

    p_push = sub.add_parser("push")
    p_push.add_argument("--notebook", required=True)
    p_push.add_argument("--slug", required=True)
    p_push.add_argument("--title", required=True)
    p_push.add_argument("--no-gpu", action="store_true")
    p_push.add_argument("--no-internet", action="store_true")

    p_status = sub.add_parser("status")
    p_status.add_argument("slug")

    p_wait = sub.add_parser("wait")
    p_wait.add_argument("slug")
    p_wait.add_argument("--interval", type=int, default=20)
    p_wait.add_argument("--max-wait", type=int, default=7200)

    p_out = sub.add_parser("output")
    p_out.add_argument("slug")
    p_out.add_argument("--dest", default="kaggle/output")

    args = parser.parse_args()

    if args.cmd == "whoami":
        print(json.dumps(whoami(), indent=2))
    elif args.cmd == "push":
        result = push(
            args.notebook,
            args.slug,
            args.title,
            gpu=not args.no_gpu,
            internet=not args.no_internet,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "status":
        owner, slug = parse_slug(args.slug)
        print(json.dumps(status(owner, slug), indent=2))
    elif args.cmd == "wait":
        owner, slug = parse_slug(args.slug)
        print(json.dumps(wait(owner, slug, args.interval, args.max_wait), indent=2))
    elif args.cmd == "output":
        owner, slug = parse_slug(args.slug)
        download_output(owner, slug, args.dest)


if __name__ == "__main__":
    main()
