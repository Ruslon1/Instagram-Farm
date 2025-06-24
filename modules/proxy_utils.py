"""
Utility functions for proxy management
"""

from typing import Optional, Dict, Any
from modules.database import get_database_connection
import requests
import time


def get_account_proxy_config(username: str) -> Optional[Dict[str, Any]]:
    """Get proxy configuration for an account"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                           SELECT proxy_host, proxy_port, proxy_username, proxy_password, 
                                  proxy_type, proxy_active, proxy_status
                           FROM accounts 
                           WHERE username = ? AND proxy_active = 1
                           ''', (username,))

            proxy_data = cursor.fetchone()
            if not proxy_data or not proxy_data[0]:
                return None

            return {
                'host': proxy_data[0],
                'port': proxy_data[1],
                'username': proxy_data[2],
                'password': proxy_data[3],
                'type': proxy_data[4] or 'HTTP',
                'active': bool(proxy_data[5]),
                'status': proxy_data[6] or 'unchecked'
            }

    except Exception as e:
        print(f"Error getting proxy config for {username}: {e}")
        return None


def build_proxy_url(proxy_config: Dict[str, Any]) -> str:
    """Build proxy URL from config"""
    host = proxy_config['host']
    port = proxy_config['port']
    username = proxy_config.get('username')
    password = proxy_config.get('password')
    proxy_type = proxy_config.get('type', 'HTTP').lower()

    if username and password:
        return f"{proxy_type}://{username}:{password}@{host}:{port}"
    else:
        return f"{proxy_type}://{host}:{port}"


def get_proxy_dict(proxy_config: Dict[str, Any]) -> Dict[str, str]:
    """Get proxy dictionary for requests/instagrapi"""
    proxy_url = build_proxy_url(proxy_config)
    return {
        'http': proxy_url,
        'https': proxy_url
    }


def get_instagrapi_proxy_settings(proxy_config: Dict[str, Any]) -> Dict[str, Any]:
    """Get proxy settings formatted for instagrapi Client"""
    proxy_type = proxy_config.get('type', 'HTTP').upper()

    settings = {
        'proxy': proxy_config['host'],
        'proxy_port': proxy_config['port'],
    }

    if proxy_config.get('username') and proxy_config.get('password'):
        settings['proxy_username'] = proxy_config['username']
        settings['proxy_password'] = proxy_config['password']

    # instagrapi uses different proxy type names
    if proxy_type == 'HTTP':
        settings['proxy_type'] = 'http'
    elif proxy_type == 'SOCKS5':
        settings['proxy_type'] = 'socks5'

    return settings


def test_proxy_connection(proxy_config: Dict[str, Any], timeout: int = 15) -> bool:
    """Test if proxy is working"""
    try:
        proxy_dict = get_proxy_dict(proxy_config)

        start_time = time.time()
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxy_dict,
            timeout=timeout
        )
        response_time = time.time() - start_time

        if response.status_code == 200:
            print(f"Proxy test successful: {response_time:.2f}s")
            return True
        else:
            print(f"Proxy test failed with status: {response.status_code}")
            return False

    except Exception as e:
        print(f"Proxy test failed: {e}")
        return False


def update_proxy_status(username: str, status: str, error_message: str = None):
    """Update proxy status for account"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                           UPDATE accounts 
                           SET proxy_status = ?, proxy_last_check = CURRENT_TIMESTAMP
                           WHERE username = ?
                           ''', (status, username))

            conn.commit()

            if status == 'failed' and error_message:
                print(f"Proxy failed for {username}: {error_message}")

    except Exception as e:
        print(f"Error updating proxy status for {username}: {e}")


def is_proxy_working(username: str) -> bool:
    """Check if account has working proxy"""
    proxy_config = get_account_proxy_config(username)
    if not proxy_config:
        return False

    return proxy_config.get('status') == 'working' and proxy_config.get('active', False)


def validate_and_test_proxy(username: str) -> Optional[Dict[str, Any]]:
    """Validate and test proxy before using it for upload"""
    proxy_config = get_account_proxy_config(username)
    if not proxy_config:
        return None

    print(f"🔍 Testing proxy for {username}: {proxy_config['host']}:{proxy_config['port']}")

    # Test the proxy
    is_working = test_proxy_connection(proxy_config)

    # Update status in database
    new_status = "working" if is_working else "failed"
    update_proxy_status(username, new_status)

    if is_working:
        print(f"✅ Proxy validated for {username}")
        return proxy_config
    else:
        print(f"❌ Proxy failed for {username}, will use direct connection")
        return None