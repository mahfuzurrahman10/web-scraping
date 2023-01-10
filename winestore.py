import traceback
import requests
from bs4 import BeautifulSoup
from slugify import slugify

from urllib3.exceptions import InsecureRequestWarning

from library.db_inserter import sites_inserter, product_inserter
from library.img_parser import image_name_parser, upload_image
from library.library import send_slack_notification, log_printer, requests_get, notification_lite

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'If-Modified-Since': 'Mon, 19 Sep 2022 08:00:46 GMT',
    'Referer': 'https://winestore.jp/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

#%%
def get_site_details() :
    response = requests.get('https://winestore.jp', headers=headers)
    site_soup = BeautifulSoup(response.text, 'html.parser')
    try:
        site=[]
        # original store name Wassy'sについて
        store_name = "Online Wassy's"
        language = site_soup.find('html')['lang']
        site_details = {
            'url': 'https://winestore.jp',
            'name': store_name,
            'seo_name': slugify(store_name),
            'country_code':['JP'],
            'market': ['ja'],
            'language': [language],
        }
        site.append(site_details)
        return site
    except:
        pass
#%%
def get_max_page():
    response = requests_get('https://winestore.jp/c/gr411', headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    max_page = int(soup.find('div', class_='fs-c-pagination').find_all('a')[-2].text)
    return max_page + 1
#%%
def get_product_data(link):
    product_response = requests_get(f"https://winestore.jp{link}", headers=headers)
    product_soup = BeautifulSoup(product_response.text, 'html.parser')
    item = {
        'product_url' : f"https://winestore.jp{link}",
        'tax_included' : True,
        'category' : 'wine'
    }

    # image
    try:
        main_img_url =  product_soup.find('div','fs-c-productMainImage__image').find('img')['src']
        main_img_name = main_img_url.split('/')[-1].split('?')[0]
        main_img_url = f"https://static.millesima.com/s3/attachements/h531px/{main_img_name}.png"
        item['image_url'] = [main_img_url]
        item['image_bucket'] = [image_name_parser(main_img_name, FOLDER_NAME)]
    except:
        pass


    try:
        # item['name_en'] = 'Kimura Cellars Sauvignon Blanc Marlborough Home Block Vineyard [2022]'
        item['name'] = product_soup.find('span', class_='fs-c-productNameHeading__name').get_text(strip=True)
        item['seo_name'] = slugify(product_soup.find('span', class_='fs-c-productNameHeading__name').get_text(strip=True))
        item['description'] = product_soup.find('div',class_='fs-p-productDescription fs-p-productDescription--full').get_text(strip=True)
    except Exception as e:
        print(e)
        pass

    try:
        item['sku'] = product_soup.find('span', class_='fs-c-productNumber__number').text
    except:
        pass

    try:
        for table_data in product_soup.find('table', class_='productSpec_Tbl').find_all('tr'):
            if '生産者' in table_data.find('th').text:
                item['winery'] = table_data.find('td').text
            elif '生産年' in table_data.find('th').text:
                item['vintage'] = table_data.find('td').text
            elif 'タイプ' in table_data.find('th').text:
                item['taste'] = table_data.find('td').find_all('span')[-1].get_text(strip=True).split(' ')[1]
                item['product_type'] = table_data.find('td').find_all('span')[0].text.split(' ')[1]
            elif '生産地' in table_data.find('th').text:
                item['country_origin'] = table_data.find('td').text.split('/')[0]
                item['region'] = table_data.find('td').text.split('/')[1]

    except:
        pass

    # reviews

    try:
        reviews = []
        for table_data in product_soup.find('table', class_='productSpec_Tbl').find_all('tr'):
            if '評価・得点' in table_data.find('th').text:
                for review_data in table_data.find('td').find_all('span'):
                    try:
                        review = {
                            'reviewer_name': review_data.text.split('：')[0],
                            'review_score': float(review_data.text.split('：')[1].replace('点','').replace('+','').replace('、','')) / 20 ,
                        }
                        reviews.append(review)
                    except:
                        for review_split in review_data.get_text(strip=True).split('、'):
                            review = {
                                'reviewer_name': review_split.split('：')[0],
                                'review_score': float(review_split.split('：')[1].replace('点','').replace('+','').replace('、','')) / 20 ,
                            }
                            reviews.append(review)
        item['reviews'] = reviews
    except:
        pass

    # price
    try:
        prices = []
        price = {
            'format' : 'bottle',
            'currency' : 'JPY'
        }

        if product_soup.find('div', class_='fs-c-productPrice fs-c-productPrice--listed'):
            price['package_price'] = product_soup.find('span', class_='fs-c-productPrice__main__price fs-c-price').get_text(strip=True).replace('¥','').replace(',','')
            price['unit_price'] = product_soup.find('span', class_='fs-c-productPrice__main__price fs-c-price').get_text(strip=True).replace('¥','').replace(',','')

            price['package_discounted_price'] = product_soup.find('div', class_='fs-c-productPrice fs-c-productPrice--selling').find('span',class_='fs-c-productPrice__main__price fs-c-price').get_text(strip=True).replace('¥','').replace(',','')
            price['unit_discounted_price'] = product_soup.find('div', class_='fs-c-productPrice fs-c-productPrice--selling').find('span',class_='fs-c-productPrice__main__price fs-c-price').get_text(strip=True).replace('¥','').replace(',','')
        else:
            try:
                price['package_price'] = product_soup.find('span',class_='fs-c-productPrice__main__price fs-c-price').get_text(strip=True).replace('¥','').replace(',','')
                price['unit_price'] = product_soup.find('span',class_='fs-c-productPrice__main__price fs-c-price').get_text(strip=True).replace('¥','').replace(',','')
            except:
                pass

        try:
            for table_data in product_soup.find('table', class_='productSpec_Tbl').find_all('tr'):
                if '容量' in table_data.find('th').text:
                    price['format_size'] = table_data.find('td').text
        except Exception as e:
            print(e)
            pass

        try:
            price['stock'] = product_soup.find('div', class_='fs-c-productStock').get_text(strip=True).split(' in')[0].replace('在庫数','')
        except:
            pass
        prices.append(price)
        item['prices'] = prices
    except:
        pass

    return item
#%%
if __name__ == "__main__":
    site_data = {
        'url': 'https://winestore.jp/',
        'name': "Wassy'sについて",
        'country_code': 'JP',
        'market': ['JP'],
        'language': ['ja'],
    }
    try:
        OUTPUT = []
        FOLDER_NAME = 'winestore_img'
        max_page = get_max_page()
        for page in range(1, max_page):
            params = {
                'page': page,
                'sort': 'latest',
            }
            response = requests_get('https://winestore.jp/c/gr411', params=params, headers=headers)
            page_soup = BeautifulSoup(response.text, 'html.parser')

            for product in page_soup.find('div', class_='fs-c-productList__list').find_all('article',class_='fs-c-productList__list__item fs-c-productListItem'):
                link = product.find('h2').find('a')['href']
                OUTPUT.append(get_product_data(link))

        sites_inserter(site_data)
        product_inserter(OUTPUT, site_data)

        # upload_image(FOLDER_NAME)
        # notification_lite(f'{len(OUTPUT)} rows inserted/updated', site_data['name'])
    except Exception as e:
        # notification_lite("Scraping failed", site_data['name'])
        traceback.print_exc()