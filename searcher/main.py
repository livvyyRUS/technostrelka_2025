import asyncio
import logging
import os
import pickle
import re
from contextlib import asynccontextmanager
from typing import List, Optional

import aiohttp
import torch
from aiohttp import ClientTimeout
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util

ip_database = "localhost:8000"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


class MovieSearchEngine:
    """
    Асинхронный класс для семантического поиска фильмов с использованием SentenceTransformer.
    Фильмы загружаются через API или добавляются через метод add_movies.
    """

    def __init__(self, api_url: str, model_name: str = "distiluse-base-multilingual-cased-v1",
                 cache_path: str = "movies_cache.pkl"):
        """
        :param api_url: URL API, с которого будут загружаться фильмы (например, "http://localhost:8000").
        :param model_name: название модели для SentenceTransformer.
        :param cache_path: путь к файлу кэша эмбеддингов и данных.
        """
        self.api_url = api_url.rstrip("/")
        self.cache_path = cache_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Используем устройство: {self.device}")
        self.model = SentenceTransformer(model_name, device=self.device)
        self.movies = []  # список фильмов (каждый фильм — словарь с ключами id, title, tagline, overview, genres, keywords)
        self.texts = []  # агрегированные текстовые представления фильмов
        self.embeddings = None

    async def init(self):
        """
        Асинхронный инициализатор: загружает фильмы из кэша или через API.
        """
        if os.path.exists(self.cache_path):
            await self.load_cache()
        else:
            await self.load_movies()
            await self.save_cache()
        return self

    def preprocess_text(self, text: Optional[str]) -> str:
        """
        Приводит текст к нижнему регистру, удаляет лишние знаки пунктуации и пробелы.
        """
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def create_movie_text(self, movie: dict) -> str:
        """
        Формирует агрегированное текстовое представление фильма на основе его полей.
        :param movie: словарь с данными фильма.
        """
        parts = []
        if movie.get("title"):
            parts.append(self.preprocess_text(movie["title"]))
        if movie.get("tagline"):
            parts.append(self.preprocess_text(movie["tagline"]))
        if movie.get("overview"):
            parts.append(self.preprocess_text(movie["overview"]))
        if movie.get("genres"):
            genres_str = ", ".join(movie["genres"])
            parts.append("жанры: " + self.preprocess_text(genres_str))
        if movie.get("keywords"):
            keywords_str = ", ".join(movie["keywords"])
            parts.append("ключевые слова: " + self.preprocess_text(keywords_str))
        return ". ".join(parts)

    async def load_movies(self):
        """
        Асинхронно загружает фильмы через API и вычисляет эмбеддинги.
        """
        try:
            async with aiohttp.ClientSession(timeout=ClientTimeout(total=9999)) as session:
                async with session.get(f"http://{ip_database}/movies/all_movies") as response:
                    response.raise_for_status()
                    movies_data = await response.json()
            self.movies = movies_data
            self.texts = [self.create_movie_text(movie) for movie in movies_data]
            embeddings = self.model.encode(self.texts, convert_to_tensor=True)
            self.embeddings = embeddings.to(self.device)
            logging.info(f"Загружено {len(self.movies)} фильмов и рассчитаны эмбеддинги.")
        except Exception as e:
            logging.error(f"Ошибка при загрузке фильмов: {e}")

    async def add_movies(self, new_movies: List[dict]):
        """
        Добавляет новые фильмы в индекс и обновляет эмбеддинги.
        :param new_movies: список словарей с данными фильма.
        """
        if not new_movies:
            return

        new_texts = [self.create_movie_text(movie) for movie in new_movies]
        new_embeddings = self.model.encode(new_texts, convert_to_tensor=True).to(self.device)
        self.movies.extend(new_movies)
        self.texts.extend(new_texts)
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = torch.cat([self.embeddings, new_embeddings], dim=0)
        logging.info(f"Добавлено {len(new_movies)} новых фильмов. Всего фильмов: {len(self.movies)}.")
        await self.save_cache()

    def search(self, query: str, top_k: int = 5):
        """
        Выполняет семантический поиск по заданному запросу.
        :param query: строка запроса.
        :param top_k: количество возвращаемых результатов.
        :return: список кортежей (фильм, сходство)
        """
        query = self.preprocess_text(query)
        query_embedding = self.model.encode(query, convert_to_tensor=True).to(self.device)
        cos_scores = util.cos_sim(query_embedding, self.embeddings)[0]
        top_results = torch.topk(cos_scores, k=top_k)
        results = []
        for score, idx in zip(top_results.values, top_results.indices):
            movie = self.movies[idx]
            results.append((movie, float(score)))
        logging.info(f"Выполнен поиск по запросу: '{query}'")
        return results

    async def save_cache(self):
        """
        Асинхронно сохраняет кэш (фильмы, тексты и эмбеддинги) в файл.
        Для работы с файловой системой используется asyncio.to_thread.
        """
        try:
            data = {
                "movies": self.movies,
                "texts": self.texts,
                "embeddings": self.embeddings.cpu() if self.embeddings is not None else None
            }
            await asyncio.to_thread(self._write_cache, data)
            logging.info(f"Кэш сохранён в {self.cache_path}.")
        except Exception as e:
            logging.error(f"Ошибка при сохранении кэша: {e}")

    def _write_cache(self, data):
        with open(self.cache_path, "wb") as f:
            pickle.dump(data, f)

    async def load_cache(self):
        """
        Асинхронно загружает кэш из файла.
        """
        try:
            data = await asyncio.to_thread(self._read_cache)
            self.movies = data["movies"]
            self.texts = data["texts"]
            self.embeddings = data["embeddings"]
            if self.embeddings is not None:
                self.embeddings = self.embeddings.to(self.device)
            logging.info(f"Кэш загружен из {self.cache_path}. Загружено {len(self.movies)} фильмов.")
        except Exception as e:
            logging.error(f"Ошибка при загрузке кэша: {e}")

    def _read_cache(self):
        with open(self.cache_path, "rb") as f:
            return pickle.load(f)


# Определяем модель данных для фильма через Pydantic
class Movie(BaseModel):
    id: int
    title: Optional[str] = None
    tagline: Optional[str] = None
    overview: Optional[str] = None
    genres: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    """
    global search_engine

    # Инициализация при старте
    api_url = f"http://{ip_database}/api/"
    search_engine = await MovieSearchEngine(api_url).init()
    logging.info("Инициализация поискового движка завершена")

    yield  # Здесь приложение работает

    # При завершении можно добавить логику очистки
    logging.info("Приложение завершает работу")


# Создаём экземпляр FastAPI с указанием lifespan-менеджера
app = FastAPI(lifespan=lifespan)

# Глобальная переменная для экземпляра поискового движка
search_engine: Optional[MovieSearchEngine] = None


@app.post("/search/add_movie")
async def add_movies(movies: List[Movie]):
    """
    Добавление списка фильмов.
    Принимает JSON-массив объектов с полями id, title, tagline, overview, genres, keywords.
    """
    if not movies:
        raise HTTPException(status_code=400, detail="Нет данных для добавления")
    movie_dicts = [movie.dict() for movie in movies]
    await search_engine.add_movies(movie_dicts)
    return {"message": f"Добавлено {len(movie_dicts)} фильмов."}


@app.get("/search")
async def search(query: str, top_k: int = 5):
    results = search_engine.search(query, top_k=top_k)
    ids = []
    for movie, score in results:
        movie_id = movie.get("row_id")
        if movie_id is not None:
            ids.append(movie_id)
        else:
            logging.warning(f"В фильме отсутствует ключ 'id': {movie}")
    return {"results": ids}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8001)
