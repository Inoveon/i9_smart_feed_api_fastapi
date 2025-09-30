#!/usr/bin/env python3
"""
Reseta ou cria o usuário admin com a senha informada.

Uso:
  .venv/bin/python scripts/reset_admin_password.py --username admin --password admin123
  .venv/bin/python scripts/reset_admin_password.py --email admin@i9smart.com.br --password admin123
"""
import argparse
import sys

from passlib.context import CryptContext
from sqlalchemy import text

from app.config.database import SessionLocal


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", dest="username", help="username do usuário")
    parser.add_argument("--email", dest="email", help="email do usuário")
    parser.add_argument("--password", dest="password", required=True, help="nova senha")
    args = parser.parse_args()

    if not args.username and not args.email:
        print("Informe --username ou --email", file=sys.stderr)
        sys.exit(2)

    db = SessionLocal()
    try:
        hashed = pwd_context.hash(args.password)

        # Se existir, atualiza a senha; senão cria admin básico
        if args.username:
            where = "username = :val"
            val = args.username
        else:
            where = "email = :val"
            val = args.email

        updated = db.execute(
            text(
                f"""
                UPDATE users SET hashed_password = :hashed, updated_at = now()
                WHERE {where}
                """
            ),
            {"hashed": hashed, "val": val},
        ).rowcount

        if updated == 0:
            # cria usuário
            import uuid
            new_id = str(uuid.uuid4())
            db.execute(
                text(
                    """
                    INSERT INTO users (id, email, username, hashed_password, full_name, role, is_active, is_verified)
                    VALUES (CAST(:id AS uuid), :email, :username, :hashed, :full_name, CAST(:role AS userrole), true, true)
                    """
                ),
                {
                    "id": new_id,
                    "email": args.email or "admin@i9smart.com.br",
                    "username": args.username or "admin",
                    "hashed": hashed,
                    "full_name": "Administrador",
                    "role": "admin",
                },
            )

        db.commit()
        print("✓ Senha ajustada com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
