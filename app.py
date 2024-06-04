from flask import Flask, jsonify, Response, request
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from collections import deque

app = Flask(__name__)

URL_LIST = [
    "https://www.cse.edu.cn/index/index.html?category=59",
    "http://www.moe.gov.cn/jyb_xxgk/moe_1777/moe_1778/",
    "http://www.moe.gov.cn/jyb_xxgk/moe_1777/moe_1779/",
    "http://www.moe.gov.cn/jyb_xwfb/s5148/",
    "http://www.moe.gov.cn/jyb_xwfb/s271/"
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
    title = soup.find('h1').get_text(strip=True)
    content_div = soup.find('div', class_='main_con')
    content = content_div.get_text(strip=True) if content_div else ""
    date_div = soup.find('div', class_='source_con')
    if date_div:
        date = date_div.find('time').get_text(strip=True)
    else: 
        date = None
    return title, content, date

def parse_moe_news(soup, base_url):
    news_data = []
    news_section = soup.find('ul', id='list')
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
            if 'news.eol.cn' in base_url:
                latest_news_links = parse_eol_news(soup)
            elif 'cse.edu.cn' in base_url:
                latest_news_links = parse_cse_news(soup)
            elif 'moe.gov.cn' in base_url:
                latest_news_links = parse_moe_news(soup, base_url)
            # 添加其他解析逻辑...
            
            for news_url in latest_news_links:
                if isinstance(news_url, tuple):
                    news_url, date = news_url
                    if news_url not in visited:
                        queue.append((news_url, date))
                else:
                    if news_url not in visited:
                        queue.append(news_url)
        else:
            if 'news.eol.cn' in base_url:
                news_details = extract_eol_news_details(soup, url)
                news_data.append(news_details)
            elif 'cse.edu.cn' in base_url:
                title, content, date = extract_cse_news_details(soup)
                if datetime.strptime(date[-10:], "%Y-%m-%d").date() >= start_date:
                # if True:
                    news_data.append({
                        'url': url,
                        'title': title,
                        'content': content,
                        'date': date
                    })
            elif 'moe.gov.cn' in base_url:
                title, content = extract_moe_news_details(soup)
                if datetime.strptime(date[-10:], "%Y-%m-%d").date() >= start_date:
                # if True:
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

@app.route('/fetch_news/<start_date>', methods=['GET'])
def fetch_news(start_date):
    print(f"Fetching news from URLs: {URL_LIST}")
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
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
