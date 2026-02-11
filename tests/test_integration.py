"""
Integration tests using realistic KAS SOAP XML responses.
These test the full parsing pipeline from raw XML to Python objects.
"""
import unittest
from unittest.mock import MagicMock, patch
from kas_sdk import KasClient, KasApiError, KasAuthError, KasConnectionError


# --- Realistic SOAP XML fixtures (mimic actual KAS API responses) ---

# A successful response with a Response wrapper (typical for most actions)
XML_SUCCESS_SIMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <SOAP-ENV:Body>
    <ns1:KasApiResponse xmlns:ns1="urn:xmethods-delayed-quotes">
      <return xsi:type="xsd:string">
        <item>
          <key>ReturnString</key>
          <value>TRUE</value>
        </item>
        <item>
          <key>Response</key>
          <value>
            <item>
              <key>ReturnString</key>
              <value>TRUE</value>
            </item>
            <item>
              <key>ReturnInfo</key>
              <value>98765</value>
            </item>
          </value>
        </item>
      </return>
    </ns1:KasApiResponse>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

# A DNS record list response (list of DNS entries)
XML_DNS_RECORDS = b"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <SOAP-ENV:Body>
    <ns1:KasApiResponse xmlns:ns1="urn:xmethods-delayed-quotes">
      <return xsi:type="xsd:string">
        <item>
          <key>ReturnString</key>
          <value>TRUE</value>
        </item>
        <item>
          <key>Response</key>
          <value>
            <item>
              <key>ReturnString</key>
              <value>TRUE</value>
            </item>
            <item>
              <key>ReturnInfo</key>
              <value>
                <item>
                  <key>0</key>
                  <value>
                    <item><key>record_id</key><value>11111</value></item>
                    <item><key>record_name</key><value>www</value></item>
                    <item><key>record_type</key><value>A</value></item>
                    <item><key>record_data</key><value>1.2.3.4</value></item>
                    <item><key>record_aux</key><value>0</value></item>
                  </value>
                </item>
                <item>
                  <key>1</key>
                  <value>
                    <item><key>record_id</key><value>22222</value></item>
                    <item><key>record_name</key><value>mail</value></item>
                    <item><key>record_type</key><value>MX</value></item>
                    <item><key>record_data</key><value>mail.example.com.</value></item>
                    <item><key>record_aux</key><value>10</value></item>
                  </value>
                </item>
              </value>
            </item>
          </value>
        </item>
      </return>
    </ns1:KasApiResponse>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

# A SOAP fault response
XML_SOAP_FAULT = b"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
  <SOAP-ENV:Body>
    <SOAP-ENV:Fault>
      <faultcode>SOAP-ENV:Client</faultcode>
      <faultstring>Wrong credentials</faultstring>
    </SOAP-ENV:Fault>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

# XML with explicit namespace prefixes on item/key/value tags
XML_WITH_NAMESPACES = b"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:ns2="urn:kas-types">
  <SOAP-ENV:Body>
    <ns1:KasApiResponse xmlns:ns1="urn:xmethods-delayed-quotes">
      <return>
        <ns2:item>
          <ns2:key>ReturnString</ns2:key>
          <ns2:value>TRUE</ns2:value>
        </ns2:item>
        <ns2:item>
          <ns2:key>Response</ns2:key>
          <ns2:value>
            <ns2:item>
              <ns2:key>ReturnString</ns2:key>
              <ns2:value>TRUE</ns2:value>
            </ns2:item>
            <ns2:item>
              <ns2:key>ReturnInfo</ns2:key>
              <ns2:value>ns_test_ok</ns2:value>
            </ns2:item>
          </ns2:value>
        </ns2:item>
      </return>
    </ns1:KasApiResponse>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""


class TestCustomExceptions(unittest.TestCase):
    """Verify exception hierarchy and that credentials raise the right types."""

    def test_kas_auth_error_is_kas_api_error(self):
        self.assertTrue(issubclass(KasAuthError, KasApiError))

    def test_kas_connection_error_is_kas_api_error(self):
        self.assertTrue(issubclass(KasConnectionError, KasApiError))

    def test_missing_login_raises_kas_auth_error(self):
        with self.assertRaises(KasAuthError):
            KasClient(kas_login=None, kas_auth_data='pass')

    def test_missing_login_env_fallback(self):
        """When KAS_LOGIN env var is set, no exception should be raised."""
        with patch.dict('os.environ', {'KAS_LOGIN': 'w999', 'KAS_PASS': 'secret'}):
            client = KasClient()
            self.assertEqual(client.kas_login, 'w999')


class TestXmlParsing(unittest.TestCase):
    """Test full SOAP XML parsing pipeline."""

    def setUp(self):
        self.client = KasClient('user', 'pass')

    def test_simple_success_response(self):
        result = self.client._parse_soap_map(XML_SUCCESS_SIMPLE)
        self.assertEqual(result['ReturnString'], 'TRUE')
        self.assertEqual(result['ReturnInfo'], '98765')

    def test_dns_record_list_parsed_as_list(self):
        result = self.client._parse_soap_map(XML_DNS_RECORDS)
        records = result['ReturnInfo']
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['record_type'], 'A')
        self.assertEqual(records[1]['record_type'], 'MX')
        self.assertEqual(records[1]['record_aux'], '10')

    def test_soap_fault_raises_kas_api_error(self):
        with self.assertRaises(KasApiError) as ctx:
            self.client._parse_soap_map(XML_SOAP_FAULT)
        self.assertIn('Wrong credentials', str(ctx.exception))

    def test_namespace_prefixed_tags_parsed_correctly(self):
        """Regression: namespace-prefixed <ns2:item> tags must be handled."""
        result = self.client._parse_soap_map(XML_WITH_NAMESPACES)
        self.assertEqual(result['ReturnString'], 'TRUE')
        self.assertEqual(result['ReturnInfo'], 'ns_test_ok')

    def test_invalid_xml_raises_kas_api_error(self):
        with self.assertRaises(KasApiError):
            self.client._parse_soap_map(b'<broken xml')


class TestDnsServiceIntegration(unittest.TestCase):
    """Test DnsService methods with realistic XML responses."""

    @patch('kas_sdk.client.requests.post')
    def test_get_dns_settings_returns_list(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = XML_DNS_RECORDS

        client = KasClient('user', 'pass')
        records = client.dns.get_dns_settings('example.com.')

        self.assertIsInstance(records, list)
        self.assertEqual(records[0]['record_name'], 'www')
        self.assertEqual(records[0]['record_data'], '1.2.3.4')

    @patch('kas_sdk.client.requests.post')
    def test_add_dns_settings_returns_id(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = XML_SUCCESS_SIMPLE

        client = KasClient('user', 'pass')
        result = client.dns.add_dns_settings('example.com', 'A', 'test', '5.6.7.8')

        self.assertEqual(result, '98765')

    @patch('kas_sdk.client.requests.post')
    def test_connection_error_raises_kas_connection_error(self, mock_post):
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError("timeout")

        client = KasClient('user', 'pass')
        with self.assertRaises(KasConnectionError):
            client.dns.get_dns_settings('example.com.')


class TestDryRunMode(unittest.TestCase):

    def test_dry_run_does_not_call_requests(self):
        with patch('kas_sdk.client.requests.post') as mock_post:
            client = KasClient('user', 'pass', dry_run=True)
            result = client.dns.get_dns_settings('example.com.')
            mock_post.assert_not_called()

    def test_dry_run_via_env_var(self):
        with patch.dict('os.environ', {'KAS_DRY_RUN': '1'}):
            client = KasClient('user', 'pass')
            self.assertTrue(client.dry_run)


if __name__ == '__main__':
    unittest.main()
