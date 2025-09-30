import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import settings
from app.dependencies.cache import cache
from app.middleware.api_key import verify_api_key
from app.models.campaign import Campaign
from app.models.image import CampaignImage

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/active")
@cache(expire=120, key_prefix="tablets_active_all")
async def get_all_active(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    items = (
        db.query(Campaign)
        .filter(
            Campaign.is_deleted == False,  # noqa: E712
            Campaign.status == "active",
            Campaign.start_date <= now,
            Campaign.end_date >= now,
        )
        .order_by(Campaign.priority.desc(), Campaign.created_at.desc())
        .all()
    )
    return {
        "campaigns": [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "default_display_time": c.default_display_time,
                "stations": c.stations,
            }
            for c in items
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/active/{station_code}")
# @cache(expire=120, key_prefix="tablets_active")  # Temporariamente desabilitado
async def get_active_for_station(
    station_code: str, request: Request, db: Session = Depends(get_db)
):
    """
    Retorna campanhas ativas para uma estação específica (TABLETS).

    Lógica de targeting hierárquico:
    1. Campanhas GLOBAIS (arrays vazias) - sempre incluídas
    2. Campanhas por REGIÃO - se a estação pertencer à região
    3. Campanhas por FILIAL - se a estação pertencer à filial
    4. Campanhas por ESTAÇÃO - se a estação estiver na lista

    **IMPORTANTE**: Usa a mesma lógica de /api/campaigns/active/{station_code}
    """
    from app.models.branch import Branch
    from app.models.station import Station

    now = datetime.utcnow()

    try:
        # Buscar informações da estação
        station = (
            db.query(Station)
            .filter(
                Station.code == station_code, Station.is_active == True  # noqa: E712
            )
            .first()
        )

        # Buscar todas as campanhas ativas
        all_campaigns = (
            db.query(Campaign)
            .filter(
                Campaign.is_deleted == False,  # noqa: E712
                Campaign.status == "active",
                Campaign.start_date <= now,
                Campaign.end_date >= now,
            )
            .all()
        )

        # Filtrar campanhas aplicáveis
        campaigns = []
        branch_code = None
        region = None

        if station:
            branch = station.branch
            branch_code = branch.code if branch else None
            region = branch.region if branch else None

        for campaign in all_campaigns:
            # 1. Campanha GLOBAL (todas arrays vazias ou None)
            branches = campaign.branches or []
            regions = campaign.regions or []
            stations = campaign.stations or []

            if not branches and not regions and not stations:
                campaigns.append(campaign)
                continue

            # Só continuar se temos estação válida
            if not station:
                continue

            # 2. Campanha REGIONAL
            if regions and not branches and not stations:
                if region in regions:
                    campaigns.append(campaign)
                continue

            # 3. Campanha por FILIAL (todas estações da filial)
            if branches and not stations:
                if branch_code in branches:
                    campaigns.append(campaign)
                continue

            # 4. Campanha por ESTAÇÃO específica
            if branches and stations:
                if branch_code in branches and station_code in stations:
                    campaigns.append(campaign)

        # Ordenar por prioridade e remover duplicatas
        seen = set()
        unique_campaigns = []
        for c in sorted(
            campaigns,
            key=lambda x: (-x.priority if x.priority else 0, x.created_at),
            reverse=True,
        ):
            if c.id not in seen:
                seen.add(c.id)
                unique_campaigns.append(c)
        campaigns = unique_campaigns

    except Exception as e:
        print(f"Erro em tablets get_active_for_station: {e}")
        import traceback

        traceback.print_exc()
        campaigns = []

    # Buscar imagens de cada campanha
    campaigns_with_images = []
    for c in campaigns:
        # Buscar imagens ativas da campanha
        images = (
            db.query(CampaignImage)
            .filter(
                CampaignImage.campaign_id == c.id,
                CampaignImage.active == True,  # noqa: E712
            )
            .order_by(CampaignImage.order)
            .all()
        )

        # Construir base URL dinamicamente usando o Request do FastAPI
        # O FastAPI já trata X-Forwarded-Host e X-Forwarded-Proto automaticamente
        base_url = str(request.base_url).rstrip("/")

        # Se vier via proxy reverso, usar os headers corretos
        if request.headers.get("x-forwarded-host"):
            protocol = request.headers.get("x-forwarded-proto", "http")
            host = request.headers.get("x-forwarded-host")
            base_url = f"{protocol}://{host}"
        elif request.headers.get("host"):
            # Usar o Host header se disponível
            host = request.headers.get("host")
            # Verificar se já tem protocolo
            if not host.startswith("http"):
                protocol = "https" if request.url.scheme == "https" else "http"
                # base_url = f"{protocol}://{host}"

        # Formatar imagens
        formatted_images = []
        for img in images:
            # Calcular checksum MD5 (simplificado - em produção usar hash real do arquivo)
            checksum = hashlib.md5(f"{img.id}".encode()).hexdigest()

            formatted_images.append(
                {
                    "id": str(img.id),
                    "campaign_id": str(c.id),
                    "order_index": img.order,
                    "display_time": img.display_time,  # null usará default_display_time
                    "width": img.width,
                    "height": img.height,
                    "mime_type": img.mime_type,
                    "size_bytes": img.size_bytes,
                    "checksum": checksum,
                    "download_url": f"/api/tablets/images/{img.id}",
                }
            )

        campaigns_with_images.append(
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "default_display_time": c.default_display_time,
                "priority": c.priority or 0,
                "targeting_level": (
                    "global"
                    if not (c.branches or [])
                    and not (c.regions or [])
                    and not (c.stations or [])
                    else (
                        "regional"
                        if (c.regions or []) and not (c.branches or [])
                        else (
                            "branch"
                            if (c.branches or []) and not (c.stations or [])
                            else "station"
                        )
                    )
                ),
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat(),
                "images": formatted_images,
            }
        )

    # Request ID tracking
    request_id = request.headers.get("x-request-id")

    response = {
        "station_code": station_code,
        "branch_code": branch_code if station else None,
        "region": region if station else None,
        "campaigns": campaigns_with_images,
        "total": len(campaigns),
        "timestamp": datetime.utcnow().isoformat(),
        "cache_ttl": 120,
    }

    if request_id:
        response["request_id"] = request_id

    return response


@router.head("/images/{image_id}")
@router.get("/images/{image_id}")
async def get_tablet_image(
    image_id: str,
    request: Request,  # Para detectar método (GET/HEAD)
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
    accept: Optional[str] = Header(None),
    range_header: Optional[str] = Header(None, alias="Range"),
    db: Session = Depends(get_db),
):
    """
    Download seguro de imagem para tablets com suporte a cache e WebP.

    Suporta:
    - HEAD requests para verificar cache
    - ETag/If-None-Match para cache
    - Accept header para WebP
    - Range requests para download parcial
    - X-Request-ID para tracking
    """
    import io
    import os
    import uuid

    from fastapi.responses import FileResponse, StreamingResponse
    from PIL import Image as PILImage

    # Gerar request_id se não fornecido
    request_id = x_request_id or str(uuid.uuid4())

    # Buscar imagem no banco
    image = (
        db.query(CampaignImage)
        .filter(
            CampaignImage.id == image_id, CampaignImage.active == True  # noqa: E712
        )
        .first()
    )

    if not image:
        raise HTTPException(
            status_code=404,
            detail=f"Imagem {image_id} não encontrada",
            headers={"X-Request-ID": request_id},
        )

    # Verificar se a campanha está ativa
    campaign = (
        db.query(Campaign)
        .filter(
            Campaign.id == image.campaign_id,
            Campaign.is_deleted == False,  # noqa: E712
            Campaign.status == "active",
        )
        .first()
    )

    if not campaign:
        raise HTTPException(
            status_code=403,
            detail="Imagem não autorizada para esta API Key",
            headers={"X-Request-ID": request_id},
        )

    # Calcular checksum/ETag
    checksum = hashlib.md5(f"{image.id}".encode()).hexdigest()
    etag = f'"{checksum}"'

    # Verificar If-None-Match
    if if_none_match and if_none_match == etag:
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Cache-Control": "public, max-age=86400",
                "X-Request-ID": request_id,
            },
        )

    # Resolver caminho do arquivo de forma robusta
    def pick_local_path() -> str:
        candidates = []

        # 1) Se URL aponta para /static/uploads, usar esse caminho relativo
        if getattr(image, "url", None):
            url = image.url or ""
            if url.startswith("/static/uploads/"):
                candidates.append(url.lstrip("/"))

        # 2) Caminho padrão legado (sem subpastas)
        candidates.append(os.path.join("static", "uploads", image.filename))

        # 3) Caminho com subpastas (campaigns/{campaign_id}/filename)
        candidates.append(
            os.path.join("static", "uploads", "campaigns", str(image.campaign_id), image.filename)
        )

        # 4) Fallback de desenvolvimento em repo/
        if image.original_filename:
            candidates.append(os.path.join("repo", image.original_filename))
        candidates.append(os.path.join("repo", image.filename))

        # Selecionar o primeiro arquivo existente e com conteúdo válido (não zeros)
        for path in candidates:
            try:
                if not os.path.exists(path) or not os.path.isfile(path):
                    continue
                size = os.path.getsize(path)
                if size <= 0:
                    continue
                with open(path, "rb") as fh:
                    head = fh.read(16)
                # Rejeitar arquivos preenchidos só com zeros
                if head and any(b != 0 for b in head):
                    return path
            except Exception:
                continue

        return ""

    upload_path = pick_local_path()
    if not upload_path:
        raise HTTPException(
            status_code=404,
            detail="Arquivo de imagem não encontrado no servidor",
            headers={"X-Request-ID": request_id},
        )

    # Seleção de variante a servir (original, webp, jpeg baseline)
    serve_path = upload_path
    serve_mime = image.mime_type or "image/jpeg"
    headers = {
        "Cache-Control": "public, max-age=86400",
        "ETag": etag,
        "X-Image-Width": str(image.width or 1920),
        "X-Image-Height": str(image.height or 1080),
        "X-Campaign-Id": str(image.campaign_id),
        "X-Request-ID": request_id,
        "Accept-Ranges": "bytes",
        "X-Resolved-Path": upload_path,
    }

    # Verificar se cliente aceita WebP
    supports_webp = bool(accept and "image/webp" in accept)

    # Tentar WebP primeiro, se aceito
    if supports_webp and serve_mime != "image/webp":
        try:
            cache_dir = os.path.join("static", "cache")
            os.makedirs(cache_dir, exist_ok=True)
            webp_path = os.path.join(cache_dir, f"{image.id}.webp")
            # Gerar se não existir ou se original for mais novo
            if not os.path.exists(webp_path) or os.path.getmtime(webp_path) < os.path.getmtime(upload_path):
                pil_image = PILImage.open(upload_path)
                pil_image.save(webp_path, format="WEBP", quality=85)
            serve_path = webp_path
            serve_mime = "image/webp"
            headers["ETag"] = f'"{checksum}-webp"'
            headers["Vary"] = "Accept"
            headers["X-Image-Format"] = "webp-optimized"
            headers["X-Original-Format"] = image.mime_type or "image/jpeg"
        except Exception as e:
            print(f"Erro ao converter para WebP: {e}")

    # Se não servir WebP, garantir JPEG baseline quando JPEG progressivo
    if serve_mime == "image/jpeg" and serve_path == upload_path:
        try:
            with PILImage.open(upload_path) as pil_image:
                is_jpeg = (pil_image.format or "").upper() == "JPEG"
                info = getattr(pil_image, "info", {}) or {}
                is_progressive = bool(info.get("progressive") or info.get("progression"))
                if is_jpeg and is_progressive:
                    cache_dir = os.path.join("static", "cache")
                    os.makedirs(cache_dir, exist_ok=True)
                    baseline_path = os.path.join(cache_dir, f"{image.id}.baseline.jpg")
                    # Regenerar se ausente ou desatualizado
                    if not os.path.exists(baseline_path) or os.path.getmtime(baseline_path) < os.path.getmtime(upload_path):
                        # Converter para baseline (não progressivo)
                        rgb = pil_image.convert("RGB")
                        rgb.save(baseline_path, format="JPEG", quality=85, optimize=True, progressive=False)
                    serve_path = baseline_path
                    headers["ETag"] = f'"{checksum}-baseline"'
                    headers["X-Image-Format"] = "jpeg-baseline"
                    headers["X-Original-Format"] = image.mime_type or "image/jpeg"
        except Exception as e:
            print(f"Erro ao verificar/gerar JPEG baseline: {e}")

    # Tamanho e mtime finais
    file_size = os.path.getsize(serve_path)
    headers["Last-Modified"] = datetime.utcfromtimestamp(os.path.getmtime(serve_path)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    headers["X-Resolved-Path"] = serve_path

    # HEAD: retornar apenas headers da variante escolhida
    if request.method == "HEAD":
        headers["Content-Type"] = serve_mime
        headers["Content-Length"] = str(file_size)
        headers["Connection"] = "keep-alive"
        return Response(status_code=200, headers=headers)

    # Range request
    if range_header:
        try:
            # Parse Range header (bytes=0-1023)
            range_str = range_header.replace("bytes=", "").strip()
            parts = range_str.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

            # Validar range
            if start >= file_size or end >= file_size or start > end:
                return Response(
                    status_code=416,
                    headers={
                        "Content-Range": f"bytes */{file_size}",
                        "X-Request-ID": request_id,
                    },
                )

            # Ler parte do arquivo
            with open(serve_path, "rb") as f:
                f.seek(start)
                data = f.read(end - start + 1)

            headers["Content-Length"] = str(len(data))
            headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            headers["Content-Type"] = serve_mime

            return Response(
                content=data,
                status_code=206,
                headers=headers,
                media_type=serve_mime,
            )
        except Exception as e:
            print(f"Erro ao processar Range: {e}")

    # Resposta normal - arquivo completo
    if "X-Image-Format" not in headers:
        headers["X-Image-Format"] = "original"

    headers["Connection"] = "keep-alive"

    return FileResponse(
        serve_path,
        status_code=200,
        headers=headers,
        media_type=serve_mime,
    )
