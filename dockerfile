FROM python:3.13-alpine

# Устанавливаем системные зависимости
RUN apk add --no-cache gcc musl-dev libpq-dev postgresql-client

WORKDIR /backend

# Копируем только requirements.txt для кэширования установки зависимостей
COPY requirements.txt .

# Устанавливаем зависимости (если requirements.txt не изменился, этот слой кэшируется)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной исходный код и скрипт ожидания
COPY . .
COPY wait-for-postgres.sh /wait-for-postgres.sh
RUN chmod +x /wait-for-postgres.sh

# Открываем порт
EXPOSE 8082

# По умолчанию запускаем приложение
CMD ["python3", "main.py"]
