from flask import Flask, jsonify, request, Response
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from collections import deque

app = Flask(__name__)

def fetch_latest_news(base_url):
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

@app.route('/fetch_news', methods=['GET'])
def fetch_news():
    base_url = request.args.get('base_url', 'https://news.eol.cn')
    print(f"Fetching news from: {base_url}")
    news_data = fetch_latest_news(base_url)
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
