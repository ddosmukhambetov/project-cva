import asyncio
import base64
import json
import os
from io import TextIOBase
from typing import cast

import httpx

from machine_learning.core.config import settings
from machine_learning.utils.signals_handler import register_signals, stop_signal_received

restricted_words_in_repository_name = (
    'offensive',
    'pentest',
    'vulnerab',
    'security',
    'hack',
    'exploit',
    'ctf ',
    ' ctf',
    'capture the flag',
    'attack'
)
restricted_words_in_repository_description = (
    'offensive security',
    'pentest',
    'exploits',
    'vulnerability research',
    'hacking',
    'security framework',
    'vulnerability database',
    'simulated attack',
    'security research'
)


def contains_restricted_word(text: str, restricted_words: tuple) -> bool:
    return any(restricted_word in text.lower() for restricted_word in restricted_words)


async def filter_irrelevant_data(parsed_data: dict, filtered_data: dict, output_file_path: str) -> None:
    async with httpx.AsyncClient() as client:

        for repository in parsed_data:
            repository_name = repository.split('https://github.com/')[-1]

            if repository_name in filtered_data['contains_restricted_words']:
                continue
            if repository_name in filtered_data['does_not_contains_restricted_words']:
                continue

            if contains_restricted_word(repository_name, restricted_words_in_repository_name):
                filtered_data['contains_restricted_words'][repository_name] = {}
                print(f'Found restricted word in repository name: {repository_name}')
                continue

            readme_url = f'https://api.github.com/repos/{repository_name}/readme'

            try:
                response = await client.get(readme_url, headers=settings.collect_data_config.get_httpx_headers)
                response.raise_for_status()

                readme_content = response.json()
                if 'content' in readme_content:
                    decoded_content = base64.b64decode(readme_content['content']).decode('utf-8')
                    if contains_restricted_word(decoded_content, restricted_words_in_repository_description):
                        filtered_data['contains_restricted_words'][repository_name] = {}
                        print(f'Found restricted word in repository description: {repository_name}')
                        continue

            except httpx.HTTPStatusError as e:
                # print(f'HTTP error occurred for repository {repository}: {e}')
                pass

            filtered_data['does_not_contains_restricted_words'][repository_name] = {}
            print(f'Repository {repository_name} does not contain restricted words')

            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, cast(TextIOBase, f), indent=4)

            if stop_signal_received:
                break


async def main() -> None:
    register_signals()

    parsed_data_file_path = settings.collect_data_config.parsed_data_file_path
    filtered_data_file_path = settings.collect_data_config.filtered_file_path

    if os.path.exists(parsed_data_file_path) and os.path.getsize(parsed_data_file_path) > 0:
        with open(parsed_data_file_path, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
    else:
        raise FileNotFoundError(f'File {parsed_data_file_path} not found, please parse data first')

    if os.path.exists(filtered_data_file_path) and os.path.getsize(filtered_data_file_path) > 0:
        with open(filtered_data_file_path, 'r', encoding='utf-8') as f:
            filtered_data = json.load(f)
    else:
        filtered_data = {'contains_restricted_words': {}, 'does_not_contains_restricted_words': {}}

    await filter_irrelevant_data(parsed_data, filtered_data, output_file_path=filtered_data_file_path)


if __name__ == '__main__':
    asyncio.run(main())
