from pathlib import Path

from environs import Env

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = Env()
env.read_env(str(BASE_DIR / '.env'))


class CollectDataConfig:
    github_token: str = env('GITHUB_TOKEN')

    data_dir = BASE_DIR / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    parsed_data_file_path: str = str(BASE_DIR / data_dir / 'parsed_data.json')
    filtered_file_path: str = str(BASE_DIR / data_dir / 'filtered_data.json')

    @property
    def get_httpx_headers(self) -> dict:
        return {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.cloak-preview'
        }


class Settings:
    base_dir: Path = BASE_DIR

    collect_data_config: CollectDataConfig = CollectDataConfig()


settings = Settings()
