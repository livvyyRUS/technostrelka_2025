import requests
from django.shortcuts import render

from config import ip_address_db


def movie(request, id_film):
    response = requests.get(f'http://{ip_address_db}/movies/?movie={id_film}')
    answer = response.json()[0]

    data = {
        "poster_path": f"homepage/images{answer.get('poster_path')}",
        "genres": ', '.join(answer.get('genres')),
        "release_date": answer.get('release_date'),
        "vote_average": round(answer.get('vote_average'), 1),
        "title": answer.get('title'),
        "overview": answer.get('overview')
    }
    return render(request, 'movie/movie.html', context=data)
