import datetime
import os
import re
from bs4 import BeautifulSoup
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi,en-US;q=0.7,en;q=0.3",
}


def scrape_single_article(url):
    """
    Hàm phân tích nội dung chuyên sâu, giữ lại hình ảnh và liên kết,
    loại bỏ triệt để mục lục điều hướng và ký tự rác.
    """
    try:
        print(f"\n[+] Đang xử lý bóc tách và tối ưu hóa cự ly văn bản: {url} ...")
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            print(f"✗ Không thể truy cập website. Mã lỗi: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Định vị khu vực nội dung chính
        content_zone = soup.find(["article", "main"])
        if not content_zone:
            content_zone = soup.find("div", class_=re.compile(r"(content|main-content|entry-content|post-body|article-content)", re.IGNORECASE))
        if not content_zone:
            content_zone = soup

        # Loại bỏ các thành phần đồ họa rác và kịch bản ẩn
        for svg in content_zone.find_all("svg"):
            svg.decompose()
        for btn in content_zone.find_all(["button", "script", "style", "noscript"]):
            btn.decompose()

        # Quét qua toàn bộ các thẻ chức năng cốt lõi
        elements = content_zone.find_all(["h2", "h3", "h4", "p", "li", "pre", "code", "a", "img"])
        
        reconstructed_html = []
        blacklist_words = ["on this page", "hướng dẫn sử dụng", "copy", "chia sẻ cài đặt android"]

        for el in elements:
            # Nếu là thẻ ảnh, giữ lại thuộc tính src để hiển thị
            if el.name == "img":
                src = el.get("src") or el.get("data-src")
                if src:
                    reconstructed_html.append(f'<img src="{src}" alt="Hình ảnh bài viết" />')
                continue

            text = el.get_text().strip()
            
            # Chặn các dòng trống, dấu chấm rác hoặc ký tự đơn lẻ
            if not text or text in [".", "...", "<>", ">", "<"] or len(text) < 2:
                continue
                
            # Kiểm tra bộ lọc từ khóa rác
            if any(word in text.lower() for word in blacklist_words):
                continue

            # Làm sạch các ký tự mũi tên thô
            text = re.sub(r"(➔|➜|➔|➡|➔|➦|➧|➨|箭头|►|▼|▲)", "", text)
            
            # Tái tạo cấu trúc HTML sạch, giữ lại thẻ liên kết nếu có
            if el.name in ["pre", "code"]:
                reconstructed_html.append(f"<pre><code>{text}</code></pre>")
            elif el.name in ["h2", "h3", "h4"]:
                reconstructed_html.append(f"<{el.name}>{text}</{el.name}>")
            elif el.name == "li":
                reconstructed_html.append(f"<li>{text}</li>")
            elif el.name == "a":
                href = el.get("href", "#")
                reconstructed_html.append(f'<p><a href="{href}" target="_blank">{text}</a></p>')
            else:
                reconstructed_html.append(f"<p>{text}</p>")

        content_html = "\n".join(reconstructed_html)
        return {"content": content_html, "url": url}

    except Exception as e:
        print(f"✗ Lỗi hệ thống khi bóc tách: {e}")
        return None


def export_to_blogger_html(posts, output_filename="blogger_export.html"):
    """
    Hàm xuất bản tệp HTML cấu trúc tràn viền 100%, nâng độ đậm font chữ,
    và ép các dấu chấm danh sách (bullet points) tiến sát lại gần chữ cái.
    """
    if not posts:
        print("✗ Không có dữ liệu để xuất file.")
        return

    # Tối ưu hóa CSS: Thiết lập margin-left và padding-left cho li để thu hẹp cự ly dấu chấm
    html_template = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blogger Pure Content</title>
    <style>
        /* Ép toàn bộ khung hiển thị căng tràn 100% màn hình, triệt tiêu lề trống */
        html, body { margin: 0 !important; padding: 0 !important; background-color: #ffffff; color: #000000 !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; -webkit-text-size-adjust: 100%; }
        .container { width: 100% !important; max-width: 100% !important; margin: 0 !important; padding: 12px !important; box-sizing: border-box; }
        .post-box { width: 100% !important; margin: 0 0 20px 0 !important; padding: 0 !important; }
        
        /* Cấu hình văn bản chữ diễn giải phóng to và đậm nét đen thuần */
        .post-content { font-size: 19px !important; color: #000000 !important; word-wrap: break-word; line-height: 1.7; font-weight: 450; }
        .post-content p { margin: 0 0 16px 0 !important; text-align: justify; color: #000000 !important; }
        
        /* [TỐI ƯU CỰ LY DẤU CHẤM]: Ép dấu chấm tiến sát lại gần chữ cái đầu dòng */
        .post-content li { margin-left: 18px !important; padding-left: 2px !important; margin-bottom: 10px; color: #000000 !important; list-style-position: outside; }
        
        /* Làm đậm và rõ các thẻ tiêu đề */
        .post-content h2 { font-size: 26px !important; color: #000000 !important; margin-top: 25px; margin-bottom: 15px; font-weight: 700; }
        .post-content h3 { font-size: 22px !important; color: #000000 !important; margin-top: 20px; margin-bottom: 15px; font-weight: 700; }
        
        /* Giữ định dạng liên kết rõ ràng */
        .post-content a { color: #0366d6 !important; text-decoration: underline; font-weight: 600; }
        
        /* Cấu hình hộp chứa code block rõ ràng, sắc nét */
        pre, code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace !important; background-color: #f6f8fa !important; color: #b31d28 !important; padding: 16px; border-radius: 6px; font-size: 15px; overflow-x: auto; display: block; white-space: pre; text-align: left; border: 1px solid #d1d5da; line-height: 1.5; margin: 15px 0; width: 100%; box-sizing: border-box; font-weight: normal; }
        
        /* Đảm bảo hình ảnh hiển thị tràn viền mượt mà */
        .post-content img { max-width: 100% !important; height: auto !important; display: block; margin: 15px auto; border-radius: 6px; border: 1px solid #e1e4e8; }
    </style>
</head>
<body>
    <div class="container">
"""

    html_content = html_template

    for post in posts:
        html_content += f"""
        <div class="post-box">
            <div class="post-content">
                {post['content']}
            </div>
        </div>
"""

    html_content += """
    </div>
</body>
</html>"""

    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n[✓] CẬP NHẬT THÀNH CÔNG: Tệp tin tối ưu đã lưu tại '{output_filename}'!")
        print("[!] Đã xử lý kéo sát cự ly dấu chấm đầu dòng (li) tiến gần chữ cái.")
    except Exception as e:
        print(f"✗ Lỗi ghi file HTML: {e}")


def main():
    print("=" * 60)
    print("    CÔNG CỤ XUẤT HTML TỐI ƯU CỰ LY PHÔNG CHỮ V2.1       ")
    print("=" * 60)

    scraped_data_list = []

    while True:
        url_input = input(
            "\nNhập URL bài viết cần cào (hoặc gõ 'exit' để đóng gói HTML): "
        ).strip()

        if url_input.lower() == "exit":
            break

        if not url_input.startswith("http"):
            print("✗ URL không hợp lệ!")
            continue

        result = scrape_single_article(url_input)
        if result:
            scraped_data_list.append(result)
            print("-> Đã xử lý tối ưu cấu trúc danh sách thành công.")

    if scraped_data_list:
        export_to_blogger_html(scraped_data_list)
    else:
        print("\n[-] Không có dữ liệu để xử lý.")


if __name__ == "__main__":
    main()
