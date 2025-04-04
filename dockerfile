FROM python:3.13-alpine

# Устанавливаем зависимости
RUN apk add --no-cache gcc musl-dev libpq-dev

WORKDIR /backend

# Копируем файлы проекта
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Открываем порт
EXPOSE 8082

# Запускаем приложение
CMD ["python3", "main.py"]
