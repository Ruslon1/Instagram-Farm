"""
Proxy monitoring and health check service
"""

import asyncio
import time
from typing import List, Dict, Any
from modules.database import get_database_connection
from modules.proxy_utils import test_proxy_connection, update_proxy_status, get_account_proxy_config


class ProxyMonitoringService:
    """Service for monitoring proxy health and performance"""

    @staticmethod
    async def get_all_proxy_accounts() -> List[Dict[str, Any]]:
        """Get all accounts with proxy configured"""
        try:
            with get_database_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT username,
                           proxy_host,
                           proxy_port,
                           proxy_username,
                           proxy_password,
                           proxy_type,
                           proxy_active,
                           proxy_status,
                           proxy_last_check
                    FROM accounts
                    WHERE proxy_host IS NOT NULL
                    ORDER BY username
                ''')

                accounts = []
                for row in cursor.fetchall():
                    accounts.append({
                        'username': row[0],
                        'proxy_host': row[1],
                        'proxy_port': row[2],
                        'proxy_username': row[3],
                        'proxy_password': row[4],
                        'proxy_type': row[5] or 'HTTP',
                        'proxy_active': bool(row[6]),
                        'proxy_status': row[7] or 'unchecked',
                        'proxy_last_check': row[8]
                    })

                return accounts

        except Exception as e:
            print(f"Error getting proxy accounts: {e}")
            return []

    @staticmethod
    async def check_proxy_health(username: str) -> Dict[str, Any]:
        """Check health of proxy for specific account"""
        try:
            proxy_config = get_account_proxy_config(username)
            if not proxy_config:
                return {
                    'username': username,
                    'status': 'no_proxy',
                    'message': 'No proxy configured'
                }

            print(f"🔍 Checking proxy health for {username}...")
            start_time = time.time()

            is_working = test_proxy_connection(proxy_config, timeout=15)
            response_time = time.time() - start_time

            new_status = "working" if is_working else "failed"
            update_proxy_status(username, new_status)

            return {
                'username': username,
                'status': new_status,
                'response_time': round(response_time, 2),
                'proxy_host': proxy_config['host'],
                'proxy_port': proxy_config['port'],
                'message': 'Proxy is working' if is_working else 'Proxy connection failed'
            }

        except Exception as e:
            print(f"Error checking proxy health for {username}: {e}")
            update_proxy_status(username, "failed", str(e))

            return {
                'username': username,
                'status': 'error',
                'message': f'Health check failed: {str(e)}'
            }

    @staticmethod
    async def check_all_proxies() -> List[Dict[str, Any]]:
        """Check health of all configured proxies"""
        accounts = await ProxyMonitoringService.get_all_proxy_accounts()
        results = []

        print(f"🏥 Starting health check for {len(accounts)} proxy accounts...")

        for account in accounts:
            if not account['proxy_active']:
                results.append({
                    'username': account['username'],
                    'status': 'disabled',
                    'message': 'Proxy is disabled for this account'
                })
                continue

            try:
                result = await ProxyMonitoringService.check_proxy_health(account['username'])
                results.append(result)

                # Small delay between checks to avoid overwhelming proxies
                await asyncio.sleep(1)

            except Exception as e:
                results.append({
                    'username': account['username'],
                    'status': 'error',
                    'message': f'Check failed: {str(e)}'
                })

        # Summary
        working = len([r for r in results if r['status'] == 'working'])
        failed = len([r for r in results if r['status'] == 'failed'])

        print(f"📊 Proxy health check completed: {working} working, {failed} failed out of {len(results)} total")

        return results

    @staticmethod
    async def get_proxy_statistics() -> Dict[str, Any]:
        """Get proxy usage and performance statistics"""
        try:
            accounts = await ProxyMonitoringService.get_all_proxy_accounts()

            total_accounts = len(accounts)
            active_proxies = len([a for a in accounts if a['proxy_active']])
            working_proxies = len([a for a in accounts if a['proxy_status'] == 'working' and a['proxy_active']])
            failed_proxies = len([a for a in accounts if a['proxy_status'] == 'failed'])
            unchecked_proxies = len([a for a in accounts if a['proxy_status'] == 'unchecked'])

            # Group by proxy type
            proxy_types = {}
            for account in accounts:
                proxy_type = account['proxy_type']
                if proxy_type not in proxy_types:
                    proxy_types[proxy_type] = 0
                proxy_types[proxy_type] += 1

            return {
                'total_accounts_with_proxy': total_accounts,
                'active_proxies': active_proxies,
                'working_proxies': working_proxies,
                'failed_proxies': failed_proxies,
                'unchecked_proxies': unchecked_proxies,
                'proxy_types': proxy_types,
                'health_percentage': round((working_proxies / active_proxies * 100) if active_proxies > 0 else 0, 1)
            }

        except Exception as e:
            print(f"Error getting proxy statistics: {e}")
            return {
                'total_accounts_with_proxy': 0,
                'active_proxies': 0,
                'working_proxies': 0,
                'failed_proxies': 0,
                'unchecked_proxies': 0,
                'proxy_types': {},
                'health_percentage': 0
            }

    @staticmethod
    async def auto_disable_failed_proxies(failure_threshold: int = 3) -> List[str]:
        """Automatically disable proxies that have been failing consistently"""
        try:
            with get_database_connection() as conn:
                cursor = conn.cursor()

                # For now, we'll just disable proxies that have been failing
                # In a more advanced implementation, you could track failure counts
                cursor.execute('''
                    SELECT username
                    FROM accounts
                    WHERE proxy_active = 1
                      AND proxy_status = 'failed'
                ''')

                failed_accounts = [row[0] for row in cursor.fetchall()]

                if failed_accounts:
                    print(f"🚫 Auto-disabling {len(failed_accounts)} consistently failed proxies...")

                    # Disable failed proxies
                    cursor.execute('''
                        UPDATE accounts
                        SET proxy_active = 0
                        WHERE proxy_active = 1
                          AND proxy_status = 'failed'
                    ''')

                    conn.commit()

                    print(f"✅ Disabled proxies for accounts: {', '.join(failed_accounts)}")

                return failed_accounts

        except Exception as e:
            print(f"Error auto-disabling failed proxies: {e}")
            return []