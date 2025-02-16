import json

import unittest
from pyapi_zabbix import ZabbixAPI, ZabbixAPIException, ssl_context_compat
from pyapi_zabbix.logger import HideSensitiveService
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch
from sys import version_info

# For Python 2 and 3 compatibility
if version_info[0] == 2:
    urlopen = 'urllib2.urlopen'
    res_type = str
elif version_info[0] >= 3:
    res_type = bytes
    urlopen = 'urllib.request.urlopen'


class MockResponse(object):

    def __init__(self, ret, code=200, msg='OK'):
        self.ret = ret
        self.code = code
        self.msg = msg
        self.headers = {'content-type': 'text/plain; charset=utf-8'}

    def read(self):
        return res_type(self.ret.encode('utf-8'))

    def getcode(self):
        return self.code


class TestZabbixAPI(unittest.TestCase):

    def setUp(self):
        "Mock urllib2.urlopen"
        self.patcher = patch(urlopen)
        self.urlopen_mock = self.patcher.start()

    def test_decorator_ssl_context_compat(self):
        @ssl_context_compat
        def test_decorator(*args, **kwargs):
            def response(*args, **kwargs):
                return args, kwargs
            return response(*args, **kwargs)

        arg, context = test_decorator(True)
        self.assertIs(arg[0], True)
        self.assertIn('context', context, msg='SSL context is missing.')
        self.assertIsNotNone(context.get('context'),
                             msg='SSL context is None.')

    def test_api_version(self):
        ret = {'result': '2.2.5'}
        self.urlopen_mock.return_value = MockResponse(json.dumps(ret))
        res = ZabbixAPI().api_version()
        self.assertEqual(res, '2.2.5')

    def test_login(self):
        req = {'user': 'Admin', 'password': 'zabbix'}
        ret = {
            'jsonrpc': '2.0',
            'result': '0424bd59b807674191e7d77572075f33',
            'id': 1
        }
        self.urlopen_mock.return_value = MockResponse(json.dumps(ret))
        res = ZabbixAPI().user.login(**req)
        self.assertEqual(res, '0424bd59b807674191e7d77572075f33')

    def test_login_with(self):
        """Test automatic user.logout when using context manager"""

        login_ret = {
            'jsonrpc': '2.0',
            'result': '0424bd59b807674191e7d77572075f33',
            'id': 1
        }
        logout_ret = {
            "jsonrpc": "2.0",
            "result": True,
            "id": 1
        }
        self.urlopen_mock.side_effect = [MockResponse(json.dumps(login_ret)),
                                         MockResponse(json.dumps(logout_ret))]

        with ZabbixAPI() as zapi:
            # Check you are authenticated:
            self.assertEqual(zapi.auth, login_ret['result'])
        # Check that you are no longer authenticated when outside:
        self.assertEqual(zapi.auth, None)
        # Zabbix API is accessed two times: user.login(), user.logout().
        self.assertEqual(self.urlopen_mock.call_count, 2)

    def test_do_request(self):
        req = 'apiinfo.version'
        ret = {
            'jsonrpc': '2.0',
            'result': '2.2.5',
            'id': 1
        }
        self.urlopen_mock.return_value = MockResponse(json.dumps(ret))
        res = ZabbixAPI().do_request(req)
        self.assertEqual(res, ret)

    def test_get_id_item(self):
        ret = {
            'jsonrpc': '2.0',
            'result':
            [{
                'itemid': '23298',
                'hostid': '10084',
                'name': 'Test Item',
                'key_': 'system.cpu.switches',
                'description': '',
            }],
            'id': 1,
        }
        self.urlopen_mock.return_value = MockResponse(json.dumps(ret))
        res = ZabbixAPI().get_id('item', item='Test Item')
        self.assertEqual(res, 23298)

    @unittest.skipUnless(version_info >= (3, 4),
                         "Test not supported for python < 3.4")
    def test_hide_sensitive_in_logger(self):
        """Test that logger hides passwords and auth keys (python 3.4+)"""

        ret = {
            'jsonrpc': '2.0',
            'result': '0424bd59b807674191e7d77572075f33',
            'id': 1
        }
        self.urlopen_mock.return_value = MockResponse(json.dumps(ret))

        with self.assertLogs('pyapi_zabbix', level='DEBUG') as cm:

            # Create ZabbixAPI class instance
            zapi = ZabbixAPI(url='https://localhost/zabbix',
                             user='Admin', password='PASSWORD')

            ret = {
                'jsonrpc': '2.0',
                'result':
                [{
                    'itemid': '23298',
                    'hostid': '10084',
                    'name': 'Test Item',
                    'key_': 'system.cpu.switches',
                    'description': '',
                }],
                'id': 1,
            }
            self.urlopen_mock.return_value = MockResponse(json.dumps(ret))
            zapi.get_id('item', item='Test Item')

        log_string = "".join(cm.output)

        self.assertNotIn('PASSWORD', log_string)
        self.assertNotIn('0424bd59b807674191e7d77572075f33', log_string)

        # count number or passwords/token replacements
        # (including 'DEBUG:pyapi_zabbix.api:ZabbixAPI.login(Admin,********)')
        self.assertEqual(log_string.count(HideSensitiveService.HIDEMASK), 4)

    def test_hide_sensitive_in_exception(self):
        """Test that exception raised hides passwords and auth keys"""

        with self.assertRaises(ZabbixAPIException) as cm:
            res = {
                'code': -32602,
                'message': 'Invalid params',
                'data': 'Incorrect API "host2".',
                'json': """
                {'jsonrpc': '2.0',
                 'method': 'host2.get',
                 'params': {'monitored_hosts': 1, 'output': 'extend'},
                 'id': '1',
                 'auth': '0424bd59b807674191e7d77572075f33'}
                 """
            }
            raise ZabbixAPIException(res)

        self.assertNotIn("0424bd59b807674191e7d77572075f33", cm.exception.json)
        self.assertEqual(
            cm.exception.json.count(HideSensitiveService.HIDEMASK),
            1)

    def tearDown(self):
        self.patcher.stop()
