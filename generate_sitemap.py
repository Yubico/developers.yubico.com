import os
import time
import sys

OUTPUT_DIR = "htdocs/dist/"
BASE_URL = "https://developers.yubico.com"

def generate_sitemap():
    pages = []

    # Walk through the generated site files
    for root, _, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith(".html"):
                url_path = os.path.relpath(os.path.join(root, file), OUTPUT_DIR)
                lastmod = time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(os.path.join(root, file))))
                pages.append({"url": "/" + url_path, "lastmod": lastmod})

    # Generate XML sitemap
    sitemap_entries = []
    for page in pages:
        entry = '<url><loc>{}{}</loc><lastmod>{}</lastmod></url>'.format(BASE_URL, page["url"], page["lastmod"])
        sitemap_entries.append(entry)

    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{}
</urlset>""".format("\n".join(sitemap_entries))

    # Save sitemap.xml
    sitemap_path = os.path.join(OUTPUT_DIR, "sitemap.xml")
    
    # Python 2.x: Use "wb" for binary mode
    mode = "wb" if sys.version_info[0] < 3 else "w"
    with open(sitemap_path, mode) as f:
        f.write(sitemap_xml)

    print("Generated sitemap at {}".format(sitemap_path))

def main():
    generate_sitemap()

if __name__ == "__main__":
    main()
