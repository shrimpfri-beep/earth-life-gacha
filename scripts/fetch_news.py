#!/usr/bin/env python3
"""1 in 8 Billion — 실시간 뉴스 수집기 (GitHub Actions에서 1시간마다 실행)

Google 뉴스 한국어 검색 RSS(국가별 최근 7일)와 연합뉴스 국제 RSS를 읽어
게임과 같은 저장소의 news.json으로 저장합니다. 표준 라이브러리만 사용합니다.
"""
import json, os, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

COUNTRIES = {
    'NGA': '나이지리아', 'ETH': '에티오피아', 'COD': '콩고민주공화국 OR 민주콩고', 'IND': '인도 모디 OR 뉴델리 OR 인도 경제',
    'PAK': '파키스탄', 'BGD': '방글라데시', 'IDN': '인도네시아', 'CHN': '중국 경제 OR 중국 정부', 'KOR': '대한민국 사회 OR 통계청',
    'EGY': '이집트', 'DZA': '알제리', 'BRA': '브라질', 'MEX': '멕시코', 'USA': '미국 경제 OR 미국 정부', 'DEU': '독일', 'UZB': '우즈베키스탄',
}
WORLD_RSS = 'https://www.yna.co.kr/rss/international.xml'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'news.json')
UA = {'User-Agent': 'Mozilla/5.0 (compatible; earth-life-gacha-news/1.0; +https://github.com)'}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def parse(xml_bytes, default_source='', limit=8):
    root = ET.fromstring(xml_bytes)
    items = []
    for it in root.iter('item'):
        title = (it.findtext('title') or '').strip()
        link = (it.findtext('link') or '').strip()
        src = (it.findtext('source') or '').strip() or default_source
        if src and title.endswith(' - ' + src):
            title = title[: -(len(src) + 3)]
        try:
            t = int(parsedate_to_datetime(it.findtext('pubDate') or '').timestamp() * 1000)
        except Exception:
            t = None
        if title and link.startswith('http'):
            items.append({'title': title, 'url': link, 'domain': src, 'time': t})
    seen, out = set(), []
    for a in sorted(items, key=lambda a: a['time'] or 0, reverse=True):
        k = a['title'].lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(a)
    return out[:limit]


def main():
    try:
        with open(OUT, encoding='utf-8') as f:
            prev = json.load(f)
    except Exception:
        prev = {'countries': {}, 'world': []}
    data = {'updatedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'sources': ['Google 뉴스 한국어 검색 RSS (국가별 최근 7일)', '연합뉴스 국제 RSS'],
            'countries': {}, 'world': prev.get('world', []), 'errors': []}
    for iso, q in COUNTRIES.items():
        url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': q + ' when:7d', 'hl': 'ko', 'gl': 'KR', 'ceid': 'KR:ko'})
        try:
            data['countries'][iso] = parse(fetch(url))
        except Exception as e:
            data['countries'][iso] = prev.get('countries', {}).get(iso, [])
            data['errors'].append(f'{iso}: {e}')
        time.sleep(1.5)
    try:
        data['world'] = parse(fetch(WORLD_RSS), '연합뉴스', limit=12)
    except Exception as e:
        data['errors'].append(f'world: {e}')
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('updated', data['updatedAt'], {k: len(v) for k, v in data['countries'].items()}, 'world', len(data['world']), 'errors', data['errors'])


if __name__ == '__main__':
    main()
