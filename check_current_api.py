import json
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dict_current.json', encoding='utf-8') as f:
    data = json.load(f)

words = data.get('words', [])
print(f'Total words: {len(words)}')

print(f'\nПервые 10 слов:')
for i, w in enumerate(words[:10], 1):
    print(f'  {i}. {w.get("word", "?")} - trainDate: {w.get("trainDate", "?")}')

print(f'\nПоследние 10 слов:')
for i, w in enumerate(words[-10:], len(words)-9):
    print(f'  {i}. {w.get("word", "?")} - trainDate: {w.get("trainDate", "?")}')

# Группируем по датам
dates = {}
for w in words:
    d = w.get('trainDate', '')[:10] if w.get('trainDate') else 'null'
    dates[d] = dates.get(d, 0) + 1

print(f'\nРаспределение по датам:')
for d in sorted(dates.keys()):
    print(f'  {d}: {dates[d]} слов')
