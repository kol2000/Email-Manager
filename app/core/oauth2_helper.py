from core.i18n import tx
import urllib.parse
import requests
import secrets
import time
DEFAULT_CLIENT_ID = '9e5f94bc-e8a4-4e73-b8be-63364c29d753'
SCOPES = ['offline_access', 'https://outlook.office.com/IMAP.AccessAsUser.All', 'https://outlook.office.com/SMTP.Send']
REDIRECT_URI = 'https://localhost'

class SeleniumOAuth2:

    def __init__(self, client_id=None):
        self.client_id = client_id or DEFAULT_CLIENT_ID
        self.driver = None

    def init_driver(self):
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            options = Options()
            options.add_argument('--inprivate')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1280,900')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
            options.add_experimental_option('useAutomationExtension', False)
            self.driver = webdriver.Edge(options=options)
            return (True, None)
        except Exception as e:
            return (False, tx('Browser initialization failed: {0}', str(e)))

    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

    def authorize_semi_auto(self, email='', progress_callback=None, timeout=120):
        try:
            state = secrets.token_urlsafe(16)
            params = {'client_id': self.client_id, 'response_type': 'code', 'redirect_uri': REDIRECT_URI, 'response_mode': 'query', 'scope': ' '.join(SCOPES), 'state': state}
            if email:
                params['login_hint'] = email
            base_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
            auth_url = f'{base_url}?{urllib.parse.urlencode(params)}'
            if progress_callback:
                progress_callback(tx('Opening the authorization page. Please sign in...'))
            self.driver.get(auth_url)
            if progress_callback:
                progress_callback(tx('Waiting for sign-in...'))
            auth_code = None
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    current_url = self.driver.current_url
                    if 'code=' in current_url:
                        parsed = urllib.parse.urlparse(current_url)
                        url_params = urllib.parse.parse_qs(parsed.query)
                        if 'code' in url_params:
                            auth_code = url_params['code'][0]
                            if progress_callback:
                                progress_callback(tx('Authorization code received!'))
                            break
                    if 'error=' in current_url:
                        parsed = urllib.parse.urlparse(current_url)
                        url_params = urllib.parse.parse_qs(parsed.query)
                        error_desc = url_params.get('error_description', [tx('Authorization failed')])[0]
                        error_desc = urllib.parse.unquote(error_desc)
                        return (None, None, tx('Authorization failed: {0}', error_desc))
                except Exception:
                    return (None, None, tx('Browser was closed'))
                time.sleep(1)
            if not auth_code:
                return (None, None, tx('Authorization timed out'))
            if progress_callback:
                progress_callback(tx('Obtaining token...'))
            token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
            data = {'client_id': self.client_id, 'code': auth_code, 'redirect_uri': REDIRECT_URI, 'grant_type': 'authorization_code', 'scope': ' '.join(SCOPES)}
            response = requests.post(token_url, data=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                refresh_token = result.get('refresh_token')
                if refresh_token:
                    return (self.client_id, refresh_token, None)
                else:
                    return (None, None, tx('No refresh_token returned'))
            else:
                error_data = response.json()
                error = error_data.get('error_description', response.text)
                return (None, None, tx('Failed to obtain token: {0}', error))
        except Exception as e:
            return (None, None, tx('Authorization error: {0}', str(e)))
