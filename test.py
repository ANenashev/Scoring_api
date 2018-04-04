import unittest
import api
from store import Store
import hashlib
import datetime


def cases(test_cases):
    def test_decorator(fn):
        def test_decorated(self, *args):
            for case in test_cases:
                fn(self, case)
        return test_decorated
    return test_decorator


class TestFields(unittest.TestCase):

    @cases([2, 37.5, ['val1', 'val2']])
    def test_CharField(self, value):
        field = api.CharField()
        self.assertRaises(ValueError, field.validate, value)

    @cases([2, 37.5, ['val1', 'val2'], 'char'])
    def test_ArgumentsField(self, value):
        field = api.ArgumentsField()
        self.assertRaises(ValueError, field.validate, value)

    @cases(['string', 42, 3.5, ['a', 4]])
    def test_EmailField(self, value):
        field = api.EmailField()
        self.assertRaises(ValueError, field.validate, value)

    @cases(['string', 42, 3.5, ['a', 4], '89198802222', '7XXXXXXXXXX'])
    def test_PhoneField(self, value):
        field = api.PhoneField()
        self.assertRaises(ValueError, field.validate, value)

    @cases(['2/19/1991', '1.08.04', '12 June 2012'])
    def test_DateField(self, value):
        field = api.DateField()
        self.assertRaises(ValueError, field.validate, value)

    @cases(['2/19/1991', '1.08.04', '01.07.1920'])
    def test_BirthDayField(self, value):
        field = api.BirthDayField()
        self.assertRaises(ValueError, field.validate, value)

    @cases(['0', '1', '2', 3, 1.1])
    def test_GenderField(self, value):
        field = api.GenderField()
        self.assertRaises(ValueError, field.validate, value)

    @cases([[2.2, 3, 2324, 8000], 2312, 'client1'])
    def test_ClientIDsField(self, value):
        field = api.ClientIDsField()
        self.assertRaises(ValueError, field.validate, value)


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = Store()

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def generate_token(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            key = datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT
            request["token"] = hashlib.sha512(key.encode('utf-8')).hexdigest()
        else:
            key = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(key.encode('utf-8')).hexdigest()

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}}
        ])
    def test_bad_auth(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ])
    def test_invalid_method_request(self, request):
        self.generate_token(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)


if __name__ == "__main__":
    unittest.main()
