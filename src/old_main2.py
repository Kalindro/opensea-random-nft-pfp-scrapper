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

from src.utils.dir_paths import OUTPUTS_DIR
from src.utils.logger_custom import default_logger as logger


class OpenSeaScraper:
    def __init__(self):
        load_dotenv()
        self.TIMEOUT = 5
        self.COLLECTIONS_LIMIT = 50
        self.PFP_amount = 2
        self.base_url = "https://api.opensea.io/api/v2"
        self.api_key = os.getenv("OPENSEA_API_KEY")
        self.headless = False
        self.detach = True

    def _send_request(self, url: str, params: dict = tp.Optional):
        """Sends a request to the OpenSea API with API"""
        headers = {
            "X-API-KEY": self.api_key
        }
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

        except Exception as err:
            logger.exception(f"Error: {err}")

    def scrape_and_save(self):
        """Main function, save all the random NFT pfp's"""
        top_collections = self.get_top_collections()
        filtered_top_collections = [collection for collection in top_collections if collection["image_url"]]
        top_collections_with_image = self.download_images_to_collections(filtered_top_collections)
        random_collections = random.sample(top_collections_with_image, 100)

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

    def download_images_to_collections(self, collections: list) -> list:
        """Download images to collections dicts"""
        top_collections_with_image_url = [collection for collection in collections if collection["image_url"]]
        for collection in top_collections_with_image_url:
            time.sleep(1)
            try:
                response = requests.get(f"{collection['image_url']}", timeout=self.TIMEOUT)
                collection["image"] = response.content

            except RequestsTimeoutException as err:
                logger.error(f"Request error fetching image: {err}, {collection['name']}, {collection['image_url']}")

            except Exception as err:
                logger.exception(f"Error: {err}")

        top_collections_with_image = [collection for collection in top_collections_with_image_url if collection["image"]]

        return top_collections_with_image

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
                    "image_url": collection["image_url"]
                } for collection in data["collections"]]
            )

            next_str = data.get("next")  # Get the URL for the next page (if any)
            params = {
                "limit": 100,
                "next": next_str
            }
            if not next_str:
                break

        logger.success(f"Got all {self.COLLECTIONS_LIMIT} collections")
        time.sleep(1)
        return top_collections

if __name__ == "__main__":
    scraper = OpenSeaScraper()
    scraper.scrape_and_save()
