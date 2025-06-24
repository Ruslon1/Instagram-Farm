from fastapi import APIRouter, HTTPException
from typing import List
import requests
import time
from api.models import Account, AccountCreate, ProxySettings, ProxyTestResult, ProxyUpdate
from modules.database import get_database_connection
from services.proxy_monitoring_service import ProxyMonitoringService

router = APIRouter()


@router.get("/", response_model=List[Account])
async def get_accounts():
    """Get all Instagram accounts with proxy info"""
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
                                  COALESCE(status, 'active')          as status,
                                  COALESCE(posts_count, 0)            as posts_count,
                                  last_login,
                                  proxy_host,
                                  proxy_port,
                                  COALESCE(proxy_status, 'unchecked') as proxy_status,
                                  COALESCE(proxy_active, 0)           as proxy_active
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
                    last_login=row[4],
                    proxy_host=row[5],
                    proxy_port=row[6],
                    proxy_status=row[7],
                    proxy_active=bool(row[8])
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


@router.put("/{username}/proxy")
async def update_account_proxy(username: str, proxy_settings: ProxySettings):
    """Update proxy settings for account"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if account exists
            cursor.execute("SELECT username FROM accounts WHERE username = ?", (username,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Account not found")

            # Update proxy settings
            cursor.execute('''
                           UPDATE accounts
                           SET proxy_host       = ?,
                               proxy_port       = ?,
                               proxy_username   = ?,
                               proxy_password   = ?,
                               proxy_type       = ?,
                               proxy_active     = ?,
                               proxy_status     = 'unchecked',
                               proxy_last_check = NULL
                           WHERE username = ?
                           ''', (
                               proxy_settings.proxy_host,
                               proxy_settings.proxy_port,
                               proxy_settings.proxy_username,
                               proxy_settings.proxy_password,
                               proxy_settings.proxy_type,
                               proxy_settings.proxy_active,
                               username
                           ))

            conn.commit()

        return {"message": f"Proxy settings updated for account {username}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update proxy settings: {str(e)}")


@router.delete("/{username}/proxy")
async def remove_account_proxy(username: str):
    """Remove proxy settings from account"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if account exists
            cursor.execute("SELECT username FROM accounts WHERE username = ?", (username,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Account not found")

            # Clear proxy settings
            cursor.execute('''
                           UPDATE accounts
                           SET proxy_host       = NULL,
                               proxy_port       = NULL,
                               proxy_username   = NULL,
                               proxy_password   = NULL,
                               proxy_type       = NULL,
                               proxy_active     = 0,
                               proxy_status     = 'unchecked',
                               proxy_last_check = NULL
                           WHERE username = ?
                           ''', (username,))

            conn.commit()

        return {"message": f"Proxy settings removed from account {username}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove proxy settings: {str(e)}")


@router.post("/{username}/proxy/test", response_model=ProxyTestResult)
async def test_account_proxy(username: str):
    """Test proxy settings for account"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Get proxy settings
            cursor.execute('''
                           SELECT proxy_host, proxy_port, proxy_username, proxy_password, proxy_type
                           FROM accounts
                           WHERE username = ?
                           ''', (username,))

            proxy_data = cursor.fetchone()
            if not proxy_data or not proxy_data[0]:
                raise HTTPException(status_code=400, detail="No proxy configured for this account")

            proxy_host, proxy_port, proxy_username, proxy_password, proxy_type = proxy_data

            # Test proxy connection
            result = await test_proxy_connection(proxy_host, proxy_port, proxy_username, proxy_password, proxy_type)

            # Update proxy status in database
            new_status = "working" if result.success else "failed"
            cursor.execute('''
                           UPDATE accounts
                           SET proxy_status     = ?,
                               proxy_last_check = CURRENT_TIMESTAMP
                           WHERE username = ?
                           ''', (new_status, username))
            conn.commit()

            return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test proxy: {str(e)}")


@router.get("/{username}/proxy")
async def get_account_proxy(username: str):
    """Get proxy settings for account (without password)"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                           SELECT proxy_host,
                                  proxy_port,
                                  proxy_username,
                                  proxy_type,
                                  proxy_active,
                                  proxy_status,
                                  proxy_last_check
                           FROM accounts
                           WHERE username = ?
                           ''', (username,))

            proxy_data = cursor.fetchone()
            if not proxy_data:
                raise HTTPException(status_code=404, detail="Account not found")

            if not proxy_data[0]:  # No proxy configured
                return {
                    "proxy_configured": False,
                    "proxy_active": False
                }

            return {
                "proxy_configured": True,
                "proxy_host": proxy_data[0],
                "proxy_port": proxy_data[1],
                "proxy_username": proxy_data[2],
                "proxy_type": proxy_data[3],
                "proxy_active": bool(proxy_data[4]),
                "proxy_status": proxy_data[5],
                "proxy_last_check": proxy_data[6]
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proxy settings: {str(e)}")


@router.post("/proxy/check-all")
async def check_all_proxies():
    """Check health of all configured proxies"""
    try:
        results = await ProxyMonitoringService.check_all_proxies()
        return {
            "message": "Proxy health check completed",
            "results": results,
            "summary": {
                "total_checked": len(results),
                "working": len([r for r in results if r['status'] == 'working']),
                "failed": len([r for r in results if r['status'] == 'failed']),
                "disabled": len([r for r in results if r['status'] == 'disabled']),
                "errors": len([r for r in results if r['status'] == 'error'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check proxies: {str(e)}")


@router.get("/proxy/statistics")
async def get_proxy_statistics():
    """Get proxy usage and performance statistics"""
    try:
        stats = await ProxyMonitoringService.get_proxy_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proxy statistics: {str(e)}")


async def test_proxy_connection(host: str, port: int, username: str = None, password: str = None,
                                proxy_type: str = "HTTP") -> ProxyTestResult:
    """Test proxy connection by making request to external service"""
    try:
        # Normalize proxy type
        normalized_type = proxy_type.upper()
        if normalized_type == 'HTTPS':
            protocol = 'http'  # HTTPS proxies use HTTP protocol
        elif normalized_type == 'SOCKS5':
            protocol = 'socks5'
        else:
            protocol = 'http'

        # Build proxy URL
        if username and password:
            proxy_url = f"{protocol}://{username}:{password}@{host}:{port}"
        else:
            proxy_url = f"{protocol}://{host}:{port}"

        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }

        print(f"🔍 Testing proxy: {proxy_type} {host}:{port}")
        print(f"🔗 Proxy URL: {proxy_url}")

        # Try multiple test endpoints
        test_urls = [
            'http://httpbin.org/ip',
            'https://httpbin.org/ip',
            'http://icanhazip.com',
            'https://api.ipify.org?format=json'
        ]

        for test_url in test_urls:
            try:
                print(f"🌐 Testing with: {test_url}")
                start_time = time.time()

                response = requests.get(
                    test_url,
                    proxies=proxies,
                    timeout=20,
                    verify=False  # Skip SSL verification
                )

                response_time = time.time() - start_time

                if response.status_code == 200:
                    try:
                        # Try to extract IP from response
                        if 'json' in response.headers.get('content-type', ''):
                            ip_data = response.json()
                            external_ip = ip_data.get('origin', ip_data.get('ip', 'Unknown'))
                        else:
                            external_ip = response.text.strip()
                    except:
                        external_ip = "Unknown"

                    print(f"✅ Proxy test successful: {response_time:.2f}s, IP: {external_ip}")

                    return ProxyTestResult(
                        success=True,
                        message=f"Proxy is working correctly (via {test_url})",
                        response_time=round(response_time, 2),
                        external_ip=external_ip
                    )
                else:
                    print(f"❌ Status {response.status_code} from {test_url}")

            except requests.exceptions.Timeout:
                print(f"⏰ Timeout with {test_url}")
                continue
            except requests.exceptions.ProxyError as e:
                print(f"🚫 Proxy error with {test_url}: {e}")
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"🔌 Connection error with {test_url}: {e}")
                continue
            except Exception as e:
                print(f"❓ Error with {test_url}: {e}")
                continue

        # All URLs failed
        return ProxyTestResult(
            success=False,
            message="All test URLs failed - proxy may be down or misconfigured"
        )

    except Exception as e:
        print(f"❌ Proxy test exception: {e}")
        return ProxyTestResult(
            success=False,
            message=f"Proxy test failed: {str(e)}"
        )