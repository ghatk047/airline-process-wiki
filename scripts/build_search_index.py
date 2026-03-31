#!/usr/bin/env python3
"""
build_search_index.py
Generates search-index.json at the repo root from data/processes.json.
Run after each pipeline batch: python3 scripts/build_search_index.py
"""
import json, os, sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSES_JSON = os.path.join(REPO_ROOT, 'data', 'processes.json')
OUTPUT_PATH    = os.path.join(REPO_ROOT, 'search-index.json')
BASE_PATH      = 'airline-process-wiki'  # GitHub Pages base path

def build_index():
    with open(PROCESSES_JSON, encoding='utf-8') as f:
        data = json.load(f)

    procs = data.get('processes', [])
    index = []

    for p in procs:
        if p.get('status') != 'Complete':
            continue

        step_names = []
        systems    = []
        for step in p.get('l4_steps', []):
            sn = step.get('name', '').strip()
            if sn:
                step_names.append(sn)
            sys_val = step.get('system', '').strip()
            if sys_val and sys_val not in systems:
                systems.append(sys_val)

        keywords_parts = [
            p['id'],
            p.get('l3_name', ''),
            p.get('l2_process', ''),
            p.get('l1_domain', ''),
        ] + step_names + systems

        keywords = ' '.join(keywords_parts).lower()

        excerpt = ' · '.join(step_names[:4])

        wiki_path = p.get('wiki_path', '').strip('/')
        url = f'/{BASE_PATH}/{wiki_path}/'

        index.append({
            'id':            p['id'],
            'title':         p.get('l3_name', ''),
            'l1':            p.get('l1_domain', ''),
            'l2':            p.get('l2_process', ''),
            'url':           url,
            'systems':       systems[:6],
            'steps_preview': excerpt,
            'keywords':      keywords,
        })

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, separators=(',', ':'), ensure_ascii=False)

    size_kb = os.path.getsize(OUTPUT_PATH) // 1024
    print(f'search-index.json written: {len(index)} entries, {size_kb} KB → {OUTPUT_PATH}')

if __name__ == '__main__':
    build_index()
