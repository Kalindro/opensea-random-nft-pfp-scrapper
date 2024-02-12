import os
import os.path
import random
import time
import typing as tp
from io import BytesIO

import requests
from PIL import Image, UnidentifiedImageError
from dotenv import load_dotenv
from requests.exceptions import Timeout as RequestsTimeoutException
from werkzeug.utils import secure_filename

from src.utils.dir_paths import OUTPUTS_DIR
from src.utils.logger_custom import default_logger as logger


class OpenSeaScraper:
    def __init__(self):
        # ### # Static settings # ### #
        load_dotenv()
        self.TIMEOUT = 5
        self.api_key = os.getenv("OPENSEA_API_KEY")
        self.base_url = "https://api.opensea.io/api/v2"

        # ### # General # ### #
        self.PFP_amount = 200
        self.COLLECTIONS_LIMIT = self.PFP_amount * 10  # For some randomness, doesn't take that much longer

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
        random_collections = random.sample(collections, self.PFP_amount)
        random_collections_with_image = self.download_images_to_collections(random_collections)

        logger.info("Saving images")
        for index, collection in enumerate(random_collections_with_image):
            if index % 10 == 0:
                logger.info(f"Saving image number {index}...")
            safe_name = secure_filename(collection["name"])
            image = collection["image"]

            try:
                image = Image.open(BytesIO(image))
                image.thumbnail((256, 256))
                output_path = os.path.join(OUTPUTS_DIR, "pfps", f"{safe_name}.png")
                image.save(output_path, format="PNG")

            except UnidentifiedImageError as err:
                logger.error(f"Weird image format, skipping nr {index}: {err}")

            except Exception as err:
                logger.exception(f"Error: {err}, {output_path}")

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

        logger.info("Downloading images to collections")
        for index, collection in enumerate(collections):
            time.sleep(0.5)
            if index % 10 == 0:
                logger.info(f"Downloading image number {index}...")

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
                logger.exception(f"Error: {err}, {collection['name']}, {url}")

        collections_with_image = [collection for collection in collections if "image" in collection and collection["image"]]
        logger.success("Downloaded all images")

        return collections_with_image

    def get_collections(self) -> list:
        """Fetches collections that have ipfs link in image_url"""
        collections = []
        params = {
            "limit": 100,
        }
        url = f"{self.base_url}/collections"

        logger.info("Getting top collections info")
        while len(collections) < self.COLLECTIONS_LIMIT:
            logger.info(f"Getting collection number {len(collections) + 1}...")
            data = self._send_request(url, params)
            collections.extend(
                [{
                    "name": collection["name"],
                    "slug": collection["collection"],
                    "description": collection["description"],
                    "project_url": collection["project_url"],
                    "collection_image_url": collection["image_url"]
                } for collection in data["collections"] if "http" in collection["image_url"]]
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
