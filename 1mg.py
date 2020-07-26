import os
import re
import sys
import math
import json
import string
import shutil
import logging
import argparse
import traceback
from datetime import datetime as dt
from concurrent.futures import as_completed, ThreadPoolExecutor

import requests
import pandas as pd
from bs4 import BeautifulSoup, NavigableString

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC


def get_logger(log_level=logging.INFO):
    filename = os.path.split(__file__)[-1]
    log = logging.getLogger(filename)
    log_level = logging.INFO
    log.setLevel(log_level)
    log_handler = logging.StreamHandler()
    log_formatter = logging.Formatter('%(levelname)s: %(asctime)s - %(name)s:%(lineno)d - %(message)s')
    log_handler.setFormatter(log_formatter)
    log.addHandler(log_handler)
    return log

log = get_logger(__file__)


LIMIT = 50


class OnemgScraper:

    def __init__(self, url, args, settings):
        self.url = url
        self.args, self.settings = args, settings
        self.data = []

    def get_title(self, soup):
        try:
            return soup.find("h1", class_="DrugHeader__title___1NKLq").text.strip()
        except Exception as err:
            log.error(err)
            raise Exception("Error on loading the product details")

    def get_brand_name(self, soup):
        try:
            return soup.find("h1", class_="DrugHeader__title___1NKLq").text.strip().split(" ")[0]
        except:
            return ""

    def get_pack_size(self, soup):
        try:
            return soup.find("div", class_="DrugPriceBox__quantity___2LGBX").text.strip()
        except:
            return ""

    def get_url_image(self, soup):
        try:
            return soup.find("div", class_="slick-list").find("img").attrs["src"]
        except:
            return ""

    def get_about(self, soup):
        return self.get_introduction(soup)

    def get_features(self, soup):
        try:
            return soup.find("h2", class_="DrugOverview__title___1OwgG", string=re.compile(r"how to use .*", re.IGNORECASE)).next.next.text
        except:
            return ""

    def get_uses_details(self, soup):
        try:
            uses = []
            for li in soup.find("h2", class_="DrugOverview__title___1OwgG", string=re.compile(r"uses of .*", re.IGNORECASE)).next.next.find_all("li"):
                if not isinstance(li, NavigableString):
                    uses.append(li.text)
            return "\n".join(uses)
        except:
            return ""

    def get_warnings(self, soup):
        try:
            dom_warnings = soup.find("h2", class_="DrugOverview__title___1OwgG", string=re.compile(r".*safety advice.*", re.IGNORECASE)).next.next
            warnings = ""
            for title in dom_warnings.find_all("div", class_="DrugOverview__warning-top___UD3xX"):
                warnings += "\n" + " - ".join(filter(lambda x: len(x) > 0, [content.text for content in title.contents]))
                warnings += "\n\t" + title.next_sibling.text
            return warnings.strip()
        except:
            return ""

    def get_introduction(self, soup):
        try:
            return soup.find("h2", class_="DrugOverview__title___1OwgG", string="Introduction").next.next.text
        except:
            return ""

    def get_direction_of_use(self, soup):
        return self.get_features(soup)

    def get_dosage(self, soup):
        return self.get_features(soup)

    def get_unit(self, soup):
        try:
            return self.get_pack_size(soup).split(" ")[1]
        except:
            return ""

    def get_mrp(self, soup):
        try:
            return soup.find("div", class_="DrugPriceBox__bestprice-slashed-price___2ANwD").text
        except:
            return self.get_selling_price(soup)

    def get_selling_price(self, soup):
        try:
            return soup.find("div", class_="DrugPriceBox__best-price___32JXw").text
        except:
            try:
                return soup.find("div", class_="DrugPriceBox__price___dj2lv").text
            except:
                return ""

    def get_sub_category_1(self, soup):
        try:
            return soup.find("div", id="breadcrumbs-drug").get_text().split(">")[1]
        except:
            return ""

    def get_sub_category_2(self, soup):
        try:
            return soup.find("div", id="breadcrumbs-drug").get_text().split(">")[2]
        except:
            return ""

    def get_overview(self, soup):
        try:
            return soup.find("div", id="overview").prettify()
        except:
            return ""

    def get_product_url(self, endpoint):
        return OnemgManager.base_url + endpoint

    def extract(self, product, soup):
        return {
            "product_url": self.get_product_url(product["slug"]),
            "brand_name": self.get_brand_name(soup),
            "title": self.get_title(soup),
            "pack_size": self.get_pack_size(soup),
            "image_url": self.get_url_image(soup),
            "company_name": product.get("manufacturer_name", "NA"),
            "company_logo": "NA",
            "about": self.get_about(soup),
            "features": self.get_features(soup),
            "uses_details": self.get_uses_details(soup),
            "warnings": self.get_warnings(soup),
            "introduction": self.get_introduction(soup),
            "direction_of_use": self.get_direction_of_use(soup),
            "dosage": self.get_dosage(soup),
            "unit": self.get_unit(soup),
            "mrp": self.get_mrp(soup),
            "selling_price": self.get_selling_price(soup),
            "category": product.get("type", "NA").title(),
            "sub_category_1": self.get_sub_category_1(soup).title(),
            "sub_category_2": self.get_sub_category_2(soup).title(),
            "overview[do-not-delete]": self.get_overview(soup)
        }

    def get_info(self, product):
        product_url = self.get_product_url(product["slug"])

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        log_path = '/dev/null' if sys.platform == "linux" else "NUL"
        chrome = webdriver.Chrome(self.settings["driver_path"]["value"], chrome_options=options, service_log_path=log_path)
        chrome.get(product_url)

        try:
            wait = self.settings["page_load_timeout"]["value"]
            WebDriverWait(chrome, wait).until(EC.presence_of_element_located((By.ID, "overview")))
            soup = BeautifulSoup(chrome.page_source, "html.parser")
            info = self.extract(product, soup)
            return info
        except (TimeoutException, Exception) as err:
            log.error(f"Error on loading the product info: {product_url}")
            log.error(f"Error Message: {err}")
        finally:
            chrome.close()

    def get(self):
        log.info(f"Fetching from: {self.url}")
        response = requests.get(self.url)
        if response.status_code == 200:
            res_data = response.json()
            products = res_data["data"]["skus"]
            
            count = 1
            workers = self.settings["workers"]["value"]
            with ThreadPoolExecutor(workers) as executor:        
                for info in executor.map(self.get_info, products):
                    if info:
                        self.data.append(info)
                    if count % 2 == 0:
                        log.info("So far {} has been fetched ...".format(count))
                    count += 1
        else:
            log.error(f"Got status ({response.status}). Exit!")
            sys.exit(1)

        return self.data


class OnemgManager:

    base_url = "https://www.1mg.com"

    def __init__(self, label, p1, p2, args, settings):
        self.label, self.p1, self.p2 = label, p1, p2
        self.args, self.settings = args, settings

        self.limit = LIMIT
        self.url = self.base_url + "/pharmacy_api_gateway/v4/drug_skus/by_prefix?prefix_term={label}&page={page}&per_page={limit}"

        self.dir_output = "output"
        self.xlsx_output = os.path.join(self.dir_output, self.label, "{}_{}.xlsx".format(self.p1, self.p2))

        self.data = []

    def get(self):
        for page in range(self.p1, self.p2+1):
            url = self.url.format(label=self.label, page=page, limit=self.limit)
            data = OnemgScraper(url, self.args, self.settings).get()
            if data:
                self.data.extend(data)
        return self.data

    def setup(self):
        path = os.path.join(self.dir_output, self.label)
        os.makedirs(path, exist_ok=True)

    def save(self):
        df = pd.DataFrame(self.data)
        df.to_excel(self.xlsx_output, index=False)
        log.info("Fetched data has been stored in {} file".format(self.xlsx_output))


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-lc', "--lc", help="To see how many records in the website", action="store_true")
    arg_parser.add_argument('-l', "--label", help="Enter any of [a-z] (lower-case)")
    arg_parser.add_argument('-p1', "--page_from", type=int)
    arg_parser.add_argument('-p2', "--page_to", type=int)
    return arg_parser.parse_args()


def get_settings():
    with open("settings.json", "r") as f:
        return json.load(f)


def validate_args(args):
    if args.label:
        if not (args.page_from or args.page_to):
            raise Exception("-p1 && -p2 are required!")


def list_category():
    print("\n\n")
    print("\t\tLabel | Count | Pages")
    print("\t\t=====================")
    for alphabet in string.ascii_lowercase:
        url = OnemgManager.base_url + f"/pharmacy_api_gateway/v4/drug_skus/by_prefix?prefix_term={alphabet}&page=1&per_page=1"
        response = requests.get(url).json()
        total_count = response["meta"]["total_count"]
        total_pages = math.ceil(total_count / LIMIT)
        print(f"\t\t{alphabet} - {total_count} - {total_pages}")
    print("\n\n")


def main():
    start = dt.now()
    log.info("Script starts at: {}".format(start.strftime("%d-%m-%Y %H:%M:%S %p")))

    args, settings = get_args(), get_settings()
    if args.lc:
        return list_category()
    validate_args(args)

    onemg = OnemgManager(args.label, args.page_from, args.page_to, args, settings)
    onemg.setup()

    try:
        onemg.get()
    except Exception as e:
        log.error(f"Error: {e}")
        traceback.print_exc()
    finally:
        onemg.save()

    end = dt.now()
    log.info("Script ends at: {}".format(end.strftime("%d-%m-%Y %H:%M:%S %p")))
    elapsed = round(((end - start).seconds / 60), 4)
    log.info("Time Elapsed: {} minutes".format(elapsed))


if __name__ == "__main__":
    main()
