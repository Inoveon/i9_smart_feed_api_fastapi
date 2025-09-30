#!/usr/bin/env python3
import os
import mimetypes
from pathlib import Path
from datetime import datetime, timedelta
import json
import urllib.request
import urllib.parse


BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
REPO_DIR = Path(os.getenv("IMAGES_DIR", "repo"))


def http_post_form(url: str, fields: dict) -> dict:
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def http_post_json(url: str, payload: dict, token: str) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def http_post_multipart(url: str, files: list[Path], token: str) -> dict:
    # Build simple multipart body for one or more files under field name 'files'
    boundary = "----BoundaryBulkUpload"
    body = bytearray()
    for f in files:
        mime = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        body.extend((f"--{boundary}\r\n").encode())
        body.extend((
            f"Content-Disposition: form-data; name=\"files\"; filename=\"{f.name}\"\r\n"
            f"Content-Type: {mime}\r\n\r\n"
        ).encode())
        body.extend(f.read_bytes())
        body.extend(b"\r\n")
    body.extend((f"--{boundary}--\r\n").encode())

    req = urllib.request.Request(url, data=bytes(body), headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {token}",
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def main():
    if not REPO_DIR.exists():
        print(f"Diretório não encontrado: {REPO_DIR}")
        return

    # 1) Login
    auth = http_post_form(f"{BASE_URL}/api/auth/login", {"username": "admin", "password": "admin123"})
    token = auth.get("access_token")
    if not token:
        print("Falha no login; verifique credenciais e servidor.")
        return

    # 2) Descobrir imagens
    imgs = sorted([p for p in REPO_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}])
    if not imgs:
        print("Nenhuma imagem encontrada em 'repo/'.")
        return

    print(f"Encontradas {len(imgs)} imagens. Criando campanhas e subindo arquivos...")

    created = 0
    for img in imgs:
        # 3) Criar campanha para cada imagem
        payload = {
            "name": f"Teste - {img.stem}",
            "description": "Campanha de teste criada automaticamente",
            "status": "active",
            "start_date": datetime.utcnow().isoformat() + "Z",
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z",
            "default_display_time": 5000,
            "stations": ["001"],
            "priority": 1,
        }
        try:
            camp = http_post_json(f"{BASE_URL}/api/campaigns/", payload, token)
            cid = camp.get("id")
            if not cid:
                print(f"Falha ao criar campanha para {img.name}: {camp}")
                continue
            # 4) Upload da imagem na campanha
            res = http_post_multipart(f"{BASE_URL}/api/campaigns/{cid}/images", [img], token)
            print(f"✓ {img.name}: campanha {cid} e upload OK")
            created += 1
        except Exception as e:
            print(f"Erro com {img.name}: {e}")

    print(f"Concluído. {created}/{len(imgs)} campanhas criadas com upload.")


if __name__ == "__main__":
    main()

