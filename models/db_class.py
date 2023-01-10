from sqlalchemy import Column, INTEGER, VARCHAR, FLOAT, String, JSON, TEXT, BOOLEAN, TIMESTAMP
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

# con


Base = declarative_base()


class Sites(Base):
    __tablename__ = 'sites'

    md5_hash = Column(String, primary_key=True)
    url = Column(VARCHAR(255))
    name = Column(VARCHAR(255))
    seo_name = Column(VARCHAR(255))
    country_code = Column(VARCHAR(255))
    market = Column(JSON)
    language = Column(JSON)

    # def __get_key__(self):
    #     return 'md5_hash'

    def __repr__(self):
        return self.md5_hash


class Products(Base):
    __tablename__ = 'products'

    md5_hash = Column(VARCHAR(255), primary_key=True)
    site_md5_hash = Column(VARCHAR(255))
    name = Column(VARCHAR(255))
    name_en = Column(VARCHAR(255))
    seo_name = Column(VARCHAR(255))
    winery = Column(VARCHAR(255))
    winery_description = Column(VARCHAR(255))
    vineyard = Column(VARCHAR(255))
    brand = Column(VARCHAR(255))
    category = Column(VARCHAR(255))
    product_type = Column(VARCHAR(255))
    additional_product_type = Column(VARCHAR(255))
    production_method = Column(TEXT)
    variety = Column(VARCHAR(255))
    composition = Column(VARCHAR(255))
    description = Column(TEXT)
    description_en = Column(TEXT)
    vintage = Column(VARCHAR(255))
    alcohol_percentage = Column(VARCHAR(255))
    ph = Column(VARCHAR(255))
    sugar = Column(VARCHAR(255))
    acidity = Column(VARCHAR(255))
    taste = Column(VARCHAR(255))
    is_kosher = Column(BOOLEAN)
    is_organic = Column(BOOLEAN)
    is_vegan = Column(BOOLEAN)
    allergens = Column(VARCHAR(255))
    closure_type = Column(VARCHAR(255))
    is_aggregated = Column(BOOLEAN)
    wine_shop = Column(VARCHAR(255))
    distributor = Column(VARCHAR(255))
    country_origin = Column(VARCHAR(255))
    appellation = Column(VARCHAR(255))
    region = Column(VARCHAR(255))
    sub_region = Column(VARCHAR(255))
    town = Column(VARCHAR(255))
    sku = Column(VARCHAR(255))
    ean = Column(VARCHAR(255))
    product_url = Column(VARCHAR(255))
    image_url = Column(JSON)
    image_bucket = Column(JSON)
    tax_included = Column(BOOLEAN)
    serving_temperature = Column(VARCHAR(255))
    sea_level_height = Column(VARCHAR(255))
    oenologist = Column(VARCHAR(255))

    def __repr__(self):
        return 'blah'


class Prices(Base):
    __tablename__ = 'prices'

    product_md5_hash = Column(VARCHAR(255), primary_key=True)
    format = Column(VARCHAR(255))
    format_size = Column(VARCHAR(255))
    currency = Column(VARCHAR(255))
    package = Column(VARCHAR(255))
    package_price = Column(FLOAT)
    package_discounted_price = Column(FLOAT)
    package_buying_price = Column(FLOAT)
    unit_price = Column(FLOAT)
    unit_discounted_price = Column(FLOAT)
    unit_buying_price = Column(FLOAT)
    stock = Column(FLOAT)
    scraped_at = Column(TIMESTAMP)

    def __repr__(self):
        return 'blah'


class Ratings(Base):
    __tablename__ = 'ratings'

    md5_hash = Column(VARCHAR, primary_key=True)
    product_md5_hash = Column(VARCHAR(255))
    rating_count = Column(INTEGER)
    rating_average = Column(FLOAT(precision=2))

    def __repr__(self):
        return 'blah'


class Reviews(Base):
    __tablename__ = 'reviews'

    md5_hash = Column(VARCHAR, primary_key=True)
    product_md5_hash = Column(VARCHAR(255))
    review_score = Column(FLOAT)
    review_details = Column(TEXT)
    reviewer_name = Column(VARCHAR(255))
    reviewer_username = Column(VARCHAR(255))
    review_date = Column(TIMESTAMP)
    is_expert_review = Column(BOOLEAN)

    def __repr__(self):
        return 'blah'


class Shops(Base):
    __tablename__ = 'shops'

    merchant_id = Column(VARCHAR(255), primary_key=True)
    merchant_name = Column(VARCHAR(255))
    email = Column(VARCHAR(255))
    phone_number = Column(VARCHAR(255))
    delivery_area = Column(JSON)
    merchant_type = Column(VARCHAR(255))
    premise_type = Column(VARCHAR(255))
    aggregation_type = Column(VARCHAR(255))
    max_delivery_time = Column(INTEGER)
    pickup = Column(BOOLEAN)
    delivery = Column(BOOLEAN)
    shipping = Column(BOOLEAN)
    delivery_hours = Column(JSON)
    business_hours = Column(JSON)
    last_inventory_upload = Column(TIMESTAMP)
    store_id = Column(VARCHAR(255))
    store_web_id = Column(VARCHAR(255))
    website_url = Column(VARCHAR(255))
    primary_domain = Column(VARCHAR(255))
    additional_domains = Column(JSON)
    storefront_widget_url = Column(VARCHAR(255))
    full_address = Column(VARCHAR(255))
    location = Column(JSON)
    district = Column(VARCHAR(255))
    province = Column(VARCHAR(255))
    street_address = Column(VARCHAR(255))
    zipcode = Column(VARCHAR(255))
    state = Column(VARCHAR(255))
    city = Column(VARCHAR(255))
    country_code = Column(VARCHAR(255))
    apt = Column(VARCHAR(255))

    def __repr__(self):
        return 'blah'
