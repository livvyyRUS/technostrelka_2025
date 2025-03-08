# Запуск микросервиса базы данных

Перейдите в директорию с данным микросервисом
```shell
cd database
```

Если требуется, то установите requirements.txt
```shell
pip install requirements.txt
```

Добавьте в директорию data файл tmdb_database.db, который располагается на яндекс диске - https://disk.yandex.ru/d/EHhKA0Pxe8b7BA

Запустите проект
```shell
python main.py
```

Парсер находится в этой же директории


Для его работы требуется api_key из TMDB\
Запуск парсера
```shell
python parser.py
```

# Запуск микросервиса поиска

Перейдите в директорию с данным микросервисом
```shell
cd searcher
```

Если требуется, то установите requirements.txt
```shell
pip install requirements.txt
```

Запустите проект
```shell
python main.py
```

# Запуск микросервиса веб-сервиса

Перейдите в директорию с данным микросервисом
```shell
cd app/NEkinopoisk
```

Если требуется, то установите requirements.txt
```shell
pip install requirements.txt
```

Запустите проект (айпи и порт могут быть другими)
```shell
python manage.py runserver localhost:80
```


# Смена айпи адресов
Если требуется сменить айпи адреса или порты, то меняется в следующих местах:
В каждом main.py в database и в searcher

В конфиге в app/NEkinopoisk