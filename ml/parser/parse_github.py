import asyncio
import json
import os
import pathlib
import signal
import time
from io import TextIOBase
from typing import cast

import httpx
from environs import Env
from tqdm import tqdm

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

env = Env()
env.read_env(str(BASE_DIR / '.env'))

github_token = env('GITHUB_TOKEN')

keywords = (
    'buffer overflow',
    'denial of service',
    'dos',
    'XML External Entity (XXE)',
    'vulnerability',
    'CVE',
    'Cross-Site Scripting (XSS)',
    'National Vulnerability Database (NVD)',
    'malicious code',
    'Cross-Site Request Forgery (CSRF)',
    'exploit',
    'directory traversal',
    'Remote Code Execution (RCE)',
    'Cross-Site Request Forgery (XSRF)',
    'session fixation',
    'cross-origin resource sharing (CORS)',
    'infinite loop',
    'brute force',
    'cache overflow',
    'command injection',
    'cross frame scripting',
    'CSV injection',
    'eval injection',
    'execution after redirect',
    'format string',
    'path disclosure',
    'function injection',
    'replay attack',
    'session hijacking',
    'smurf attack',
    'SQL injection',
    'flooding',
    'data tampering',
    'input sanitization',
    'hardcoded secret',
    'insecure deserialization',
    'credential leakage',
    'information disclosure',
    'user enumeration',
    'race condition',
    'parameter pollution',
    'XML injection',
    'API key exposure',
    'arbitrary file upload',
    'insufficient logging',
)
suffixes = (
    'prevent',
    'fix',
    'attack',
    'protect',
    'issue',
    'correct',
    'update',
    'improve',
    'change',
    'check',
    'malicious',
    'insecure',
    'vulnerable',
    'vulnerability',
    'remediate',
    'secure',
    'audit',
    'identify',
    'document',
    'expose',
    'monitor',
    'analyze',
)
keywords_tuple = tuple(f'{keyword} {suffix}' for keyword in keywords for suffix in suffixes)


def signal_handler(signal, frame):
    global stop_signal_received
    stop_signal_received = True
    print("Stop signal received (CTRL + C), exiting...")


stop_signal_received = False
signal.signal(signal.SIGINT, signal_handler)


async def fetch_commits_by_keyword(keyword: str, commits: dict, token: str, output_file_path: str) -> None:
    per_page = 100
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.cloak-preview'}
    url, params = 'https://api.github.com/search/commits', {'q': keyword, 'per_page': per_page}

    pbar = tqdm(total=per_page, desc=f'Fetching commits for {keyword}', unit='commit')

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(url, headers=headers, params=params)
            remaining_limit = int(response.headers.get('X-RateLimit-Remaining', 0))
            if remaining_limit == 0:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0) - time.time())
                print(f"Rate limit exceeded. Reset time: {reset_time} seconds")
                await asyncio.sleep(max(0, reset_time))

            response.raise_for_status()

            data = response.json()
            for item in data.get('items', []):
                repository_url = item['repository']['html_url']
                if repository_url not in commits:
                    commit_data = {
                        'url': item['url'],
                        'html_url': item['html_url'],
                        'sha': item['sha'],
                        'message': item['commit']['message'],
                        'keyword': keyword,
                    }
                    commits[repository_url] = {}
                    commits[repository_url][item['sha']] = commit_data
                    pbar.update(1)
                else:
                    if item['sha'] not in commits[repository_url]:
                        commit_data = {
                            'url': item['url'],
                            'html_url': item['html_url'],
                            'sha': item['sha'],
                            'message': item['commit']['message'],
                            'keyword': keyword,
                        }
                        commits[repository_url][item['sha']] = commit_data
                        pbar.update(1)

                with open(output_file_path, 'w', encoding='utf-8') as f:
                    json.dump(commits, cast(TextIOBase, f), indent=4, ensure_ascii=False)

                if stop_signal_received:
                    break
            if stop_signal_received:
                break

            if 'Link' in response.headers:
                links = response.headers['Link'].split(',')
                next_link = [link[link.index('<') + 1:link.index('>')] for link in links if 'rel="next"' in link][0]
                url = next_link if next_link else None
            else:
                url = None


async def main() -> None:
    data_dir = BASE_DIR / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = str(data_dir / 'commits.json')

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r', encoding='utf-8') as f:
            commits = json.load(f)
    else:
        commits = {}

    for keyword in keywords_tuple:
        await fetch_commits_by_keyword(keyword, commits, github_token, output_file_path=file_path)
        if stop_signal_received:
            break


if __name__ == '__main__':
    asyncio.run(main())
