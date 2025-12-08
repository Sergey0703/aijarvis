"""
Тестовый скрипт для проверки MongoDB подключения
"""
import os
from mongodb_client import VocabularyClient

# Установите ваш connection string
os.environ["MONGODB_URI"] = "mongodb+srv://sergey0703:<password>@cluster0.llssu.mongodb.net/?retryWrites=true&w=majority"
os.environ["MONGODB_DB"] = "cluster0"
os.environ["MONGODB_COLLECTION"] = "words"

def test_vocabulary():
    """Тестируем все функции VocabularyClient"""

    print("=" * 60)
    print("TESTING MONGODB VOCABULARY CLIENT")
    print("=" * 60)

    # Создаём клиента
    vocab = VocabularyClient()

    # Проверяем подключение
    print(f"\n✅ Connected: {vocab.is_connected()}")

    if not vocab.is_connected():
        print("❌ Failed to connect. Check MONGODB_URI")
        return

    # Статистика словаря
    print("\n📊 VOCABULARY STATISTICS:")
    stats = vocab.get_word_count()
    print(f"  Total words: {stats['total']}")
    print(f"  Trained: {stats['trained']}")
    print(f"  Untrained: {stats['untrained']}")

    # Получаем 5 случайных слов
    print("\n🎲 RANDOM 5 WORDS:")
    random_words = vocab.get_random_words(count=5)
    for word_data in random_words:
        word = word_data.get("word")
        translate = word_data.get("translate")
        traini = word_data.get("traini", False)
        status = "✅" if traini else "❌"
        print(f"  {status} {word} - {translate}")

    # Получаем не тренированные слова
    print("\n📖 UNTRAINED WORDS (first 3):")
    untrained = vocab.get_untrained_words(count=3)
    for word_data in untrained:
        word = word_data.get("word")
        translate = word_data.get("translate")
        print(f"  📝 {word} - {translate}")

    # Тестируем поиск слова
    print("\n🔍 SEARCH WORD 'epilraph':")
    word_data = vocab.search_word("epilraph")
    if word_data:
        print(f"  Found: {word_data.get('word')}")
        print(f"  Translation: {word_data.get('translate')}")
        print(f"  Transcript: {word_data.get('transcript')}")
        print(f"  Trained: {word_data.get('traini')}")

    # Форматируем слово для урока
    if word_data:
        print("\n📄 FORMATTED FOR LESSON:")
        lesson_text = vocab.format_word_for_lesson(word_data)
        print(f"  {lesson_text}")

    # Закрываем соединение
    vocab.close()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    test_vocabulary()
