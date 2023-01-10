import glob
import json
import os
from threading import Thread

import boto3
import requests
from magic import Magic
from psycopg2.extras import RealDictCursor

from config import IMG_ROOT_FOLDER, AWS_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET, BRIGHT_DATA_UNBLOCKED_PROXY
from library.library import log_printer, chunkify, generate_postgres


def create_img_folder(folder_name: str) -> None:
    if not os.path.exists(os.path.join(os.getcwd(), IMG_ROOT_FOLDER)):
        os.mkdir(IMG_ROOT_FOLDER)
    if not os.path.exists(os.path.join(os.getcwd(), IMG_ROOT_FOLDER, folder_name)):
        os.mkdir(f'{IMG_ROOT_FOLDER}/{folder_name}')


def delete_images(folder_name: str):
    images = glob.glob(f"{IMG_ROOT_FOLDER}/{folder_name}/*")
    for i in images:
        os.remove(i)

    log_printer('Images deleted')


def image_name_parser(file_name: str, folder_name: str):
    file_name_ = f'{IMG_ROOT_FOLDER}/{folder_name}/{file_name}'
    return file_name_


def store_image(url: str, file_name: str):
    if len(glob.glob(file_name)) > 0:
        return file_name

    try:
        res = requests.get(url, stream=True, verify=False, timeout=10)
        if res.status_code == 403:
            raise Exception
    except Exception as e:
        try:
            res = requests.get(url, stream=True, verify=False, timeout=10, proxies=BRIGHT_DATA_UNBLOCKED_PROXY)
        except Exception as e:
            log_printer(f'Cant download {url}, error: {e}')
            return None

    open(file_name, 'wb').write(res.content)
    return file_name


def get_images_to_download(folder_name: str):
    to_return = {}
    db = generate_postgres()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    query = f"select image_url, image_bucket from products where image_bucket::text like '%{IMG_ROOT_FOLDER}/{folder_name}%';"
    cursor.execute(query)
    x = cursor.fetchall()
    for i in x:
        img_url, img_bucket = i['image_url'], i['image_bucket']
        for j, items in enumerate(img_url):
            to_return[img_bucket[j]] = img_url[j]
    return to_return


def get_boto3_client():
    session = boto3.session.Session()
    return session.client('s3',
                          endpoint_url=AWS_ENDPOINT_URL,
                          aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


def boto3_uploader(file_list: list) -> None:
    client = get_boto3_client()
    file_list = {k: v for element in file_list for k, v in element.items()}
    for file in file_list:
        x = store_image(url=file_list[file], file_name=file)
        if x:
            log_printer(x)
            content_type = Magic(mime=True).from_file(file)
            client.upload_file(Filename=file, Bucket=AWS_BUCKET, Key=file, ExtraArgs={'ContentType': content_type})
            os.remove(x)


def get_uploaded_images(folder_name: str) -> list:
    uploaded_images = []
    client = get_boto3_client()
    paginator = client.get_paginator('list_objects')
    page_iterator = paginator.paginate(Bucket=AWS_BUCKET, Prefix=f'{IMG_ROOT_FOLDER}/{folder_name}')
    for page in page_iterator:
        if 'Contents' in page.keys():
            for items in page['Contents']:
                uploaded_images.append(items['Key'])
        else:
            pass
    return uploaded_images


def to_upload(folder_name: str) -> list:
    to_return = []
    uploaded_images = get_uploaded_images(folder_name)
    to_download = get_images_to_download(folder_name)
    for items in to_download:
        if items not in uploaded_images:
            to_return.append({items: to_download[items]})
    log_printer(f'{len(to_return)} images will be downloaded and uploaded')
    return to_return


def upload_image(folder_name: str) -> None:
    create_img_folder(folder_name)
    thread_list = []
    log_printer('Checking images to upload')
    chunks = chunkify(to_upload(folder_name), m=10)
    log_printer('Starting image upload')
    for chunk in chunks:
        thread_list.append(Thread(target=boto3_uploader, args=(chunk,)))

    for thread in thread_list:
        thread.start()
    for thread in thread_list:
        thread.join()

    # delete_images(folder_name)
    log_printer('Uploading done')
