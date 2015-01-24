# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase
from libs.wc_client.client import WcApiClient
import httpretty


SETTINGS = {
    'WC_STORE_URL': 'http://shop.ocsial.com/test/',
    'WC_CONSUMER_KEY': 'ck_cd3bfeee1c97fff5bd64175c9d36ff24',
    'WC_CONSUMER_SECRET': 'cs_6e0775513449b4ee1eba237dedb2c0a1',
}


class HttPretty(object):
    wc = None

    def register_url(self, method, endpoint, body):
        """Helper method for registering uri
        """
        if not self.wc:
            raise Exception("Set self.wc variable, "
                            "self.wc must be WcApiClient instance.")

        httpretty.register_uri(
            getattr(httpretty, method),
            '{base}{path}'.format(base=self.wc._api_url, path=endpoint),
            body=body
        )


class MakeApiCallTestCase(TestCase, HttPretty):
    def setUp(self):
        with self.settings(**SETTINGS):
            self.wc = WcApiClient()

    @httpretty.activate
    def test_get(self):
        url = 'coupons/count'
        method = 'GET'

        self.register_url(method, url, body='{"count": 10}')
        response = self.wc.make_api_call(endpoint=url, method=method, params={})
        self.assertDictEqual(response, {'count': 10})

    @httpretty.activate
    def test_post(self):
        url = 'coupons'
        method = 'POST'

        self.register_url(method, url, body='{"coupon": {"name": "test"}}')
        response = self.wc.make_api_call(endpoint=url, method=method, params={})
        self.assertDictEqual(response, {'coupon': {'name': 'test'}})

    @httpretty.activate
    def test_delete(self):
        url = 'coupons/1'
        method = 'DELETE'

        self.register_url(method, url, body='{"message": "Deleted coupon"}')
        response = self.wc.make_api_call(endpoint=url, method=method, params={})
        self.assertDictEqual(response, {'message': 'Deleted coupon'})

    @httpretty.activate
    def test_put(self):
        url = 'coupons/1'
        method = 'PUT'
        params = {'coupon': {'name': 'change name'}}

        self.register_url(method, url, body='{"coupon": {"name": "change name"}}')
        response = self.wc.make_api_call(endpoint=url, method=method, params=params)
        self.assertDictEqual(response, {'coupon': {'name': 'change name'}})

    def test_method_not_supported(self):
        url = 'coupons/count'
        method = 'NOT_SUPPORTED'

        with self.assertRaises(Exception):
            self.wc.make_api_call(endpoint=url, method=method, params={})


class GenerateOauthSignatureTestCase(TestCase):
    def setUp(self):
        with self.settings(**SETTINGS):
            self.wc = WcApiClient()

    def test_signature_ok(self):
        params = {
            'oauth_consumer_key': 'consumer_key_hash',
            'oauth_timestamp': 1421919608316,
            'oauth_nonce': 1421919608316,
            'oauth_signature_method': 'HMAC-{ALGORITHM}'.format(
                ALGORITHM=self.wc.hash_algorithm.upper())
        }
        method = 'GET'
        endpoint = '/'

        with self.settings(**SETTINGS):
            self.assertEqual('cPLY8DG9YG8uPe0M08yqvw8VL+E=',
                             self.wc.generate_oauth_signature(params, method, endpoint))


class NormalizeParametersTestCase(TestCase):
    def setUp(self):
        self.wc = WcApiClient()

    def test_empty_params(self):
        self.assertDictEqual(
            {},
            self.wc.normalize_parameters({})
        )

    def test_simple_params(self):
        params_for_testing = {
            'filter[period]': 'week'
        }

        result_params = {
            'filter%255Bperiod%255D': 'week'
        }

        self.assertDictEqual(
            result_params,
            self.wc.normalize_parameters(params_for_testing)
        )

    def test_difficult_params(self):
        params_for_testing = {
            'foo_dict': {
                'bar_str': 1,
            },
            'foo_list': [1, 2],
            'foo_str': 'simple_str',
            'foo_int': 1,
            'foo_float': 1.5,
            'foo_without_floating_part': 1.0,
            'foo_bool_true': True,
            'foo_bool_false': False,
        }

        result_params = {
            'foo_dict': '',
            'foo_list': '',
            'foo_str': 'simple_str',
            'foo_int': '1',
            'foo_float': '1.5',
            'foo_without_floating_part': '1',
            'foo_bool_true': '1',
            'foo_bool_false': '',
        }

        self.assertDictEqual(
            result_params,
            self.wc.normalize_parameters(params_for_testing)
        )


class CreateOrderTestCase(TestCase, HttPretty):
    def setUp(self):
        with self.settings(**SETTINGS):
            self.wc = WcApiClient()

    @httpretty.activate
    def test_ok(self):
        self.register_url('POST', 'orders', body='{"order": {"status": "ok"}}')
        response = self.wc.create_order(data={"order": {"status": "ok"}})

        self.assertDictEqual(response, {"order": {"status": "ok"}})