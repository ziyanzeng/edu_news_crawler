from flask import Flask, jsonify, Response, request
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from datetime import date
from datetime import timedelta
from collections import deque

app = Flask(__name__)

URL_LIST = [
    "https://www.cse.edu.cn/index/index.html?category=59",
    "http://www.moe.gov.cn/jyb_xxgk/moe_1777/moe_1778/",
    "http://www.moe.gov.cn/jyb_xxgk/moe_1777/moe_1779/",
    "http://www.moe.gov.cn/jyb_xwfb/s5148/",
    "http://www.moe.gov.cn/jyb_xwfb/s271/",
    "http://www.moe.gov.cn/was5/web/search?channelid=239993",
    "https://www.cse.edu.cn/index/index.html?category=42",
    "https://mp.weixin.qq.com/mp/appmsgalbum?__biz=Mzg2ODA0ODkwNA==&action=getalbum&album_id=1409137364018216961&scene=173&subscene=&sessionid=svr_366a36a69f6&enterid=1716877342&from_msgid=2247527499&from_itemidx=1&count=3&nolastread=1#wechat_redirect",
    "https://www.chyxx.com/wiki/jiaoyuye"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-us",
    "Connection": "keep-alive",
    "Accept-Charset": "GB2312,utf-8;q=0.7,*;q=0.7",
}

# def parse_eol_news(soup):
#     news_data = []
#     news_section = soup.find('div', class_='zxdt-con')
#     if news_section:
#         latest_news_links = news_section.find_all('a', href=True)
#         for link in latest_news_links:
#             news_url = link['href']
#             if not news_url.startswith('http'):
#                 news_url = 'https://news.eol.cn' + news_url
#             news_data.append(news_url)
#     return news_data

# def extract_eol_news_details(soup, url):
#     title = soup.find('title').get_text(strip=True)
#     content_div = soup.find('div', class_='TRS_Editor')
#     content = content_div.get_text(strip=True) if content_div else ""
#     return {
#         'url': url,
#         'title': title,
#         'content': content,
#         'date': str(datetime.now().date())
#     }

def parse_cse_news(soup):
    news_data = []
    news_section = soup.find('ul', class_='project_list')
    if news_section:
        latest_news_links = news_section.find_all('a', href=True)
        for link in latest_news_links:
            news_url = link['href']
            if not news_url.startswith('http'):
                news_url = 'https://www.cse.edu.cn' + news_url
            news_data.append(news_url)
    return news_data

def extract_cse_news_details(soup):
    h1_tags = soup.find_all('h1', style='text-align: center; line-height: 2em;')
    title = "".join([tag.get_text(strip=True) for tag in h1_tags])
    
    content_div = soup.find('div', class_='main_con')
    content = content_div.get_text(strip=True) if content_div else ""
    
    date_div = soup.find('time')
    date = date_div.get_text(strip=True) if date_div else None
    
    return title, content, date

def parse_cse_42_news(soup):
    news_data = []
    news_section = soup.find('ul', class_='list_ul')
    if news_section:
        latest_news_links = news_section.find_all('a', href=True)
        for link in latest_news_links:
            news_url = link['href']
            if not news_url.startswith('http'):
                news_url = 'https://www.cse.edu.cn' + news_url
            news_data.append(news_url)
    return news_data

def parse_moe_news(soup, base_url):
    news_data = []
    news_section = soup.find('ul', id="list")
    if news_section:
        latest_news_items = news_section.find_all('li')
        for item in latest_news_items:
            link = item.find('a', href=True)
            date_span = item.find('span')
            if link and date_span:
                news_url = link['href']
                date = date_span.get_text(strip=True)
                if not news_url.startswith('http'):
                    news_url = base_url + news_url[2:]
                news_data.append((news_url, date))
    return news_data

def extract_moe_news_details(soup):
    title = soup.find('h1').get_text(strip=True)
    content_div = soup.find('div', class_='TRS_Editor')
    content = content_div.get_text(strip=True) if content_div else ""
    return title, content
    
def parse_moe_was5_news(soup):
    news_data = []
    news_section = soup.find('div', class_="scy_lbsj-right-nr")
    if news_section:
        latest_news_item = news_section.find_all('li')
        for item in latest_news_item:
            link = item.find('a', href=True)
            date_span = item.find('span')
            if link and date_span: 
                news_url = link['href']
                date = date_span.get_text(strip=True)
                news_data.append((news_url, date))
    return news_data
    
def extract_moe_was5_details(soup):
    title = soup.find('h1').get_text(strip=True)
    content_div = soup.find('div', id='downloadContent')
    content = content_div.get_text(strip=True) if content_div else ""
    return title, content

def parse_wechat_album(soup):
    news_data = []
    news_items = soup.find_all('li', class_='album__list-item js_album_item js_wx_tap_highlight wx_tap_cell')
    
    for item in news_items:
        link = item.get('data-link')
        date_tag = item.find('span', class_='js_article_create_time album__item-info-item')
        if link and date_tag:
            date_text = date_tag.get_text(strip=True)
            
            # 将 Unix 时间戳转换为日期
            try:
                date = datetime.fromtimestamp(int(date_text)).strftime('%Y-%m-%d')
            except ValueError:
                print(f"Invalid timestamp: {date_text}")
                continue
            
            if not link.startswith('http'):
                link = 'https://mp.weixin.qq.com' + link
            
            news_data.append((link, date))
    
    return news_data

def extract_wechat_article_details(soup):
    try:
        title = soup.find('h1', class_='rich_media_title').get_text(strip=True)
    except AttributeError:
        print("Title tag not found in provided soup...")
        title = "教育报告"
    content_div = soup.find('div', class_='rich_media_content', id='js_content')
    content = content_div.get_text(strip=True) if content_div else ""
    return title, content


def parse_chyxx_news(soup):
    news_data = []
    news_section = soup.find_all('li', class_='hot_item wiki-sublist__entry')
    for item in news_section:
        link = item.find('a', href=True)
        if link:
            news_url = link['href']
            if not news_url.startswith('http'):
                news_url = 'https://www.chyxx.com' + news_url
            news_data.append(news_url)
    return news_data

def extract_chyxx_article_details(soup):
    title = soup.find('h1', class_='cx-article__title').get_text(strip=True)
    content_div = soup.find('div', class_='wiki-article__body')
    content = content_div.get_text(strip=True) if content_div else ""
    date_span = soup.find('span', class_='t-14 t-placeholder l-24 mr-32')
    date = date_span.get_text(strip=True) if date_span else ""
    return title, content, date[:10]

def fetch_latest_news(base_url, start_date):
    # 初始化队列和新闻数据
    queue = deque([base_url])
    visited = set()
    news_data = []

    while queue:
        url = queue.popleft()
        if url in visited:
            continue
        
        if isinstance(url, tuple):
            url, date = url
        
        visited.add(url)

        response = requests.get(url, headers=HEADERS, allow_redirects=True)
        response.raise_for_status()  # 确保请求成功
        soup = BeautifulSoup(response.content, 'html.parser')
        
        if url == base_url:
            # 根据base_url选择解析方法
            if 'cse.edu.cn/index/index.html?category=59' in base_url:
                latest_news_links = parse_cse_news(soup)
            elif 'cse.edu.cn/index/index.html?category=42' in base_url:
                latest_news_links = parse_cse_42_news(soup)
            elif 'moe.gov.cn/jyb_xwfb/' in base_url or 'moe.gov.cn/jyb_xxgk/' in base_url:
                latest_news_links = parse_moe_news(soup, base_url)
            elif 'moe.gov.cn/was5' in base_url:
                latest_news_links = parse_moe_was5_news(soup)
            elif 'mp.weixin.qq.com' in base_url:
                latest_news_links = parse_wechat_album(soup)
            elif 'chyxx.com' in base_url:
                latest_news_links = parse_chyxx_news(soup)
            # 添加其他解析逻辑...
            
            print(f"base url is: {base_url}")
            
            for news_url in latest_news_links:
                if isinstance(news_url, tuple):
                    news_url, date = news_url
                    if news_url not in visited:
                        queue.append((news_url, date))
                else:
                    if news_url not in visited:
                        queue.append(news_url)
        else:
            if 'cse.edu.cn' in base_url:
                title, content, date = extract_cse_news_details(soup)
                if datetime.strptime(date[-10:], "%Y-%m-%d").date() >= start_date:
                    news_data.append({
                        'url': url,
                        'title': title,
                        'content': content,
                        'date': date[-10:]
                    })
            elif 'moe.gov.cn/jyb_xwfb' in base_url:
                title, content = extract_moe_news_details(soup)
                if datetime.strptime(date[-10:], "%Y-%m-%d").date() >= start_date:
                    news_data.append({
                        'url': url,
                        'title': title,
                        'content': content,
                        'date': date[-10:]
                    })
            elif 'moe.gov.cn/was5' in base_url:
                title, content = extract_moe_was5_details(soup)
                if datetime.strptime(date[-10:], "%Y-%m-%d").date() >= start_date:
                    news_data.append({
                        'url': url,
                        'title': title,
                        'content': content,
                        'date': date[-10:]
                    })
            elif 'mp.weixin.qq.com' in base_url:
                title, content = extract_wechat_article_details(soup)
                date = date.strip()
                try:
                    if datetime.strptime(date, "%Y-%m-%d").date() >= start_date:  # 根据实际日期格式
                        news_data.append({
                            'url': url,
                            'title': title,
                            'content': content,
                            'date': date
                        })
                except ValueError as e:
                    print(f"Date parsing error for URL: {url}, date: {date}, error: {e}")
            elif 'chyxx.com' in base_url:
                title, content, date = extract_chyxx_article_details(soup)
                if datetime.strptime(date, "%Y-%m-%d").date() >= start_date:
                    news_data.append({
                        'url': url,
                        'title': title,
                        'content': content,
                        'date': date
                    })
            # 为其他网站添加相应的解析和提取逻辑...
    
    return news_data

def fetch_news_from_urls(url_list, start_date):
    all_news_data = []
    for url in url_list:
        news_data = fetch_latest_news(url, start_date)
        if news_data:
            all_news_data.extend(news_data)
    return all_news_data

def fetch_backup_latest_news(base_url):
    # 初始化队列和新闻数据
    queue = deque([base_url])
    visited = set()
    news_data = []

    while queue:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        response = requests.get(url)
        response.raise_for_status()  # 确保请求成功
        soup = BeautifulSoup(response.content, 'html.parser')

        if url == base_url:
            # 查找最新新闻的链接
            news_section = soup.find('div', class_='zxdt-con')
            if news_section:
                latest_news_links = news_section.find_all('a', href=True)
                for link in latest_news_links:
                    news_url = link['href']
                    if not news_url.startswith('http'):
                        news_url = base_url + news_url
                    if news_url not in visited:
                        queue.append(news_url)
        else:
            # 提取新闻标题和内容
            title = soup.find('title').get_text(strip=True)
            content_div = soup.find('div', class_='TRS_Editor')
            content = content_div.get_text(strip=True) if content_div else ""

            news_data.append({
                'url': url,
                'title': title,
                'content': content,
                'date': str(datetime.now().date())
            })

    return news_data

@app.route('/fetch_news/<prev_days>', methods=['GET'])
def fetch_news(prev_days):
    print(f"Fetching news from URLs: {URL_LIST}")
    start_date = date.today() - timedelta(days=int(prev_days))
    all_news_data = fetch_news_from_urls(URL_LIST, start_date)
    # 对 JSON 数据进行编码处理并确保使用 utf-8 编码
    json_data = json.dumps(all_news_data, ensure_ascii=False)
    response = Response(json_data, content_type='application/json; charset=utf-8')
    return response

@app.route('/fetch_news', methods=['GET'])
def fetch_news_default():
    print(f"Fetching news from URLs: {URL_LIST}")
    start_date = date.today() - timedelta(days=1)
    all_news_data = fetch_news_from_urls(URL_LIST, start_date)
    # 对 JSON 数据进行编码处理并确保使用 utf-8 编码
    json_data = json.dumps(all_news_data, ensure_ascii=False)
    response = Response(json_data, content_type='application/json; charset=utf-8')
    return response

@app.route('/fetch_backup', methods=['GET'])
def fetch_backup():
    base_url = 'https://news.eol.cn'
    news_data = fetch_backup_latest_news(base_url)
    print(f"Fetching news from single backup site: {base_url}")
    # 对 JSON 数据进行编码处理并确保使用 utf-8 编码
    json_data = json.dumps(news_data, ensure_ascii=False)
    response = Response(json_data, content_type='application/json; charset=utf-8')
    return response

@app.errorhandler(404)
def page_not_found(e):
    return jsonify(error=str(e)), 404

if __name__ == '__main__':
    print("Starting Flask app on port 5001")
    app.run(host='0.0.0.0', port=5001)  # 修改端口号为5001
