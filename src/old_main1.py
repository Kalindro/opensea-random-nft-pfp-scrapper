import os
import os.path
import random
import time
import typing as tp
from io import BytesIO

import requests
from PIL import Image
from dotenv import load_dotenv
from requests.exceptions import Timeout as RequestsTimeoutException
from selenium import webdriver
from selenium.common.exceptions import TimeoutException as SeleniumTimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager

from src.utils.dir_paths import OUTPUTS_DIR
from src.utils.logger_custom import default_logger as logger
from utils.user_agents import user_agents


class OpenSeaScraper:
    def __init__(self):
        load_dotenv()
        self.TIMEOUT = 5
        self.driver = None
        self.COLLECTIONS_LIMIT = 200
        self.PFP_amount = 100
        self.base_url = "https://api.opensea.io/api/v2"
        self.api_key = os.getenv("OPENSEA_API_KEY")
        self.headless = False
        self.detach = True

    def _send_request(self, url: str, params: dict = tp.Optional):
        """Sends a request to the OpenSea API with API"""
        headers = {
            "X-API-KEY": self.api_key
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def scrape_and_save(self):
        """Main function, save all the random NFT pfp's"""
        self.driver = self.driver_init()
        valid_top_collections = [collection for collection in self.get_top_collections() if collection["image"]]
        random_collections = random.sample(valid_top_collections, 100)
        self.driver.quit()

        for collection in random_collections:
            name = collection["name"]
            image = collection["image"]

            if image:
                try:
                    image = Image.open(BytesIO(image))
                    image.thumbnail((256, 256))
                    output_path = os.path.join(OUTPUTS_DIR, "pfps", f"{name}.png")
                    image.save(output_path)

                except Exception as err:
                    logger.exception(f"Error: {err}")
        logger.success("Finished saving all PFP's")

    def get_top_collections(self) -> list:
        """Fetches collections"""
        top_collections = []
        params = {
            "limit": 100,
        }
        url = f"{self.base_url}/collections"

        logger.info("Getting top collections info...")
        while len(top_collections) < self.COLLECTIONS_LIMIT:
            logger.info(f"Getting collection number {len(top_collections) + 1}")
            data = self._send_request(url, params)
            top_collections.extend(
                [{
                    "name": collection["name"],
                    "slug": collection["collection"],
                    "image": self.get_nft_image(collection["collection"])
                } for collection in data["collections"]]
            )

            next_str = data.get("next")  # Get the URL for the next page (if any)
            params = {
                "limit": 100,
                "next": next_str
            }
            if not next_str:
                break

            if len(top_collections) > self.COLLECTIONS_LIMIT / 2:
                logger.info("Half way there...")

        time.sleep(1)
        return top_collections

    def get_nft_image(self, collection_slug: str) -> tp.Union[bytes, None]:
        """Get image url of first NFT in the collection"""
        url = f"{self.base_url}/collection/{collection_slug}/nfts"
        params = {
            "limit": 1
        }
        try:
            data = self._send_request(url, params)
            if data["nfts"] and data["nfts"][0]["opensea_url"]:
                self.driver.get(data["nfts"][0]["opensea_url"])
                image_element = WebDriverWait(self.driver, self.TIMEOUT).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.Image--image")))
                image_source_url = image_element.get_attribute("src")
                response = requests.get(image_source_url, timeout=self.TIMEOUT)
                return response.content
            else:
                return None

        except SeleniumTimeoutException as err:
            logger.error(f"Selenium error fetching image: {err}, {data['nfts'][0]['opensea_url']}, {data['nfts'][0]['collection']}")
            return None

        except RequestsTimeoutException as err:
            logger.error(f"Request error fetching image: {err}, {data['nfts'][0]['opensea_url']}, {data['nfts'][0]['collection']}")
            return None

        except Exception as err:
            logger.exception(f"Error: {err}")
            return None

    def driver_init(self):
        logger.info("Initializing chrome driver...")
        user_agent = random.choice(user_agents)

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={user_agent}")

        if self.headless:
            options.add_argument('--headless=new')
        if self.detach:
            options.add_experimental_option("detach", True)  # To keep window open after

        service = ChromeService(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd(
            'Network.setUserAgentOverride', {
                "userAgent": user_agent
            }
        )

        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True
        )
        logger.success("Finished initializing driver")

        return driver


if __name__ == "__main__":
    scraper = OpenSeaScraper()
    scraper.scrape_and_save()
