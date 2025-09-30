from __future__ import annotations

import os
import uuid
from typing import List

from sqlalchemy.orm import Session

from app.models.image import CampaignImage
from app.models.campaign import Campaign
from app.services.storage import upload_bytes


class ImageService:
    @staticmethod
    def upload_image(db: Session, campaign_id: str, filename: str, content_type: str, data: bytes) -> CampaignImage:
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        bucket = os.getenv("MINIO_BUCKET", "campaigns")
        key = f"campaigns/{campaign_id}/{uuid.uuid4()}_{filename}"
        url = upload_bytes(bucket, key, data, content_type)

        image = CampaignImage(
            campaign_id=campaign.id,
            filename=key.split("/")[-1],
            original_filename=filename,
            url=url,
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    @staticmethod
    def reorder_images(db: Session, campaign_id: str, ordered_ids: List[str]) -> None:
        images = (
            db.query(CampaignImage)
            .filter(CampaignImage.campaign_id == campaign_id)
            .all()
        )
        id_to_img = {str(img.id): img for img in images}
        for idx, img_id in enumerate(ordered_ids):
            if img_id in id_to_img:
                id_to_img[img_id].order = idx
        db.commit()
