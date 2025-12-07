FROM python:3.11-slim

# Системные зависимости для аудио/видео обработки
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код агента
COPY agent.py .

# Переменные окружения (будут автоматически инжектированы Hugging Face Spaces)
ENV PYTHONUNBUFFERED=1

# Экспонируем порт 7860 (стандарт HF Spaces для HTTP)
EXPOSE 7860

# Запускаем агента в production режиме
CMD ["python", "agent.py", "start"]
