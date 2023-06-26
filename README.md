Yatube - социальная сеть с возможностью авторизации, лентой персональных новостей, комментариями и подписками на авторов статейю

Как запустить проект:
    Клонировать репозиторий и перейти в него в командной строке:
    git clone [git@github.com:Anastasia7Si/hw05_final.git ](https://github.com/Anastasia7Si/hw05_final)
    cd api_yamdb
    
    Cоздать и активировать виртуальное окружение:
    python -m venv venv 
    source venv/Scripts/activate
    
    Установить зависимости из файла requirements.txt:
    pip install -r requirements.txt
    
    Выполнить миграции:
    python manage.py makemigrations
    python manage.py migrate

    Запустить проект:
    python manage.py runserver

Технологии:
Python 3.7 Django 3.2
