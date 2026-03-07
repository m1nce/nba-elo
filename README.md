<h1>🚧 THIS PROJECT IS STILL UNDER CONSTRUCTION! 🚧</h1>

# NBA Elo Simulator 🏀

Inspired by [Mr V's Garage F1 ELO Engine](https://www.youtube.com/watch?v=U16a8tdrbII&t=329s), this project aims to simulate an Elo engine on NBA game data.

Note: Data used in this project was web scraped from [basketball-reference.com](https://www.basketball-reference.com/) and [wikipedia.org](https://www.wikipedia.org/).

<!-- GETTING STARTED -->
## Getting Started

The following instructions will guide you through setting up a copy of the project on your local machine for development and testing purposes.

### Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js 22** — use [nvm](https://github.com/nvm-sh/nvm): `nvm install` (reads `.nvmrc`)
- **pnpm 10** — `corepack enable && corepack prepare pnpm@10 --activate`
- **Python 3.11+** with [uv](https://docs.astral.sh/uv/) — `pip install uv`
- **PostgreSQL** — running locally with a database named `nba_elo`

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/m1nce/nba-rating.git
   cd nba-rating
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and update `DATABASE_URL` if your PostgreSQL credentials differ from the defaults:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/nba_elo
   ```

3. **Install Python dependencies**
   ```bash
   uv sync
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend && pnpm install && cd ..
   ```

### Data Setup

5. **Scrape game data** (outputs `data/1975-2024.csv` — takes several minutes due to rate limiting)
   ```bash
   uv run python -m backend.NBAScraper --beginning 1975 --end 2024
   ```

6. **Migrate data and seed Elo ratings into PostgreSQL**
   ```bash
   uv run python -m backend.migrate
   ```

### Running the App

7. **Start the backend** (API available at http://127.0.0.1:8000)
   ```bash
   uv run uvicorn backend.app.main:app --reload
   ```

8. **Start the frontend** (in a separate terminal, available at http://localhost:5173)
   ```bash
   cd frontend && pnpm run dev
   ```

<!-- LANGUAGES/FRAMEWORKS -->
## Built With

Major frameworks/libraries/languages used in this project:

* [![Python][Python]][Python-url]
* [![FastAPI][FastAPI]][FastAPI-url]
* [![React][React]][React-url]
* [![TypeScript][TypeScript]][TypeScript-url]

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<!-- MARKDOWN LINKS & IMAGES -->
[Python]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[Python-url]: https://www.python.org/about/
[FastAPI]: https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi
[FastAPI-url]: https://fastapi.tiangolo.com/
[React]: https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB
[React-url]: https://react.dev/
[TypeScript]: https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white
[TypeScript-url]: https://www.typescriptlang.org/
