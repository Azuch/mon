import telepot
import psutil
import time

# Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual Telegram bot token
bot = telepot.Bot('7143459072:AAGsH5x6A3XxYmgdywiUVsXbhRzovN3M_s0')

def check_process(pid):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        if proc.info['pid'] == pid:
            return True, proc.info['cmdline']
    return False, None

def send_message(chat_id, message):
    bot.sendMessage(chat_id, message)

def monitor_process(chat_id, pid, command):
    while True:
        done, _ = check_process(pid)
        if not done:
            send_message(chat_id, f"The process {pid} with command '{command}' is done")
            break
        time.sleep(5)  # Check every 5 seconds

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'text':
        command = msg['text']
        if command.isdigit():
            pid = int(command)
            exists, command = check_process(pid)
            if exists:
                send_message(chat_id, f"Process {pid} with command '{command}' is running")
                monitor_process(chat_id, pid, command)
            else:
                send_message(chat_id, f"No process found with PID {pid}")

bot.message_loop(handle)

# Keep the program running
while True:
    time.sleep(10)
(venv) root@2cpu:~# vim 01.py 
(venv) root@2cpu:~# screen -r mon
[detached from 6751.mon]
(venv) root@2cpu:~# vim 01.py 
(venv) root@2cpu:~# cat 01.py 
import requests
from lxml import html
import asyncio
import aiohttp
import aiofiles
from urllib.parse import urljoin
import os
import subprocess
import telepot
import time

semaphore = asyncio.Semaphore(50)

bot = telepot.Bot('7143459072:AAGsH5x6A3XxYmgdywiUVsXbhRzovN3M_s0')
chat_id = 888252097

def send_message(message):
    bot.sendMessage(chat_id, message)

async def download_image(url, filename, session):
    async with semaphore:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise aiohttp.ClientError(f"{url} Failed to download image: {response.status}")

                content = await response.read()
                async with aiofiles.open(filename, 'wb') as f:
                    await f.write(content)
            print(f"Image downloaded: {filename}")
        except Exception as e:
            async with aiofiles.open('error_log.txt', 'a') as f:
                await f.write(f"Failed to download {url}: {str(e)}\n")
            print(f"Failed to download {url}: {str(e)}")

def extract_image_links(url):
    # Send a GET request to the URL
    response = requests.get(url)
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        tree = html.fromstring(response.content)
        # Extract image links using XPath
        img_urls = tree.xpath('//article[@class="chapter-detail"]//img/@src')
        return img_urls
    else:
        print(f"{url} Failed to retrieve the page. Status code: {response.status_code}")
        return []

def extract_chapter_link(manga_url):
    response = requests.get(manga_url)
    if response.status_code == 200:
        # Parse the HTML content
        tree = html.fromstring(response.content)
        # Extract chapter links using XPath
        rel_chapter_urls = tree.xpath('//article[@class="list-chapter"]//a/@href')
        base_url = 'https://m.blogtruyen.vn'
        chapter_urls = [urljoin(base_url, url) for url in rel_chapter_urls]
        chapter_urls.reverse()
        return chapter_urls
    else:
        print(f"{manga_url} Failed to retrieve the page. Status code: {response.status_code}")
        return []

async def download_chapter(url, chapter_name, manga_name, session):
    os.makedirs(os.path.join(manga_name, chapter_name), exist_ok=True)
    img_links = extract_image_links(url)
    tasks = [download_image(link, os.path.join(manga_name, chapter_name, f"{index}.jpg"), session=session) for index, link in enumerate(img_links)]
    await asyncio.gather(*tasks)

async def main():
    with open('links.txt') as f:
        manga_urls = [line.strip() for line in f if line.strip()]  # Remove newline and whitespace, ignore empty lines    
    for manga_url in manga_urls:
        manga_name = manga_url.split('/')[-1]
        os.makedirs(manga_name, exist_ok=True)
        chapter_urls = extract_chapter_link(manga_url)
        timeout = aiohttp.ClientTimeout(total=2)  # Adjusted timeout to 60 seconds

        async with aiohttp.ClientSession(timeout=timeout) as session:
            for index, chapter_url in enumerate(chapter_urls):
                await download_chapter(chapter_url, f"chapter-{index}", manga_name, session)
                await asyncio.sleep(3)
        print(f"Done for {manga_name}")
        # After downloading all chapters, archive the manga directory
        #tar_command = f"tar -czf {manga_name}.tgz {manga_name}"
        #subprocess.run(tar_command, shell=True, check=True)

        # Upload the compressed file to OneDrive using rclone
        #rclone_command = f"rclone copy --transfers=100 ./{manga_name}.tgz onedrive:manga/"
        #subprocess.run(rclone_command, shell=True, check=True)
        #print(f"{manga_name} archive uploaded to OneDrive.")

if __name__ == "__main__":
    try:
        start_time = time.time()
        start_time_human = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stop_time))
        send_message(f"Manga downloader program has started at {start_time_human}")
        asyncio.run(main())
    except Exception as e:
        send_message(f"The manga downloader program has encountered an error: {e}")
    finally:
        stop_time = time.time()
        stop_time_readable = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stop_time))
        duration = stop_time - start_time
        duration_readable = time.strftime('%H:%M:%S', time.gmtime(duration))
        send_message(f"Manga downloader program has stopped at {stop_time_readable}, Duration: {duration_readable}")
