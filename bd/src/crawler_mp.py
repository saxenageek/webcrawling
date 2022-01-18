#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import time
import csv
import re
import os
import sys
from functools import partial
from itertools import product
p = os.path.abspath('../..')
if p not in sys.path:
    sys.path.append(p)
from utilities.ansi_units import return_uom
from utilities.getproxies import get_proxies
from multiprocessing import Pool, cpu_count
from webdriver_manager.chrome import ChromeDriverManager
from pandas import read_excel
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service


class Spider(object):
  """Spider class with crawling functions."""

  def __init__(self):
    options = Options()
    options.add_argument('--headless')  # Runs Chrome in headless mode.
    #options.add_argument('--no-sandbox')  # Bypass OS security model
    #options.add_argument('start-maximized')
    #options.add_argument('disable-infobars')
    #options.add_argument('--disable-extensions')
    #options.add_argument("--disable-gpu")
    options.add_argument('disable-blink-features=AutomationControlled')
    #options.add_argument('user-agent=fake-useragent')
    #options.add_argument("ignore-certificate-errors")
    service = Service(ChromeDriverManager().install())
    self.driver = webdriver.Chrome(service=service, options=options, service_log_path='/dev/null')
    self.outdict = []
    self.tempdict = {}
    self.description1 = ""
    self.item_url_base_path = "https://www.bd.com/en-us/searchresults?term="

  def extract_imagesandmetadata(self, itemcode):
    searchurl = self.item_url_base_path + itemcode + "&tab=2&cats="
    print("Crawling ..." + searchurl)

    try:
      self.driver.get(searchurl)
    except Exception as e:
      print("Driver.get failed ..", str(e))
      pass
    itemelement = ""
    html = ""
    self.tempdict = {}
    
    self.tempdict["ManufacturerPartNumber"] = itemcode    
    self.tempdict["ManufacturerName"] = "BECTON DICKINSON"    
    self.tempdict["ManufacturerIdentifier"] = "001292192"
    self.tempdict["ManufacturerIdentifierType"] = "DUNS"
    self.tempdict["ManufacturerMarket"] = "US"
    self.tempdict["SupplierPartNumber"] = itemcode    
    self.tempdict["SupplierName"] = "BECTON DICKINSON"
    self.tempdict["SupplierIdentifier"] = "001292192"
    self.tempdict["SupplierIdentifierType"] = "DUNS"
    self.tempdict["SupplierMarket"] = "US"
    self.tempdict["Source"] = "IPA"
    self.tempdict["DeviceIdentifier"] = ""    
   
    time.sleep(1) 
    try:
      itemelement = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="'+ itemcode +'"]')))
      
      if itemelement:
        itemurl = itemelement.get_attribute('href')
        self.tempdict["ManufacturerItemURL"] = itemurl
        self.tempdict["SupplierItemURL"] = itemurl

        try:
          itemelement.click() # clicking on item page link
          html = self.driver.page_source

          # image code
          try:
            imageelement = self.driver.find_element(By.XPATH, '//*[@id="page"]/main/div/div[1]/div[1]/div/p/a/img')
          except:
            try:
              imageelement = self.driver.find_element(By.XPATH, '//*[@id="slider"]/div/div/div[1]/div/a/img')
            except:
              try:
                imageelement = self.driver.find_element(By.XPATH, '//*[@id="page"]/main/div/div[1]/div[1]/p/img')
              except:
                imageelement = ""
          if imageelement:
            imageurl = imageelement.get_attribute('src')
            imagename = str(imageurl).split("/")[-1]
            imagename = re.sub(r"\?.*", "", imagename)
            if imageurl:
              self.tempdict["ImageURL"] = imageurl
              self.tempdict["ImageFilename"] = imagename
            else:
              self.tempdict["ImageURL"] = ""
              self.tempdict["ImageFilename"] = ""
          else:
            self.tempdict["ImageURL"] = ""
            self.tempdict["ImageFilename"] = ""
            pass

          # market status code
          self.tempdict["ManufacturerMarketStatus"] = ""
          self.tempdict["ManufacturerMarketStatus"] = ""
          status = re.findall(r'Discontinued|Obsolete|Out of Service|Not Orderable|Recalled', html, re.DOTALL)
          if status:
            self.tempdict["ManufacturerMarketStatus"] = "NON-ORDERABLE"
            self.tempdict["SupplierMarketStatus"] = "NON-ORDERABLE"
          else:
            self.tempdict["ManufacturerMarketStatus"] = "ORDERABLE"
            self.tempdict["SupplierMarketStatus"] = "ORDERABLE"

          # brand code
          try:
            brand = re.findall(r'<strong>Brand.*?<td>\s*(.*?)\s*</td>', html, re.DOTALL)
            
            # print(brand)
            if brand:
              brand = brand[0]
              self.tempdict["BrandName"] = brand
            else:
              self.tempdict["BrandName"] = ""
          except Exception as e:
            # print(str(e))
            self.tempdict["BrandName"] = ""
            pass

          # clean subscript from brand
          if self.tempdict["BrandName"]:
            if "™" in self.tempdict["BrandName"]:
              self.tempdict["BrandName"] = self.tempdict["BrandName"].replace("™", "")

          # speciality code, category is equivalent to it
          try:
            speciality = re.findall(r'<strong>Specialty.*?<td>\s*(.*?)\s*</td>', html, re.DOTALL)
            if len(speciality) >= 1:
              speciality = speciality[0]
              # print(speciality)
              self.tempdict["ManufacturerCategory"] = speciality
              self.tempdict["SupplierCategory"] = speciality
            else:
              self.tempdict["ManufacturerCategory"] = ""
              self.tempdict["SupplierCategory"] = ""
          except Exception as e:
            # print(str(e))
            self.tempdict["ManufacturerCategory"] = ""
            self.tempdict["SupplierCategory"] = ""
            pass

          sku_refelement = ""
          # description1 code (sku /ref)
          try:
            sku_refelement = re.findall(r'SKU/REF Name</h2>.*?<h2.*?>\s*(.*?)\s*</h2>', html, re.DOTALL) 
            # print(sku_refelement)           
            if sku_refelement:
              self.description1 = sku_refelement[0]
            else:
              self.description1 = ""
          except:
            self.description1 = ""
            pass

          descriptionelement = ""
          # description code
          try:
            descriptionelement = re.findall(r'Description</h2>.*?<h2.*?>\s*(.*?)\s*</h2>', html, re.DOTALL) 
            
            if descriptionelement:
              self.tempdict["ManufacturerItemDescription"] = (self.description1 + " " + descriptionelement[0]).strip()
              self.tempdict["SupplierItemDescription"] = (self.description1 + " " + descriptionelement[0]).strip()
            elif self.description1:
              self.tempdict["ManufacturerItemDescription"] = (self.description1).strip()
              self.tempdict["SupplierItemDescription"] = (self.description1).strip()
            else:
              self.tempdict["ManufacturerItemDescription"] = ""
              self.tempdict["SupplierItemDescription"] = ""
          except Exception as e:
            # print("We are here", str(e))
            self.tempdict["ManufacturerItemDescription"] = ""
            self.tempdict["SupplierItemDescription"] = ""
            pass

          # alternate brand code
          try:
            alternatebrand = re.findall(r'(\w+™)', self.tempdict["ManufacturerItemDescription"], re.DOTALL)
            if alternatebrand and not self.tempdict["BrandName"]:
              self.tempdict["BrandName"] = alternatebrand[0]
          except Exception as e:
            print("Encoding Failed ", str(e))
            pass

          # flags code
          if "non-sterile" in self.tempdict["ManufacturerItemDescription"].lower():
            self.tempdict["SterilePackagedFlag"] = "0"
          elif "sterile" in self.tempdict["ManufacturerItemDescription"].lower():
            self.tempdict["SterilePackagedFlag"] = "1"
          else:
            self.tempdict["SterilePackagedFlag"] = ""

          if "contains latex" in self.tempdict["ManufacturerItemDescription"].lower():
            self.tempdict["LatexFlag"] = "1"
          elif "latex free" in self.tempdict["ManufacturerItemDescription"].lower():
            self.tempdict["LatexFlag"] = "0"
          else:
            self.tempdict["LatexFlag"] = ""

          if "single use" in self.tempdict["ManufacturerItemDescription"].lower():
            self.tempdict["SingleUseFlag"] = "1"
          elif "not applicable" in self.tempdict["ManufacturerItemDescription"].lower():
            self.tempdict["SingleUseFlag"] = "0"
          else:
            self.tempdict["SingleUseFlag"] = ""

          if "packaged in pairs" in self.tempdict["ManufacturerItemDescription"].lower():
            self.tempdict["QuantityofEach"] = "1"
            self.tempdict["UnitofMeasure"] = "PR"
          else:
            self.tempdict["QuantityofEach"] = "1"
            self.tempdict["UnitofMeasure"] = "EA"
        
          try:
            self.tempdict["UnitofMeasure"] = return_uom(self.tempdict["ManufacturerItemDescription"])
          except Exception as e:
            print("Return uom function failed", str(e))
            self.tempdict["UnitofMeasure"] = "EA"
            pass
        except Exception as e:
          print("Item Click Failed", str(e))
          return
    except Exception as e:
      print("Item Element " + itemcode + " Not Found", str(e))
      return

    self.tempdict["Key"] = self.tempdict["ManufacturerPartNumber"] + "-" + str(self.tempdict["ManufacturerIdentifier"])
    if self.tempdict["UnitofMeasure"]:
      self.tempdict["Key"] += "-" + self.tempdict["UnitofMeasure"]
    if self.tempdict["QuantityofEach"]:
      self.tempdict["Key"] += "-" + self.tempdict["QuantityofEach"]
    self.tempdict["Key"] += "-" + self.tempdict["ManufacturerMarket"]
    self.outdict.append(self.tempdict)
 
  
  def start_crawl(self, item, formatted_time, manufacturer_id):
    self.extract_imagesandmetadata(item)
    self.driver.close()
    CreateOutputFile(self.outdict, manufacturer_id, formatted_time)


def CreateOutputFile(content, manufacturer_id, formatted_time):
    headers = ["Source","Key","DeviceIdentifier","ManufacturerIdentifier","ManufacturerIdentifierType",
    "ManufacturerName","ManufacturerPartNumber","ManufacturerItemDescription","ManufacturerCategory",
    "ManufacturerMarket","ManufacturerMarketStatus","SupplierIdentifier","SupplierIdentifierType",
    "SupplierName","SupplierPartNumber","SupplierItemDescription","SupplierCategory","SupplierMarket",
    "SupplierMarketStatus","BrandName","UnitofMeasure","QuantityofEach","LatexFlag",
    "SterilePackagedFlag","SingleUseFlag","ImageFilename","ImageURL","ManufacturerItemURL",
    "SupplierItemURL","GTIN","ManufacturerAlternateItemDescription","ManufacturerAlternatePartNumbers","SupplierAlternatePartNumber"]
    #formatted_time = datetime.now().strftime('%Y%m%d%H%M%S')
    output_file_name = "egress/" + formatted_time + "/IPA-SCAP-" + manufacturer_id + "Mockup-" + formatted_time + ".csv"
    try:
        output_folder_path = f"egress/{formatted_time}"
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        with open(output_file_name, 'a') as output_file:
            dict_writer = csv.DictWriter(output_file, headers, lineterminator='\n')
            for d in content:
                try:
                    dict_writer.writerow(d)
                except Exception as e:
                    print(str(e))
                    pass
    except Exception as e:
        print(e)
    return True

def GetItemCodes(ingressfilename):
    start_urls = []
    count = 0
    my_sheet = "BD-CareFusion"
    df = read_excel(ingressfilename, sheet_name = my_sheet)
    start_urls = df["Mfg Part Num"]
    return start_urls


def ProcessSpider(formatted_time, manufacturer_id, item):
    print("Debug: ", item)
    spider = Spider()
    spider.start_crawl(item, formatted_time, manufacturer_id)

def ProcessItems(items, formatted_time, manufacturer_id):
    func = partial(ProcessSpider, formatted_time, manufacturer_id)
    with Pool(processes=(cpu_count() - 1)) as pool:
        pool.map(func, items)
    pool.join()

def run(ingressfilesname, manufacturer_id):
    formatted_time = datetime.now().strftime('%Y%m%d%H%M%S')
    headers = ["Source","Key","DeviceIdentifier","ManufacturerIdentifier","ManufacturerIdentifierType",
    "ManufacturerName","ManufacturerPartNumber","ManufacturerItemDescription","ManufacturerCategory",
    "ManufacturerMarket","ManufacturerMarketStatus","SupplierIdentifier","SupplierIdentifierType",
    "SupplierName","SupplierPartNumber","SupplierItemDescription","SupplierCategory","SupplierMarket",
    "SupplierMarketStatus","BrandName","UnitofMeasure","QuantityofEach","LatexFlag",
    "SterilePackagedFlag","SingleUseFlag","ImageFilename","ImageURL","ManufacturerItemURL",
    "SupplierItemURL","GTIN","ManufacturerAlternateItemDescription","ManufacturerAlternatePartNumbers","SupplierAlternatePartNumber"]
    output_file_name = "egress/" + formatted_time + "/IPA-SCAP-" + manufacturer_id + "Mockup-" + formatted_time + ".csv"

    try:
        output_folder_path = f"egress/{formatted_time}"
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)

        with open(output_file_name, 'w') as output_file:
            dict_writer = csv.DictWriter(output_file, headers, lineterminator='\n', quotechar = "'")
            dict_writer.writeheader()
    except Exception as e:
        print(e)

    ItemsList = GetItemCodes(ingressfilesname)
    print("Starting batch job for", str(len(ItemsList)), "records")
    ProcessItems(ItemsList, formatted_time, manufacturer_id)
    return formatted_time
