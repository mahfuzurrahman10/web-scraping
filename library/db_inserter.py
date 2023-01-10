import datetime
import hashlib
import json

from slugify import slugify


from library.library import postgres_hybrid_insert, log_printer
from models.db_class import *

sites_column = ['md5_hash', 'url', 'name', 'seo_name', 'country_code', 'market', 'language']
sites_table_name = 'sites'
prices_column = ['product_md5_hash', 'format', 'format_size', 'currency', 'package', 'package_price', 'package_discounted_price',
                 'package_buying_price', 'unit_price', 'unit_discounted_price', 'unit_buying_price', 'stock', 'scraped_at']
prices_table_name = 'prices'
reviews_column = ['md5_hash', 'product_md5_hash', 'review_score', 'review_details', 'reviewer_name', 'reviewer_username', 'review_date', 'is_expert_review']
reviews_table_name = 'reviews'
ratings_column = ['md5_hash', 'product_md5_hash', 'rating_count', 'rating_average']
ratings_table_name = 'ratings'
products_column = ['md5_hash', 'site_md5_hash', 'name', 'name_en', 'seo_name', 'winery', 'winery_description', 'vineyard', 'brand', 'category', 'product_type',
                   'additional_product_type',
                   'production_method', 'variety', 'composition', 'description', 'description_en', 'vintage', 'alcohol_percentage', 'ph', 'sugar', 'acidity', 'taste',
                   'is_kosher', 'is_organic', 'is_vegan', 'allergens', 'closure_type', 'is_aggregated', 'wine_shop', 'distributor', 'country_origin', 'appellation', 'region',
                   'sub_region', 'town', 'sku', 'ean', 'product_url', 'image_url', 'image_bucket', 'tax_included', 'serving_temperature', 'sea_level_height', 'oenologist']
products_table_name = 'products'
time_ = datetime.datetime.now()


def sites_inserter(site_data: dict):
    site_url, site_name, country_code, market, language = site_data['url'], site_data['name'], site_data['country_code'], site_data['market'], site_data['language']
    site_data = [{
        'md5_hash': hashlib.md5(site_url.encode()).hexdigest(),
        'url': site_url,
        'name': site_name,
        'seo_name': slugify(site_name),
        'country_code': country_code,
        'market': market,
        'language': language
    }]
    postgres_hybrid_insert(site_data, Sites)


def prices_inserter(data: list):
    for items in data:
        items.update({
            'scraped_at': time_
        })
        for col in prices_column:
            if col not in items.keys():
                items[col] = None
    postgres_hybrid_insert(data, Prices, on_conflict=False)


def reviews_inserter(data: list):
    for items in data:
        items.update({
            'md5_hash': hashlib.md5(json.dumps(items, sort_keys=True).encode()).hexdigest()
        })
        for col in reviews_column:
            if col not in items.keys():
                items[col] = None
    postgres_hybrid_insert(data, Reviews)


def ratings_inserter(data: list):
    for items in data:
        items.update({
            'md5_hash': hashlib.md5(json.dumps(items, sort_keys=True).encode()).hexdigest()
        })
        for col in ratings_column:
            if col not in items.keys():
                items[col] = None
    postgres_hybrid_insert(data, Ratings)


def product_inserter(all_data: list, site_data: dict):
    site_url = site_data['url']
    site_md5_hash = hashlib.md5(site_url.encode()).hexdigest()
    reviews, ratings, prices = [], [], []
    for items in all_data:
        if items:
            product_md5_hash = hashlib.md5(f"{items['seo_name']}|{items['product_url']}".encode()).hexdigest()
            items.update({
                'md5_hash': product_md5_hash,
                'site_md5_hash': site_md5_hash
            })
            for col in products_column:
                if col not in items.keys():
                    items[col] = None

            if 'reviews' in items.keys():
                if items['reviews']:
                    for x in items['reviews']:
                        x.update({'product_md5_hash': product_md5_hash})
                    reviews += items['reviews']
                items.pop('reviews')

            if 'ratings' in items.keys():
                if items['ratings']:
                    for x in items['ratings']:
                        x.update({'product_md5_hash': product_md5_hash})
                    ratings += items['ratings']
                items.pop('ratings')

            if 'prices' in items.keys():
                if items['prices']:
                    for x in items['prices']:
                        x.update({'product_md5_hash': product_md5_hash})
                    prices += items['prices']
                items.pop('prices')

    log_printer(f'Inserting {len(all_data)} products')
    postgres_hybrid_insert(all_data, Products)
    log_printer(f'Inserting {len(reviews)} reviews')
    reviews_inserter(reviews)
    log_printer(f'Inserting {len(reviews)} ratings')
    ratings_inserter(ratings)
    log_printer(f'Inserting {len(prices)} prices')
    prices_inserter(prices)
