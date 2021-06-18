import re
import subprocess

from pydantic import (
    FilePath,
    HttpUrl
)

import fanficfare
from fanficfare import adapters, writers, exceptions
from fanficfare.configurable import Configuration

from webserial_update.errors import EqualChapterError, LocalAheadOfRemoteError, NoChaptersFoundError, WebserialUpdateError

# Shamelessly stolen from https://github.com/MrTyton/AutomatedFanfic/blob/d062eb1dd8ede38208f97b95e5f73503415f61f4/fanficdownload.py
url_parsers = [
        (re.compile('(https?://).*(fanfiction.net/s/\d*)/?.*'), "www."), #ffnet - TODO confirm prefix
        (re.compile('(https?://).*(archiveofourown.org/works/\d*)/?.*'), ""), #ao3
        (re.compile('(https?://).*(fictionpress.com/s/\d*)/?.*'), ""), #fictionpress - TODO confirm prefix
        (re.compile('(https?://).*(royalroad.com/fiction/\d*)/?.*'), "www."), #royalroad
        (re.compile('(https?://)(.*)'), "") #other sites
]
equal_chapters = re.compile(r".* already contains \d* chapters.")
chapter_difference = re.compile( r".* contains \d* chapters, more than source: \d*.")
bad_chapters = re.compile( r".* doesn't contain any recognizable chapters, probably from a different source.  Not updating.")
more_chapters = re.compile( r".*File\(.*\.epub\) Updated\(.*\) more recently than Story\(.*\) - Skipping")

class FanFicFare:
    # Maybe look into not shelling out for this?
    def download_serial(self, ebook: FilePath, url: HttpUrl, update: bool = True, force: bool = False) -> str:
        command = [
             'fanficfare',
        ]

        if update:
            command.extend([
                 '-u',
                 '--update-cover',
             ])

        if force:
            command.append('--force')

        command.extend([
             '--non-interactive',
             '--option=is_adult=true',
             '--option=always_overwrite=true',
             f'--option=output_filename={ebook}',
             str(url)
        ])

        result = subprocess.run(command, capture_output=True)
        output = result.stdout.decode('utf-8')
        error = result.stderr.decode('utf-8')

        if equal_chapters.search(output):
            raise EqualChapterError("No new chapters for this serial.")
        if bad_chapters.search(output):
            raise NoChaptersFoundError("No chapters found.")
        if more_chapters.search(output):
            raise LocalAheadOfRemoteError("Your local file has been updated more recently than the story.")
        if error:
            raise WebserialUpdateError(error)

        return output

    def get_metadata(self, url: str) -> bytes:
        configuration = Configuration(adapters.getConfigSectionsFor(url), 'epub')
        adapter = adapters.getAdapter(configuration, url)
        adapter.is_adult = True
        metadata = adapter.getStoryMetadataOnly().getAllMetadata()

        return metadata
