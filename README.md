## Opensea Random NFT PFP Scrapper

Simple tool to scrap random NFT's (actually collections images, it's much faster than additionally checking for image of actual collections NFT's).  
They can be used as Discord/Twitter profile pictures, very useful for people with, for some reason, a lot of accounts :)  

___

Actually it's not that random, OpenSea endpoint doesn't specify what order of collections output there is, I assume it's from the latest ones.  
That's why the output varies depending on when you run it plus some randomness added by me (it fetches 10x more collections
(with not much more waiting needed) than needed and chooses from them by random).

___

Maybe in future I will add scrapping for top N projects, so all images will be legit PFP's of known projects
as currently a lot of downloaded images are shit.

___

Regular poetry install. You need to provide OpenSea API key in .env file (.env.example as example). It's easy to get, nowadays you receive it instantly.
___

Main running file: [src/main.py](src/main.py).  
You need to specify `self.PFP_amount` in there. Please input more than you need as many of the images won't be
suitable for a PFP so there is some manual review required. And some will fail to download, the final number of PFP's will always be a bit smaller
than desired.

___

The images are saved in [outputs/pfps](outputs/pfps).

