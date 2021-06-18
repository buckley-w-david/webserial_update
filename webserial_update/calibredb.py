import re
import subprocess
from typing import List, Dict, Tuple

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
            'calibredb',
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

    def get_metadata(self, calibre_id: int) -> Dict[str, str]:
        completed_process = self.run(['show_metadata', str(calibre_id)])
        result = completed_process.stdout.decode('utf-8')
        if result:
            ret = {}
            for line in result.split("\n"):
                try:
                    key, value = line.split(":", 1)
                    ret[key.strip()] = value.strip()
                except Exception:
                    pass
            return ret
        else:
            return {}

    def set_metadata(self, calibre_id: int, metadata: List[Tuple[str, str]]) -> None:
        command = ['set_metadata', str(calibre_id)]
        for name, value in metadata:
            command.append(f"--field")
            command.append(f"{name}:{value}")

        completed_process = self.run(command)
        return completed_process.stdout.decode('utf-8')

    def export(self, id: int, output_directory: DirectoryPath) -> str:
        completed_process = self.run(['export', str(id), '--dont-save-cover', '--dont-write-opf', '--single-dir', '--to-dir', str(output_directory)])
        return completed_process.stdout

    def remove(self, id: int) -> str:
        completed_process = self.run(['remove', str(id)])
        return completed_process.stdout.decode('utf-8')

    def add(self, ebook: FilePath, duplicate: bool = True) -> int:
        # FIXME use duplicate flag
        completed_process = self.run(['add', '-d', str(ebook)])
        result = completed_process.stdout.decode('utf-8')
        err = completed_process.stderr.decode('utf-8')
        match = added.search(result)
        if match:
            return int(match.group(1))
        else:
            raise WebserialUpdateError(result if not err else err)
