# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import string
import datetime
import time
import os
import urllib
import urllib.request
import urllib.error
import random
import bs4
import logging
import pymysql

__author__ = '刘宇威'
__date__ = 2017 / 5 / 12

my_headers = [
    # 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36',
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36",
    # up is chrome
    '''Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.22 Safari/537.36 SE 2.X MetaSr 1.0''',
    # up is sougou
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36 115Browser/7.2.4''',
    # up is 115
    '''Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393''',
    # up is edge
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko"
    # up is IE

    # http://www.cnblogs.com/sink_cup/archive/2011/03/15/http_user_agent.html # 必要时的补充

]  # 模仿phone效果一样

snopes_url = "http://www.snopes.com/"
snopes_facts_url = 'http://www.snopes.com/category/facts/'
field_list = ['title', 'description', 'claim', 'published_date', 'updated_date',
                 'rating', 'content', 'sources', 'tag_list', 'category', 'repost_cnt']
random.seed(datetime.datetime.now())
# @deprecated 用来保存所有采集过页面的 url
# unique_url_list = set()
# 对于news分类来说 不用这个转换也可以 url自带日期转换
month_dict = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12'
}


def filename_sanitize(filename):
    """
    把字符串变为合法 文件名
    :param filename:
    :return:
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return ''.join(c for c in filename if c in valid_chars)


def date_transfer(date):
    """
    :param date: e.g. May 8th, 2017
    :return: YYYY-MM-DD
    """
    index = date.find(':')
    if index != -1:
        date = date[(index+1):]
    m, d, y = date.strip().replace(',', '').rstrip().split()
    d = d.rstrip('st').rstrip('nd').rstrip('rd').rstrip('th')  # remove Ordinal Numbers
    if len(d) == 1:
        d = '0' + d
    return "%s-%s-%s" % (y, month_dict[m], d)


def process_str(s):
    """
    \xa0 : &nbsp;
    :param s: 
    :return: 
    """
    return s.replace('\xa0', ' ')


def get_response(url, referer):
    """  爬取被墙网站需要使用代理
    @获取页面
    :return: 成功时返回页面内容，否则返回 None
    """
    random_header = random.choice(my_headers)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", random_header)
    req.add_header('Host', 'www.snopes.com')  # url 参数可能需要更换
    req.add_header("Referer", referer)          # 从哪里跳转来的
    flag = "Global"
    # flag = "non Global"
    try:
        code = 404  # 状态码
        if flag == "Global":
            # 使用全局代理
            response = urllib.request.urlopen(req)
        else:
            # 使用多个代理的情况，随机从列表 list 中选取一个
            proxy_config_list = [
                                  {'http': 'http://127.0.0.1:60404/'},  # lantern
                                  {'http': 'http://127.0.0.1:1080/'},
                                  # {'http': 'http://127.0.0.1:8085/'}       # xx-net
                                  ]
            proxy_config = random.choice(proxy_config_list)
            proxy_support = urllib.request.ProxyHandler(proxy_config)
            logger = logging.getLogger('proxy')
            logger.info("   current proxy is: %s" % proxy_config)
            print("\tcurrent proxy is: %s" % proxy_config)
            opener = urllib.request.build_opener(proxy_support)
            response = opener.open(req)
        code = response.code
        bsObj = bs4.BeautifulSoup(response, "lxml")
        response.close()
        return bsObj

    except urllib.error.HTTPError as e:
        """
         # 得到访问返回的状态码 200 才正常  301是永久重定向、302临时重定向(3开头的普遍都是..)  404不存在
         # 403禁止访问 : 浏览器可以访问但urllib不行：反扒
         # 500 服务器忙 服务器无响应：服务器端的问题
      """
        print("The server couln\'t fulfill the request")
    except urllib.error.URLError as e:
        print("We failed to reach a server.")
        print("Reason" + str(e.reason))

    return None


def get_links(bsObj):
    """
    处理导航页的内容
    得到页面中链接到 article 内容的 url
    得到下一页的 url
    :param bsObj: beautiful soup4 Obj，其内容是网页的response
    :return: [ariticle_url_list, next_homepage_url]
    """
    ariticle_url_list = []
    article_list = bsObj.findAll("article")  # 拿到<article> </article>
    for article in article_list:
        cur_url = article.a.attrs['href']
        ariticle_url_list.append(cur_url)
    article_list_pagination__div = bsObj.find("div", {"class": "article-list-pagination"})
    next_homepage_url = list(article_list_pagination__div.find_all('a'))[-1].attrs["href"]
    return [ariticle_url_list, next_homepage_url]


def scrapping_content(bsObj):
    """
    处理内容页的内容，提取需要存入数据库(MySQL) 的信息，并保存一份
    返回结果为失败(保存本地log) or 成功
    :param bsObj: beautiful soup4 Obj，其内容是网页的response
    :return:
    """

    def get_description():
        description = ""
        h2_tag = bsObj.find("h2", {"class": "article-description"})
        if h2_tag is not None:
            description = h2_tag.get_text()
        return description

    def get_claim():
        claim = ""
        ''' 第一种板式下的采集策略 '''
        p_tag = bsObj.find("p", {"itemprop": "claimReviewed"})
        if p_tag is not None:
            claim = p_tag.get_text().strip().rstrip()
            return process_str(claim)

        ''' 第二种板式下的采集策略 '''
        nonlocal version
        div_tag = bsObj.find('div', {'class': 'entry-content article-text legacy'})
        if div_tag is not None:  # 理论上都有这个 div 标签的
            p_tag_list = div_tag.find_all('p')
            p_index = 0
            for p_tag in p_tag_list:
                ''' 只找前10个p '''
                p_content = p_tag.get_text().strip().rstrip()
                if p_content.startswith("Claim:"):
                    claim = p_content.strip('Claim:').strip()
                    version = "2.0"  # 页面的板式是第二种板式
                    return process_str(claim)
                p_index += 1
                if p_index == 10:
                    break
        return claim

    def get_date():
        try:
            date_wrapper_span = list(bsObj.find_all("span", {"class": "date-wrapper"}))
            published_date = date_transfer(date_wrapper_span[0].get_text())
            if len(date_wrapper_span) == 1:
                updated_date = ''
            else:
                updated_date = date_transfer(date_wrapper_span[1].get_text())
            return published_date, updated_date
        except AttributeError :
            return "", ""
        except IndexError:
            return "", ""

    def get_rating():
        nonlocal version
        if version == "2.0":
            font_tag = bsObj.find('font', {'class': 'status_color'})
            if font_tag is not None:
                font_tag = font_tag.get_text()
                return font_tag

        try:
            #  bs 识别的属性值会按照空格分隔，所以这个表达式可以把所有的rating抓到
            rating = bsObj.find('div', {'class', 'claim'}).span.get_text()
        except AttributeError:
            rating = ''
            font_tag = bsObj.find('font', {'class': 'status_color'})
            if font_tag is not None:
                font_tag = font_tag.get_text()
                version = "2.0"
        return rating

    def get_content():
        """
        拿到正文内容
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

        nonlocal version
        content = ''
        article_text_div = bsObj.find('div', {'class': 'article-text'})
        sibling_list = []
        try:  # 强制要求没有 itemprop 属性， 就可以得到 origin 标签
            origin_tag = article_text_div.find('h3', {'class': 'section-break', 'itemprop': ''})
            sibling_list = origin_tag.next_siblings
        except AttributeError:
            div = article_text_div.find('div', {'style': 'text-align: justify;'})
            if div is not None:  # 第三种板式，多一层 div
                sibling_list = div.children
            else:
                sibling_list = article_text_div.children  # 文章中没有'Origin'栏目，但不一定是第二、三种板式
                # print('without Origin:')
        finally:
            if version == "2.0":  # 页面的板式是第二种板式
                # print('version 2.0')
                start_with_orgin = False
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
                        if sibling.name == 'p':
                            p_content = sibling.get_text().strip().rstrip()
                            if p_content.startswith("Last updated:"):
                                # print("找到last updates 了")
                                break

                        # 从 origin 之后开始抓取正文内容
                        if start_with_orgin:
                            # print('找到 start_with_origin 了')
                            content += sibling.get_text().strip()
                        elif sibling.name == 'p':
                            # print('sibling is %s' % sibling)
                            p_content = sibling.get_text().strip().rstrip()
                            # print('p_contnet is :%s' % p_content)
                            if p_content.startswith("Origins:"):
                                start_with_orgin = True
                                content += p_content.strip('Origins:').strip()

            else:  # 页面的板式是第一种板式
                for sibling in sibling_list:
                    if isinstance(sibling, bs4.element.Tag):
                        # 说明 origin 后的正文内容已经结束
                        if (sibling.name == 'div' and contain_class(sibling.get('class'))) \
                                or (sibling.name == 'footer' and sibling['class'] == 'article-footer'):
                            break
                        content += sibling.get_text()
            return process_str(content)

    def get_sources():
        sources = ''
        try:
            article_sources_box_div = bsObj.find('div',{'class':'article-sources-box'})
            for p in article_sources_box_div.find_all('p'):
                sources += p.get_text()
        except AttributeError:
            pass
        return process_str(sources)

    def get_tag_list():
        """
        即为 Filed Under 下的多个 tag 标签
        在 <p></p>标签中，class 为 tag-box all-tags
        :return: 用 | 线分隔开
        """
        a_list = bsObj.find("p", {"class": "tag-box"})  # <a /> list
        if a_list is None:
            return ""
        tag_list = []
        for a in a_list.find_all("a"):
            tag_href = a["href"]   # class="show-all-tags nohash" 用来显示更多标签，不是需要的内容
            if tag_href != "#show-all-tags":
                tag_list.append(a.get_text())
        return '|'.join(tag_list)

    def get_category():
        """
        ①文章所属的目录，目录可能不存在
        ②存在目录的情况，我假定格式如下：
            Fact Check > category
        即只有一个子目录 category，全部都在Fact Check 目录之下
        :return: category 或者 ""
        """
        div = bsObj.find("div", {"class":"breadcrumb-nav"})
        a_list = div.find_all("a")
        category = ""
        if len(a_list) > 1:
            category = a_list[-1].get_text()
        return category

    def get_repost_cnt():
        repost_cnt = ""
        try:
            div = bsObj.find("div", {"class":"image-frame-socialShares"})
            span = div.find("span", {"class": "count"})
            repost_cnt = span.find("span", {"class": "num social_total" })["data-total"]
        except AttributeError:
            # os.system("pause")
            pass
        return repost_cnt

    version = "1.0"  # 默认页面的板式是第一种板式

    title = bsObj.find("h1", {"itemprop": "headline"}).get_text()
    description = get_description()
    claim = get_claim()  # 必须在 get_content 之前执行
    # print('global version is %s' % version)
    published_date, updated_date = get_date()
    rating = get_rating()  # true/ false/ UNPROVEN / ...
    content = get_content()
    sources = get_sources()
    tag_list = get_tag_list()  # Donald Trump|Hilary
    category = get_category()
    repost_cnt = get_repost_cnt()
    return title, description, claim, published_date, updated_date, rating, content, sources, tag_list, category, repost_cnt


class Article:
    def __init__(self, url, title, description, claim, published_date, updated_date,
                 rating, content, sources, tag_list, category, repost_cnt):
        self.url = url
        self.title = title
        self.description = description
        self.claim = claim
        self.published_date = published_date
        self.updated_date = updated_date
        self.rating = rating
        self.content = content
        self.sources = sources
        self.tag_list = tag_list
        self.category = category
        self.repost_cnt = repost_cnt

    def print_sc(self):
        for key, val in self.__dict__.items():
            print("%s: %s" % (key, val))


def reload_progress():
    """
    1. reload the url already processed into unique_url_list. 
    2. reload the progress of the Web spider.
    inlcuding the:
        homepage url
        current article url
    3. log 内容写的繁琐是为了以后出错以后更方便排查
    :return: 
    """
    homepage_url = ''
    new_article_url_list = []
    new_article_url = ''
    cur_referer = ''
    with open('log.txt', 'r', encoding='utf8') as file_reader:
        homepage_url = file_reader.readline().rstrip()
        article_url_list = file_reader.readlines()
        for i in range(len(article_url_list)):
            article_url = article_url_list[i]
            if article_url.rstrip() == 'Below is to be scrapping.':
                new_article_url = article_url_list[i+1].rstrip()
                break
    bsObj = get_response(homepage_url,snopes_facts_url)
    if bsObj is None:  # 理论上不会发生
        print('homepage can\'t reach, response is error')
        return None, None, None
    cur_referer = homepage_url
    article_url_list, homepage_url = get_links(bsObj)
    if new_article_url in article_url_list:
        index = article_url_list.index(new_article_url)
        new_article_url_list = article_url_list[index:]
    else:
        print("根据上次存储的导航页 homepage 信息，以及待抓取页面url，不能判断出应该从哪里继续开始这次的任务")
        return None,None,None
    return cur_referer, new_article_url_list, homepage_url,


def main():
    """
    1. 使用时需要修改：
        get_response():
            如果使用了全局代理，可以将 flag 设置为 GLobal
            否则，需要设置使用代理的各参数，例如 ip、端口、协议类型。如果有多个代理可以使用列表。
        main():
            next_page
        insert2database():
            连接 MySql 的参数

    2. 保存记录会写入 record.txt，出错的信息会记录在 log.txt，这两个文件每次运行会被重写。
    :return:
    """

    find_duplicate = False
    cur_referer = snopes_url
    next_homepage = snopes_facts_url   # initial home page
    # next_homepage = "http://www.snopes.com/category/facts/page/7/"   # initial home page
    article_list = []
    article_url_list = []
    cnt = 0
    with open('record.txt', 'w', encoding='utf8') as file_writer:  # 清空内容
        file_writer.write('')
    try:
        # 是否需要根据上次的进度来继续任务
        # user_input = input('Reload?\nInput yes/y to reload, others to start at the initial homepage.\n')
        # is_reload = (user_input == 'y' or user_input == 'yes')
        is_reload = False
        while True:
            cnt = 0  # number of successful processed urls
            if is_reload:
                is_reload = False
                cur_referer, article_url_list, next_homepage = reload_progress()
                if cur_referer is None:
                    break
            else:
                my_response = get_response(next_homepage, cur_referer)  # homepage
                cur_referer = next_homepage  # set to current homegape
                if my_response is None:   # 理论上不会发生
                    print('homepage can\'t reach, response is error'); break
                article_url_list, next_homepage = get_links(my_response)
            print("start process HOME PAGE: %s" % cur_referer)  # report the progress, current homepage
            with open('record.txt', 'a+', encoding='utf8') as file_writer:  # record homepage url
                file_writer.write("start process HOME PAGE: %s\n" % cur_referer)
            for content_url in article_url_list:
                print("start process %s" % content_url)  # report the progress
                if content_url == 'http://www.snopes.com/50-hottest-urban-legends/' \
                        or content_url == 'http://www.snopes.com/25-hottest-urban-legends/'\
                        or content_url == 'http://www.snopes.com/faq/' \
                        or content_url == 'http://www.snopes.com/info/news/news.asp' \
                        or content_url == 'http://www.snopes.com/business/names/fubu.asp':   # 436
                    print('ignore this url and continue')
                    continue
                with open('record.txt', 'a+', encoding='utf8') as file_writer:  # record article url
                    file_writer.write("start process %s\n" % content_url)

                # if content_url not in unique_url_list:
                #      unique_url_list.add(content_url)
                # else:
                #     find_duplicate = True
                #     print("find duplicate url, scraping is done.")
                #     raise NameError('find duplicate item, scraping is done.')

                bsObj = get_response(content_url, cur_referer)
                #  add while here
                if bsObj is None:
                    for i in range(10):  # 重连 10 次
                        time.sleep(2*(i+1))
                        bsObj = get_response(content_url, cur_referer)
                        if bsObj is not None:
                            break
                if bsObj is None:
                    print("访问失败")
                    return
                #  重连失败

                title, description, claim, published_date, updated_date, rating, content, sources, tag_list, category, repost_cnt = scrapping_content(bsObj)
                # 为了方便 debug，采用一次一条插入数据库published_date, updated_date
                insert2database([Article(content_url, title,description, claim, published_date, updated_date,
                                         rating,content, sources, tag_list, category, repost_cnt)])
                # 将一个 list 插入数据库
                # article_list.append(Article(content_url,title,description,claim,date,rating,content, sources))
                time.sleep(2)  # sleep 2 seconds

    finally:
        # current home page
        # successfully processed content url
        with open('log.txt', 'w', encoding='utf8') as file_writer:
            # write the home page url
            file_writer.write(cur_referer+'\n')
            for i in range(cnt):
                file_writer.write(article_url_list[i] + '\n')
            file_writer.write('Below is to be scrapping.\n')
            # 为了防止页面更新带来的错误，reload 时应该重新分析当前 homepage，然后接上上次的操作。
            # 在距离上次操作经过很久时，有可能 homepage 整个都被刷新掉了（小概率）
            for i in range(cnt, len(article_url_list)):
                file_writer.write(article_url_list[i] + '\n')

        # 因为数据库插入过程中可能会出错，现采用一次插一条的方法。
        # insert into database
        # insert2database(article_list)

        # write back the processed urls
        # with open('unique_url_list.txt', 'w', encoding='utf8') as file_writer:
        #     file_writer.write('\n'.join(unique_url_list))


def insert2database(article_list):

    def escape_quote(s):
        return s.replace("'", "\\'")

    """
    插入数据库，需要修改连接数据库的参数
    None 代表缺少某一个元素
    这里设置的是遇到重复 url 的页面就终止插入数据库的操作
    :param article_list: instances of Article
    :return: 
    """
    # Connect to the database
    connection = pymysql.connect(host='127.0.0.1',
                                 port=3306,
                                 user='root',
                                 password='asdfjkl;',
                                 db='db_snopes',
                                 charset='utf8mb4',  # encoding emoji
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()
    try:
        for article in article_list:
            # find if there has duplicate
            existed = cursor.execute("select * from `tb_snopes` where `url` = %s;", (article.url,))
            if bool(existed) is False:
                # 注意 sql 语句需要转义， 需要用 bind variables
                sql = "INSERT INTO `tb_snopes`" \
                      "(`url`, `title`, `description`, `claim`, `published_date`, `updated_date`, " \
                      "`rating`, `content`, `sources`, `tag_list`, `category`, `repost_cnt`)" \
                      "  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
                # Create a new record
                # article.print_sc()
                status =cursor.execute(sql, (article.url, article.title, article.description, article.claim, article.published_date, article.updated_date,
                                     article.rating, article.content, article.sources, article.tag_list, article.category, article.repost_cnt))
                cursor.connection.commit()
            else:   # 更新
                cursor_res = cursor.fetchone()
                url = cursor_res["url"]
                # 用来判断哪些部分完成了更新
                update_field_value = dict()
                for field in field_list:
                    if cursor_res[field] != escape_quote(article.__dict__[field]):
                        update_field_value[field] = (cursor_res[field], article.__dict__[field])

                ''' bing的参数的实现 '''
                sql = "UPDATE `tb_snopes` " \
                      "SET " \
                      "`url`=%s," \
                      "`title`=%s," \
                      "`description`=%s," \
                      "`claim`=%s," \
                      "`published_date`=%s," \
                      "`updated_date`=%s," \
                      "`rating`=%s," \
                      "`content`=%s," \
                      "`sources`=%s," \
                      "`tag_list`=%s," \
                      "`category`=%s," \
                      "`repost_cnt`=%s" \
                      "WHERE `url`=%s;"

                ''' sql字符串的实现方式 '''
                sql = "UPDATE `tb_snopes` " \
                      "SET " \
                      "`url`='%s'," \
                      "`title`='%s'," \
                      "`description`='%s'," \
                      "`claim`='%s'," \
                      "`published_date`='%s'," \
                      "`updated_date`='%s', " \
                      "`rating`='%s'," \
                      "`content`='%s'," \
                      "`sources`='%s'," \
                      "`tag_list`='%s'," \
                      "`category`='%s'," \
                      "`repost_cnt`='%s'" \
                      "WHERE `url`='%s';"
                # print(sql % ((article.url, article.title, article.description, article.claim,
                #                      article.published_date, article.updated_date, article.rating,
                #                      article.content, article.sources, article.tag_list, article.category,
                #                      article.repost_cnt, url)))
                ''' bing的参数的实现 '''
                # status = cursor.execute(sql, (article.url, article.title, article.description, article.claim,
                #                      article.published_date, article.updated_date, article.rating,
                #                      article.content, article.sources, article.tag_list, article.category,
                #                      article.repost_cnt, url))
                ''' sql字符串的实现方式 '''
                status = cursor.execute(sql % (article.url,
                                               escape_quote(article.title),
                                               escape_quote(article.description),
                                               escape_quote(article.claim),
                                               escape_quote(article.published_date),
                                               escape_quote(article.updated_date),
                                               escape_quote(article.rating),
                                               escape_quote(article.content),
                                               escape_quote(article.sources),
                                               escape_quote(article.tag_list),
                                               escape_quote(article.category),
                                               escape_quote(article.repost_cnt),
                                               url))
                print("\tupdate %s" % bool(status))  # 1 for succeed, 0 for failed  # 数据没有变化的时候也不会更新
                if bool(status):
                    for k,v in update_field_value.items():
                        print("\t更新字段%s" % k)
                        print("\t\t更新前:%s" % repr(v[0]))
                        print("\t\t更新后:%s" % repr(v[1]))
                cursor.connection.commit()

                # print('Already existed item in database!\nurl: %s ' % article.url)
                # raise NameError('Already existed item in database!\nurl: %s ' % article.url)
    finally:
        connection.close()


if __name__ == '__main__':
    """ 主函数部分 """
    main()

