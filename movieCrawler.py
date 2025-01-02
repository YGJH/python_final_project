from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import random
import concurrent.futures
import multiprocessing
import json
import time
from urllib.parse import urlparse
import re

def setup_chrome_driver(port):
    try:
        chrome_options = webdriver.ChromeOptions()
        # 刪除原本的 driver 宣告
        # 設定 chrome_options
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        chrome_options.add_argument("--headless")  # 啟動Headless 無頭
        chrome_options.add_argument('--disable-gpu')  # 關閉GPU 避免某些系統或是網頁出錯
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--remote-debugging-port={port}")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument(" --enable-unsafe-swiftshader")

        # 模擬真實瀏覽器標頭
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36")
        
        # 更新 ChromeDriver 配置
        chrome_service = ChromeService()
        driver = webdriver.Chrome(
            service=chrome_service,
            options=chrome_options
        )

        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"})
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None

def fetch_page_source(url, port):
    """
    與 fetch_jable_data() 類似，用 Selenium 進入指定網址並回傳 page_source，
    可以用於前往其他連結。
    """
    import random
    try:
        driver = setup_chrome_driver(port)
        while driver is None:
            print("重新設定 driver")    
            driver = setup_chrome_driver(random.randint(3300 , 12000))
            

        driver.get(url)
        
        # 設置 nextFilmCard.length 為 10000

        page_source = driver.page_source
        driver.quit()

        return page_source
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None

def fetch_page_source2(url, port):
    """
    與 fetch_jable_data() 類似，用 Selenium 進入指定網址並回傳 page_source，
    可以用於前往其他連結。
    """
    import random
    try:
        driver = setup_chrome_driver(port)
        while driver is None:
            print("重新設定 driver")
            driver = setup_chrome_driver(random.randint(3300 , 12000))
        
        driver.get(url)
        
        # 設置 nextFilmCard.length 為 10000
        driver.execute_script("window.nextFilmCard.length = 100;")
        for i in range(50):
            # 觸發 query() 函數
            driver.execute_script("window.query();")
            # time.sleep(2)  # 等待 query() 執行完畢
            driver.execute_script("window.nextFilmCard.index++;")
            
        soup = BeautifulSoup(driver.page_source, "html.parser")
        container = soup.find_all("div", class_="film-item")
    
        print(len(container))            
        driver.quit()

        return container
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None


def get_domain(url):
    """擷取網址的 domain name"""
    parsed_url = urlparse(url)
    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return domain

# 使用範例
def collect_video_links(html_content , url):
    links = []
    url = get_domain(url)
    for con in html_content:
        try:
            a = con.find("a")   
            if(len(a.get("href")) < len('https://video.friday.tw/movie/detail')):
                if  "/movie/detail" in a.get("href"):
                    links.append(url+a.get("href"))
                continue

            links.append(a.get("href"))
        except Exception as e:
            print(f"解析影片連結時發生錯誤: {e}")
            continue
    print(links)
    return links


def fetch_jable_data(url):
    page_source = fetch_page_source2(url, port=9222)
    # print(page_source)
    if not page_source:
        return []
    # 先記錄所有影片連結
    
    links = collect_video_links(page_source, url )
    return links

def format_json_string(json_str):
    """格式化 JSON 字串，移除換行和多餘空格"""
    # 移除換行和多餘空格
    formatted_str = re.sub(r'\s+', ' ', json_str)
    # 解析並重新格式化 JSON
    json_obj = json.loads(formatted_str)
    # 轉換回單行 JSON 字串
    return json.dumps(json_obj, ensure_ascii=False)

def clean_json_string(json_str):
    """清理並格式化 JSON 字串"""
    # 移除換行和多餘空格
    cleaned = re.sub(r'\s+', ' ', json_str.strip())
    # 移除最後的逗號和多餘的大括號
    cleaned = re.sub(r',\s*}$', '}', cleaned)
    # 確保 JSON 格式正確
    cleaned = re.sub(r'}\s*{', '},{', cleaned)
    return cleaned

def extract_actor_names(actors_list):
    """提取演員名稱"""
    names = []
    for actor in actors_list:
        try:
            # 使用正則表達式找出 name 欄位的值
            name_match = re.search(r'"name":\s*"([^"]+)"', actor)
            if name_match:
                names.append(name_match.group(1))
        except Exception as e:
            print(f"解析演員名稱時發生錯誤: {e}")
            continue
    return names


def fetch_video_details(link, port):
    link_url = link
    try:
        sub_page_source = fetch_page_source(link_url, port)
        movie = None  # 初始化 movie 變數
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None
    
    try:
        if sub_page_source:
            movie = {}
            sub_soup = BeautifulSoup(sub_page_source, "html.parser")  # 解析頁面內容
            score_tag = sub_soup.find('p', class_='score-num-text')
            if score_tag:
                score = score_tag.text.strip()
                movie['score'] = score
            else:
                movie['score'] = 'N/A'
            scripts = sub_soup.find_all("script", type="application/ld+json")
            if not scripts:
                print(f"找不到 JSON 資料的 <script> 標籤: {link['url']}")
                return None

            info = scripts[-1]
            # 解析 JSON 資料
            info_data = json.loads(info.text)
            
            # 使用解析后的 JSON 資料提取 description 和 actors
            movie['description'] = info_data.get('description', 'N/A')
            
            # 提取所需字段
            movie['url'] = info_data.get('url', '')
            movie['countryOfOrigin'] = info_data.get('countryOfOrigin', '')
            movie['datePublished'] = info_data.get('datePublished', '')
            movie['image'] = info_data.get('image', '')
            directors = info_data.get('director', [])
            movie['director'] = [director.get('name') for director in directors if director.get('name')]
            movie['genre'] = info_data.get('genre', [])
            actors_list = info_data.get('actor', [])
            actor_names = [actor.get('name') for actor in actors_list if actor.get('name')]
            movie['actors'] = actor_names
    except Exception as e:
        print(f"解析影片詳情時發生錯誤: {e}")
        movie = None

    if movie:
        print(movie)
        return movie
    return None



def fetch_all_video_details(url):
    print(f'Starting {multiprocessing.cpu_count()} processes')
    all_video_details = []
    
    print(f'正在爬取: {url}')
    links = fetch_jable_data(url)
    if not links:
        print(f"在 {url} 中找不到任何影片")
        return None
    video_details_list = []
    with concurrent.futures.ThreadPoolExecutor(multiprocessing.cpu_count()) as executor:
        ports = [3300 + i for i in range(len(links))]
        results = executor.map(fetch_video_details, links, ports)
        for result in results:
            if result:
                video_details_list.append(result)


    print(f'從 {url} 成功爬取 {len(video_details_list)} 個影片資訊')
    all_video_details.extend(video_details_list)

    print(f'總共爬取 {len(all_video_details)} 個影片資訊')
    
    try:
        with open("video_details.json", "w", encoding="utf-8") as f:
            json.dump(all_video_details, f, ensure_ascii=False, indent=4)
        print('成功保存數據到 video_details.json')

    except Exception as e:
        print(f'保存數據時發生錯誤: {str(e)}')

if __name__ == "__main__":
    url = 'https://video.friday.tw/movie/filter/all/all/all/all'
    fetch_all_video_details(url)
