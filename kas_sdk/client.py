import requests
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
import time
import os
import logging
from .exceptions import KasApiError, KasAuthError, KasConnectionError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Official API Endpoint
SOAP_URL = "https://kasapi.kasserver.com/soap/KasApi.php"

# Configure logging for the client
logger = logging.getLogger(__name__)

class KasClient:
    """
    A robust client for the All-Inkl KAS SOAP API.
    Handles authentication, XML creation, and response parsing.
    Enforces quirks like 'No Integers' in parameters.
    """

    def __init__(self, kas_login: Optional[str] = None, kas_auth_data: Optional[str] = None, kas_auth_type: str = "plain", api_url: str = SOAP_URL, flood_protection_delay: float = 2.0, dry_run: bool = False):
        """
        Initialize the KAS Client.
        
        Credentials Resolution Order:
        1. Explicit Arguments
        2. Environment Variables (KAS_LOGIN, KAS_PASS)
        3. System Keyring (service='kas_api', username=kas_login)

        :param kas_login: KAS Login (e.g. w012345). Optional if in Env.
        :param kas_auth_data: KAS Password. Optional if in Env or Keyring.
        :param kas_auth_type: Auth type, usually 'plain' or 'sha1'
        :param api_url: URL to the SOAP endpoint
        :param flood_protection_delay: Delay in seconds between requests.
        :param dry_run: If True, do not send requests to the API.
        """
        # 1. Resolve Login
        self.kas_login = kas_login or os.getenv('KAS_LOGIN')
        if not self.kas_login:
            raise KasAuthError("KAS Login is required. Provide it as argument or set KAS_LOGIN environment variable.")

        # 2. Resolve Password
        self.kas_auth_data = kas_auth_data or os.getenv('KAS_PASS')
        
        # 3. Try Keyring if password missing
        if not self.kas_auth_data:
            try:
                import keyring
                # Try to get password from keyring for the resolved login
                key_pass = keyring.get_password("kas_api", self.kas_login)
                if key_pass:
                    self.kas_auth_data = key_pass
                    logger.info(f"Loaded password for {self.kas_login} from System Keyring.")
            except ImportError:
                logger.debug("Keyring module not installed, skipping credential lookup.")
            except Exception as e:
                logger.warning(f"Keyring lookup failed: {e}")

        if not self.kas_auth_data:
             # Just warn here? Or raise? KAS API will fail anyway.
             # Better to raise early so user knows what's missing.
             # But maybe dry_run allows missing pass?
             if not dry_run and not os.getenv('KAS_DRY_RUN'): # Check effective dry_run later
                  # Actually let's just log warning, maybe auth_type doesn't need data (unlikely)
                  logger.warning("No KAS Password found. API calls will likely fail.")

        self.kas_auth_type = kas_auth_type
        self.api_url = api_url
        self.flood_protection_delay = flood_protection_delay
        
        # Determine strict dry_run setting either from parameter or environment variable
        self.dry_run = dry_run or os.getenv('KAS_DRY_RUN', '').lower() in ('true', '1', 'yes')
        
        if self.dry_run:
            logger.warning("KAS SDK is running in DRY-RUN mode. No requests will be sent.")
            
        self._last_request_time = 0.0

    # Maps service attribute name -> (module path, class name)
    _SERVICE_MAP = {
        'account':             ('kas_sdk.services.account',             'AccountService'),
        'dns':                 ('kas_sdk.services.dns',                 'DnsService'),
        'domain':              ('kas_sdk.services.domain',              'DomainService'),
        'mailaccount':         ('kas_sdk.services.mailaccount',         'MailAccountService'),
        'cronjob':             ('kas_sdk.services.cronjob',             'CronjobService'),
        'database':            ('kas_sdk.services.database',            'DatabaseService'),
        'ftpuser':             ('kas_sdk.services.ftpuser',             'FtpUserService'),
        'softwareinstall':     ('kas_sdk.services.softwareinstall',     'SoftwareInstallService'),
        'mailfilter':          ('kas_sdk.services.mailfilter',          'MailFilterService'),
        'mailforward':         ('kas_sdk.services.mailforward',         'MailForwardService'),
        'mailinglist':         ('kas_sdk.services.mailinglist',         'MailingListService'),
        'ddns':                ('kas_sdk.services.ddns',                'DdnsService'),
        'subdomain':           ('kas_sdk.services.subdomain',           'SubdomainService'),
        'symlink':             ('kas_sdk.services.symlink',             'SymlinkService'),
        'ssl':                 ('kas_sdk.services.ssl',                 'SslService'),
        'sambauser':           ('kas_sdk.services.sambauser',           'SambaUserService'),
        'chown':               ('kas_sdk.services.chown',               'ChownService'),
        'directoryprotection': ('kas_sdk.services.directoryprotection', 'DirectoryProtectionService'),
        'session':             ('kas_sdk.services.session',             'SessionService'),
        'statistic':           ('kas_sdk.services.statistic',           'StatisticService'),
        'dkim':                ('kas_sdk.services.dkim',                'DkimService'),
    }

    def __getattr__(self, name: str):
        """Lazily imports and instantiates a service on first access."""
        if name in self._SERVICE_MAP:
            import importlib
            module_path, class_name = self._SERVICE_MAP[name]
            module = importlib.import_module(module_path)
            service = getattr(module, class_name)(self)
            # Cache on instance so subsequent accesses skip __getattr__
            object.__setattr__(self, name, service)
            return service
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def request(self, action: str, params: Dict[str, Any]) -> Any:
        """
        Sends a Raw-SOAP Request to the API.

        :param action: Name of the KAS action (e.g., 'get_subdomains')
        :param params: Dictionary with parameters for the action
        :return: A dictionary with the answer or raises an exception on error
        """
        # Enforce Flood Protection
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self.flood_protection_delay:
            time.sleep(self.flood_protection_delay - time_since_last)
        
        # 1. Sanitize Parameters: Convert ALL values to strings (Rule #1)
        clean_params = {k: str(v) for k, v in params.items() if v is not None}

        # Auth and Payload Construction
        req_data = {
            'kas_login': self.kas_login,
            'kas_auth_type': self.kas_auth_type,
            'kas_auth_data': self.kas_auth_data,
            'kas_action': action,
            'KasRequestParams': clean_params
        }
        json_payload = json.dumps(req_data)

        # Manual SOAP Envelope Construction
        soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
        <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <SOAP-ENV:Body>
            <ns1:KasApi xmlns:ns1="urn:xmethods-delayed-quotes">
                <KasRequest xsi:type="xsd:string">{json_payload}</KasRequest>
            </ns1:KasApi>
        </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>"""

        if self.dry_run:
            logger.info(f"[DRY-RUN] Action: {action}")
            logger.info(f"[DRY-RUN] Params: {clean_params}")
            logger.debug(f"[DRY-RUN] SOAP Body: {soap_body}")
            
            # Return a mock successful response
            return {
                'ReturnString': 'TRUE',
                'ReturnInfo': 'DRY_RUN_ACTIVE', 
                'RequestParams': clean_params,
                'Response': {'ReturnString': 'TRUE', 'ReturnInfo': 'DRY_RUN_ACTIVE'} # Handles unwrapping logic
            }

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'User-Agent': 'Python-KAS-SDK/1.0'
        }

        try:
            response = requests.post(self.api_url, data=soap_body, headers=headers, timeout=30)
            self._last_request_time = time.time()
            response.raise_for_status()
            return self._parse_soap_map(response.content)
        except KasApiError:
            raise
        except Exception as e:
            raise KasConnectionError(f"HTTP Request failed: {e}") from e

    def _parse_soap_map(self, xml_content: bytes) -> Any:
        try:
            root = ET.fromstring(xml_content)

            # Check for Faults
            for elem in root.iter():
                if 'faultstring' in elem.tag and elem.text:
                    raise KasApiError(f"KAS API Fault: {elem.text.strip()}")

            # Find return node
            return_node = None
            for elem in root.iter():
                if 'return' in elem.tag:
                    return_node = elem
                    break

            if return_node is None:
                return {}

            result = self._parse_element(return_node)
            
            # Automatic unwrapping of 'Response' wrapper if present
            # KAS often returns {'Request': {...}, 'Response': {...}}
            if isinstance(result, dict) and 'Response' in result:
                return result['Response']
            
            return result

        except ET.ParseError as e:
            raise KasApiError(f"Could not parse XML response: {e}") from e

    @staticmethod
    def _local_tag(element: ET.Element) -> str:
        """Returns the local tag name without XML namespace prefix."""
        tag = element.tag
        return tag.split('}', 1)[1] if '}' in tag else tag

    def _parse_element(self, element: ET.Element) -> Any:
        """
        Recursively parses an XML element into Python types (Dict, List, String).
        KAS API typically uses <item><key>...</key><value>...</value></item> for Maps.
        """
        children = list(element)
        if not children:
            return element.text.strip() if element.text else ""

        parsed_dict = {}
        parsed_list = []

        for child in children:
            if self._local_tag(child) == 'item':
                key_node = None
                value_node = None
                for sub in child:
                    local = self._local_tag(sub)
                    if local == 'key':
                        key_node = sub
                    elif local == 'value':
                        value_node = sub

                if key_node is not None and value_node is not None:
                    key = key_node.text.strip() if key_node.text else ""
                    parsed_dict[key] = self._parse_element(value_node)
                else:
                    parsed_list.append(self._parse_element(child))
            else:
                parsed_dict[self._local_tag(child)] = self._parse_element(child)

        if parsed_dict:
            # Heuristic: If all keys are integers '0', '1', '2'..., likely a List
            if all(k.isdigit() for k in parsed_dict.keys()):
                # Check if they are sequential 0 to N?
                # For safety, let's return the list of values sorted by key
                try:
                    sorted_keys = sorted(parsed_dict.keys(), key=int)
                    # If keys are compact '0'..'N', return list
                    if int(sorted_keys[0]) == 0 and int(sorted_keys[-1]) == len(parsed_dict) - 1:
                        return [parsed_dict[k] for k in sorted_keys]
                except (ValueError, IndexError):
                    pass
            return parsed_dict
        
        if parsed_list:
            return parsed_list

        return element.text.strip() if element.text else ""
