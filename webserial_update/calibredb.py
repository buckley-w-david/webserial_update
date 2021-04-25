import re
import subprocess
from typing import List

from pydantic import FilePath, DirectoryPath

from webserial_update.errors import WebserialUpdateError

added = re.compile(r"Added book ids: (\d+)")
class CalibreDb:
    def __init__(self, username: str, password: str, library: str):
        self.username = username
        self.password = password
        self.library = library

    def run(self, command):
        full_command = [
            '/usr/bin/python', '/usr/bin/calibredb', # Have to specifically use system python here since we're in a virtual environment
            *command,
            '--with-library', self.library,
            '--username', self.username,
            '--password', self.password
        ]

        return subprocess.run(
            full_command,
            capture_output=True
        )

    def search(self, query: str) -> List[int]:
        completed_process = self.run(['search', query])
        result = completed_process.stdout.decode('utf-8')
        if result:
            return [int(id) for id in result.split(',')]
        else:
            return []

    def export(self, id: int, output_directory: DirectoryPath) -> str:
        completed_process = self.run(['export', str(id), '--dont-save-cover', '--dont-write-opf', '--single-dir', '--to-dir', str(output_directory)])
        return completed_process.stdout

    def remove(self, id: int) -> str:
        completed_process = self.run(['remove', str(id)])
        return completed_process.stdout.decode('utf-8')

    def add(self, ebook: FilePath, duplicate: bool = True) -> int:
        # TODO use duplicate flag
        completed_process = self.run(['add', '-d', str(ebook)])
        result = completed_process.stdout.decode('utf-8')
        match = added.search(result)
        if match:
            return int(match.group(1))
        else:
            raise WebserialUpdateError("Something went wrong adding the book")
