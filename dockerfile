FROM python:3.13-alpine

# Устанавливаем зависимости
RUN apk add --no-cache gcc musl-dev libpq-dev postgresql-client

WORKDIR /backend

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код и скрипт ожидания
COPY . .
COPY wait-for-postgres.sh /wait-for-postgres.sh
RUN chmod +x /wait-for-postgres.sh

# Открываем порт
EXPOSE 8082

# По умолчанию запускаем приложение
CMD ["python3", "main.py"]