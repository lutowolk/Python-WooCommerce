# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
import collections
import requests
import hashlib
import urllib
import time
import json
import hmac
import php


class WcApiClient(object):
    consumer_key = ''

    consumer_secret = ''

    store_url = None

    api_endpoint = 'wc-api/v2/'

    hash_algorithm = 'sha1'

    def __init__(self):
        self.store_url = getattr(settings, 'WC_STORE_URL', '')
        self.consumer_key = getattr(settings, 'WC_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'WC_CONSUMER_SECRET', '')
        self._api_url = self.get_api_url()

    def get_api_url(self):
        return '{store_url}/{api_endpoint}'.format(
            store_url=self.store_url.rstrip('/'),
            api_endpoint=self.api_endpoint
        )

    def make_api_call(self, endpoint, params=None, method='GET'):
        """
        Do request to external api

        :param endpoint: basestring
        :param params: dict
        :param method: basestring
        :return: dict
        """
        method = method.lower()

        support_methods = ['delete', 'post', 'put', 'get']

        if method not in support_methods:
            raise Exception("Error. Parameter `method` support only {support_methods}. {method} not supported".format(
                support_methods=', '.join((m.upper() for m in support_methods)),
                method=method.upper()
            ))

        params = params or {}

        params['oauth_consumer_key'] = self.consumer_key
        params['oauth_timestamp'] = int(time.mktime(time.gmtime())) + 9 * 3600  # timezone GMT+9
        params['oauth_nonce'] = int(time.time())
        params['oauth_signature_method'] = 'HMAC-{ALGORITHM}'.format(ALGORITHM=self.hash_algorithm.upper())
        params['oauth_signature'] = self.generate_oauth_signature(params, method.upper(), endpoint)

        query_string = '?{queries}'.format(queries=php.http_build_query(params).rstrip('&')) \
            if params else ''

        request_url = '{api_url}{endpoint}{query_string}'.format(
            api_url=self._api_url, endpoint=endpoint, query_string=query_string)

        headers = {
            'Content-Type': 'application/json'
        }

        make_request = getattr(requests, method)
        response = make_request(request_url, data=json.dumps(params), headers=headers)

        return response.json()

    def generate_oauth_signature(self, params, method, endpoint):
        """
        Generate signature in accordance with the check_oauth_signature
        https://github.com/woothemes/woocommerce/blob/master/includes/api/class-wc-api-authentication.php#L204
        """
        base_request_uri = urllib.quote('{api_url}{endpoint}'.format(
            api_url=self._api_url,
            endpoint=endpoint),
            ''  # quote slash
        )

        # normalize parameter key/values and sort them
        params = self.normalize_parameters(params)
        params = collections.OrderedDict(sorted(params.items()))

        # form query string
        query_params = ['{param_key}%3D{param_value}'.format(param_key=key, param_value=value)
                        for key, value in params.items()]

        # join with ampersand
        query_string = '%26'.join(query_params)

        # form string to sign (first key)
        string_to_sign = '{http_method}&{base_request_uri}&{query_string}'.format(
            http_method=method, base_request_uri=base_request_uri, query_string=query_string
        )

        hash_signature = hmac.new(
            str(self.consumer_secret),
            str(string_to_sign),
            getattr(hashlib, self.hash_algorithm)).digest()

        return hash_signature.encode('base64').replace('\n', '')

    @staticmethod
    def normalize_parameters(params):
        """
        Python analog for function
        https://github.com/woothemes/woocommerce/blob/master/includes/api/class-wc-api-authentication.php#L274
        """
        params = params or {}
        normalized_parameters = {}

        def get_value_like_as_php(val):
            """
            Prepare value for urllib.quote

            If value not basestring instance,
            return value in accordance with the next rules

            :return: basestring
            """
            if isinstance(val, basestring):
                return val
            elif isinstance(val, bool):
                return '1' if val else ''
            elif isinstance(val, int):
                return str(val)
            elif isinstance(val, float):
                return str(int(val)) if val % 1 == 0 else str(val)
            else:
                return ''

        for key, value in params.items():
            value = get_value_like_as_php(value)

            # percent symbols (%) must be double-encoded
            key = urllib.quote(urllib.unquote(str(key))).replace('%', '%25')
            value = urllib.quote(urllib.unquote(str(value))).replace('%', '%25')

            normalized_parameters[key] = value

        return normalized_parameters

    def create_order(self, data):
        """Shortcut method for create order
        :param data: dict
        :return: dict
        """
        data = data or {}
        return self.make_api_call('orders', data, 'POST')