from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import random
import concurrent.futures
import json


def fetch_page_source(url, port):
    """
    與 fetch_jable_data() 類似，用 Selenium 進入指定網址並回傳 page_source，
    可以用於前往其他連結。
    """
    try:
        # 配置 Selenium 瀏覽器
        chrome_options = webdriver.ChromeOptions('C:\\Users\\jihut\\Downloads\\chromedriver_win32\\chromedriver.exe')  # Optional argument, if not specified will search path.)

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
        driver = webdriver.Chrome(options=chrome_options,
                                  service=Service(ChromeDriverManager().install()))

        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"})
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        driver.get(url)

        # 減少爬取頻率，避免被封
        # time.sleep(1)

        # 取得頁面內容
        page_source = driver.page_source
        driver.quit()

        return page_source
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None


def collect_video_links(html_content):
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


def fetch_jable_data(url):
    page_source = fetch_page_source(url, port=9222)
    # print(page_source)
    if not page_source:
        return []
    # 先記錄所有影片連結
    links = collect_video_links(page_source)
    return links


def fetch_video_details(link, port):
    link_url = link["url"]
    sub_page_source = fetch_page_source(link_url, port)
    if sub_page_source:
        sub_soup = BeautifulSoup(sub_page_source, "html.parser")
        avatar_tags = sub_soup.find_all("img", class_="avatar rounded-circle")
        avatar_tags2 = sub_soup.find_all(
            "span", class_="placeholder rounded-circle")
        model_names = [tag.get("data-original-title", "未知女優")
                       for tag in avatar_tags]
        model_names += [tag.get("data-original-title", "未知女優")
                        for tag in avatar_tags2]
        comment = []
        # 抓取留言評論
        comment_tags = sub_soup.find_all(
            "section", class_="comments pb-3 pb-lg-4")
        for comment_tag in comment_tags:
            comment_tag = comment_tag.find_all("div", class_="right")
            for c in comment_tag:
                comment.append(
                    c.find("p", class_="comment-text").find("span").text)

        # if model_names:
        #     print(f"片名: {link['title']}, 連結: {
        #           link_url}, 女優: {', '.join(model_names)}")
        #     if comment:
        #         print(f"留言評論: {', '.join(comment)}")

        # else:
        #     print(f"片名: {link['title']}, 連結: {link_url}, 女優: 未知女優")
        #     if comment:
        #         print(f"留言評論: {', '.join(comment)}")

        video_details = {
            "title": link["title"],
            "url": link_url,
            "models": model_names,
            "comments": comment
        }
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
    links = fetch_jable_data(url)
    if not links:
        print("找不到任何影片")
        return
    video_details_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        ports = [9222 + i for i in range(len(links))]
        results = executor.map(fetch_video_details, links, ports)
        for result in results:
            if result:
                video_details_list.append(result)
    with open("video_details.json", "w", encoding="utf-8") as f:
        json.dump(video_details_list, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    url = "https://jable.tv/models/saika-kawakita/"
    fetch_all_video_details(url)
