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
1. Клонировать репозиторий:
```bash
git clone https://github.com/a-prokopenko/yatube_final.git
```
2. Перейти в директорию проекта, создать и активировать виртуальное окружение:
```bash
cd yatube_final/
python3 -m venv venv
source venv/bin/activate
```
3. Установить зависимости из файла ```requirements.txt```:
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
4. Выполнить миграции:
```bash
python3 yatube/manage.py migrate
```
5. Запустить проект:
```bash
python3 yatube/manage.py runserver
```
