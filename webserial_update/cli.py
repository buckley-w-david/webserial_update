import logging
import os
from tempfile import TemporaryDirectory, NamedTemporaryFile
from typing import Optional, List

import typer

from webserial_update.errors import WebserialUpdateError
from webserial_update.config import Settings
from webserial_update.calibredb import CalibreDb
from webserial_update.utils import most_recent_file, download_serial, normalize_url

logging.getLogger("fanficfare").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

# TODO configurable log level
logging.basicConfig(level=logging.INFO)

app = typer.Typer()

# TODO DRY this out
# TODO Figure out how to marry pydantic settings and CLI args

def update_serials(calibredb: CalibreDb, serial_urls: List[str]):
    with TemporaryDirectory() as tempdir:
        for url in serial_urls:
            normalized_url = normalize_url(url)

            search_query = f"Identifiers:url:{normalized_url}"
            matching_ids = calibredb.search(search_query)
            if not matching_ids:
                logger.warning("Did not find calibre record for %s", search_query)

                try:
                    with NamedTemporaryFile(suffix='.epub', dir=str(tempdir)) as f:
                        download_serial(f.name, normalized_url, update=False)
                        new_id = calibredb.add(f.name)
                        logger.info(f"Added %s as %s", url, new_id)
                except WebserialUpdateError as e:
                    logger.warning("%s skipping", e)
                except Exception as e:
                    logger.error("🔥🔥🔥 %s 🔥🔥🔥", e)
            elif len(matching_ids) > 1:
                logger.warning("%s returned more than 1 result. skipping", search_query)
            else:
                calibre_id = matching_ids[0]
                logger.info("Found %s as %s", url, calibre_id)

                # It'd be nice if export gave the exported file name
                calibredb.export(calibre_id, tempdir)
                exported_serial = most_recent_file(tempdir)

                try:
                    download_serial(exported_serial, normalized_url, update=True)
                    calibredb.remove(calibre_id)
                    new_id = calibredb.add(exported_serial)
                    logger.info(f"Added %s as %s", url, new_id)
                except WebserialUpdateError as e:
                    logger.warning("%s skipping", e)
                except Exception as e:
                    logger.error("🔥🔥🔥 %s 🔥🔥🔥", e)

@app.command()
def update():
    settings = Settings()
    with open(settings.urls, 'r') as f:
        serial_urls = [url.strip() for url in f.readlines()]

    calibredb = CalibreDb(settings.calibre_username, settings.calibre_password, settings.calibre_library)
    update_serials(calibredb, serial_urls)


import re
pattern = re.compile(r"url:([^\s,]+)")
@app.command()
def fetch(search_query: str):
    settings = Settings()
    calibredb = CalibreDb(settings.calibre_username, settings.calibre_password, settings.calibre_library)
    if search_query == 'all':
        search_query = f"Identifiers:url:"

    matching_ids = calibredb.search(search_query)
    for calibre_id in matching_ids:
        logger.info("Found %s for %s", calibre_id, search_query)
        metadata = calibredb.get_metadata(calibre_id)
        match = pattern.search(metadata.get('Identifiers', ''))
        if match:
            print(match.group(1))
        else:
            continue

@app.command()
def add(urls: List[str], also_update: bool = False):
    settings = Settings()

    with open(settings.urls, 'r') as f:
        serial_urls = [url.strip() for url in f.readlines()]

    serial_urls.extend(urls)
    dedupe = sorted(normalize_url(url) for url in set(serial_urls))

    with open(settings.urls, 'w') as f:
        f.write('\n'.join(dedupe))

    if also_update:
        calibredb = CalibreDb(settings.calibre_username, settings.calibre_password, settings.calibre_library)
        update_serials(calibredb, urls)

from typing import Tuple
@app.command(help="Apply specified metadata values to all supplied ids")
def set_metadata(id: List[int] = typer.Option(None), name: List[str] = typer.Option(None), value: List[str] = typer.Option(None)):
    settings = Settings()

    calibredb = CalibreDb(settings.calibre_username, settings.calibre_password, settings.calibre_library)
    for serial_id in id:
        calibredb.set_metadata(serial_id, zip(name, value))


if __name__ == '__main__':
    app()
