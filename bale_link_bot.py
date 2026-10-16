import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ----------------- تنظیمات -----------------
BOT_TOKEN = "112797179:uLmhDhzZgfAhXpR7Ks44XtqVsguqqbE7CvE"
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"

def fetch_page_info(url):
    """استخراج عنوان، عکس شاخص و توضیحات از لینک"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # عنوان
        title_tag = soup.find("meta", property="og:title") or soup.find("title")
        title = title_tag["content"] if title_tag and title_tag.get("content") else (title_tag.text if title_tag else "پست جدید")
        
        # عکس
        image_tag = soup.find("meta", property="og:image")
        image_url = image_tag["content"] if image_tag else None
        if image_url:
            image_url = urljoin(url, image_url)
            
        # توضیحات
        desc_tag = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
        description = desc_tag["content"] if desc_tag and desc_tag.get("content") else ""

        return {
            "title": title.strip(),
            "image_url": image_url,
            "description": description.strip(),
            "link": url
        }
    except Exception as e:
        print("خطا در پردازش لینک:", e)
        return None

def send_bale_message(chat_id, data):
    """ساخت و ارسال پست آماده به کاربر"""
    caption = f"📌 **{data['title']}**\n\n"
    if data['description']:
        caption += f"{data['description']}\n\n"
    caption += f"🔗 [مشاهده کامل در سایت]({data['link']})"
    
    if data['image_url']:
        url = f"{BASE_URL}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": data['image_url'], "caption": caption, "parse_mode": "Markdown"}
    else:
        url = f"{BASE_URL}/sendMessage"
        payload = {"chat_id": chat_id, "text": caption, "parse_mode": "Markdown"}

    requests.post(url, json=payload)

def main():
    offset = 0
    print("🤖 ربات بله روشن شد و آماده دریافت لینک است...")
    
    while True:
        try:
            # دریافت پیام‌های جدید (Long Polling)
            res = requests.get(f"{BASE_URL}/getUpdates", params={"offset": offset, "timeout": 20}).json()
            
            if res.get("ok") and res.get("result"):
                for update in res["result"]:
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")

                    if text.startswith("http://") or text.startswith("https://"):
                        requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": "⏳ در حال ساخت پست..."})
                        
                        page_data = fetch_page_info(text)
                        if page_data:
                            send_bale_message(chat_id, page_data)
                        else:
                            requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": "❌ نتوانستم اطلاعات این لینک را دریافت کنم."})
                    elif text == "/start":
                        requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": "سلام! فقط کافیست لینک محصول یا پست سایت را برای من بفرستی تا پست کانال بله را برایت بسازم."})

        except Exception as e:
            print("خطا در ارتباط با سرور:", e)
            time.sleep(3)

if __name__ == "__main__":
    main()
