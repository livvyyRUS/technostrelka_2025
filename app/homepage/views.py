import requests
from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect

from config import ip_address_db


def index(request, page=None):
    token = request.COOKIES.get('auth_token')
    if page is None:
        return redirect('/1')

    response = requests.get(f'http://{ip_address_db}/movies/all/?page={page}').json()
    data = {
        "recommendations": [{
            "image_url": f"homepage/images{rrr.get('poster_path')}",
            "title": rrr.get('title'),
            "description": ', '.join(rrr.get('genres')),
            "id": rrr.get('row_id')
        } for rrr in response]
    }
    return render(request, 'homepage/index.html', context=data)


def page_not_found(request, exception):
    return HttpResponseNotFound(render(request, 'homepage/error404.html'))
