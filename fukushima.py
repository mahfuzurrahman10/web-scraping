import requests
from bs4 import BeautifulSoup
from slugify import slugify

import traceback
from library.db_inserter import sites_inserter, product_inserter
from library.img_parser import image_name_parser
from library.library import send_slack_notification, log_printer, requests_get, notification_lite

cookies = {
    'colorme_reference_token': '152109e1270042be8981aaf28cd0ff1e',
    'colorme_browsing_history': 'a%3A2%3A%7Bi%3A0%3Bs%3A9%3A%22136454730%22%3Bi%3A1%3Bs%3A7%3A%222121586%22%3B%7D',
    'colorme_PHPSESSID': 'c3bd05ff450edeecf83c733d5ea6a9f2',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    # Requests sorts cookies= alphabetically
    # 'Cookie': 'colorme_reference_token=152109e1270042be8981aaf28cd0ff1e; colorme_browsing_history=a%3A2%3A%7Bi%3A0%3Bs%3A9%3A%22136454730%22%3Bi%3A1%3Bs%3A7%3A%222121586%22%3B%7D; colorme_PHPSESSID=c3bd05ff450edeecf83c733d5ea6a9f2',
    'Referer': 'http://fukushimasaketen.com/?mode=cate&cbid=112098&csid=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
}

response = requests.get('http://fukushimasaketen.com/', cookies=cookies, headers=headers, verify=False)


# %%
def get_all_category(cbid):
    params = {
        'mode': 'cate',
        'cbid': cbid,
        'csid': '0',
    }

    category_response = requests.get('http://fukushimasaketen.com/', params=params, cookies=cookies, headers=headers,
                                     verify=False)
    soup_category = BeautifulSoup(category_response.text, 'html.parser')
    return soup_category


# %%
def get_page_number(product_soup):
    try:
        if product_soup.find('dt', class_='pagenavi'):
            total_items = int(product_soup.find('dt', class_='pagenavi').find_all('span')[0].text)
            items_per_page = int(product_soup.find('dt', class_='pagenavi').find_all('span')[-1].text)
            print(round(total_items / items_per_page))
            return round(total_items / items_per_page)
    except:
        pass


# %%
def get_product_id(pid):
    params = {
        'pid': pid,
    }
    pid_response = requests.get('http://fukushimasaketen.com/', params=params, cookies=cookies, headers=headers,
                                verify=False)
    soup_pid = BeautifulSoup(pid_response.text, 'html.parser')
    description = soup_pid.find('div', {"id": 'detail'}).find_all('dd')[-1].find('div').get_text(strip=True)
    return description


# %%
def get_sub_category(cbid, csid):
    params = {
        'mode': 'cate',
        'cbid': cbid,
        'csid': csid,
    }
    product_response = requests.get('http://fukushimasaketen.com/', params=params, cookies=cookies, headers=headers,
                                    verify=False)
    soup_product = BeautifulSoup(product_response.text, 'html.parser')
    return soup_product


# %%
def get_price_details(product_data):
    prices = []
    price = {
        'format': 'bottle',
        'currency': 'JPY'
    }
    details = product_data.find('div', class_='caption').find('p', class_='item_price').get_text(strip=True)
    product_des = product_data.find('div', class_='caption').find('p', class_='item_explain').get_text(strip=True)
    description = product_des.split(',')

    # package prices
    try:
        price['package_price'] = details.split('円')[0]
        price['unit_price'] = details.split('円')[0]
    except:
        pass

    # formate size
    capacity = '容量'
    contents = '内容量'
    for text in description:
        try:
            if capacity in text:
                price['format_size'] = text.split(None)[-1]
        except:
            pass
    prices.append(price)
    return prices


# %%
def get_product_data(product_soup):
    response_url = 'http://fukushimasaketen.com/'
    try:
        category_type = product_soup.find('div', class_='pankuzu').get_text(strip=True)
        category = category_type.split('»')[1].replace('\u3000', " ")
        product_type = category_type.split('»')[2].replace('\u3000', " ")

        for product_data in product_soup.find_all('dd'):
            try:
                item = {
                    'tax_included': True
                }

                # item image
                main_img_url = product_data.find('div', class_='cat_item_img').find('img')['src']
                main_img_name = main_img_url.split('/')[-1].split('?')[0]
                image_url = main_img_url.split('?')[0]
                main_img_url = f"{image_url}"
                item['image_url'] = [main_img_url]
                item['image_bucket'] = [image_name_parser(main_img_name, FOLDER_NAME)]
            except:
                pass

            # item url and name
            try:
                row_url = product_data.find('div', class_='caption').find('p', class_='item_title').find('a')['href']
                item['sku'] = row_url.split('=')[-1]
                item['product_url'] = f'{response_url}{row_url}'
            except:
                pass

            try:
                row_product = product_data.find('div', class_='caption').find('p', class_='item_title').text
                item['name'] = row_product.split('\n')[0].replace('\u3000', " ")
                item['seo_name'] = slugify(item['name'])
            except:
                pass

            # item description
            try:
                pid_url = product_data.find('div', class_='caption').find('p', class_='item_title').find('a')['href']
                pid = pid_url.split('=')[-1]
                description = get_product_id(pid)
                item['description'] = description
            except:
                pass

            # item explain
            try:
                details = product_data.find('div', class_='caption').find('p', class_='item_explain').get_text(
                    strip=True)
                item_details = details.split(',')

                alcohol = 'アルコール'
                origin_country = '産'
                # origin_palace   = '原産地'
                temperature = '飲み頃温度'

                for text in item_details:
                    try:
                        if alcohol in text:
                            item['alcohol_percentage'] = text.split(None)[-1].replace('度', '').replace('%', '')
                        elif temperature in text:
                            item['serving_temperature'] = text.split('度')[-1].replace('\u3000', '')
                        elif origin_country in text:
                            item['winery'] = text.split('国')[-1].replace('\u3000', '')
                        else:
                            pass
                    except:
                        pass
            except:
                pass

            # item type and category
            try:
                item['category'] = category
                item['product_type'] = product_type
            except:
                pass

            # price details
            try:
                prices = get_price_details(product_data)
                item['prices'] = prices
                # print(item)
            except:
                pass
    except Exception as e:
        print(e)
    return item


# %%
if __name__ == "__main__":
    site_data = {
        'url': 'http://fukushimasaketen.com/',
        'name': "福島酒店",
        'country_code': 'JP',
        'market': ['JP'],
        'language': ['ja'],
    }
    try:
        OUTPUT = []
        FOLDER_NAME = 'fukushima_img'
        category_id = ['119398', '124158', '112098', '117292', '109343', '124159']

        # product data for all category
        for cbid in category_id:
            category_soup = get_all_category(cbid)
            for data in category_soup.find_all('div', class_='caption'):
                sub_category_name = data.get_text(strip=True)
                sub_category_link = data.find_all('a', href=True)
                for value in sub_category_link:
                    sub_category_id = value.attrs['href'].split('=')[-1]
                    product_soup = get_sub_category(cbid, sub_category_id)
                    pages = get_page_number(product_soup)
                    if pages is not None:
                        for page in range(1, pages + 1):
                            params = {
                                'mode': 'cate',
                                'cbid': cbid,
                                'csid': sub_category_id,
                                'page': page
                            }
                            response = requests_get('http://fukushimasaketen.com/', params=params, cookies=cookies,
                                                    headers=headers, verify=False)
                            soup = BeautifulSoup(response.text, 'html.parser')
                            product_response = get_product_data(soup)
                            OUTPUT.append(product_response)

        # data insert
        sites_inserter(site_data)
        product_inserter(OUTPUT, site_data)

        # upload_image(FOLDER_NAME)
        # notification_lite(f'{len(OUTPUT)} rows inserted/updated', site_data['name'])
    except Exception as e:
        # notification_lite("Scraping failed", site_data['name'])
        traceback.print_exc()
