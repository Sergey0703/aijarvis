import json

with open('dict.json', encoding='utf-8') as f:
    data = json.load(f)

words = data.get('words', [])
total = data.get('total', 0)
print(f'Total words returned: {total}')

dates = {}
null_count = 0
for w in words:
    td = w.get('trainDate', '')
    if not td:
        null_count += 1
    else:
        year = td[:4]
        dates[year] = dates.get(year, 0) + 1

print(f'Words with trainDate empty/null: {null_count}')
print('\nDistribution by year:')
for year in sorted(dates.keys()):
    print(f'  {year}: {dates[year]} words')

if words:
    print(f'\nFirst 5 words trainDate:')
    for i in range(min(5, len(words))):
        print(f'  {i+1}. {words[i].get("word", "?")} - trainDate: {words[i].get("trainDate", "null")}')
    print(f'\nLast 5 words trainDate:')
    for i in range(max(0, len(words)-5), len(words)):
        print(f'  {i+1}. {words[i].get("word", "?")} - trainDate: {words[i].get("trainDate", "null")}')
