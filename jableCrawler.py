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
    try:
        try:
            driver = setup_chrome_driver(port)
        except Exception as e:
            print(f"設定 ChromeDriver 時發生錯誤: {e}")
            driver = None
            while driver is None:
                port = random.randint(9322, 11200)
                driver = setup_chrome_driver(port)
        if driver is None:
            print("無法設定 ChromeDriver")
            return None
        driver.get(url)
        page_source = driver.page_source
        driver.quit()
        return page_source
    except Exception as e:
        print(f"獲取頁面失敗: {e}")
        if driver:
            driver.quit()
        return None


def collect_video_links(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        # print(soup.prettify())
        container = soup.find("div", id="list_videos_common_videos_list")
        if not container:
            return []
        video_divs = container.find_all("div", class_="col-6 col-sm-4 col-lg-3")
        links = []
        for video in video_divs:
            detail_div = video.find("div", class_="detail")
            if detail_div:
                link_tag = detail_div.find("a", href=True)
                title_tag = detail_div.find("h6", class_="title")
                if link_tag and title_tag:
                    links.append({
                        "title": title_tag.get_text(strip=True),
                        "url": link_tag["href"]
                    })
        return links
    except Exception as e:
        print(f"解析 HTML 內容時發生錯誤: {e}")
        return []
    
def fetchLinks(parm):
    if parm[0] is not None:
        link = collect_video_links(fetch_page_source(parm[0], parm[1]))
        return link
    return None

def fetch_jable_data(urls):
    links = []
    for i in range(1,2):
        url = urls+str(i)+'/'
        print(f"正在爬取: {url}")
        page_source = fetch_page_source(url, port=9322)
        if not page_source:
            continue
            
        soup = BeautifulSoup(page_source, "html.parser")
        containers = soup.find_all('div', class_='horizontal-img-box ml-3 mb-3')
        href = [container.find('a')['href'] for container in containers]
        parm = [(href[i], 3300+i) for i in range(len(href))]
        print(parm)
        with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
            results = p.map(fetchLinks,parm)
            for i in results:
                links.extend(i)

        print(f"第 {i} 頁完成，目前共 {len(links)} 個連結")
    if links:
        print(f"總共找到 {len(links)} 個影片連結")
        return links
    else:    
        print("找不到任何影片")
        return None

def fetch_video_details(link, port):
    link_url = link["url"]
    sub_page_source = fetch_page_source(link_url, port)
    if sub_page_source:
        sub_soup = BeautifulSoup(sub_page_source, "html.parser")
        
        # 獲取演員信息
        avatar_tags = sub_soup.find_all("img", class_="avatar rounded-circle")
        avatar_tags2 = sub_soup.find_all("span", class_="placeholder rounded-circle")
        model_names = [tag.get("data-original-title", "未知女優") for tag in avatar_tags]
        model_names += [tag.get("data-original-title", "未知女優") for tag in avatar_tags2]
        
        # 獲取標籤
        tag_list = []
        tag_container = sub_soup.find_all("h5", class_="tags h6-md")
        # return None
        if(tag_container):
            tag_container = tag_container[0].find_all("a")
            for tag in tag_container:
                # print(tag)
                tag_list.append(tag.text.strip())
        
        # 獲取評論
        comments = []
        comment_tags = sub_soup.find_all("section", class_="comments pb-3 pb-lg-4")
        for comment_tag in comment_tags:
            comment_divs = comment_tag.find_all("div", class_="right")
            for div in comment_divs:
                comment_text = div.find("p", class_="comment-text")
                if comment_text and comment_text.find("span"):
                    comments.append(comment_text.find("span").text.strip())
        
        # 獲取觀看次數和評分
        views = "0"
        rating = "0"
        info_div = sub_soup.find_all("h6")
        if info_div:
            info_div = info_div[0].find_all("span", class_="mr-3")
            try:
                # 移除所有空白字元
                views = info_div[1].text.strip().replace(" ", "")
            except Exception:
                pass
            
        rating_tag = sub_soup.find_all("div", class_="my-3")
        if rating_tag:
            rating_tag = rating_tag[0].find("span", class_="count")
            if rating_tag:
                rating = rating_tag.text.strip().replace(" ", "")
            
            # 尋找評分
        
        
        # 獲取描述
        
        video_details = {
            "title": link["title"],
            "url": link_url,
            "models": model_names,
            "tags": tag_list,
            "comments": comments,
            "views": views,
            "rating": rating,
        }
        print(video_details)
        return video_details
    return None


def random_video_info(url):
    links = fetch_jable_data(url)
    if not links:
        print("找不到任何影片")
        return
    random_link = random.choice(links)
    fetch_video_details(random_link, port=9222)


def fetch_all_video_details(url):
    print(f'Starting {multiprocessing.cpu_count()} processes')
    all_video_details = []
    
    print(f'正在爬取: {url}')
    links = fetch_jable_data(url)
    if not links:
        print(f"在 {url} 中找不到任何影片")
        return
        
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
    
    # 保存到 video_details.json
    try:
        with open("video_details.json", "w", encoding="utf-8") as f:
            json.dump(all_video_details, f, ensure_ascii=False, indent=4)
        print('成功保存數據到 video_details.json')
        return None
    except Exception as e:
        print(f'保存數據時發生錯誤: {str(e)}')

if __name__ == "__main__":
    # urls = ["https://jable.tv/models/saika-kawakita/",
    # 'https://jable.tv/models/moe-amatsuka/',
    # 'https://jable.tv/models/yumeno-aika/',
    # 'https://jable.tv/models/mayuki-ito/',
    # 'https://jable.tv/models/aizawa-minami/',
    # 'https://jable.tv/models/arina-hashimoto/',
    # 'https://jable.tv/s1/models/yua-mikami/',
    # 'https://jable.tv/models/tsumugi-akari/',
    # 'https://jable.tv/hot/',
    # 'https://jable.tv/models/aoi/',
    # 'https://jable.tv/models/b435825a4941964079157dd2fc0a8e5a/',
    # 'https://jable.tv/models/sonoda-mion/',
    # 'https://jable.tv/models/rion/',
    # 'https://jable.tv/models/akiho-yoshizawa/',
    # 'https://jable.tv/models/saki-okuda/',
    # 'https://jable.tv/models/1ef59d3651b3600c80cf04e15dd0e3a0/',
    # 'https://jable.tv/models/5bb0ee22c9c0709d6374b244a7c3462f/',
    # 'https://jable.tv/s1/models/mitani-akari/',
    # 'https://jable.tv/models/yoshitaka-nene/',
    # 'https://jable.tv/s1/models/hukada-eimi/',
    # 'https://jable.tv/models/780d1292b5d51f1c94b685a0e90a3c73/',
    # 'https://jable.tv/models/jessica-kizaki/',
    # 'https://jable.tv/models/julia/',
    # 'https://jable.tv/models/non-ohana/',
    # 'https://jable.tv/s1/models/hatano-yui/',
    # 'https://jable.tv/models/aika/',
    # 'https://jable.tv/models/shiina-sora/',
    # 'https://jable.tv/models/airi-kijima/',
    #         'https://jable.tv/models/non-ohana/',
    #         'https://jable.tv/models/sumire-kurokawa/',
    #         'https://jable.tv/models/rin-azuma/',
    #         'https://jable.tv/models/kojima-minami/',
    #         'https://jable.tv/models/hoshina-ai/',
    #         'https://jable.tv/models/hibiki-otsuki/',
    #         'https://jable.tv/models/tsubasa-amami/',
    #         'https://jable.tv/models/arisaka-miyuki/',
    #         'https://jable.tv/models/matsuri-kiritani/',
    #         'https://jable.tv/models/minami-hatsukawa/',
    #         'https://jable.tv/models/kurea-hasumi/',
    #         'https://jable.tv/models/kurea-hasumi/',
    #         'https://jable.tv/models/mei-satsuki/',
    #         'https://jable.tv/models/nozomi-ishihara/',
    #         'https://jable.tv/models/mio-kimijima/',
    #         'https://jable.tv/models/sakura-mana/']
    urls = 'https://jable.tv/models/'
    fetch_all_video_details(urls)
