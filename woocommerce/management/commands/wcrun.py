# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from optparse import make_option
from django.core.management.base import BaseCommand
from libs.wc_client.client import WcApiClient
import json


class Command(BaseCommand):
    help = 'Run api request to woocommerce'

    option_list = BaseCommand.option_list + (
        make_option('-e',
                    '--endpoint',
                    dest='endpoint',
                    default='',
                    help='Endpoint, example: orders/count'),
        make_option('-p',
                    '--params',
                    dest='params',
                    default=None,
                    help='Params in json, example: "{foo: \"bar\"}"'),
        make_option('-m',
                    '--method',
                    dest='method',
                    default='GET',
                    help='Http method, by default GET'),
    )

    def handle(self, *args, **options):

        wc = WcApiClient()

        response = wc.make_api_call(
            options.get('endpoint'),
            params=json.loads(options.get('params') or '{}'),
            method=options.get('method') or 'GET'
        )

        print json.dumps(response)