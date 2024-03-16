from bs4 import BeautifulSoup, NavigableString, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

from os import remove
from time import sleep

class Parser:
    def __init__(self, option="firefox") -> None:
        opt = {
            "edge": webdriver.EdgeOptions(),
            "firefox": webdriver.FirefoxOptions(),
        }
        options = opt[option]
        options.add_argument('--incognito')
        options.add_argument('--no-sandbox')
        options.add_argument('--disk-cache-size=0')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage') 
        self.driver = webdriver.Remote("#", options=options) # link on your selenium grid server 
    
    
    goods_count = None
    
    def auth(self, email:str, password:str) -> bool:
        url_login = "https://kaspi.kz/mc/#/login"
        try:
           
            self.driver.get(url=url_login)
            

            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="email_tab"]'))).click()
                    
            #auth
            email_field = self.driver.find_element(By.XPATH, '//*[@id="user_email_field"]')
            email_field.send_keys(email)
         
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="continue_button"]'))).click()

            psw_field = self.driver.find_element(By.XPATH, '//*[@id="password_field"]')
            psw_field.send_keys(password)
           
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sign_in_button"]'))).click()
            
            sleep(3)
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[1]/nav/div[1]/a[1]')))

            return True
        
        except Exception as ex:
            print(ex)
            return False

        
    def get_vendor_codes(self) -> list:
        data = []
        xpath_next = '//*[@id="offers-table"]/div[2]/div/nav/a[2]'
        def get_id():
            with open("index_selenium.html", "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "lxml")
                for br in soup.findAll('br'):
                    next_s = br.nextSibling
                    if not (next_s and isinstance(next_s,NavigableString)):
                        continue
                    next2_s = next_s.nextSibling
                    if next2_s and isinstance(next2_s,Tag) and next2_s.name == 'br':
                        text = str(next_s).strip()
                        if text:
                            data.append(next_s.replace(" ", ""))

        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div[2]/div/div/div/ul[2]/li[1]'))).click()
            self.goods_count = int(WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/section/div[2]/div/section/div[2]/div[2]/table/tfoot/tr/th/div'))).text[10:])
            while True:
                WebDriverWait(self.driver, 25).until(EC.invisibility_of_element_located((By.XPATH, '//*[@id="app"]/div[2]/section/div[2]/div/div[1]/div[1]')))
                WebDriverWait(self.driver, 25).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/section/div[2]/div/section/div[2]/div[2]/table/tbody/tr[1]/td[2]/div/div/div[1]/div/img')))
         
                with open("index_selenium.html", "w", encoding="utf-8") as file:
                    file.write(self.driver.page_source)

                get_id()

                element_next = WebDriverWait(self.driver, 25).until(EC.element_to_be_clickable((By.XPATH, xpath_next)))
                if element_next.get_attribute("disabled") == "true":
                    break
                element_next.click()

            return data
        except Exception as ex:
            print(ex)
            return []
        
        finally:
            remove("index_selenium.html")
    
    def get_links(self, vendor_codes:list) -> list:
        try:
            data = []
            xpath_card_link = '//*[@id="app"]/div[2]/section/div[2]/div/div[1]/div/div[2]/a[1]'
            count = 0
            for vendor_code in vendor_codes:
                self.driver.get(url='https://kaspi.kz/mc/#/products/active/1')
                WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/section/div[2]/div/div[3]/h4')))
                self.driver.get(url='https://kaspi.kz/mc/#/products/' + vendor_code)
                
                el_link = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath_card_link)))
            
                data.append(el_link.get_attribute('href'))
                
                if count >= 20:
                    sleep(1)
                    self.driver.refresh()
                    count = 0
                count += 1
            return data
        except Exception as ex:
            print(ex)
            return []
        
    def get_products_info(self, links:list) -> list:
        xpath_close = '//*[@id="dialogService"]/div/div[1]/div[2]/i'
        xpath_price = '//*[@id="ItemView"]/div[2]/div/div[2]/div/div[1]/div[3]/div[1]/div[2]'
        xpath_spinner = '//*[@id="offers"]/div/div/div[1]/table/tr/td/div/div'
        xpath_next = '//*[@id="offers"]/div/div/div[2]/li[last()]'
        xpath_image = '//*[@id="ItemView"]/div[2]/div/div[1]/div/div[1]/div/div[1]/ul/li/div/img'
        try:
            data = []

            #close dialog
            try:
                self.driver.get(links[0])
                WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath_close))).click()
            except:
                pass
            
            #parse
            for link in links:
                self.driver.get(url=link)

                data_product = []
                sellers = []

                WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath_price)))

                soup_inf = BeautifulSoup(self.driver.page_source, "lxml")
                data_name = soup_inf.select('#ItemView > div.item > div > div.item__inner-right > div > div:nth-child(1) > h1')[0].text

                image = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath_image)))
                image_link = image.get_attribute('src')

                data_product.append(data_name)
                data_product.append(image_link)
                
                try:
                    self.driver.find_element(By.XPATH, xpath_next)
                    
                    while True:
                        el_next = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath_next)))
                        WebDriverWait(self.driver, 20).until(EC.invisibility_of_element_located((By.XPATH, xpath_spinner)))
                        
                        soup = BeautifulSoup(self.driver.page_source, "lxml")
                        data_sellers = soup.select('#offers > div > div > div > table > tbody > tr > td:nth-child(1) > a')
                        data_price = soup.select('.sellers-table__self > tbody:nth-child(3) > tr > td:nth-child(4) > div:nth-child(1)')

                        for seller, price in zip(data_sellers, data_price):
                            sellers.append([seller.text, int("".join([i for i in str(price.text) if i.isdigit()]))])
                        
                        

                        if el_next.get_attribute("class") != "pagination__el":
                            break

                        el_next.click()

                except:
                    WebDriverWait(self.driver, 20).until(EC.invisibility_of_element_located((By.XPATH, xpath_spinner)))
                    soup = BeautifulSoup(self.driver.page_source, "lxml")
                    
                    data_sellers = soup.select('#offers > div > div > div > table > tbody > tr > td:nth-child(1) > a')
                    data_price = soup.select('.sellers-table__self > tbody:nth-child(3) > tr > td:nth-child(4) > div:nth-child(1)')

                    for seller, price in zip(data_sellers, data_price):
                        sellers.append([seller.text, int("".join([i for i in str(price.text) if i.isdigit()]))])
                    

                data_product.append(sellers)
                data.append(data_product)

            return data
        except Exception as ex:
            print(ex)
            return []

    
    def get_sellers(self, links:list) -> list:
        xpath_close = '//*[@id="dialogService"]/div/div[1]/div[2]/i'
        xpath_price = '//*[@id="ItemView"]/div[2]/div/div[2]/div/div[1]/div[3]/div[1]/div[2]'
        xpath_spinner = '//*[@id="offers"]/div/div/div[1]/table/tr/td/div/div'
        xpath_next = '//*[@id="offers"]/div/div/div[2]/li[last()]'
        try:
            data = []

            #close dialog
            try:
                self.driver.get(links[0])
                WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath_close))).click()
            except:
                pass
            
            #parse
            for link in links:
                self.driver.get(url=link)
                try:
                    WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_price)))
                except:
                    data.append(['u2p_bot_price_error', link])
                    continue
                try:
                    self.driver.find_element(By.XPATH, xpath_next)
                    data_product = []
                    while True:
                        el_next = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, xpath_next)))
                        WebDriverWait(self.driver, 20).until(EC.invisibility_of_element_located((By.XPATH, xpath_spinner)))
                        
                        soup = BeautifulSoup(self.driver.page_source, "lxml")
                        data_sellers = soup.select('#offers > div > div > div > table > tbody > tr > td:nth-child(1) > a')
                        data_price = soup.select('.sellers-table__self > tbody:nth-child(3) > tr > td:nth-child(4) > div:nth-child(1)')

                        for seller, price in zip(data_sellers, data_price):
                            data_product.append([seller.text, int("".join([i for i in str(price.text) if i.isdigit()]))])
                        
                        

                        if el_next.get_attribute("class") != "pagination__el":
                            break

                        el_next.click()
                    data.append(data_product)

                except:
                    data_product = []
                    
                    WebDriverWait(self.driver, 20).until(EC.invisibility_of_element_located((By.XPATH, xpath_spinner)))
                    soup = BeautifulSoup(self.driver.page_source, "lxml")
                    
                    data_sellers = soup.select('#offers > div > div > div > table > tbody > tr > td:nth-child(1) > a')
                    data_price = soup.select('.sellers-table__self > tbody:nth-child(3) > tr > td:nth-child(4) > div:nth-child(1)')

                    for seller, price in zip(data_sellers, data_price):
                
                        data_product.append([seller.text, int("".join([i for i in str(price.text) if i.isdigit()]))])

                    data.append(data_product)
    
            return data
        except Exception as ex:
            print(ex)
            return []

    def check_product_is_actice(self, links:list) -> list:
        data = []
        xpath_close = '//*[@id="dialogService"]/div/div[1]/div[2]/i'
        xpath_price_out = '//*[@id="ItemView"]/div[2]/div/div[2]/div/div[1]/div[3]/span'
        try:
                self.driver.get(links[0])
                WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath_close))).click()
        except:
            pass


        for link in links:
            self.driver.get(link)
            try:
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_price_out)))
                data.append(False)
            except:
                data.append(True)
        return data
    

    def change_price(self, vendor_codes_and_prices:list) -> bool:
        try:
            self.driver.get(url='https://kaspi.kz/mc/#/products/active/1')
            for vendor_code_and_price in vendor_codes_and_prices:
                    WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/section/div[2]/div/div[3]/h4')))
                    self.driver.get(url='https://kaspi.kz/mc/#/products/' + str(vendor_code_and_price[0]))
                    input_price = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/section/div[2]/div/div[2]/div[2]/div/table/thead/tr[2]/th[2]/div/span/div[2]/input')))
                    if input_price.get_attribute("disabled") != "disabled":
                        input_price.clear()
                        input_price.send_keys(str(vendor_code_and_price[1]))
                        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/section/div[2]/div/div[2]/div[3]/button[1]'))).click()
                        sleep(3)

            return True
        except Exception as ex:
            print(ex)
            
    def parser_close(self):
        self.driver.quit()