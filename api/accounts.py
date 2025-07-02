from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import requests
import time
from api.models import AccountCreate, ProxySettings, ProxyTestResult
from modules.database import get_database_connection
from modules.uploader import test_instagram_connection, cleanup_session
from services.proxy_monitoring_service import ProxyMonitoringService

router = APIRouter()


@router.get("/")
async def get_accounts():
    """Get all Instagram accounts with proxy info - returns JSON directly"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # PostgreSQL compatible query with safe result handling
            cursor.execute('''
                           SELECT username,
                                  theme,
                                  COALESCE(status, 'active')          as status,
                                  COALESCE(posts_count, 0)            as posts_count,
                                  last_login,
                                  proxy_host,
                                  proxy_port,
                                  COALESCE(proxy_status, 'unchecked') as proxy_status,
                                  COALESCE(proxy_active, FALSE)       as proxy_active
                           FROM accounts
                           WHERE COALESCE(active, TRUE) = TRUE
                           ORDER BY username
                           ''')

            accounts = []
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    try:
                        # Safe access to row elements
                        username = row[0] if len(row) > 0 else ""
                        theme = row[1] if len(row) > 1 else ""
                        status = row[2] if len(row) > 2 else "active"
                        posts_count = row[3] if len(row) > 3 else 0
                        last_login = row[4] if len(row) > 4 else None
                        proxy_host = row[5] if len(row) > 5 else None
                        proxy_port = row[6] if len(row) > 6 else None
                        proxy_status = row[7] if len(row) > 7 else "unchecked"
                        proxy_active = row[8] if len(row) > 8 else False

                        # Convert last_login to string if it's a datetime
                        last_login_str = None
                        if last_login:
                            if hasattr(last_login, 'isoformat'):
                                last_login_str = last_login.isoformat()
                            else:
                                last_login_str = str(last_login)

                        account_dict = {
                            "username": username,
                            "theme": theme,
                            "status": status,
                            "posts_count": int(posts_count) if posts_count else 0,
                            "last_login": last_login_str,
                            "proxy_host": proxy_host,
                            "proxy_port": proxy_port,
                            "proxy_status": proxy_status,
                            "proxy_active": bool(proxy_active)
                        }
                        accounts.append(account_dict)
                    except Exception as row_error:
                        print(f"Error processing row {row}: {row_error}")
                        continue

            print(f"Successfully fetched {len(accounts)} accounts")
            return JSONResponse(content=accounts)

    except Exception as e:
        print(f"Error in get_accounts: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch accounts: {str(e)}")


@router.post("/")
async def create_account(account: AccountCreate):
    """Add new Instagram account with login verification"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if account exists
            cursor.execute("SELECT username FROM accounts WHERE username = %s", (account.username,))
            existing = cursor.fetchone()

            if existing:
                raise HTTPException(status_code=400, detail="Account already exists")

            # First, test Instagram connection to verify credentials
            print(f"🧪 Testing Instagram login for @{account.username}")

            # Test connection and create session
            login_success = test_instagram_connection(
                username=account.username,
                password=account.password,
                two_fa_key=account.two_fa_key
            )

            if not login_success:
                print(f"❌ Login verification failed for @{account.username}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to verify Instagram credentials. Please check username, password, and 2FA key."
                )

            print(f"✅ Login verification successful for @{account.username}")

            # Insert new account with verified status
            cursor.execute('''
                           INSERT INTO accounts (username, password, theme, "2FAKey", status, active, posts_count,
                                                 last_login)
                           VALUES (%s, %s, %s, %s, 'active', TRUE, 0, CURRENT_TIMESTAMP)
                           ''', (account.username, account.password, account.theme, account.two_fa_key))

            conn.commit()

        return {
            "message": f"Account {account.username} created and verified successfully",
            "verified": True,
            "session_created": True
        }

    except HTTPException:
        # Clean up any created session files on error
        try:
            cleanup_session(account.username)
        except:
            pass
        raise
    except Exception as e:
        # Clean up any created session files on error
        try:
            cleanup_session(account.username)
        except:
            pass
        print(f"Error creating account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")


@router.post("/{username}/verify")
async def verify_account(username: str):
    """Verify existing account login and refresh session"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Get account details
            cursor.execute(
                'SELECT username, password, "2FAKey" FROM accounts WHERE username = %s',
                (username,)
            )
            account_data = cursor.fetchone()

            if not account_data:
                raise HTTPException(status_code=404, detail="Account not found")

            account_username, password, two_fa_key = account_data

            print(f"🧪 Verifying Instagram login for @{username}")

            # Clean up existing session first
            cleanup_session(username)

            # Test connection and create fresh session
            login_success = test_instagram_connection(
                username=account_username,
                password=password,
                two_fa_key=two_fa_key
            )

            if not login_success:
                print(f"❌ Login verification failed for @{username}")

                # Update account status to error
                cursor.execute('''
                               UPDATE accounts
                               SET status     = 'error',
                                   last_login = NULL
                               WHERE username = %s
                               ''', (username,))
                conn.commit()

                raise HTTPException(
                    status_code=400,
                    detail="Failed to verify Instagram credentials. Please check account status."
                )

            print(f"✅ Login verification successful for @{username}")

            # Update account status and last login
            cursor.execute('''
                           UPDATE accounts
                           SET status     = 'active',
                               last_login = CURRENT_TIMESTAMP
                           WHERE username = %s
                           ''', (username,))
            conn.commit()

        return {
            "message": f"Account @{username} verified successfully",
            "verified": True,
            "session_refreshed": True,
            "status": "active"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error verifying account: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to verify account: {str(e)}")


@router.put("/{username}/proxy")
async def update_account_proxy(username: str, proxy_settings: ProxySettings):
    """Update proxy settings for account"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if account exists
            cursor.execute("SELECT username FROM accounts WHERE username = %s", (username,))
            account = cursor.fetchone()

            if not account:
                raise HTTPException(status_code=404, detail="Account not found")

            # Update proxy settings
            cursor.execute('''
                           UPDATE accounts
                           SET proxy_host       = %s,
                               proxy_port       = %s,
                               proxy_username   = %s,
                               proxy_password   = %s,
                               proxy_type       = %s,
                               proxy_active     = %s,
                               proxy_status     = 'unchecked',
                               proxy_last_check = NULL
                           WHERE username = %s
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
        print(f"Error updating proxy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update proxy settings: {str(e)}")


@router.delete("/{username}/proxy")
async def remove_account_proxy(username: str):
    """Remove proxy settings from account"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if account exists
            cursor.execute("SELECT username FROM accounts WHERE username = %s", (username,))
            account = cursor.fetchone()

            if not account:
                raise HTTPException(status_code=404, detail="Account not found")

            # Clear proxy settings
            cursor.execute('''
                           UPDATE accounts
                           SET proxy_host       = NULL,
                               proxy_port       = NULL,
                               proxy_username   = NULL,
                               proxy_password   = NULL,
                               proxy_type       = NULL,
                               proxy_active     = FALSE,
                               proxy_status     = 'unchecked',
                               proxy_last_check = NULL
                           WHERE username = %s
                           ''', (username,))

            conn.commit()

        return {"message": f"Proxy settings removed from account {username}"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error removing proxy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove proxy settings: {str(e)}")


@router.post("/{username}/proxy/test")
async def test_account_proxy(username: str):
    """Test proxy settings for account"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Get proxy settings
            cursor.execute('''
                           SELECT proxy_host, proxy_port, proxy_username, proxy_password, proxy_type
                           FROM accounts
                           WHERE username = %s
                           ''', (username,))

            proxy_data = cursor.fetchone()
            if not proxy_data or not proxy_data[0]:
                raise HTTPException(status_code=400, detail="No proxy configured for this account")

            proxy_host, proxy_port, proxy_username, proxy_password, proxy_type = proxy_data

            # Test proxy connection
            result = await test_proxy_connection(proxy_host, proxy_port, proxy_username, proxy_password, proxy_type)

            # Update proxy status in database
            new_status = "working" if result["success"] else "failed"
            cursor.execute('''
                           UPDATE accounts
                           SET proxy_status     = %s,
                               proxy_last_check = CURRENT_TIMESTAMP
                           WHERE username = %s
                           ''', (new_status, username))
            conn.commit()

            return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error testing proxy: {e}")
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
                           WHERE username = %s
                           ''', (username,))

            proxy_data = cursor.fetchone()
            if not proxy_data:
                raise HTTPException(status_code=404, detail="Account not found")

            if not proxy_data[0]:  # No proxy configured
                return {
                    "proxy_configured": False,
                    "proxy_active": False
                }

            # Convert datetime to string if needed
            proxy_last_check = proxy_data[6]
            if proxy_last_check and hasattr(proxy_last_check, 'isoformat'):
                proxy_last_check = proxy_last_check.isoformat()

            return {
                "proxy_configured": True,
                "proxy_host": proxy_data[0],
                "proxy_port": proxy_data[1],
                "proxy_username": proxy_data[2],
                "proxy_type": proxy_data[3],
                "proxy_active": bool(proxy_data[4]) if proxy_data[4] is not None else False,
                "proxy_status": proxy_data[5],
                "proxy_last_check": proxy_last_check
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting proxy: {e}")
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
        print(f"Error checking all proxies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check proxies: {str(e)}")


@router.get("/proxy/statistics")
async def get_proxy_statistics():
    """Get proxy usage and performance statistics"""
    try:
        stats = await ProxyMonitoringService.get_proxy_statistics()
        return stats
    except Exception as e:
        print(f"Error getting proxy stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get proxy statistics: {str(e)}")


async def test_proxy_connection(host: str, port: int, username: str = None, password: str = None,
                                proxy_type: str = "HTTP") -> dict:
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

                    return {
                        "success": True,
                        "message": f"Proxy is working correctly (via {test_url})",
                        "response_time": round(response_time, 2),
                        "external_ip": external_ip
                    }
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
        return {
            "success": False,
            "message": "All test URLs failed - proxy may be down or misconfigured"
        }

    except Exception as e:
        print(f"❌ Proxy test exception: {e}")
        return {
            "success": False,
            "message": f"Proxy test failed: {str(e)}"
        }