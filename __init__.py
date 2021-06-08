#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:fdm=marker:ai
from __future__ import absolute_import, division, print_function, unicode_literals

__license__ = 'GPL v3'
__copyright__ = '2021, YoungJae Hur <yjhur82 at gmail.com> based on google search by Kovid Goyal <kovid at kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import time, re, os
from threading import Thread
from lxml.html import fromstring

try:
    from queue import Empty, Queue
except ImportError:
    from Queue import Empty, Queue

from calibre import as_unicode, random_user_agent
from calibre.ebooks.metadata import check_isbn
from calibre.ebooks.metadata.sources.base import Source


class Worker(Thread):  # {{{

    def __init__(self, basic_data, relevance, result_queue, br, timeout, log, plugin):
        Thread.__init__(self)
        self.daemon = True
        self.br, self.log, self.timeout = br, log, timeout
        self.result_queue, self.plugin, self.aladin = result_queue, plugin, basic_data['aladin']
        self.relevance = relevance

    def run(self):
        url = "https://www.aladin.co.kr/shop/wproduct.aspx?ItemId={}".format(self.aladin)
        try:
            mi = self.parseItemPage(url)
            mi.source_relevance = self.relevance
            self.plugin.clean_downloaded_metadata(mi)
            self.result_queue.put(mi)
        except:
            self.log.exception('Failed to parse details for aladin: {}'.format(self.aladin))

    def to_str(self, bytes_or_str):
        if isinstance(bytes_or_str, bytes):
            value = bytes_or_str.decode('utf-8')
        else:
            value = bytes_or_str
        return value

    def getComment(self, ref, isbn):
        try:
            from urllib.parse import urlencode
        except ImportError:
            from urllib import urlencode

        comment_list = []

        comment_base_url = "https://www.aladin.co.kr/shop/product/getContents.aspx?"
        aladin_comment_url = comment_base_url + urlencode(dict(ISBN=isbn, name='Introduce'))
        publisher_comment_url = comment_base_url + urlencode(dict(ISBN=isbn, name='PublisherDesc'))
        aladin_comment = self.parseComment(ref, aladin_comment_url)
        publisher_comment = self.parseComment(ref, publisher_comment_url)

        if aladin_comment:
            comment_list.append("책소개")
            comment_list.append(str(aladin_comment).strip())

        if publisher_comment:
            comment_list.append("출판사 책소개")
            publisher_commnet = re.sub(" 접기$", "", str(publisher_comment).strip())
            comment_list.append(publisher_commnet.strip())

        comment = "\n\n".join(comment_list)
        comment = re.sub("\r", "", comment)
        return comment

        # if comment_list:
        #     comment = "\n\n".join(comment_list)
        #     comment = re.sub("\r", "", comment)
        #     return comment
        #
        # else:
        #     return None

    def parseComment(self, ref, url):
        comment = ''
        br = self.br.clone_browser()
        br.addheaders = [
            ('Referer', ref),
        ]
        raw = br.open_novisit(url, timeout=self.timeout).read()
        try:
            html = fromstring(raw.decode('utf-8'))
        except:
            self.log('Comment page empty', url)
            return comment
        for comment_node in html.xpath("//div[contains(@class, 'Ere_prod_mconts_LS') and contains(text(),'책소개')]"):
            full_length = comment_node.xpath("..//div[@id='div_PublisherDesc_All']")
            if full_length:
                comment = full_length[0].text_content()
            else:
                comment = comment_node.xpath("../div[contains(@class, 'Ere_prod_mconts_R')]")[0].text_content()
        return comment

    def parseItemPage(self, url):
        try:
            raw = self.br.open_novisit(url, timeout=self.timeout).read()
            html = fromstring(raw)
            if not html.xpath("//title"):
                if '19세' in raw.decode('utf-8'):
                    self.log.warning('19세 연령제한 페이지입니다.')
                    home = os.path.expanduser('~')
                    desktop = os.path.join(home, 'Desktop')
                    file = os.path.join(desktop, self.aladin+'.html')
                    try:
                        raw = open(file).read()
                    except:
                        self.log.error(file, 'not found')
                    html = fromstring(raw)
                    self.log.debug('loaded saved page')
            else:
                self.log.debug('ItemQuery ', url)
        except:
            self.log.exception('Failed to load item page: %r' % url)
            return

        mi = self.getMetaInstance()
        mi.set_identifier('aladin', self.aladin)

        for authors_node in html.xpath("//a[contains(@class, 'Ere_sub2_title') and contains(@href, 'AuthorSearch')]"):
            if authors_node.text_content():
                mi.authors.append(authors_node.text_content())
        if not mi.authors:
            mi.authors = html.xpath("//meta[@name='author']")[0].attrib['content'].split(',')

        publisher_node = html.xpath("//a[contains(@class, 'Ere_sub2_title') and contains(@href, 'PublisherSearch')]")
        if publisher_node:
            mi.publisher = publisher_node[0].text_content()

        # original_node = html.xpath("//a[contains(@class, 'Ere_sub2_title') and contains(text(),'원제')]")
        # if original_node:
        #     metadic['original'] = re.sub('원제 : ', '', original_node[0].text_content())

        title_node = html.xpath("//meta[@name='title']")
        if title_node:
            p = re.compile(r'''[:,;!@$%^&*(){}.`~"\s\[\]/]《》「」“”''')
            mi.title = re.sub(p, '', str(title_node[0].attrib['content']))
            subtitle_node = html.xpath("//span[contains(@class, 'Ere_sub1_title')]")
            if subtitle_node:
                mi.title = mi.title + ' ' + subtitle_node[0].text_content().strip()

        pubdate_node = html.xpath("//meta[@itemprop='datePublished']")
        if pubdate_node:
            pubdate = pubdate_node[0].attrib['content']
            if pubdate:
                from calibre.utils.date import parse_only_date
                mi.pubdate = parse_only_date(pubdate)

        old_publish = html.xpath("//div[contains(@class, 'Ere_btn_old')]/a")
        if old_publish:
            if re.search('구판', old_publish[0].text_content()):
                mi.title = mi.title + ' (개정판 ' + str(mi.pubdate)[:4] + ')'
            # elif re.search('개정판', old_publish[0].text_content()):
            #     mi.title = mi.title + ' (구판)'
            # itemid_p = re.compile("ItemId=[0-9]*$")
            # if re.search(itemid_p, old_publish[0].attrib['href']):
            #     item_str = re.findall(itemid_p, old_publish[0].attrib['href'])[0]
            #     Worker(dict(aladin=re.sub("ItemId=", "", item_str)), self.relevance, self.result_queue,
            #            self.br, self.timeout, self.log, self.plugin).start()


        cover_url_node = html.xpath("//meta[@property='og:image']")
        if cover_url_node:
            mi.has_cover = self.plugin.cache_identifier_to_cover_url(self.aladin,
                                                                     cover_url_node[0].attrib['content']) is not None

        isbn_node = html.xpath("//meta[@property='books:isbn']")
        if isbn_node:
            self.log.debug('aladin:', self.aladin, ' isbn:', isbn_node[0].attrib['content'], ' try get comment')
            comment = self.getComment(url, isbn_node[0].attrib['content'])
            if comment:
                mi.comments = comment
            else:
                filename = str(cover_url_node[0].attrib['content']).split("/")[-1]
                mi.comments = self.getComment(url, filename.split('_')[0])
            mi.set_identifier('isbn', isbn_node[0].attrib['content'])

        series_node = html.xpath("//a[contains(@class, 'Ere_sub1_title')]")
        if series_node:
            series_title = series_node[0].text_content()
            series_index = re.findall("\s+(\d+)\s*$", series_title)
            if series_index:
                mi.series_index = float(series_index[0].strip())
                mi.series = series_title[:-1 * len(series_index[0])]
            else:
                mi.series_index = 0
                mi.series = series_title

        rating_node = html.xpath("//div[@class='info']//a[contains(@class, 'Ere_str')]")
        if rating_node:
            mi.rating = float(rating_node[0].text_content().strip())/2

        for tag_node in html.xpath("//ul[@id='ulCategory']//a[contains(@href, 'CID')]"):
            if tag_node.text_content() and tag_node.text_content() not in mi.tags:
                mi.tags.append(tag_node.text_content())

        languages_node = html.xpath("//div[@class='conts_info_list1']/li[contains(text(),'언어')]/b")
        if languages_node:
            mi.languages = list(languages_node[0].text_content().strip())

        return mi

    def getMetaInstance(self):
        from calibre.ebooks.metadata.book.base import Metadata
        from calibre.utils.date import UNDEFINED_DATE

        mi = Metadata(title=_('Unknown'))
        mi.authors = []
        mi.pubdate = UNDEFINED_DATE
        mi.tags = []
        mi.languages = ["Korean"]
        return mi


class AladinKr(Source):
    name = 'AladinKr'
    author = 'YoungJae Hur'
    version = (1, 0, 0)
    minimum_calibre_version = (3, 6, 0)
    description = _('알라딘에서 책 정보와 표지 다운로드 - 최용석님의 Aladin.co.kr 플러그인의 aladin.co.kr 호환')

    capabilities = frozenset(['identify', 'cover'])
    touched_fields = frozenset([
        'title', 'authors', 'tags', 'pubdate', 'comments', 'publisher',
        'identifier:isbn', 'identifier:aladin', 'identifier:aladin.co.kr',
        'rating'])
    supports_gzip_transfer_encoding = True
    has_html_comments = False

    @property
    def user_agent(self):
        # Pass in an index to random_user_agent() to test with a particular
        # user agent
        return random_user_agent(allow_ie=False)

    def _get_book_url(self, aladin):
        if aladin:
            return 'https://www.aladin.co.kr/shop/wproduct.aspx?ItemId={}'.format(aladin)

    def get_book_url(self, identifiers):  # {{{
        if identifiers.get('aladin', None):
            aladin = identifiers.get('aladin', None)
            return 'aladin', aladin, self._get_book_url(aladin)
        if identifiers.get('aladin.co.kr', None):
            aladin = identifiers.get('aladin.co.kr', None)
            return 'aladin', aladin, self._get_book_url(aladin)

    # }}}

    def get_cached_cover_url(self, identifiers):  # {{{
        sku = None
        if identifiers.get('aladin', None):
            sku = identifiers.get('aladin', None)
        elif identifiers.get('aladin.co.kr', None):
            sku = identifiers.get('aladin.co.kr', None)
        elif identifiers.get('isbn', None):
            isbn = identifiers.get('isbn', None)
            sku = self.cached_isbn_to_identifier(isbn)
        return self.cached_identifier_to_cover_url(sku)

    # }}}

    def create_query(self, log, title=None, authors=None, identifiers={}):
        try:
            from urllib.parse import urlencode
        except ImportError:
            from urllib import urlencode
        BASE_URL = "https://www.aladin.co.kr/search/wsearchresult.aspx?"
        params = {
            'ViewRowCount': 50,  # 50 results are the maximum
        }
        isbn = check_isbn(identifiers.get('isbn', None))
        if isbn:
            params['KeyISBN'] = isbn
            return BASE_URL + urlencode(params)
        elif title or authors:
            params['SearchWord'] = []
            title_tokens = list(self.get_title_tokens(title))
            log.info(title_tokens)
            if title_tokens:
                params['SearchWord'].extend(title_tokens)
            author_tokens = self.get_author_tokens(authors, only_first_author=True)
            if author_tokens:
                params['SearchWord'].extend(author_tokens)
            params['SearchWord'] = ' '.join(params['SearchWord'])
            return BASE_URL + urlencode(params)
        else:
            return None

    # }}}

    def parselist(self, raw):
        item_list = []
        for item_node in fromstring(raw).xpath("//div[@class='ss_book_list']//li//a[contains(@href, 'ItemId')]"):
            itemid_p = re.compile("ItemId=[0-9]*$")
            # seriesid_p = re.compile("SRID=[0-9]*$")
            if re.search(itemid_p, item_node.attrib['href']):
                item_str = re.findall(itemid_p, item_node.attrib['href'])[0]
                # if re.search(seriesid_p, str(tostring(item))):
                #     seriesid = re.findall(seriesid_p, str(tostring(item)))[0]
                #     items.append(dict(aladin=itemid, series=seriesid))
                # else:
                #     items.append(dict(aladin=itemid))
                if re.sub("ItemId=", "", item_str) not in item_list:
                    item_list.append(re.sub("ItemId=", "", item_str))
        return [dict(aladin=x) for x in item_list]

    def identify(self, log, result_queue, abort, title=None, authors=None,  # {{{
                 identifiers={}, timeout=30):

        br = self.browser
        br.addheaders = [
            ('Referer', 'https://www.aladin.co.kr/'),
            ('X-Requested-With', 'XMLHttpRequest'),
            ('Cache-Control', 'no-cache'),
            ('Pragma', 'no-cache'),
            ('verify_ssl', 'True'),
            ("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                           "Version/14.1 Safari/605.1.15"),
        ]

        if 'aladin' in identifiers:
            items = [dict(aladin=identifiers['aladin'])]
        elif 'aladin.co.kr' in identifiers:
            items = [dict(aladin=identifiers['aladin.co.kr'])]
        else:
            query = self.create_query(log, title=title, authors=authors,
                                      identifiers=identifiers)
            if not query:
                log.error('Insufficient metadata to construct query')
                return
            log('Using query URL:', query)
            try:
                raw = br.open(query, timeout=timeout).read().decode('utf-8')
            except Exception as e:
                log.exception('Failed to make identify query: %r' % query)
                return as_unicode(e)
            items = self.parselist(raw)
            if items is None:
                log.error('Failed to get list of matching items')
                log.debug('Response text:')
                log.debug(raw)
                return

        if (not items and identifiers and title and authors and
                not abort.is_set()):
            return self.identify(log, result_queue, abort, title=title,
                                 authors=authors, timeout=timeout)
        if not items:
            return

        workers = []
        for i, item in enumerate(items):
            workers.append(Worker(item, i, result_queue, br.clone_browser(), timeout, log, self))

        if not workers:
            return

        for w in workers:
            w.start()
            # Don't send all requests at the same time
            time.sleep(0.1)

        while not abort.is_set():
            a_worker_is_alive = False
            for w in workers:
                w.join(0.2)
                if abort.is_set():
                    break
                if w.is_alive():
                    a_worker_is_alive = True
            if not a_worker_is_alive:
                break

    # }}}

    def download_cover(self, log, result_queue, abort,  # {{{
                       title=None, authors=None, identifiers={}, timeout=30, get_best_cover=False):
        cached_url = self.get_cached_cover_url(identifiers)
        if cached_url is None:
            log.info('No cached cover found, running identify')
            rq = Queue()
            self.identify(log, rq, abort, title=title, authors=authors,
                          identifiers=identifiers)
            if abort.is_set():
                return
            results = []
            while True:
                try:
                    results.append(rq.get_nowait())
                except Empty:
                    break
            results.sort(key=self.identify_results_keygen(
                title=title, authors=authors, identifiers=identifiers))
            for mi in results:
                cached_url = self.get_cached_cover_url(mi.identifiers)
                if cached_url is not None:
                    break
        if cached_url is None:
            log.info('No cover found')
            return

        if abort.is_set():
            return
        br = self.browser
        log('Downloading cover from:', cached_url)
        try:
            cdata = br.open_novisit(cached_url, timeout=timeout).read()
            result_queue.put((self, cdata))
        except:
            log.exception('Failed to download cover from:', cached_url)
    # }}}


if __name__ == '__main__':
    from calibre.ebooks.metadata.sources.test import (
        test_identify_plugin, title_test, authors_test, comments_test, pubdate_test, series_test)

    tests = [
        # (  # A book with an ISBN
        #     {'identifiers': {'isbn': '9788939205109'}},
        #     [title_test('체 게바라 평전', exact=True),
        #     authors_test(['장 코르미에','김미선']),
        #     ]
        # ),
        (  # A book with an aladin id
            {'identifiers': {'aladin.co.kr': '215739377'}},
            [title_test('해리 포터', exact=False)]
        ),
        # (  # A book with an aladin id
        #     {'identifiers': {'aladin': '208556'}},
        #     [title_test('Harry', exact=False)]
        # ),
    ]
    start, stop = 0, len(tests)

    tests = tests[start:stop]
    test_identify_plugin(AladinKr.name, tests)
