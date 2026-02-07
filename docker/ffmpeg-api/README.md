# FFmpeg Audio Compressor API

Простой API для сжатия аудио файлов (оптимизация для транскрибации речи).

## Сжатие
- Моно (вместо стерео)
- 16kHz (вместо 44.1kHz)
- 32kbps битрейт
- Формат: MP3

**Результат**: 15 МБ → 4-5 МБ (~70% уменьшение)
**Скорость транскрибации**: 6-7 минут → 2-3 минуты

## Деплой на сервер

### 1. Загрузить файлы на сервер
```bash
scp -i "c:/projects/aijarvis/.ssh_hetzner_key" -r "c:/projects/aijarvis/docker/ffmpeg-api" root@46.62.246.93:/opt/
```

### 2. SSH на сервер и запустить
```bash
ssh -i "c:/projects/aijarvis/.ssh_hetzner_key" root@46.62.246.93
cd /opt/ffmpeg-api
docker compose up -d --build
```

### 3. Проверить
```bash
docker logs ffmpeg-audio-compressor
curl http://localhost:3000/health
```

## API Endpoints

### POST /compress
Сжимает аудио файл.

**Request**: multipart/form-data с полем `audio`

**Response**: Сжатый MP3 файл

### GET /health
Проверка статуса сервиса.

**Response**: `{"status": "ok", "service": "ffmpeg-audio-compressor"}`
