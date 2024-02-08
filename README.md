## Opensea Random NFT PFP Scrapper

Simple tool to scrap random NFT's (actually collections images, it's much faster than additionally checking for image of actual collections NFT's).  
They can be used as Discord/Twitter profile pictures, very useful for people with, for some reason, a lot of accounts :)

___

You need to provide OpenSea API key in .env file (.env.example as example). It's easy to get, nowadays you receive it instantly.

___

Main running file: [src/main.py](src/main.py).  
You need to specify `self.PFP_amount` in there. Please input more than you need as many of the images won't be
suitable for a PFP so there is some manual review required.  

___

The images are saved in [outputs/pfps](outputs/pfps).

