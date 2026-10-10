"""Official table extraction, unit normalization, and provenance-preserving quality checks."""
import re
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile
import numpy as np
import pandas as pd
from pypdf import PdfReader
from .common import ROOT, read_csv, write_csv, write_json, load_config

def name_key(value):
    value=str(value).strip().translate(str.maketrans({'ı':'i','İ':'I','ş':'s','Ş':'S','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O','ç':'c','Ç':'C'}))
    return ''.join(c for c in unicodedata.normalize('NFKD',value) if not unicodedata.combining(c)).casefold()

def normalize_unit(value, unit, metric):
    """Return canonical value and unit; missing stays NaN; incompatible units fail."""
    units={'production':{'t':(1,'t'),'tonnes':(1,'t'),'ton':(1,'t'),'kg':(.001,'t'),'thousand_t':(1000,'t')},'area':{'ha':(1,'ha'),'da':(.1,'ha'),'decare':(.1,'ha'),'thousand_da':(100,'ha')},'yield':{'t_per_ha':(1,'t_per_ha'),'kg_per_da':(.01,'t_per_ha')},'farm_gate_price':{'TRY_per_kg':(1,'TRY_per_kg'),'TRY_per_tonne':(.001,'TRY_per_kg')}}
    if metric not in units or unit not in units[metric]:
        raise ValueError(f'Unsupported metric/unit: {metric}/{unit}')
    multiplier, normalized=units[metric][unit]
    if value is None or pd.isna(value):
        return np.nan, normalized
    return float(value)*multiplier, normalized

def observation(source, province, year, metric, value, unit, description, code, page):
    return dict(year=year,province=province,district='',product_code=code,product_description=description,metric=metric,value=value,unit=unit,source_institution=source['institution'],source_url=source['url'],reference_year=year,publication_date='',access_date='2026-10-10',data_status='VERIFIED',notes=f'PDF page {page}; provincial observation. Source rounding retained; not local contracted supply.',geographic_level='province',source_id=source['source_id'],official_product_code='',available_date='',original_unit=unit,original_value=value,raw_file='data/raw/official/'+source['raw_filename'])

def extract_official_agriculture():
    sources=read_csv('sources.csv').fillna('').set_index('source_id').to_dict('index')
    result=[]
    source=dict(source_id='TEPGE_TOMATO_2024',**sources['TEPGE_TOMATO_2024'])
    path=ROOT/'data/raw/official'/source['raw_filename']
    if path.exists():
        text=PdfReader(path).pages[33].extract_text()
        if 'Ek Tablo 11.' not in text or 'bin da' not in text or 'bin ton' not in text:
            raise ValueError('Official tomato table schema changed; review required')
        for province in ['Bursa','Manisa','Balıkesir']:
            match=re.search(r'^'+re.escape(province)+r'\s+([\d.\s]+)$',text,re.M)
            if match is None:
                raise ValueError(f'Official row absent: {province}')
            values=[float(x.replace('.','')) for x in match.group(1).split()]
            if len(values)!=10:
                raise ValueError(f'Unexpected tomato row length: {province}')
            for i,year in enumerate(range(2019,2024)):
                result.append(observation(source,province,year,'area',values[i],'thousand_da','Domates (Salçalık)','TOMATO_PROCESSING',34))
                result.append(observation(source,province,year,'production',values[i+5],'thousand_t','Domates (Salçalık)','TOMATO_PROCESSING',34))
    for sid,province in [('GUIDE_6','Bursa'),('GUIDE_7','Manisa'),('GUIDE_8','Balıkesir')]:
        source=dict(source_id=sid,**sources[sid])
        path=ROOT/'data/raw/official'/source['raw_filename']
        if not path.exists():
            continue
        for page_index,page in enumerate(PdfReader(path).pages):
            text=page.extract_text() or ''
            if 'Tablo 5.' not in text or 'Seçilmiş Sebzelerin' not in text:
                continue
            for label,code in [('Domates (Salçalık)','TOMATO_PROCESSING'),('Biber (Salçalık)','PEPPER_PROCESSING'),('Patlıcan','EGGPLANT')]:
                match=re.search(r'^'+re.escape(label)+r'\s+[\d.]+\s+([\d.]+)\s+[\d,]+',text,re.M)
                if match:
                    result.append(observation(source,province,2024,'production',float(match.group(1).replace('.','')),'t',label,code,page_index+1))
    columns=read_csv('data_dictionary.csv').field.tolist()
    frame=pd.DataFrame(result,columns=columns)
    write_csv(frame,'data/processed/official_observations.csv')
    return frame

def normalize_observations(frame):
    frame=frame.copy()
    geography=read_csv('config/geography.csv').fillna('')
    provinces={name_key(x):x for x in geography.province.unique()}
    districts={(name_key(r.province),name_key(r.district)):r.district for r in geography.itertuples()}
    errors=[]
    for index,row in frame.iterrows():
        frame.at[index,'province']=provinces.get(name_key(row.province),str(row.province).strip())
        district='' if pd.isna(row.district) else str(row.district).strip()
        frame.at[index,'district']=districts.get((name_key(row.province),name_key(district)),district)
        try:
            value,unit=normalize_unit(row.value,row.unit,row.metric)
            if 'original_value' not in frame or pd.isna(row.get('original_value')):
                frame.at[index,'original_value']=row.value
            if 'original_unit' not in frame or pd.isna(row.get('original_unit')):
                frame.at[index,'original_unit']=row.unit
            frame.at[index,'value']=value
            frame.at[index,'unit']=unit
        except ValueError as error:
            errors.append(dict(row=int(index),issue='INVALID_UNIT',detail=str(error)))
            frame.at[index,'value']=np.nan
    frame=frame.drop(columns=['province_code','district_code'],errors='ignore')
    frame=frame.merge(geography[['province','district','province_code','district_code']],on=['province','district'],how='left')
    province_codes=geography.drop_duplicates('province').set_index('province').province_code.to_dict()
    frame['province_code']=frame.province.map(province_codes)
    return frame,errors

def deflate_prices(frame, indices, base_year):
    """Use official same-vintage annual index levels, never producer indices as local prices."""
    frame=frame.copy()
    frame['constant_price_try']=np.nan
    if indices.empty or indices[indices.data_status=='VERIFIED'].empty:
        return frame
    indices=indices[indices.data_status=='VERIFIED'].copy()
    if indices.year.duplicated().any() or indices.base.nunique()!=1 or (indices['index']<=0).any():
        raise ValueError('Deflator must have unique years, positive levels, one common base/vintage')
    levels=indices.set_index('year')['index']
    if base_year not in levels:
        return frame
    mask=frame.metric=='farm_gate_price'
    frame.loc[mask,'constant_price_try']=frame.loc[mask,'value']*levels[base_year]/frame.loc[mask,'year'].map(levels)
    return frame

def quality_report(frame, initial_errors=()):
    issues=list(initial_errors)
    key=['geographic_level','province','district','year','product_code','metric']
    duplicates=frame[frame.duplicated(key,keep=False)]
    for idx in duplicates.index:
        issues.append(dict(row=int(idx),issue='DUPLICATE_OBSERVATION',detail='Multiple source/vintage rows require explicit adjudication; all excluded from models.'))
    for idx,row in frame.iterrows():
        if pd.notna(row.value) and (not np.isfinite(row.value) or row.value<0):
            issues.append(dict(row=int(idx),issue='INVALID_VALUE',detail='Nonfinite or negative measure'))
        if row.data_status not in ['VERIFIED','ESTIMATED','ASSUMED','MISSING']:
            issues.append(dict(row=int(idx),issue='INVALID_STATUS',detail=str(row.data_status)))
        if row.data_status=='MISSING' and pd.notna(row.value):
            issues.append(dict(row=int(idx),issue='MISSING_WITH_VALUE',detail='Status/value conflict'))
        if row.data_status=='VERIFIED' and (pd.isna(row.value) or any(pd.isna(row.get(k)) or str(row.get(k)).strip()=='' for k in ['source_url','source_institution','access_date','raw_file'])):
            issues.append(dict(row=int(idx),issue='INCOMPLETE_PROVENANCE',detail='Verified record requires value, URL, institution, access date and raw file'))
        if row.year!=row.reference_year:
            issues.append(dict(row=int(idx),issue='YEAR_MISMATCH',detail='Observation year differs from reference year'))
        if row.geographic_level=='district' and (row.province,row.district) not in set(map(tuple,read_csv('config/geography.csv')[['province','district']].values)):
            issues.append(dict(row=int(idx),issue='UNKNOWN_GEOGRAPHY',detail='Add evidenced district to geography registry'))
    eligible=frame[(frame.data_status=='VERIFIED') & frame.value.notna() & (frame.value>=0) & ~frame.duplicated(key,keep=False)].copy()
    group=['province','district','product_code','metric','geographic_level']
    for _,rows in eligible.groupby(group,dropna=False):
        if len(rows)<4:
            continue
        median=rows.value.median()
        mad=(rows.value-median).abs().median()
        if mad>0:
            for idx in rows[(rows.value-median).abs()/mad>6].index:
                issues.append(dict(row=int(idx),issue='POTENTIAL_OUTLIER',detail='Median absolute deviation flag; retained for review'))
    aggregate_checks=[]
    for (province,year,product,metric),rows in eligible.groupby(['province','year','product_code','metric']):
        prov=rows[rows.geographic_level=='province']
        local=rows[rows.geographic_level=='district']
        if len(prov)==1 and len(local):
            if local.value.sum()>prov.value.iloc[0]*1.02:
                aggregate_checks.append(dict(province=province,year=int(year),product_code=product,metric=metric,status='DISTRICT_SUM_EXCEEDS_PROVINCE'))
    expected=read_csv('data/manual/agriculture_template.csv')
    actual=eligible[eligible.geographic_level=='district'][['province','district','year','product_code','metric']].drop_duplicates()
    missing=expected.merge(actual.assign(observed=True),on=['province','district','year','product_code','metric'],how='left')
    missing=missing[missing.observed.isna()].drop(columns='observed')
    write_csv(missing,'data/processed/missing_data.csv')
    report=dict(observation_count=len(frame),verified_count=int((frame.data_status=='VERIFIED').sum()),district_verified_count=int(((frame.data_status=='VERIFIED')&(frame.geographic_level=='district')).sum()),expected_district_records=len(expected),missing_district_records=len(missing),duplicate_rows=len(duplicates),issues=issues,aggregate_checks=aggregate_checks,deflator_status='MISSING',official_district_codes='MISSING',available_dates_missing=int((eligible.available_date.isna() | (eligible.available_date=='')).sum()))
    return report

def process():
    official=extract_official_agriculture()
    parts=[official]
    for path in sorted((ROOT/'data/raw/manual').glob('*.csv')) if (ROOT/'data/raw/manual').exists() else []:
        imported=pd.read_csv(path,encoding='utf-8-sig')
        dictionary=read_csv('data_dictionary.csv')
        required=dictionary[dictionary.required.astype(str).str.lower()=='true'].field.tolist()
        if not set(required).issubset(imported.columns):
            raise ValueError(f'Manual agricultural file lacks schema fields: {path.name}')
        imported['raw_file']=str(path.relative_to(ROOT)).replace('\\','/')
        parts.append(imported)
    frame=pd.concat(parts,ignore_index=True)
    frame,errors=normalize_observations(frame)
    frame=deflate_prices(frame,read_csv('data/manual/deflator_template.csv'),load_config('assumptions.json')['base_price_year'])
    quality=quality_report(frame,errors)
    write_csv(frame,'data/processed/historical_observations.csv')
    write_json(quality,'reports/data_quality.json')
    (ROOT/'reports/data_quality.md').write_text(f'# Veri kalitesi\n\nDoğrulanmış gözlem: {quality["verified_count"]}. İlçe düzeyinde: {quality["district_verified_count"]}. Eksik ilçe ölçümü: {quality["missing_district_records"]}/{quality["expected_district_records"]}.\n\nEksik değerler sıfır yapılmadı. İl toplamları ilçelere dağıtılmadı. Salçalık biber kapya ile eşlenmedi. TEPGE bin ton/bin dekar yuvarlaması korundu. İlçe kodları ve yayımlanma tarihleri ayrıca doğrulanmalıdır. Resmî deflatör eksik olduğundan tarihsel reel fiyat serisi hesaplanmadı.\n\n'+pd.DataFrame(quality['issues']).to_string(index=False)+'\n',encoding='utf-8')
    production=frame[(frame.metric=='production')&(frame.data_status=='VERIFIED')].copy()
    trends=[]
    for group,rows in production.groupby(['province','district','product_code','geographic_level'],dropna=False):
        rows=rows.sort_values('year')
        changes=rows.value.pct_change(fill_method=None)
        years=int(rows.year.iloc[-1]-rows.year.iloc[0])
        trends.append(dict(province=group[0],district=group[1],product_code=group[2],geographic_level=group[3],start_year=int(rows.year.iloc[0]),end_year=int(rows.year.iloc[-1]),observations=len(rows),cagr=(float((rows.value.iloc[-1]/rows.value.iloc[0])**(1/years)-1) if years and rows.value.iloc[0]>0 else None),growth_volatility=(float(changes.std()) if changes.notna().sum()>1 else None),status='ESTIMATED'))
    write_csv(pd.DataFrame(trends),'data/processed/product_trends.csv')
    # Yield is calculated only from compatible valid area and production observations.
    unique_key=['province','district','year','product_code','metric','geographic_level']
    yield_input=frame[(frame.data_status=='VERIFIED')&(frame.value>=0)&frame.value.notna()&~frame.duplicated(unique_key,keep=False)]
    pivot=yield_input.pivot_table(index=['province','district','year','product_code','geographic_level'],columns='metric',values='value',aggfunc='first',dropna=False) if not yield_input.empty else pd.DataFrame()
    if 'production' in pivot and 'area' in pivot:
        valid=pivot[(pivot.area>0)&(pivot.production>=0)].copy()
        valid['calculated_yield_t_per_ha']=valid.production/valid.area
        write_csv(valid.reset_index(),'data/processed/calculated_yields.csv')
    return quality

def extract_distances():
    """Stream the published million-row KGM table and retain only requested center proxies."""
    path=ROOT/'data/raw/official/ilcemesafe.xlsx'
    if not path.exists():
        write_csv(read_csv('data/manual/distance_template.csv'),'data/processed/distance_matrix.csv')
        return
    geo=read_csv('config/geography.csv')
    origins={(name_key(r.province),name_key(r.district)):(r.province,r.district) for r in geo.itertuples()}
    sites=load_config('sites.json')
    destinations={(name_key({'BURSA_MKP':'Bursa','MANISA_SALIHLI':'Manisa','BALIKESIR_GONEN':'Balıkesir'}[s['site']]),name_key(s['district'])):s['site'] for s in sites}
    wanted=set(origins)|set(destinations)
    external={('istanbul','fatih'):'ISTANBUL',('ankara','cankaya'):'ANKARA',('izmir','konak'):'IZMIR',('balikesir','bandirma'):'BANDIRMA_EXPORT'}
    found={}
    conflicts=[]
    ns='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    with ZipFile(path) as archive:
        strings=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            xml=ET.fromstring(archive.read('xl/sharedStrings.xml'))
            strings=[''.join(t.text or '' for t in si.iter(ns+'t')) for si in xml]
        with archive.open('xl/worksheets/sheet1.xml') as stream:
            for event, element in ET.iterparse(stream,events=('end',)):
                if element.tag!=ns+'row':
                    continue
                cells=[]
                for cell in element.findall(ns+'c'):
                    node=cell.find(ns+'v')
                    value=node.text if node is not None else None
                    if cell.get('t')=='s' and value is not None:
                        value=strings[int(value)]
                    elif cell.get('t')=='inlineStr':
                        value=''.join(t.text or '' for t in cell.iter(ns+'t'))
                    cells.append(value)
                if len(cells)==5 and cells[0] and name_key(cells[0]) in {'bursa','manisa','balikesir'}:
                    origin=tuple(map(name_key,cells[:2]))
                    destination=tuple(map(name_key,cells[2:4]))
                    if origin in wanted and ((origin in origins and destination in destinations) or (origin in destinations and destination in external)):
                        key=(origin,destination)
                        km=float(cells[4])
                        if key in found and found[key]!=km:
                            conflicts.append(str(key))
                        found[key]=km
                element.clear()
    rows=[]
    url='https://www.kgm.gov.tr/SiteCollectionDocuments/KGMdocuments/Root/Uzakliklar/ilcemesafe.xlsx'
    for origin, (province,district) in origins.items():
        for dest,site in destinations.items():
            km=found.get((origin,dest))
            rows.append(dict(origin=district,origin_province=province,destination=site,destination_district=next(s['district'] for s in sites if s['site']==site),road_km=km,distance_type='DISTRICT_CENTER_PROXY',source_url=url,reference_date='',access_date='2026-10-10',data_status='VERIFIED' if km is not None else 'MISSING',notes='District centers; no OSB gate, truck restrictions, toll choice or last-mile distance. Same-district zero is center-to-center only.',raw_file='data/raw/official/ilcemesafe.xlsx'))
    for origin,site in destinations.items():
        for dest,market in external.items():
            km=found.get((origin,dest))
            rows.append(dict(origin=site,origin_province=origin[0],destination=market,destination_district=dest[1],road_km=km,distance_type='DISTRICT_CENTER_PROXY',source_url=url,reference_date='',access_date='2026-10-10',data_status='VERIFIED' if km is not None else 'MISSING',notes='Outbound representative district proxy. Port terminal and customer gate distances require separate verification.',raw_file='data/raw/official/ilcemesafe.xlsx'))
    write_csv(pd.DataFrame(rows),'data/processed/distance_matrix.csv')
    write_json(dict(extracted_routes=len(rows),missing=sum(r['road_km'] is None for r in rows),conflicting_duplicates=conflicts),'reports/distance_quality.json')
