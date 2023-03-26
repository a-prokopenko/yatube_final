# Проект Yatube — платформа для ведения блогов
[![Python](https://img.shields.io/badge/-Python-464646?style=flat&logo=Python&logoColor=ffffff&color=043A6B)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat&logo=Django&logoColor=ffffff&color=043A6B)](https://www.djangoproject.com/)
[![HTML](https://img.shields.io/badge/-HTML-464646?style=flat&logo=Html5&logoColor=ffffff&color=043A6B)](https://html.spec.whatwg.org/multipage/)
[![CSS](https://img.shields.io/badge/-CSS_Bootstrap-464646?style=flat&logo=Css3&logoColor=ffffff&color=043A6B)]([https://html.spec.whatwg.org/multipage/](https://getbootstrap.ru/))

## Описание проекта
Yatube - социальная сеть для авторов и подписчиков. Пользователи могут подписываться на избранных авторов, оставлять и удалять комментари к постам, оставлять новые посты на главной странице и в тематических группах, прикреплять изображения к публикуемым постам.

Проект реализован на MVT-архитектуре, реализована система регистрации новых пользователей, восстановление паролей пользователей через почту, система тестирования проекта на unittest, пагинация постов и кэширование страниц. Проект имеет верстку с адаптацией под размер экрана устройства пользователя.

## Технологии
- Python 3.7
- Django 2.2
- SQLite3
- Unittest
- Pytest
- CSS
- HTML

## Системные требования
- Python 3.7
- Windows/Linux/MacOS

## Установка и запуск
1. Склонируйте данный репозиторий командой:
```bash
git clone https://github.com/a-prokopenko/yatube_final.git
```
2. Перейдите в директорию проекта, создайте и активируйте виртуальное окружение следующими командами:
```bash
cd api_final_yatube/
python3 -m venv venv
```

* Если у вас Linux/macOS

    ```bash
    source env/bin/activate
    ```

* Если у вас Windows

    ```bash
    source env/scripts/activate
    ```
3. Установите зависимости из файла `requirements.txt` командой:
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```
4. Выполните миграции командой:
```bash
python3 yatube/manage.py migrate
```
5. Заполните БД начальными данными командой:
```bash
python3 yatube/manage.py loaddata yatube/data.json
```
6. Запустить проект командой:
```bash
python3 yatube/manage.py runserver
```

Развёрнутый проект доступен по адресу http://127.0.0.1:8000/
