"""Bounded downloads from registered public sources; no private API or scraping bypass."""
from html.parser import HTMLParser
from urllib.parse import urljoin
from pathlib import Path
import shutil
import requests
import pandas as pd
from pypdf import PdfReader
from .common import ROOT, read_csv, write_csv, write_json, sha256

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.extend(v for k,v in attrs if k == 'href' and v)

def download(url, target):
    """Preserve existing downloads. Fail closed on login/errors; one request per asset."""
    target = Path(target)
    if target.exists():
        return {'status':'PRESERVED','sha256':sha256(target),'bytes':target.stat().st_size}
    response = requests.get(url, timeout=60, headers={'User-Agent':'FE401-academic-feasibility/1.0 (public-file-download)'})
    response.raise_for_status()
    if not response.content:
        raise ValueError('Empty response')
    if target.suffix == '.pdf' and not response.content.startswith(b'%PDF'):
        raise ValueError('Source returned non-PDF response; manual import required')
    if target.suffix == '.xlsx' and not response.content.startswith(b'PK'):
        raise ValueError('Source returned non-XLSX response; manual import required')
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as handle:
        handle.write(response.content)
    return {'status':'DOWNLOADED','sha256':sha256(target),'bytes':target.stat().st_size}

def collect(online=False):
    sources = read_csv('sources.csv').fillna('')
    log = []
    for row in sources.to_dict('records'):
        if not row['raw_filename']:
            continue
        target = ROOT/'data/raw/official'/row['raw_filename']
        if target.exists():
            result = {'status':'PRESERVED','sha256':sha256(target),'bytes':target.stat().st_size}
        elif not online:
            result = {'status':'MISSING','reason':'Use collect --online for registered public downloads'}
        else:
            try:
                result = download(row['url'],target)
            except (requests.RequestException,ValueError) as error:
                result = {'status':'MANUAL_IMPORT_REQUIRED','reason':str(error)}
        log.append(dict(source_id=row['source_id'],url=row['url'],raw_file=str(target.relative_to(ROOT)),access_date='2026-10-10',**result))
        if target.exists() and target.suffix == '.pdf':
            text_path=ROOT/'data/processed'/f'{target.stem}_text.txt'
            try:
                text_path.write_text('\n'.join(f'PAGE {i+1}\n'+(p.extract_text() or '') for i,p in enumerate(PdfReader(target).pages)),encoding='utf-8')
            except Exception as error:
                log.append(dict(source_id=row['source_id'],status='EXTRACTION_FAILED',reason=str(error)))
    kgm=ROOT/'data/raw/official/kgm_distances.html'
    if kgm.exists():
        parser=Links()
        parser.feed(kgm.read_text(encoding='utf-8',errors='replace'))
        for href in parser.links:
            if '.xlsx' not in href.lower():
                continue
            url=urljoin(sources.loc[sources.source_id=='KGM_DISTANCES','url'].iloc[0],href)
            filename=Path(href.split('?')[0]).name
            try:
                local=ROOT/'data/raw/official'/filename
                result=download(url,local) if online or local.exists() else {'status':'MISSING','reason':'Run collect --online'}
            except (requests.RequestException,ValueError) as error:
                result={'status':'MANUAL_IMPORT_REQUIRED','reason':str(error)}
            log.append(dict(source_id='KGM_DISTANCES',url=url,raw_file='data/raw/official/'+filename,access_date='2026-10-10',**result))
    write_json(log,'reports/collection_log.json')
    return log

def import_observations(path):
    """Copy an authorized manual CSV verbatim before validation; never overwrite raw data."""
    path=Path(path).resolve()
    digest=sha256(path)
    target=ROOT/'data/raw/manual'/f'{digest[:16]}_{path.name}'
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        shutil.copy2(path,target)
    return target
