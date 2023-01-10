import json
import requests
from bs4 import BeautifulSoup
from slugify import slugify
import traceback
from library.db_inserter import sites_inserter, product_inserter
from library.img_parser import image_name_parser, upload_image
from library.library import send_slack_notification, log_printer, requests_get, notification_lite

headers = {
    'authority': 'api.store.enoteca.co.jp',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'origin': 'https://www.enoteca.co.jp',
    'referer': 'https://www.enoteca.co.jp/',
    'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
}


# %%
def get_all_data(products):
    params = {
        'wt': 'json',
        'q': 'mst:product AND product_category_sm:1 AND color_id_i:(1 OR 2 OR 3 OR 5 OR 6 OR 7 OR 14) NOT '
             'product_type_s:プリムール NOT sales_start_d:[2022-09-21T17:05:29.221Z TO *] NOT sales_end_d:[* TO '
             '2022-09-21T17:05:29.221Z]  NOT display_flag_i:0',
        'sort': 'has_stock_flag_i desc,  recommend_flag_i asc,producer_weight_i desc,lowest_price_general_i asc,'
                'score desc',
        'rows': products,
    }
    response = requests_get('https://api.store.enoteca.co.jp/select', params=params, headers=headers)
    return response.json()['response']


# %%
def get_total_product():
    params = {
        'wt': 'json',
        'q': 'mst:product AND product_category_sm:1 AND color_id_i:(1 OR 2 OR 3 OR 5 OR 6 OR 7 OR 14) NOT '
             'product_type_s:プリムール NOT sales_start_d:[2022-09-21T17:05:29.221Z TO *] NOT sales_end_d:[* TO '
             '2022-09-21T17:05:29.221Z]  NOT display_flag_i:0',
        'sort': 'has_stock_flag_i desc,  recommend_flag_i asc,producer_weight_i desc,lowest_price_general_i asc,'
                'score desc',
        'rows': '40',
    }
    response = requests_get('https://api.store.enoteca.co.jp/select', params=params, headers=headers)
    log_printer(f"total page found: {response.json()['response']['numFound']}")
    return response.json()['response']['numFound']


# %%
def get_review_data(product_code):
    product_response = requests_get(f"https://api.store.enoteca.co.jp/api/v1/products/{product_code}", headers=headers)
    review_group_id = product_response.json()['review_settings']['review_group_id']
    # rating_avg = product_response.json()['review_settings']['rating_average']
    total_review = product_response.json()['review_settings']['review_total']

    params = {
        'limit': total_review,
        'page': '1',
        'sort': 'created_at',
        'status': 'approved',
    }
    review_response = requests.get(f"https://api.store.enoteca.co.jp/api/v1/reviews/{review_group_id}", params=params,
                                   headers=headers)
    reviews = []
    review_data = review_response.json()['data']
    try:
        for value in review_data:
            review_details = {
                'reviewer_name': value["nickname"],
                'review_details': value["body"],
                'review_score': value["rating"],
                'review_date': value["created_at"],
            }
            reviews.append(review_details)
    except:
        pass

    return reviews


# %%

def get_products_data(value):
    try:
        product_details = {
            'tax_included': True,
        }
        try:
            product_details['name'] = value["product_name_s"]
            product_details['seo_name'] = slugify(value["product_name_s"])
        except:
            pass
        try:
            product_details['name_en'] = value["product_name_english_s"]
        except:
            pass

        try:
            product_details['sku'] = value["product_code_s"]
        except:
            pass
        # description
        try:
            product_details['product_url'] = value["product_url_s"]
            product_details['category'] = value["category_s"]
            product_details['product_type'] = value["product_type_s"]
        except:
            pass
        try:
            product_details['description'] = value["product_description_tm"]
        except:
            pass
        try:
            product_details['closure_type'] = value["stopper_s"]
        except:
            pass
        # region
        try:
            product_details['country_origin'] = value["country_s"]
        except Exception as e:
            print(e)
        try:
            product_details['region'] = value["area2_id_name_s"].split('_')[-1]
        except:
            pass
        # image
        try:
            main_img_name = f"{value['main_image_url_s'].split(' / ')[-1]}"
            product_details['image_url'] = [f'{value["main_image_url_s"]}']
            product_details['image_bucket'] = [image_name_parser(main_img_name, FOLDER_NAME)]
        except:
            pass
        # winery
        try:
            product_details['winery'] = value["producer_name_english_s"]
        except:
            pass
        try:
            product_details['winery_description'] = value["product_description_tm"]
        except:
            pass
        try:
            if value['latest_produced_year_i'] != value["earliest_produced_year_i"]:
                product_details['vintage'] = f'{value["earliest_produced_year_i"]}/{value["latest_produced_year_i"]}'
            else:
                product_details['vintage'] = value["earliest_produced_year_i"]
        except:
            pass
        # product prices
        try:
            prices = []
            price = {
                'format': 'bottle',
                'format_size': f'{value["size_amount_i"]} {value["size_unit_s"]}',
                'currency': 'JPY',
            }
        except:
            pass
        try:
            price['stock'] = value["has_stock_flag_i"]
        except:
            pass
        try:
            price['package'] = '1'
            price['package_price'] = value["highest_price_general_i"]
        except:
            pass
        try:
            if value["lowest_price_general_i"] != value["highest_price_general_i"]:
                price['package_discounted_price'] = value["lowest_price_general_i"]
            else:
                pass
        except:
            pass
        try:
            price['unit_price'] = value["highest_price_general_i"]
        except:
            pass
        prices.append(price)
        product_details['prices'] = prices

        # rating
        try:
            ratings = []
            rating_details = {
                'rating_count': value['review_count_i'],
                'rating_average': value['sort_r_rating_r'],
            }
            ratings.append(rating_details)
            product_details["ratings"] = ratings
        except:
            pass

        # reviews
        try:
            product_details["reviews"] = get_review_data(value['product_code_s'])
        except:
            pass
    except Exception as e:
        print(e)
    return product_details


# %%
if __name__ == "__main__":
    site_data = {
        'url': 'https://www.enoteca.co.jp/',
        'name': "Enotecaonline",
        'country_code': 'JP',
        'market': ['JP'],
        'language': ['ja'],
    }
    try:
        OUTPUT = []
        FOLDER_NAME = 'enoteca-img'

        total_products = get_total_product()
        json_data = get_all_data(total_products)
        # product details
        for json_data in json_data["docs"]:
            OUTPUT.append(get_products_data(json_data))
        sites_inserter(site_data)
        product_inserter(OUTPUT, site_data)
        # print(OUTPUT)
        # upload_image(FOLDER_NAME)
        # notification_lite(f'{len(OUTPUT)} rows inserted/updated', site_data['name'])
    except Exception as e:
        # notification_lite("Scraping failed", site_data['name'])
        traceback.print_exc()
