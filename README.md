# REST API (backend) для сервиса объявлений
### Идея
Создать RESTful API, архитектура которого облегчает расширение и замену составляющих. 
Например, чтобы можно было безболезненно заменить одну БД на другую.  
Конечно, нет смысла тратить время и силы на дополнительные абстракции, когда функционал 
приложения прост. Но цель этого проекта - самообучение его автора :wink:  
Простая реализация CRUD-приложения на Flask (один из моих проектов во время учебы в Нетологии) - [здесь](https://github.com/Femarko/Flask_HW/tree/task_1).
### Функционал
  - аутентификация и авторизация пользователей
  - CRUD-операции с объявлениями
  - поиск объявлений, в т.ч. по тексту
### Стек
  - python 3.10.12
  - pydantic
  - bcrypt
  - PostgreSQL
  - PGAdmin
  - SQLAlchemy
  - docker, docker-compose
  - pytest
  - pytest-cov
  - Linux
  - Git, GiHub
  - Flask
### Структура приложения
  - [domain](https://github.com/femarko/advert/tree/main/app/domain) (предметная область):
    - ```models.py``` - классы Python, *не связанные с таблицами БД*
    - ```services.py``` - функции, создающие пользователя / объявление, обновляющие и возвращающие их параметры
    - ```errors.py``` - кастомные классы исключений, использующиеся в приложении как часть бизнес-логики
  - [orm](https://github.com/femarko/advert/tree/main/app/orm):
    - ```__init__.py``` - инициализация object-relational mapper (```SQLAlchemy```)
    - ```table-mapper.py``` - мэппинг классов python из ```models.py``` с таблицами БД (imperative mapping)
  - [repository](https://github.com/femarko/advert/tree/main/app/repository) (абстракция постоянного хранилища данных):
    - ```repository.py``` - абстракция, реализующая доступ к БД
    - ```filtering.py``` - функционал фильтрации данных из постоянного хранилища
  - [pass_hashing_and_validation](https://github.com/femarko/advert/tree/main/app/pass_hashing_and_validation):
    - ```pass_hashing.py``` - хэширование паролей (библиотека ```bcrypt```)
    - ```validation.py``` - валидация входящих данных (библиотека ```pydantic```)
  - [flask_entrypoints](https://github.com/femarko/advert/tree/main/app/flask_entrypoints) (web-API приложения):
    - ```views.py``` - функции, которые принимают HTTP-запросы, вызывают функции из ```service_layer/app_manager.py```, передают им входящие данные и зависимости, возвращают ответы на HTTP-запросы
    - ```authentication.py``` - аутентификация пользователей (библиотека ```flask_jwt_extended```)
    - ```error_handlers.py``` - реализация кастомного исключения для web-API
    - ```run_app.py``` - запуск приложения ```Flask```
    - ```__init__.py``` - инициализация приложения ```Flask```  
  - [service_layer](https://github.com/femarko/advert/tree/main/app/service_layer):
    - ```unit_of_work.py``` - абстракция единицы работы, предоставляющая 
    сеанс взаимодействия с постоянным хранилищем данных
    - ```app_manager.py``` - функции, которые принимают входящие данные, необходимые 
    зависимости, вызывают нужные службы, в т.ч. ```unit_of_work```, фиксируют 
    изменения в БД, возвращают результат работы вызванных служб
### База данных
  - БД (```PostreSQL```) и средство просмотра ее таблиц (```PGAdmin```) "поднимаются" в docker-контейнерах ([docker-compose.yml](https://github.com/femarko/adv_app/blob/main/docker-compose.yml)).
### Тесты
Использовано pytest, pytest-cov.  
- [e2e](): тесты задейсвуют все элементы приложения, включая web-API и БД
- [integration](): тестируются функции, задействующие ORM и БД
- [unit](): изолированно тестируются отдельные функции, изоляция достигается использованием "фейков", имитирующих зависимости
### Запуск на локальном хосте
На данном этапе приложение еще не развернуто на сервере и не "упаковано" в 
docker-контейнеры. Проект можно склонировать и запустить в режиме debug на локальном 
хосте:  
```python
$ git clone git@github.com:femarko/advert.git
$ python3 -m venv venv_advert
$ source venv_advert/bin/activate  # for Linux
$ venv_advert\Scripts\activate  # for Windows
```
Необходимо также создать файл ```.env``` (образец: [.env.example]()) и установить зависимости 
в виртуальное окружение и запустить docker-контейнеры с базой данных и
```PGAdmin```:  
```python
$ pip install -r requirements.txt
$ docker-compose up -d
```



