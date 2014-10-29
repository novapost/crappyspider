import json
import urlparse

from scrapy.spider import Spider
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy import log


class CrapySpider(Spider):
    name = 'crapy_spider'

    def __init__(self, rule=None):
        super(CrapySpider, self).__init__()

        if rule:
            with open(rule) as fil:
                data = json.load(fil)

        self.config = data
        self.start_urls = data['start_urls']
        self.allowed_domains = data['allowed_domains']

    def parse(self, response):
        return [FormRequest.from_response(
            response, formdata={
                'email': self.config['email'],
                'password': self.config['password']},
            callback=self.after_login)]

    def after_login(self, response):
        # check login succeed before going on
        sel = Selector(response)
        if sel.css(self.config['login_error_selector']):
            log.msg('Login failed', level=log.ERROR)
            return

        # continue scraping with authenticated session
        log.msg('Login success', level=log.INFO)
        url_prefix = urlparse.urlparse(response.url)

        for url in sel.css('a::attr(href)').extract():
            #parsed_url = urlparse.urlparse(url)

            try:
                yield Request(url, callback=self.parse_page)
            except ValueError:
                url_final = '{scheme}://{netloc}{path}'.format(
                    scheme=url_prefix.scheme, netloc=url_prefix.netloc,
                    path=url)
                yield Request(url_final, callback=self.parse_page)

    def parse_page(self, response):
        log.msg('Status code page {status_code} for {url}'.format(
            status_code=response.status, url=response.url), level=log.INFO)
        sel = Selector(response)
        url_prefix = urlparse.urlparse(response.url)

        for url in sel.css('a::attr(href)').extract():
            try:
                yield Request(url, callback=self.parse_page)
            except ValueError:
                url_final = '{scheme}://{netloc}{path}'.format(
                    scheme=url_prefix.scheme, netloc=url_prefix.netloc,
                    path=url)
                yield Request(url_final, callback=self.parse_page)
