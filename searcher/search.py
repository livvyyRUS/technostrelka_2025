import sqlite3
import os
import pickle
import re
import logging
from sentence_transformers import SentenceTransformer, util
import torch

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Можно менять уровень: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


class MovieSearchEngine:
    """
    Класс для семантического поиска фильмов с сохранением кэша эмбеддингов.

    Для каждого фильма объединяются поля:
      - title (название)
      - tagline (слоган)
      - overview (описание)
      - жанры (из таблицы genres)
      - ключевые слова (из таблицы keywords)

    Перед объединением текст проходит предварительную обработку:
      - приведение к нижнему регистру,
      - удаление лишних знаков пунктуации и пробелов.

    Модель SentenceTransformer загружается один раз при инициализации с использованием GPU,
    если он доступен. При загрузке фильмов и добавлении новых вычисляются эмбеддинги,
    которые сохраняются в кэше для последующих запусков.
    """

    def __init__(self, db_path, model_name="distiluse-base-multilingual-cased-v1", cache_path="movies_cache.pkl"):
        """
        Инициализация поискового движка.

        :param db_path: путь к файлу базы данных SQLite.
        :param model_name: название модели для SentenceTransformer (по умолчанию "distiluse-base-multilingual-cased-v1").
        :param cache_path: путь к файлу кэша эмбеддингов и данных.
        """
        self.db_path = db_path
        self.cache_path = cache_path
        # Определяем устройство: GPU, если доступен, иначе CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(torch.cuda.is_available())
        logging.info(f"Используем устройство: {self.device}")
        # Передаём устройство в модель
        self.model = SentenceTransformer(model_name, device=self.device)
        self.movies = []  # Список фильмов; каждый фильм – кортеж:
        # (row_id, title, tagline, overview, genres, keywords)
        self.texts = []  # Агрегированные текстовые представления фильмов.
        self.embeddings = None  # Эмбеддинги для всех фильмов (torch.Tensor).

        if os.path.exists(self.cache_path):
            self.load_cache()
        else:
            self.load_movies()
            self.save_cache()

    def preprocess_text(self, text):
        """
        Выполняет предварительную обработку текста:
         - приводит к нижнему регистру,
         - удаляет знаки пунктуации (оставляет буквы, цифры и пробелы),
         - убирает лишние пробелы.

        :param text: исходный текст.
        :return: обработанный текст.
        """
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)  # удаляем все, кроме букв, цифр и пробелов
        text = re.sub(r"\s+", " ", text)  # заменяем множественные пробелы одним
        return text.strip()

    def load_movies(self):
        """
        Загружает фильмы из базы данных.

        Объединяет данные из таблицы movies с информацией о жанрах и ключевых словах.
        Затем для каждого фильма формируется агрегированное текстовое представление,
        и на его основе вычисляются эмбеддинги.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = """
            SELECT 
                m.row_id,
                m.title,
                m.tagline,
                m.overview,
                GROUP_CONCAT(DISTINCT g.name) as genres,
                GROUP_CONCAT(DISTINCT k.name) as keywords
            FROM movies m
            LEFT JOIN movie_genres mg ON m.row_id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.row_id
            LEFT JOIN movie_keywords mk ON m.row_id = mk.movie_id
            LEFT JOIN keywords k ON mk.keyword_id = k.row_id
            GROUP BY m.row_id;
            """
            cursor.execute(query)
            movies_data = cursor.fetchall()
            conn.close()

            self.movies = movies_data
            self.texts = [self.create_movie_text(movie) for movie in movies_data]
            # Вычисляем эмбеддинги с использованием GPU (модель сама использует self.device)
            embeddings = self.model.encode(self.texts, convert_to_tensor=True)
            # Перемещаем эмбеддинги на устройство (если требуется) – для кэширования переводим на CPU
            self.embeddings = embeddings.to(self.device)
            logging.info(f"Загружено {len(self.movies)} фильмов и рассчитаны эмбеддинги.")
        except Exception as e:
            logging.error(f"Ошибка при загрузке фильмов: {e}")

    def create_movie_text(self, movie):
        """
        Формирует агрегированное текстовое представление фильма на основе нескольких полей.

        :param movie: кортеж (row_id, title, tagline, overview, genres, keywords)
        :return: строка с объединённым описанием фильма.
        """
        row_id, title, tagline, overview, genres, keywords = movie
        parts = []
        if title:
            parts.append(self.preprocess_text(title))
        if tagline:
            parts.append(self.preprocess_text(tagline))
        if overview:
            parts.append(self.preprocess_text(overview))
        if genres:
            parts.append("жанры: " + self.preprocess_text(genres))
        if keywords:
            parts.append("ключевые слова: " + self.preprocess_text(keywords))
        return ". ".join(parts)

    def add_movies(self, new_movies):
        """
        Добавляет новые фильмы в индекс.

        :param new_movies: список кортежей (row_id, title, tagline, overview, genres, keywords)
                           для новых фильмов.
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
        self.save_cache()  # Обновляем кэш после добавления новых фильмов

    def search(self, query, top_k=5):
        """
        Выполняет семантический поиск по заданному запросу.

        :param query: поисковый запрос (строка).
        :param top_k: количество возвращаемых результатов (по умолчанию 5).
        :return: список кортежей (movie, similarity), где movie – кортеж с данными фильма.
        """
        # Предварительная обработка запроса
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

    def save_cache(self):
        """
        Сохраняет кэш данных (фильмы, агрегированные тексты и эмбеддинги) в файл.
        Перед сохранением эмбеддинги переводятся на CPU.
        """
        try:
            data = {
                "movies": self.movies,
                "texts": self.texts,
                "embeddings": self.embeddings.cpu() if self.embeddings is not None else None
            }
            with open(self.cache_path, "wb") as f:
                pickle.dump(data, f)
            logging.info(f"Кэш сохранён в {self.cache_path}.")
        except Exception as e:
            logging.error(f"Ошибка при сохранении кэша: {e}")

    def load_cache(self):
        """
        Загружает кэш данных из файла.
        После загрузки, если используется GPU, эмбеддинги переводятся обратно на нужное устройство.
        """
        try:
            with open(self.cache_path, "rb") as f:
                data = pickle.load(f)
            self.movies = data["movies"]
            self.texts = data["texts"]
            self.embeddings = data["embeddings"]
            if self.embeddings is not None:
                self.embeddings = self.embeddings.to(self.device)
            logging.info(f"Кэш загружен из {self.cache_path}. Загружено {len(self.movies)} фильмов.")
        except Exception as e:
            logging.error(f"Ошибка при загрузке кэша: {e}")


if __name__ == "__main__":
    db_path = "tmdb_database.db"  # Замените на актуальный путь к вашей базе данных
    search_engine = MovieSearchEngine(db_path)

    query = input("Поиск: ")
    while query:
        results = search_engine.search(query, top_k=5)
        logging.info("Результаты поиска:")
        for movie, score in results:
            row_id, title, tagline, overview, genres, keywords = movie
            logging.info(f"\nID: {row_id}\nНазвание: {title}\nТеглайн: {tagline}\nОписание: {overview}\n"
                         f"Жанры: {genres}\nКлючевые слова: {keywords}\nСходство: {score:.4f}\n")
        query = input("Поиск: ")
