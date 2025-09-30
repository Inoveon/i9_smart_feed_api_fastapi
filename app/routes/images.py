from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.config.database import get_db
from app.dependencies.auth import require_role, get_current_user
from app.services.image_service import ImageService
from app.dependencies.cache import invalidate
from app.models.image import CampaignImage
from app.models.campaign import Campaign


router = APIRouter()


class ImageUpdate(BaseModel):
    """Schema para atualização de propriedades de imagem"""
    title: Optional[str] = None
    description: Optional[str] = None
    display_time: Optional[int] = None  # em milissegundos
    active: Optional[bool] = None


@router.get("/campaigns/{campaign_id}/images", summary="Listar imagens da campanha")
async def list_campaign_images(
    campaign_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Lista todas as imagens de uma campanha específica.
    Retorna as imagens ordenadas com todas as informações.
    """
    # Verificar se a campanha existe
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.is_deleted == False
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    
    # Buscar imagens da campanha
    images = db.query(CampaignImage).filter(
        CampaignImage.campaign_id == campaign_id,
        CampaignImage.active == True
    ).order_by(CampaignImage.order).all()
    
    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.name,
        "default_display_time": campaign.default_display_time,
        "total": len(images),
        "images": [
            {
                "id": str(img.id),
                "filename": img.filename,
                "original_filename": img.original_filename,
                "url": img.url,
                "order": img.order,
                "display_time": img.display_time or campaign.default_display_time,
                "title": img.title,
                "description": img.description,
                "active": img.active,
                "size_bytes": img.size_bytes,
                "mime_type": img.mime_type,
                "width": img.width,
                "height": img.height,
                "created_at": img.created_at.isoformat() if img.created_at else None
            }
            for img in images
        ]
    }


@router.post("/campaigns/{campaign_id}/images")
async def upload_images(
    campaign_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "editor"]))
):
    """
    Upload de imagens para uma campanha.
    
    - Aceita múltiplos arquivos (máximo 10)
    - Formatos suportados: JPEG, PNG, WebP
    - Retorna no mesmo formato de GET /api/campaigns/{id}/images
    """
    # Verificar se a campanha existe
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.is_deleted == False
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo de 10 arquivos por upload"
        )
    
    uploaded = []
    for f in files:
        if f.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de arquivo não suportado: {f.content_type}. Use JPEG, PNG ou WebP."
            )
        data = await f.read()
        img = ImageService.upload_image(db, campaign_id, f.filename, f.content_type, data)
        uploaded.append(img)
    
    invalidate("active_by_station:*")
    invalidate("tablets_active:*")
    
    # Buscar todas as imagens da campanha após upload
    all_images = db.query(CampaignImage).filter(
        CampaignImage.campaign_id == campaign_id,
        CampaignImage.active == True
    ).order_by(CampaignImage.order).all()
    
    # Retornar no mesmo formato de list_campaign_images
    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.name,
        "default_display_time": campaign.default_display_time,
        "total": len(all_images),
        "uploaded_count": len(uploaded),
        "images": [
            {
                "id": str(img.id),
                "filename": img.filename,
                "original_filename": img.original_filename,
                "url": img.url,
                "order": img.order,
                "display_time": img.display_time or campaign.default_display_time,
                "title": img.title,
                "description": img.description,
                "active": img.active,
                "size_bytes": img.size_bytes,
                "mime_type": img.mime_type,
                "width": img.width,
                "height": img.height,
                "created_at": img.created_at.isoformat() if img.created_at else None
            }
            for img in all_images
        ]
    }


@router.put("/campaigns/{campaign_id}/images/order")
async def reorder_images(
    campaign_id: str,
    order: List[str],
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "editor"]))
):
    if not order:
        raise HTTPException(status_code=400, detail="Lista de IDs vazia")
    ImageService.reorder_images(db, campaign_id, order)
    invalidate("active_by_station:*")
    invalidate("tablets_active:*")
    return {"message": "Reordenação aplicada"}


@router.delete("/campaigns/{campaign_id}/images/{image_id}")
async def delete_image(
    campaign_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "editor"]))
):
    """
    Exclui uma imagem específica de uma campanha.
    
    - Verifica se a campanha existe
    - Verifica se a imagem pertence à campanha
    - Realiza soft delete (marca como inativa)
    - Reordena as imagens restantes
    """
    # Verificar se a campanha existe
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.is_deleted == False
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    
    # Verificar se a imagem existe e pertence à campanha
    image = db.query(CampaignImage).filter(
        CampaignImage.id == image_id,
        CampaignImage.campaign_id == campaign_id,
        CampaignImage.active == True
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=404, 
            detail="Imagem não encontrada ou não pertence a esta campanha"
        )
    
    # Soft delete da imagem
    image.active = False
    db.commit()
    
    # Reordenar imagens restantes
    remaining_images = db.query(CampaignImage).filter(
        CampaignImage.campaign_id == campaign_id,
        CampaignImage.active == True
    ).order_by(CampaignImage.order).all()
    
    # Atualizar ordem das imagens restantes
    for idx, img in enumerate(remaining_images):
        img.order = idx + 1
    
    db.commit()
    
    # Invalidar cache
    invalidate("active_by_station:*")
    invalidate("tablets_active:*")
    
    return {
        "message": "Imagem excluída com sucesso",
        "image_id": image_id,
        "remaining_images": len(remaining_images)
    }


@router.put("/images/{image_id}")
async def update_image(
    image_id: str,
    update_data: ImageUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(["admin", "editor"]))
):
    """
    Atualiza propriedades de uma imagem.
    
    Campos atualizáveis:
    - title: Título da imagem
    - description: Descrição detalhada
    - display_time: Tempo de exibição em milissegundos (sobrescreve o padrão da campanha)
    - active: Status ativo/inativo da imagem
    """
    # Buscar a imagem
    image = db.query(CampaignImage).filter(
        CampaignImage.id == image_id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagem não encontrada"
        )
    
    # Buscar a campanha para informações adicionais
    campaign = db.query(Campaign).filter(
        Campaign.id == image.campaign_id
    ).first()
    
    # Atualizar campos fornecidos
    update_dict = update_data.dict(exclude_unset=True)
    
    # Validar display_time se fornecido
    if 'display_time' in update_dict:
        if update_dict['display_time'] is not None:
            if update_dict['display_time'] < 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tempo de exibição deve ser no mínimo 1000ms (1 segundo)"
                )
            if update_dict['display_time'] > 60000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tempo de exibição não pode exceder 60000ms (60 segundos)"
                )
    
    # Aplicar atualizações
    for field, value in update_dict.items():
        setattr(image, field, value)
    
    db.commit()
    db.refresh(image)
    
    # Invalidar cache se a imagem foi ativada/desativada
    if 'active' in update_dict:
        invalidate("active_by_station:*")
        invalidate("tablets_active:*")
    
    # Retornar a imagem atualizada
    return {
        "id": str(image.id),
        "campaign_id": str(image.campaign_id),
        "campaign_name": campaign.name if campaign else None,
        "filename": image.filename,
        "original_filename": image.original_filename,
        "url": image.url,
        "title": image.title,
        "description": image.description,
        "display_time": image.display_time or (campaign.default_display_time if campaign else 5000),
        "active": image.active,
        "order": image.order,
        "size_bytes": image.size_bytes,
        "mime_type": image.mime_type,
        "width": image.width,
        "height": image.height,
        "updated_at": image.updated_at.isoformat() if image.updated_at else None
    }
