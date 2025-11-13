#!/usr/bin/env python3
"""Knowledge Base pipeline tool

Combines the functionality of the previous separate tools:
- improve_kb.py
- format_kb_content.py
- fix_inline_bullets.py
- restore_from_backup.py
- clean_kb_text.py

Usage: kb_pipeline.py --all | [--improve] [--format] [--fix-inline] [--restore] [--clean]

Each stage backs up modified files to `knowledge_base/backups/` with stage-specific suffixes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from datetime import datetime
from glob import glob
from typing import Callable, List


STOPWORDS = {
    'the', 'and', 'or', 'in', 'on', 'at', 'a', 'an', 'to', 'for', 'of', 'by', 'with',
    'is', 'are', 'be', 'as', 'from', 'that', 'this', 'these', 'those', 'it', 'its',
    'was', 'were', 'will', 'can', 'should', 'must', 'have', 'has', 'had'
}

PUNCT_RE = re.compile(r'[\.,:;"\(\)\?\!\[\]\/\\]')


def ts() -> str:
    return datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')


def list_kb_files(kb_dir: str) -> List[str]:
    if not os.path.isdir(kb_dir):
        return []
    return [os.path.join(kb_dir, f) for f in os.listdir(kb_dir) if f.endswith('_base.json')]


# -------------------- Improve stage (normalize, keywords, source, trim) --------------------
def generate_keywords(title: str) -> List[str]:
    words = re.findall(r"\b[a-zA-Z]{4,}\b", (title or '').lower())
    seen = set()
    out = []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def normalize_category(cat: str) -> str:
    if not cat:
        return ''
    return cat.strip().lower().replace('-', '_').replace(' ', '_')


def improve_file(path: str) -> bool:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping {path}: failed to parse JSON: {e}")
        return False

    if not isinstance(data, list):
        print(f"Skipping {path}: top-level JSON is not a list")
        return False

    changed = False
    for entry in data:
        if not isinstance(entry, dict):
            continue

        title = entry.get('title', '')
        orig_cat = entry.get('category', '')
        cat = normalize_category(orig_cat)
        if cat != orig_cat:
            entry['category'] = cat
            changed = True

        if 'source' not in entry:
            entry['source'] = ''
            changed = True

        if 'keywords' not in entry or not isinstance(entry.get('keywords'), list):
            kws = generate_keywords(title)
            entry['keywords'] = kws
            changed = True

        if 'content' in entry and isinstance(entry['content'], str):
            cleaned = '\n'.join([ln.strip() for ln in entry['content'].splitlines()])
            if cleaned != entry['content']:
                entry['content'] = cleaned
                changed = True

    if changed:
        kb_dir = os.path.dirname(path)
        backups = os.path.join(kb_dir, 'backups')
        os.makedirs(backups, exist_ok=True)
        base = os.path.basename(path)
        backup_path = os.path.join(backups, f"{base}.{ts()}.bak")
        shutil.copy2(path, backup_path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Updated {path} (backup -> {backup_path})")
    else:
        print(f"No changes needed for {path}")

    return changed


# -------------------- Format stage (bullets -> sentences, join lines) --------------------
def sentence_ending(s: str) -> bool:
    return s.endswith(('.', '!', '?'))


def clean_whitespace(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def bullets_to_sentences(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    paras = re.split(r'\n\s*\n', text)
    out_paras = []
    for p in paras:
        lines = [ln.strip() for ln in p.split('\n') if ln.strip()]
        if not lines:
            continue
        if all(re.match(r'^[-•*]\s+', ln) for ln in lines):
            sentences = []
            for ln in lines:
                content = re.sub(r'^[-•*]\s+', '', ln).strip()
                content = clean_whitespace(content)
                if not sentence_ending(content):
                    content = content.rstrip('.') + '.'
                sentences.append(content[0].upper() + content[1:] if content else content)
            out_paras.append(' '.join(sentences))
        else:
            joined = ' '.join(lines)
            joined = clean_whitespace(joined)
            if joined and not sentence_ending(joined):
                joined = joined + '.'
            out_paras.append(joined)
    return '\n\n'.join(out_paras)


def format_file(path: str) -> bool:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping {path}: JSON load error: {e}")
        return False

    if not isinstance(data, list):
        print(f"Skipping {path}: expected list top-level")
        return False

    changed = False
    for entry in data:
        if not isinstance(entry, dict):
            continue
        content = entry.get('content')
        if not isinstance(content, str) or not content.strip():
            continue

        new_content = bullets_to_sentences(content)
        if new_content != content:
            entry['content'] = new_content
            changed = True

    if changed:
        kb_dir = os.path.dirname(path)
        backups = os.path.join(kb_dir, 'backups')
        os.makedirs(backups, exist_ok=True)
        base = os.path.basename(path)
        backup_path = os.path.join(backups, f"{base}.{ts()}.fmt.bak")
        shutil.copy2(path, backup_path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Formatted {path} (backup -> {backup_path})")
    else:
        print(f"No formatting changes for {path}")

    return changed


# -------------------- Fix inline bullets stage --------------------
def split_inline_bullets(paragraph: str) -> str:
    p = paragraph.replace('\r\n', '\n').replace('\r', '\n')
    if '\n' in p:
        return paragraph
    m = re.search(r":\s*-\s*", p)
    if m:
        head = p[:m.start()].strip()
        tail = p[m.end():].strip()
        items = re.split(r"\s*-\s*", tail)
        sentences = [item.strip() for item in items if item.strip()]
        sentences = [s if s.endswith(('.', '!', '?')) else s + '.' for s in sentences]
        sentences = [s[0].upper() + s[1:] if s else s for s in sentences]
        return head + ': ' + ' '.join(sentences)
    if p.count(' - ') >= 1:
        parts = [part.strip() for part in p.split(' - ') if part.strip()]
        if len(parts) > 1:
            head = parts[0]
            items = parts[1:]
            sentences = [it if it.endswith(('.', '!', '?')) else it + '.' for it in items]
            sentences = [s[0].upper() + s[1:] if s else s for s in sentences]
            return head + ': ' + ' '.join(sentences)
    return paragraph


def fix_inline_file(path: str) -> bool:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping {path}: JSON load error: {e}")
        return False

    changed = False
    for entry in data:
        if not isinstance(entry, dict):
            continue
        content = entry.get('content')
        if not isinstance(content, str):
            continue
        new = split_inline_bullets(content)
        if new != content:
            entry['content'] = new
            changed = True

    if changed:
        kb_dir = os.path.dirname(path)
        backups = os.path.join(kb_dir, 'backups')
        os.makedirs(backups, exist_ok=True)
        base = os.path.basename(path)
        backup_path = os.path.join(backups, f"{base}.{ts()}.inlinefix.bak")
        shutil.copy2(path, backup_path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Fixed inline bullets in {path} (backup -> {backup_path})")
    else:
        print(f"No inline bullets fixed in {path}")

    return changed


# -------------------- Restore stage (use latest backup to restore hyphenation/numeric ranges) --------------------
def find_latest_backup_for(path: str) -> str | None:
    kb_dir = os.path.dirname(path)
    base = os.path.basename(path)
    pattern = os.path.join(kb_dir, 'backups', f"{base}*.bak")
    files = sorted(glob(pattern), reverse=True)
    return files[0] if files else None


def hyphen_tokens(s: str):
    return set(re.findall(r"\b[\w]+-[\w]+\b", s))


def replace_splits(current: str, backup: str) -> tuple[str, bool]:
    changed = False
    for match in re.findall(r"\b\d+[\-–—]\d+\b", backup):
        alt = re.sub(r"[-–—]", '. ', match)
        if alt in current:
            current = current.replace(alt, match)
            changed = True
        alt2 = match.replace('-', ' - ')
        if alt2 in current:
            current = current.replace(alt2, match)
            changed = True

    for token in hyphen_tokens(backup):
        parts = token.split('-')
        if len(parts) != 2:
            continue
        a, b = parts
        candidates = [f"{a}. {b}", f"{a}. {b.capitalize()}", f"{a} {b}", f"{a} . {b}"]
        for c in candidates:
            if c in current:
                current = current.replace(c, token)
                changed = True

    return current, changed


def restore_file(path: str) -> bool:
    backup = find_latest_backup_for(path)
    if not backup:
        print(f"No backup found for {path}; skipping")
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            cur = json.load(f)
        with open(backup, 'r', encoding='utf-8') as f:
            bak = json.load(f)
    except Exception as e:
        print(f"Skipping {path}: failed to read JSON: {e}")
        return False

    bak_map = {entry.get('title', ''): entry for entry in bak if isinstance(entry, dict)}

    changed_any = False
    for entry in cur:
        if not isinstance(entry, dict):
            continue
        title = entry.get('title', '')
        bak_entry = bak_map.get(title)
        if not bak_entry:
            continue
        cur_content = entry.get('content', '')
        bak_content = bak_entry.get('content', '')
        new_content, changed = replace_splits(cur_content, bak_content)
        if changed:
            entry['content'] = new_content
            changed_any = True

    if changed_any:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cur, f, indent=2, ensure_ascii=False)
        print(f"Restored artifacts in {path} using backup {os.path.basename(backup)}")
    else:
        print(f"No artifacts to restore in {path}")

    return changed_any


# -------------------- Clean stage (keywords and search_text) --------------------
def clean_text_for_search(s: str) -> str:
    s = s or ''
    s = s.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    s = PUNCT_RE.sub(' ', s)
    s = re.sub(r'\s+', ' ', s).strip().lower()
    tokens = [t for t in s.split() if t not in STOPWORDS]
    return ' '.join(tokens)


def clean_keywords(keywords) -> List[str]:
    out = []
    for kw in keywords or []:
        if not isinstance(kw, str):
            continue
        k = PUNCT_RE.sub('', kw).lower().strip()
        if not k:
            continue
        parts = [p for p in re.split(r"\s+", k) if p and p not in STOPWORDS]
        joined = ' '.join(parts)
        if joined and joined not in out:
            out.append(joined)
    return out


def clean_file(path: str) -> bool:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping {path}: failed to parse JSON: {e}")
        return False

    if not isinstance(data, list):
        print(f"Skipping {path}: top-level JSON not a list")
        return False

    changed = False
    for entry in data:
        if not isinstance(entry, dict):
            continue

        orig_kw = entry.get('keywords', [])
        new_kw = clean_keywords(orig_kw)
        if new_kw != orig_kw:
            entry['keywords'] = new_kw
            changed = True

        content = entry.get('content', '')
        new_search = clean_text_for_search(content)
        if entry.get('search_text') != new_search:
            entry['search_text'] = new_search
            changed = True

    if changed:
        kb_dir = os.path.dirname(path)
        backups = os.path.join(kb_dir, 'backups')
        os.makedirs(backups, exist_ok=True)
        base = os.path.basename(path)
        backup_path = os.path.join(backups, f"{base}.{ts()}.clean.bak")
        shutil.copy2(path, backup_path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Cleaned {path} (backup -> {backup_path})")
    else:
        print(f"No changes for {path}")

    return changed


def process_files(files: List[str], func: Callable[[str], bool]) -> int:
    changed_total = 0
    for p in files:
        try:
            if func(p):
                changed_total += 1
        except Exception as e:
            print(f"Error processing {p}: {e}")
    return changed_total


def main(argv=None):
    ap = argparse.ArgumentParser(description='Knowledge Base pipeline tool')
    ap.add_argument('--kb-dir', default=os.path.join(os.path.dirname(__file__), '..', 'knowledge_base'), help='Path to knowledge_base')
    ap.add_argument('--all', action='store_true', help='Run all stages in order')
    ap.add_argument('--improve', action='store_true', help='Normalize categories, add source/keywords, trim lines')
    ap.add_argument('--format', dest='fmt', action='store_true', help='Format content: bullets -> sentences')
    ap.add_argument('--fix-inline', action='store_true', help='Fix inline bullets')
    ap.add_argument('--restore', action='store_true', help='Restore hyphenation/numeric ranges from latest backups')
    ap.add_argument('--clean', action='store_true', help='Clean keywords and create search_text')
    args = ap.parse_args(argv)

    kb_dir = os.path.abspath(args.kb_dir)
    files = list_kb_files(kb_dir)
    if not files:
        print(f'No *_base.json files found in {kb_dir}')
        return 1

    # decide stages
    stages = []
    if args.all:
        stages = ['improve', 'format', 'fix_inline', 'restore', 'clean']
    else:
        if args.improve:
            stages.append('improve')
        if args.fmt:
            stages.append('format')
        if args.fix_inline:
            stages.append('fix_inline')
        if args.restore:
            stages.append('restore')
        if args.clean:
            stages.append('clean')

    if not stages:
        print('No stages selected. Use --all or individual flags. See --help for options.')
        return 0

    total_changed = 0
    for stage in stages:
        print(f"\n--- Stage: {stage} ---")
        if stage == 'improve':
            total_changed += process_files(files, improve_file)
        elif stage == 'format':
            total_changed += process_files(files, format_file)
        elif stage == 'fix_inline':
            total_changed += process_files(files, fix_inline_file)
        elif stage == 'restore':
            total_changed += process_files(files, restore_file)
        elif stage == 'clean':
            total_changed += process_files(files, clean_file)

    print(f"\nPipeline complete. Files changed: {total_changed} (see knowledge_base/backups for backups)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
