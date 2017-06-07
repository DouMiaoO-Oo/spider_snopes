# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pickle
import urllib
import urllib.request
import urllib.error
import bs4
import time

from scraping_snopes import date_transfer
from scraping_snopes import snopes_url
from scraping_snopes import snopes_facts_url
from scraping_snopes import get_response
from scraping_snopes import get_links
from scraping_snopes import scrapping_content
from scraping_snopes import insert2database
from scraping_snopes import reload_progress
from scraping_snopes import Article
from scraping_snopes import filename_sanitize
from scraping_snopes import process_str
from scraping_snopes import field_list

__author__ = '刘宇威'
__date__ = 2017 / 5 / 12


#  将 obj 序列化存入本地文件
def save_obj(obj, name):
    with open('obj/' + name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name ):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)


class Tester():
    """
    测试的类
    """
    def test_get_links(self, url=snopes_url):
        my_bsobj = get_response(url, snopes_facts_url)
        rumor_urls, next_url = get_links(my_bsobj)
        for rumor_url in rumor_urls:
            print(rumor_url)
        print(next_url)

    def test_date_transfer(self):
        print(date_transfer('May 8th, 2017'))

    def test_scrapping_content(self):
        # url = 'http://www.snopes.com/six-flags-flooding-photo/'  # with origin
        # url = 'http://www.snopes.com/kendra-shanice-reid-video/'  # only 1 date
        # url = 'http://www.snopes.com/2017/05/02/letter-prison-laborer/'  # without origin
        # url = 'http://www.snopes.com/2016/01/11/refugees-new-years-eve/'  # without origin
        # url = 'http://www.snopes.com/run-over-trump-protesters/'  # contain: what's true & what's false
        # url = 'http://www.snopes.com/tornado-carries-mobile-home/'  # next siblings

        ''' 第二种页面板式 '''
        # url = 'http://www.snopes.com/politics/satire/selfies.asp'
        # url = 'http://www.snopes.com/back-to-the-future-predictions/'  # without description  # bug 丢了rating
        # url = 'http://www.snopes.com/refugee-nidal-hasan/'  # without description

        ''' 第三种板式 '''
        # url = 'http://www.snopes.com/civil-war-museum-closed/'  # content 之类的内容被额外一层 div 包裹住了  # bug 丢了rating

        ''' 存在 bug 的 '''
        # url = 'http://www.snopes.com/steve-jobs-father/'
        # url = 'http://www.snopes.com/nurse-standing-elderly-man/'  # claim 抓到contnet中了, claim不在<p>标签中，所以出错了
        # url = 'http://www.snopes.com/fright-night-bite/'  # <div style='text-align: justify'> 该标签下只有日期

        # url = 'http://www.snopes.com/hot-ticket/'  # <div style='text-align: justify'> 该标签下只有日期
        url = 'http://www.snopes.com/bernie-sanders-cnn-poll/'

        my_bsObj = get_response(url, snopes_facts_url)

        span = my_bsObj.find('span', text='Origins:')
        print(span)
        p = span.find_parent('p')
        print(p)
        for sibling in p.next_siblings:
            print(sibling)
        os.system('pause')

        res = scrapping_content(my_bsObj)

        # save_obj(dict(zip(field_list,res)), filename_sanitize(url))

        for i in range(len(res)):
            field = field_list[i]
            item = res[i]
            print("%s: %s" % (field, item))

        # res = load_obj(filename_sanitize(url))
        # for i in range(len(res)):
        #     field = field_list[i]
        #     item = res[field]
        #     print("%s: %s" % (field, item))

    def test_reload_progress(self):
        """
        TBD
        :return:
        """
        cur_referer, article_url_list, homepage_url  = reload_progress()
        print("homepage is: %s" % cur_referer)
        print("next hompage is %s:" % homepage_url)
        for article_url in article_url_list:
            print(article_url)

    def test_insert2database(self):
        # content_url = 'http://www.snopes.com/georgia-driver-abandoned-dog/'
        content_url = 'http://www.snopes.com/civil-war-museum-closed/'
        content_url = 'http://www.snopes.com/covfefe-arabic-antediluvian/'
        bsObj = get_response(content_url, 'http://www.snopes.com/category/facts/')
        title, description, claim, published_date, updated_date, rating, content, sources, tag_list, category, repost_cnt = scrapping_content(
            bsObj)
        insert2database([Article(content_url, title, description, claim, published_date, updated_date,
                                 rating, content, sources, tag_list, category, repost_cnt)])


        # article = Article('baidu.com', 'aTitle', 'a description', 'a claim', '2007-13-09', '2008-10-10',
        #                    'True', 'a content', 'a sources', 'a|b|c', 'a category', '10')
        # article = Article('http://www.snopes.com/refugee-nidal-hasan/', 'American Frag', 'Fort Hood shooter Nidal Hasan was born in Virginia, and was neither "vetted" nor ever a refugee.', 'Fort Hood shooter Nidal Hasan was a “vetted refugee.”',
        #                   '2015-11-20', '', '',
        #                   'A refugee crisis out of Syria throughout 2015 caused divisive discussions on the issue of asylum in Western countries; a 13 November 2015 series of terror attacks in Paris (among other effects) caused widespread fear and suspicion of refugees both in Europe and the United States.On 18 November 2015, the Facebook page of Glenn Beck published the above-reproduced image meme featuring Fort Hood shooter Nidal Hasan. While that post didn’t specifically describe Hasan as a refugee, it implicitly stated he was “vetted” prior to his entry to the United States.Subsequent social media posts claimed Hasan (often compared to the Tsarnaev brothers) was once a refugee, admitted to the United States after a rigorous screening process. Simply put, that wasn’t even close to any version of the truth. Hasan was born and raised in Arlington, Virginia, and was thus a United States citizen by birth:Born and reared in Virginia, the son of immigrant parents from a small Palestinian town near Jerusalem, he joined the Army right out of high school, against his parents’ wishes. The Army, in turn, put him through college and then medical school, where he trained to be a psychiatrist.It appeared (as with rumors about the Tsarnaevs) that many folks conflated “refugee” (an individual forced to leave their homeland by circumstance) or “asylum seeker” (a refugee seeking a safe destination) with “Muslim” or “child of immigrants.” As a natural born American citizen, Hasan was neither a refugee nor subject to vetting of any description. Consequently, the entire rumor is based on a false premise.',
        #                   '', 'fort hood shooter|nidal hasan|refugee|syrian refugees', 'Politics', '3148')
        # insert2database([article])

    def test_proxy(self):
        url = 'https://www.google.com/'
        proxy_config_list = [
            {'http': 'http://127.0.0.1:1080/'},
            # {'http': 'http://127.0.0.1:60404/'},     # lantern
            # {'http': 'http://127.0.0.1:8085/'}       # xx-net
        ]
        for proxy_config in proxy_config_list:
            proxy_support = urllib.request.ProxyHandler(proxy_config)
            opener = urllib.request.build_opener(proxy_support)
            response = opener.open(url)
            print(response.code)


def revise():
    """ 第一遍抓取完成之后，重新抓取空值 """
    def get_content():
        """
        利用 find('span', text = 'Oring:') 拿到正文内容
        :return:
        """
        def contain_class(tag_class_list):
            """
            判断结尾的 class
            :param tag_class_list:
            :return:
            """
            if tag_class_list is None:
                return False
            # class use to indicate the ender of the content
            class_list = ['snope-content-1-after', 'proper-ad-unit', 'ad-unit-articleFooter']
            for item in class_list:
                if item in tag_class_list:
                    return True
            return False

        content = ''
        article_text_div = bsObj.find('div', {'class': 'article-text'})
        sibling_list = []
        try:  # 强制要求没有 itemprop 属性， 就可以得到 origin 标签
            origin_tag = article_text_div.find('span', text='Origins:')
            if origin_tag is None:
                origin_tag = article_text_div.find('b', text='Origins:')
            origin_tag = origin_tag.find_parent('p')
            sibling_list = origin_tag.next_siblings
            content += origin_tag.get_text().strip().strip('Origins:').strip()
        except AttributeError:
            print('这就失败了')
            return ""
        finally:
            for sibling in sibling_list:
                if isinstance(sibling, bs4.element.Tag):
                    # print('sibling is %s' % sibling.get_text())
                    # print('sibling.name is %s' % sibling.name)

                    # 说明 origin 后的正文内容已经结束，变成了广告之类的内容
                    if (sibling.name == 'div' and contain_class(sibling.get('class'))) \
                            or (sibling.name == 'footer' and sibling['class'] == 'article-footer'):
                        # print("找到广告了")
                        break
                    # 这里是第二种板式下正文部分最后跟着的 Last updated:, 正文的内容已经结束了
                    if sibling.get_text().strip().rstrip().startswith("Last updated:"):
                        break

                    # 从 origin 之后开始抓取正文内容
                    # print('找到 start_with_origin 了')
                    content += sibling.get_text().strip()

            return process_str(content)

    url_list = []
    with open('page need to revise.txt', 'r', encoding='utf8') as file:
        url_list = file.readlines()
    cur_referer = snopes_url
    for content_url in [url.strip().rstrip() for url in  url_list]:
        print("start process %s" % content_url)  # report the progress
        bsObj = get_response(content_url, cur_referer)
        if bsObj is None:
            for i in range(10):  # 重连 10 次
                time.sleep(2 * (i + 1))
                bsObj = get_response(content_url, cur_referer)
                if bsObj is not None:
                    break
        if bsObj is None:
            print("访问失败")
            return
            #  重连失败
        title, description, claim, published_date, updated_date, rating, content, sources, tag_list, category, repost_cnt = scrapping_content(
            bsObj)
        content = get_content()
        print(content)


        # 为了方便 debug，采用一次一条插入数据库published_date, updated_date
        insert2database([Article(content_url, title, description, claim, published_date, updated_date,
                                 rating, content, sources, tag_list, category, repost_cnt)])
        # 将一个 list 插入数据库
        # article_list.append(Article(content_url,title,description,claim,date,rating,content, sources))
        time.sleep(2)  # sleep 2 seconds

if __name__ == '__main__':
    """ 测试部分 """
    test = Tester()
    # test.test_get_links(url='http://www.snopes.com/category/facts/page/63/')
    # test.test_date_transfer()
    # test.test_scrapping_content()
    # test_f()
    test.test_insert2database()
    # test.test_reload_progress()
    # test.test_proxy()

    """ 修正 """
    # revise()