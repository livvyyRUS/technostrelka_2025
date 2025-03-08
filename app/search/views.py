import requests
from django.shortcuts import render

from config import ip_address_db, ip_address_search, ip_address_app


def search_page(request):
    text = request.GET.get("text", None)
    if text is None:
        data = {
            "ip_address": ip_address_app
        }
        return render(request, 'search/search.html', context=data)
    else:
        response = requests.get(f'http://{ip_address_search}/search/?query={text}&top_k=9').json()
        results = response.get("results")
        string = "&movie=".join(map(str, results))
        movies = requests.get(f"http://{ip_address_db}/movies?movie={string}").json()
        data = {
            "text": text,
            "ip_address": ip_address_app,
            "recommendations": [{
                "image_url": f"homepage/images{rrr.get('poster_path')}",
                "title": rrr.get('title'),
                "description": ', '.join(rrr.get('genres')),
                "id": rrr.get('row_id')
            } for rrr in movies]
        }
        return render(request, 'search/index.html', context=data)
