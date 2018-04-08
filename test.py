import unittest
import api
from store import Store
import hashlib
import datetime
from unittest.mock import patch
from six import string_types


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

    @cases([
        {},
        {"phone": "79198802222"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79198802222", "email": "stupnikovotus.ru"},
        {"phone": "79198802222", "email": "stupnikov@otus.ru", "gender": -1},
        {"phone": "79198802222", "email": "stupnikov@otus.ru", "gender": "1"},
        {"phone": "79198802222", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.07.1920"},
        {"phone": "79198802222", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "2/19/1991"},
        {"phone": "79198802222", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.08.2004",
         "first_name": 1},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.08.2004",
         "first_name": "Стансилав", "last_name": 2},
        {"phone": "79175002040", "birthday": "1.08.2004", "first_name": "Стансилав"},
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ])
    def test_invalid_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.generate_token(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code, arguments)
        self.assertTrue(len(response))

    @patch('store.Store.cache_get', return_value=None)
    @patch('store.Store.cache_set')
    @cases([
        {"phone": "79198802222", "email": "stupnikov@otus.ru"},
        {"phone": 79198802222, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.08.2004", "first_name": "Стансилав", "last_name": "Ступников"},
        {"gender": 0, "birthday": "01.08.2004"},
        {"gender": 2, "birthday": "01.08.2004"},
        {"first_name": "Стансилав", "last_name": "Ступников"},
        {"phone": "79198802222", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.08.2004",
         "first_name": "Стансилав", "last_name": "Ступников"},
    ])
    def test_valid_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.generate_token(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    def test_valid_score_admin_request(self):
        arguments = {"phone": "79198802222", "email": "stupnikov@otus.ru"}
        request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
        self.generate_token(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        score = response.get("score")
        self.assertEqual(score, 42)

    @cases([
        {},
        {"date": "08.04.2018"},
        {"client_ids": [], "date": "08.04.2018"},
        {"client_ids": {1: 2}, "date": "08.04.2018"},
        {"client_ids": ["1", "2"], "date": "08.04.2018"},
        {"client_ids": [1, 2], "date": "4/8/2018"},
    ])
    def test_invalid_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.generate_token(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertTrue(len(response))

    @patch('store.Store.get', return_value=b"['books','hi-tech']")
    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "08.04.2018"},
        {"client_ids": [0]},
    ])
    def test_valid_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.generate_token(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, string_types) for i in v)
                            for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))


@unittest.skip("Slow test")
class TestWithDatabaseConnection(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = Store()

        self.store.set("i:0", ["books", "hi-tech"])
        self.store.set("i:1", ["pets", "tv"])
        self.store.set("i:2", ["travel", "music"])
        self.store.set("i:3", ["cinema", "geek"])

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def generate_token(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            key = datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT
            request["token"] = hashlib.sha512(key.encode('utf-8')).hexdigest()
        else:
            key = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(key.encode('utf-8')).hexdigest()

    @cases([
        {"phone": "79198802222", "email": "stupnikov@otus.ru"},
        {"phone": 79198802222, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.08.2004", "first_name": "Стансилав", "last_name": "Ступников"},
        {"gender": 0, "birthday": "01.08.2004"},
        {"gender": 2, "birthday": "01.08.2004"},
        {"first_name": "Стансилав", "last_name": "Ступников"},
        {"phone": "79198802222", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.08.2004",
         "first_name": "Стансилав", "last_name": "Ступников"},
    ])
    def test_valid_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.generate_token(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "08.04.2018"},
        {"client_ids": [0]},
    ])
    def test_valid_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.generate_token(request)
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, string_types) for i in v)
                            for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))


if __name__ == "__main__":
    unittest.main()
