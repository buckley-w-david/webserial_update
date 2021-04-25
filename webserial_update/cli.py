import logging
import os
from tempfile import TemporaryDirectory, NamedTemporaryFile
from typing import Optional, List

import toml
import typer

from webserial_update.errors import WebserialUpdateError
from webserial_update.config import Settings
from webserial_update.calibredb import CalibreDb
from webserial_update.utils import most_recent_file, download_serial, normalize_url

logging.getLogger("fanficfare").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def update():
    settings = Settings()
    calibredb = CalibreDb(settings.calibre_username, settings.calibre_password, settings.calibre_library)
    with TemporaryDirectory() as tempdir:
        for url in settings.serial_urls:
            normalized_url = normalize_url(url)

            search_query = f"Identifiers:url:{normalized_url}"
            matching_ids = calibredb.search(search_query)
            if not matching_ids:
                logger.warning("Did not find calibre record for %s", search_query)

                try:
                    with NamedTemporaryFile(suffix='.epub', dir=str(tempdir)) as f:
                        download_serial(f.name, normalized_url, update=False, force=True)
                        new_id = calibredb.add(f.name)
                        logger.info(f"Added %s as %s", url, new_id)
                except WebserialUpdateError as e:
                    logger.warning("%s skipping", e)
                except Exception as e:
                    logger.error("🔥🔥🔥 %s 🔥🔥🔥". e)
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
                    logger.error("🔥🔥🔥 %s 🔥🔥🔥". e)


@app.command()
def add(urls: List[str], also_update: bool = False):
    config_file = os.environ.get('WEBSERIAL_UPDATE_CONFIG', 'config.toml')

    with open(config_file, 'r') as f:
        config = toml.load(f)

    config['serial_urls'].extend(urls)

    with open(config_file, 'w') as f:
        toml.dump(config, f)

    if also_update:
        update()

if __name__ == '__main__':
    app()
