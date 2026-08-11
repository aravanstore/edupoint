# -*- coding: utf-8 -*-
"""Собирает JSON-словари переводов (de/ko/zh-hans) из scratchpad, мержит их
в один каталог и компилирует .po/.mo для каждого языка через polib
(чистый Python, не требует установленного GNU gettext).
Запуск: python build_translations.py
"""
import json
import os
import glob

BASE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = r"C:\Users\user\AppData\Local\Temp\claude\C--Projects-islom-kaziat--claude-worktrees-run-folder-b-hosting-0d3a6c\e3ee32bb-acc6-434d-b406-5bf61491e72c\scratchpad"

LANG_DIRS = {
    'de': 'de',
    'ko': 'ko',
    'zh-hans': 'zh_Hans',
}

json_files = sorted(glob.glob(os.path.join(SCRATCH, 'i18n_*.json')))
print(f'Найдено словарей: {len(json_files)}')
for f in json_files:
    print('  -', os.path.basename(f))

merged = {}
conflicts = []

for path in json_files:
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    for msgid, translations in data.items():
        if msgid in merged:
            for lang in LANG_DIRS:
                existing = merged[msgid].get(lang, '')
                new = translations.get(lang, '')
                if existing and new and existing != new:
                    conflicts.append((msgid, lang, existing, new, os.path.basename(path)))
            # keep the first occurrence, fill in any missing langs
            for lang in LANG_DIRS:
                if not merged[msgid].get(lang) and translations.get(lang):
                    merged[msgid][lang] = translations[lang]
        else:
            merged[msgid] = dict(translations)

print(f'\nВсего уникальных строк: {len(merged)}')
if conflicts:
    print(f'\nКОНФЛИКТЫ ПЕРЕВОДА ({len(conflicts)}) — оставлен первый вариант:')
    for msgid, lang, old, new, src in conflicts:
        print(f'  [{lang}] "{msgid[:50]}" -> оставлено: "{old[:50]}" / из {src}: "{new[:50]}"')

# Сохраним объединённый словарь для справки
with open(os.path.join(BASE, 'locale', '_merged_translations.json'), 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2, sort_keys=True)

import polib

for lang_code, dir_name in LANG_DIRS.items():
    po = polib.POFile()
    po.metadata = {
        'Project-Id-Version': 'Edu Point 1.0',
        'Report-Msgid-Bugs-To': '',
        'POT-Creation-Date': '2026-08-10 00:00+0600',
        'PO-Revision-Date': '2026-08-10 00:00+0600',
        'Language': lang_code,
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=UTF-8',
        'Content-Transfer-Encoding': '8bit',
    }
    count = 0
    for msgid, translations in merged.items():
        msgstr = translations.get(lang_code, '')
        if not msgstr:
            continue
        entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
        po.append(entry)
        count += 1

    lc_dir = os.path.join(BASE, 'locale', dir_name, 'LC_MESSAGES')
    os.makedirs(lc_dir, exist_ok=True)
    po_path = os.path.join(lc_dir, 'django.po')
    mo_path = os.path.join(lc_dir, 'django.mo')
    po.save(po_path)
    po.save_as_mofile(mo_path)
    print(f'{lang_code}: {count} строк -> {mo_path}')

print('\nГотово.')
