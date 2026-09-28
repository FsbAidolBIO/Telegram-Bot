#!/usr/bin/env zsh
# Telegram Theme Bot Runner Script for ZSH / Bash

# Ensure script directory is working directory
cd "$(dirname "$0")"

echo "🎨 Telegram Theme Bot Launcher"
echo "=============================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️ Файл .env не найден! Создаю из .env.example..."
    cp .env.example .env
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Ошибка: python3 не установлен в системе!"
    exit 1
fi

# Check / create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Создание виртуального окружения Python (.venv)..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install / update requirements
echo "📥 Проверка и установка зависимостей..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Run unit tests to verify system integrity
echo "🧪 Запуск тестов перед стартом..."
python3 -m unittest discover tests -q

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при выполнении тестов. Проверьте файлы проекта."
    exit 1
fi

echo "🚀 Запуск бота..."
python3 bot.py
