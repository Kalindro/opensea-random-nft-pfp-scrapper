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
from werkzeug.utils import secure_filename
from src.utils.dir_paths import OUTPUTS_DIR
from src.utils.logger_custom import default_logger as logger


class OpenSeaScraper:
    def __init__(self):
        load_dotenv()
        self.PFP_amount = 100
        self.COLLECTIONS_LIMIT = self.PFP_amount * 2  # For some randomness
        self.TIMEOUT = 5
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

    def scrape_and_save(self) -> None:
        """Main function, save all the random NFT pfp's"""
        collections = self.get_collections()
        collections_with_image = self.download_images_to_collections(collections)
        random_collections_with_image = random.sample(collections_with_image, self.PFP_amount)

        for collection in random_collections_with_image:
            safe_name = secure_filename(collection["name"])
            image = collection["image"]

            try:
                image = Image.open(BytesIO(image))
                image.thumbnail((256, 256))
                output_path = os.path.join(OUTPUTS_DIR, "pfps", f"{safe_name}.png")
                image.save(output_path)

            except Exception as err:
                logger.exception(f"Error: {err}")

        logger.success("Finished saving all PFP's")

    def download_images_to_collections(self, collections: list) -> list:
        """Download images to collections dicts"""

        def _ipfs_downloader(ipfs_url) -> bytes:
            ipfs_gateways = ['gateway.pinata.cloud', 'gateway.ipfs.io', 'storry.tv', '4everland.io', 'cloudflare-ipfs.com', 'ipfs.eth.aragon.network',
                             'cf-ipfs.com', 'w3s.link', 'cf-ipfs.com', 'gw3.io', 'dweb.eu.org', 'video.oneloveipfs.com', 'permaweb.eu.org']

            cid = ipfs_url.split("/ipfs/")[-1]
            for gateway in ipfs_gateways:
                response = requests.get(f"https://{gateway}/{cid}", timeout=self.TIMEOUT)
                if response.status_code == 200:
                    break

            return response.content

        def _request_downloader(regular_url):
            response = requests.get(regular_url, timeout=self.TIMEOUT)

            return response.content

        counter = 0
        logger.info("Downloading images to collections")
        for collection in collections:
            counter += 1
            time.sleep(0.5)
            if counter % 10 == 0 or counter == 1:
                logger.info(f"Downloading image number {counter}")

            try:
                url = collection["collection_image_url"]
                if "/ipfs/" in url:
                    image = _ipfs_downloader(url)
                else:
                    image = _request_downloader(url)

                collection["image"] = image

            except RequestsTimeoutException as err:
                logger.error(f"Request error fetching image: {err}, {collection['name']}, {url}")

            except Exception as err:
                logger.exception(f"Error: {err}")

        collections_with_image = [collection for collection in collections if collection["image"]]

        return collections_with_image

    def get_collections(self) -> list:
        """Fetches collections that have ipfs link in image_url"""
        collections = []
        params = {
            "limit": 100,
        }
        url = f"{self.base_url}/collections"

        logger.info("Getting top collections info...")
        while len(collections) < self.COLLECTIONS_LIMIT:
            logger.info(f"Getting collection number {len(collections) + 1}")
            data = self._send_request(url, params)
            collections.extend(
                [{
                    "name": collection["name"],
                    "slug": collection["collection"],
                    "description": collection["description"],
                    "project_url": collection["project_url"],
                    "collection_image_url": collection["image_url"]
                } for collection in data["collections"] if collection["image_url"]]
            )

            next_str = data.get("next")  # Get the URL for the next page (if any)
            params = {
                "limit": 100,
                "next": next_str
            }
            if not next_str:
                break

        logger.success(f"Got all {self.COLLECTIONS_LIMIT} collections")
        time.sleep(0.5)

        return collections

    def get_first_nft_image_url(self, collection_slug: str) -> tp.Union[bytes, None]:
        """Get image url of first NFT in the collection"""
        url = f"{self.base_url}/collection/{collection_slug}/nfts"
        params = {
            "limit": 1
        }
        try:
            data = self._send_request(url, params)
            if data["nfts"] and data["nfts"][0]["image_url"]:
                if "/ipfs/" in data["nfts"][0]["image_url"]:
                    return data["nfts"][0]["image_url"]
            else:
                return None

        except Exception as err:
            logger.exception(f"Error: {err}")

            return None


if __name__ == "__main__":
    scraper = OpenSeaScraper()
    scraper.scrape_and_save()
