from fastapi import APIRouter, HTTPException
from typing import List
from api.models import Account, AccountCreate
from modules.database import get_database_connection

router = APIRouter()


@router.get("/", response_model=List[Account])
async def get_accounts():
    """Get all Instagram accounts"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Add missing columns if they don't exist
            try:
                cursor.execute("ALTER TABLE accounts ADD COLUMN status TEXT DEFAULT 'active'")
                cursor.execute("ALTER TABLE accounts ADD COLUMN active BOOLEAN DEFAULT TRUE")
                cursor.execute("ALTER TABLE accounts ADD COLUMN last_login TIMESTAMP")
                cursor.execute("ALTER TABLE accounts ADD COLUMN posts_count INTEGER DEFAULT 0")
                conn.commit()
            except:
                pass  # Columns already exist

            cursor.execute('''
                           SELECT username,
                                  theme,
                                  COALESCE(status, 'active') as status,
                                  COALESCE(posts_count, 0)   as posts_count,
                                  last_login
                           FROM accounts
                           WHERE COALESCE(active, 1) = 1
                           ORDER BY username
                           ''')

            accounts = []
            for row in cursor.fetchall():
                accounts.append(Account(
                    username=row[0],
                    theme=row[1],
                    status=row[2],
                    posts_count=row[3],
                    last_login=row[4]
                ))

            return accounts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch accounts: {str(e)}")


@router.post("/")
async def create_account(account: AccountCreate):
    """Add new Instagram account"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if account exists
            cursor.execute("SELECT username FROM accounts WHERE username = ?", (account.username,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Account already exists")

            # Insert new account
            cursor.execute('''
                           INSERT INTO accounts (username, password, theme, "2FAKey", status, active, posts_count)
                           VALUES (?, ?, ?, ?, 'active', 1, 0)
                           ''', (account.username, account.password, account.theme, account.two_fa_key))

            conn.commit()

        return {"message": f"Account {account.username} created successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")