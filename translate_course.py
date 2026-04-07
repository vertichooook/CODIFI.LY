import json
import time
from deep_translator import GoogleTranslator

def trans_text(text, target, retries=5):
    if not text: return ""
    
    # Реинициализация транслятора может помочь при некоторых ошибках сессии
    translator = GoogleTranslator(source='ru', target=target)
    
    for attempt in range(retries):
        try:
            if len(text) > 4000:
                # Умная разбивка длинного HTML-текста (Справочника) по тегам абзацев
                split_tag = "</p>"
                if split_tag in text:
                    chunks = []
                    current_chunk = ""
                    for part in text.split(split_tag):
                        # Для пустых частей после последнего сплита
                        if not part.strip(): continue
                        
                        part_with_tag = part + split_tag
                        if len(current_chunk) + len(part_with_tag) < 4000:
                            current_chunk += part_with_tag
                        else:
                            if current_chunk: chunks.append(current_chunk)
                            current_chunk = part_with_tag
                    if current_chunk: chunks.append(current_chunk)
                    
                    return "".join([translator.translate(c) for c in chunks])
                else:
                    parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
                    return "".join([translator.translate(p) for p in parts])
                    
            return translator.translate(text)

        except Exception as e:
            print(f"[Warn] Ошибка перевода (попытка {attempt+1}/{retries}): {e}")
            if attempt == retries - 1:
                return text # Возвращаем оригинал если все попытки провалились
            time.sleep(2 ** attempt) # 1s, 2s, 4s, 8s...
            
    return text

def translate_course():
    print("Loading courses...")
    try:
        with open('static/courses.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load: {e}")
        return

    print(f"Loaded {len(data)} items to translate.")
    total = len(data)
    
    for i, item in enumerate(data):
        has_changes = False
        
        # Сброс неправильного перевода (заглушки) для Справочника, если он упал в прошлый раз
        if item.get('id') == 0:
            if 'theory_en' in item and item['theory_en'] == item.get('theory'):
                del item['theory_en']
            if 'theory_de' in item and item['theory_de'] == item.get('theory'):
                del item['theory_de']
        
        # category
        if 'category' in item and item['category'] and 'category_en' not in item:
            item['category_en'] = trans_text(item['category'], 'en')
            item['category_de'] = trans_text(item['category'], 'de')
            has_changes = True
        
        # title
        if 'title' in item and item['title'] and 'title_en' not in item:
            item['title_en'] = trans_text(item['title'], 'en')
            item['title_de'] = trans_text(item['title'], 'de')
            has_changes = True
            
        # theory
        if 'theory' in item and item['theory'] and 'theory_en' not in item:
            item['theory_en'] = trans_text(item['theory'], 'en')
            item['theory_de'] = trans_text(item['theory'], 'de')
            has_changes = True
            
        # quizzes
        if 'quizzes' in item and item['quizzes']:
            for q in item['quizzes']:
                if 'question' in q and 'question_en' not in q:
                    q['question_en'] = trans_text(q['question'], 'en')
                    q['question_de'] = trans_text(q['question'], 'de')
                    has_changes = True
                if 'explanation' in q and 'explanation_en' not in q:
                    q['explanation_en'] = trans_text(q['explanation'], 'en')
                    q['explanation_de'] = trans_text(q['explanation'], 'de')
                    has_changes = True
                
                # options array
                if 'options' in q and 'options_en' not in q:
                    q['options_en'] = [trans_text(opt, 'en') for opt in q['options']]
                    q['options_de'] = [trans_text(opt, 'de') for opt in q['options']]
                    has_changes = True
                    
        # practice
        if 'practice' in item and item['practice'] is not None:
            if 'task' in item['practice'] and 'task_en' not in item['practice']:
                item['practice']['task_en'] = trans_text(item['practice']['task'], 'en')
                item['practice']['task_de'] = trans_text(item['practice']['task'], 'de')
                has_changes = True
            if 'hint' in item['practice'] and 'hint_en' not in item['practice']:
                item['practice']['hint_en'] = trans_text(item['practice']['hint'], 'en')
                item['practice']['hint_de'] = trans_text(item['practice']['hint'], 'de')
                has_changes = True
                
        if has_changes:
            print(f"[{i+1}/{total}] ID: {item.get('id', 'N/A')} - Переведено и сохранено.")
            # Save incrementally
            with open('static/courses.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            time.sleep(1.5) # Пауза только если делали переводы
        else:
            print(f"[{i+1}/{total}] ID: {item.get('id', 'N/A')} - Пропущен (уже переведен).")

    print(f"\nAll {total} items analyzed and translated successfully!")

if __name__ == '__main__':
    translate_course()
