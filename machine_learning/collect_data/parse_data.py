import asyncio
import json
import os
import time
from io import TextIOBase
from typing import cast

import httpx
from tqdm import tqdm

from machine_learning.core.config import settings
from machine_learning.utils.signals_handler import register_signals, stop_signal_received

keywords = (
    'buffer overflow', 'denial of service', 'dos', 'XML External Entity (XXE)', 'CVE', 'Cross-Site Scripting (XSS)',
    'National Vulnerability Database (NVD)', 'malicious code', 'Cross-Site Request Forgery (CSRF)',
    'directory traversal', 'Remote Code Execution (RCE)', 'Cross-Site Request Forgery (XSRF)', 'session fixation',
    'cross-origin resource sharing (CORS)', 'infinite loop', 'brute force', 'cache overflow', 'command injection',
    'cross frame scripting', 'CSV injection', 'eval injection', 'execution after redirect', 'format string',
    'path disclosure', 'function injection', 'replay attack', 'session hijacking', 'smurf attack', 'SQL injection',
    'flooding', 'data tampering', 'input sanitization', 'hardcoded secret', 'insecure deserialization',
    'credential leakage', 'information disclosure', 'user enumeration', 'race condition', 'parameter pollution',
    'XML injection', 'API key exposure', 'arbitrary file upload', 'insufficient logging',
)
suffixes = (
    'prevent', 'fix', 'attack', 'protect', 'issue', 'correct', 'update', 'improve', 'change', 'check', 'malicious',
    'insecure', 'vulnerable', 'vulnerability', 'remediate', 'secure', 'audit', 'identify', 'document', 'expose',
    'monitor', 'analyze',
)
keywords_tuple = tuple(f'{keyword.lower()} {suffix.lower()}' for keyword in keywords for suffix in suffixes)


async def fetch_commits_by_keyword(keyword: str, parsed_data: dict, output_file_path: str) -> None:
    per_page = 100
    url, params = 'https://api.github.com/search/commits', {'q': keyword, 'per_page': per_page, 'page': 1}

    pbar = tqdm(desc=f'Fetching commits for {keyword}', unit='commit')

    async with httpx.AsyncClient() as client:
        while url:
            try:
                response = await client.get(url, headers=settings.collect_data_config.get_httpx_headers, params=params)
                remaining_limit = int(response.headers.get('X-RateLimit-Remaining', 0))
                if remaining_limit == 0:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0) - time.time())
                    print(f"Rate limit exceeded. Reset time: {reset_time} seconds")
                    await asyncio.sleep(max(0, reset_time))

                response.raise_for_status()

                data = response.json()
                for item in data.get('items', []):
                    repository_html_url = item['repository']['html_url']
                    if repository_html_url not in parsed_data:
                        commit_data = {
                            'url': item['url'],
                            'html_url': item['html_url'],
                            'sha': item['sha'],
                            'message': item['commit']['message'],
                            'keyword': keyword,
                        }
                        parsed_data[repository_html_url] = {}
                        parsed_data[repository_html_url][item['sha']] = commit_data
                        pbar.update(1)
                    else:
                        if item['sha'] not in parsed_data[repository_html_url]:
                            commit_data = {
                                'url': item['url'],
                                'html_url': item['html_url'],
                                'sha': item['sha'],
                                'message': item['commit']['message'],
                                'keyword': keyword,
                            }
                            parsed_data[repository_html_url][item['sha']] = commit_data
                            pbar.update(1)

                    with open(output_file_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed_data, cast(TextIOBase, f), indent=4, ensure_ascii=False)

                    if stop_signal_received:
                        break
                if stop_signal_received:
                    break

                if 'Link' in response.headers:
                    links = response.headers['Link'].split(',')
                    next_link = [link[link.index('<') + 1:link.index('>')] for link in links if 'rel="next"' in link]
                    url = next_link[0] if next_link else None
                    params = {}
                else:
                    url = None

            except httpx.HTTPStatusError as e:
                print(f'HTTP error occurred for keyword {keyword}: {e}')
                break


async def main() -> None:
    register_signals()

    file_path = settings.collect_data_config.parsed_data_file_path

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
    else:
        parsed_data = {}

    for keyword in keywords_tuple:
        await fetch_commits_by_keyword(keyword, parsed_data, output_file_path=file_path)
        if stop_signal_received:
            break


if __name__ == '__main__':
    asyncio.run(main())
