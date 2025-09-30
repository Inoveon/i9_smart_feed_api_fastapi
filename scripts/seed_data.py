#!/usr/bin/env python3
import sys
import os
import uuid
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from passlib.context import CryptContext
from sqlalchemy import text

from app.config.database import SessionLocal


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_data() -> None:
    db = SessionLocal()

    admin_id = uuid.uuid4()
    hashed = pwd_context.hash("admin123")

    db.execute(
        text(
            """
            INSERT INTO users (id, email, username, hashed_password, full_name, role, is_active, is_verified)
            VALUES (CAST(:id AS uuid), :email, :username, :hashed_password, :full_name, CAST(:role AS userrole), true, true)
            ON CONFLICT (email) DO NOTHING
            """
        ),
        {
            "id": str(admin_id),
            "email": "admin@i9smart.com.br",
            "username": "admin",
            "hashed_password": hashed,
            "full_name": "Administrador",
            "role": "admin",
        },
    )

    db.execute(
        text(
            """
            INSERT INTO campaigns (
                id, name, description, status, start_date, end_date, default_display_time, stations, priority, is_deleted, created_by
            ) VALUES (
                CAST(:id AS uuid), :name, :description, CAST(:status AS campaignstatus), :start_date, :end_date, :default_display_time, :stations, :priority, false, CAST(:created_by AS uuid)
            )
            ON CONFLICT DO NOTHING
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "name": "Campanha de Inauguração",
            "description": "Primeira campanha do sistema",
            "status": "active",
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=30),
            "default_display_time": 5000,
            "stations": ["001", "002", "003"],
            "priority": 1,
            "created_by": str(admin_id),
        },
    )

    db.commit()
    print("✅ Seed data criado com sucesso!")
    db.close()


if __name__ == "__main__":
    seed_data()
