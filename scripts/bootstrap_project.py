"""Create project metadata and preserve original work with content hashes."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
for name in ['src', 'config', 'data/raw/legacy', 'data/raw/official', 'data/manual', 'data/processed', 'tests', 'output', 'reports', 'scripts']:
    (ROOT / name).mkdir(parents=True, exist_ok=True)
inventory = json.loads((ROOT / 'reports/legacy_inventory.json').read_text(encoding='utf-8'))
for entry in inventory:
    target = ROOT / 'data/raw/legacy' / entry['file']
    if not target.exists():
        shutil.copy2(ROOT / entry['file'], target)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == entry['sha256']

def save(name, rows):
    with (ROOT / name).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

source_rows = []
def source(code, institution, url, scope, method, missing, filename=''):
    source_rows.append(dict(source_id=code, institution=institution, url=url, scope=scope, access_date='2026-10-10', publication_date='', access_method=method, extraction_status='RESEARCHED', missing_information=missing, raw_filename=filename))

source('TEPGE_TOMATO_2024', 'Ministry of Agriculture and Forestry / TEPGE', 'https://arastirma.tarimorman.gov.tr/tepge/Belgeler/PDF%20%C3%9Cr%C3%BCn%20Raporlar%C4%B1/2024%20%C3%9Cr%C3%BCn%20Raporlar%C4%B1/Domates%20%C3%9Cr%C3%BCn%20Raporu%202024-396%20TEPGE.pdf', 'Provincial processing tomato, 2019-2023, Appendix Table 11, printed p.26', 'Public PDF download; extract named rows; rounded thousands retained', 'District histories; 2015-2018 and 2024-2025', 'tomato_report_2024.pdf')
source('TUIK_CROPS', 'TUIK', 'https://biruni.tuik.gov.tr/medas/', 'District crop production, area, yield, 2015-2025', 'Manual MEDAS export; no undocumented API; preserve original export', 'All eleven districts, exact official crop codes, publication dates')
source('TUIK_PORTAL', 'TUIK', 'https://veriportali.tuik.gov.tr/', 'Official statistics portal', 'Manual data browser export', 'District crop panel and classifications')
source('TUIK_CPI', 'TUIK', 'https://veriportali.tuik.gov.tr/tr/databrowser/tuik/categories/6/6_5/TR%2CDF_TUFE_SDMX_2003%2C1.0', 'Annual average CPI index, common vintage, official general purchasing-power deflator', 'Manual download; average twelve monthly index levels; never use annual inflation percentages as levels', '2015-2025 annual averages and base-year level; 2026 full-year average not yet available')
source('KGM_DISTANCES', 'KGM', 'https://www.kgm.gov.tr/Sayfalar/KGM/SiteTr/Root/Uzakliklar.aspx', 'Current road distances between district centers', 'Download only Excel link explicitly published on source page; center proxy, not truck gate route', 'Last-mile OSB access and truck restrictions', 'kgm_distances.html')
source('MGM_CLIMATE', 'MGM', 'https://mevbis.mgm.gov.tr/mevbis/ui/HelpMenu/MEVBIS_Kullanim_Kilavuzu.pdf', 'Station observations and feature release timing', 'MEVBIS membership / authorized order; manual import; no login bypass', 'Station coverage, growing-season rainfall/temperature, availability date')
source('EPIAS_ENERGY', 'EPIAS', 'https://seffaflik.epias.com.tr/', 'Wholesale energy prices', 'Authorized login or manual export; retail OSB tariffs obtained separately', 'Retail electricity, heat, connection capacity and tariffs')
source('MKP_OSB', 'Mustafakemalpasa OSB', 'https://www.mkposb.org.tr/tarihce', 'Published infrastructure background', 'Public HTML snapshot; installed infrastructure does not confirm spare capacity', 'Parcel food-use permission, water quality/quantity, discharge allocation, current tariffs', 'mkp_osb.html')
source('SALIHLI_OSB', 'Salihli OSB', 'https://salihliosb.org.tr/hizmetler/', 'Published utility services', 'Public HTML snapshot', 'Parcel permissions and binding utility allocation', 'salihli_osb.html')
source('GONEN_OSB', 'Gonen Leather Specialized and Mixed OSB', 'https://www.gonenosb.org.tr/', 'OSB identity and infrastructure', 'Public HTML snapshot; distinguish mixed industrial OSB from Gonen greenhouse agricultural OSB', 'Food use, potable-process water, capacity, contamination and parcel hazard assessment', 'gonen_osb.html')
source('GONEN_ZONING', 'Gonen OSB', 'https://www.gonenosb.org.tr/kurumsal/imar-plani', 'Published mixed-zone status and zoning plans', 'Manual plan review', 'Food plant eligibility on selected parcel')
source('FE401_PDF', 'User', '', 'Twelve factors transcribed in project request', 'Manual import of original PDF', 'Original FE401 PDF is absent; cannot verify pagination or weights')
source('SUPPLIER_QUOTES', 'Supplier / carrier / packaging manufacturer', '', 'Farm-gate offers, refined oil, vinegar, salt, spices, glass jars and transport', 'Obtain dated written quotations; no assumed figures promoted to VERIFIED', 'All binding quotes, monthly availability, quality, payload, return costs')
source('AFAD_HAZARD', 'AFAD', 'https://tdth.afad.gov.tr/TDTH/loginControl.xhtml', 'Parcel seismic hazard', 'Authorized manual assessment; geotechnical and flood/fire study separately', 'Parcel coordinates, soil study, flood and fire protection')
wb = load_workbook(ROOT / 'data/raw/legacy/lutenitsa_tesis_yeri_fizibilite_lojistikli.xlsx', data_only=True)
for row in range(6, 9):
    url = wb['URETIM_2024'][f'G{row}'].value
    province = wb['URETIM_2024'][f'A{row}'].value
    source(f'GUIDE_{row}', 'Ministry of Agriculture and Forestry', url, f'{province} provincial 2024 crops in 2025 investment guide', 'Public PDF download; verify legacy values against original PDF', 'District series and exact pepper-to-kapya mapping', f'guide_{row}.pdf')
save('sources.csv', source_rows)

districts = {'Bursa':['Karacabey','Mustafakemalpaşa'], 'Balıkesir':['Susurluk','Gönen','Manyas','Bigadiç','Sındırgı'], 'Manisa':['Salihli','Akhisar','Saruhanlı','Turgutlu']}
save('config/geography.csv', [dict(province=p, district=d, province_code={'Bursa':'16','Balıkesir':'10','Manisa':'45'}[p], district_code='', district_code_status='MISSING') for p,ds in districts.items() for d in ds])
products = [('TOMATO_PROCESSING','Processing tomatoes'),('TOMATO_FRESH','Fresh tomatoes'),('PEPPER_KAPYA','Red kapya pepper'),('PEPPER_PROCESSING','Processing peppers, official generic class'),('EGGPLANT','Eggplant'),('GARLIC_DRY','Dry garlic'),('SUNFLOWER_OILSEED','Oilseed sunflower'),('HERBS_SPICES','Herbs and spices: disaggregate on import')]
save('config/products.csv', [dict(product_code=c,product_description=d,official_code='',mapping_status='MISSING',notes='Project identifier; not an official TUIK code. No implicit mapping.') for c,d in products])
fields = dict(year='Observation year; integer',province='Official province name',district='District name; empty only for provincial/national level',product_code='Project product classification',product_description='Original product description',metric='production / area / yield / farm_gate_price',value='Numeric value; empty means missing',unit='t / kg / ha / da / t_per_ha / kg_per_da / TRY_per_kg',source_institution='Publishing institution',source_url='Exact source URL',reference_year='Year measured; must agree with year',publication_date='ISO date or empty if unavailable',access_date='ISO date',data_status='VERIFIED / ESTIMATED / ASSUMED / MISSING',notes='Transformations and caveats',geographic_level='district / province / national',source_id='Registry key',official_product_code='Source classification code or empty; never invented',available_date='Earliest public availability, ISO date; missing excludes ex-ante model',original_unit='Original measurement unit',original_value='Original reported number',raw_file='Preserved relative source path')
save('data_dictionary.csv', [dict(field=k,definition=v,required=k not in ['publication_date','official_product_code','available_date','original_unit','original_value']) for k,v in fields.items()])
headers = list(fields)
template=[]
for p, ds in districts.items():
    for d in ds:
        for year in range(2015,2026):
            for c, description in products:
                if c not in ['TOMATO_PROCESSING','PEPPER_KAPYA','EGGPLANT','GARLIC_DRY','SUNFLOWER_OILSEED','HERBS_SPICES']:
                    continue
                for metric, unit in [('production','t'),('area','da'),('yield','kg_per_da'),('farm_gate_price','TRY_per_kg')]:
                    r = dict.fromkeys(headers, '')
                    r.update(year=year,province=p,district=d,product_code=c,product_description=description,metric=metric,unit=unit,reference_year=year,data_status='MISSING',geographic_level='district',source_id='TUIK_CROPS',source_institution='TUIK',source_url='https://biruni.tuik.gov.tr/medas/',notes='Missing observation; never substitute zero.')
                    template.append(r)
save('data/manual/agriculture_template.csv',template)
for name, columns in {
    'deflator_template.csv':['year','index','base','source_url','data_status','publication_date'],
    'climate_template.csv':['province','district','station_id','year','feature','value','unit','available_date','source_url','data_status'],
    'supplier_offers_template.csv':['supplier_id','site','province','district','ingredient','month','available_tonnes','participation_limit','price_try_per_tonne','handling_try_per_tonne','freight_try_per_tonne','freight_try_per_truck','transport_loss','quality_eligible','source_url','quote_date','price_year','price_basis','data_status'],
    'distance_template.csv':['origin','destination','road_km','distance_type','source_url','reference_date','data_status'],
    'utilities_template.csv':['site','utility','available_capacity','capacity_unit','price','price_unit','source_url','quote_date','data_status'],
    'screening_template.csv':['site','food_use','water','wastewater','energy','land_hazard','evidence_url','reference_date'],
}.items():
    save('data/manual/'+name,[dict.fromkeys(columns,'')])

recipe=[]
codes=['PEPPER_KAPYA','TOMATO_PROCESSING','EGGPLANT','GARLIC_DRY','REFINED_SUNFLOWER_OIL','SPICES','SALT','VINEGAR']
labels=['Kırmızı kapya biber','Salçalık domates','Patlıcan','Kuru sarımsak','Rafine ayçiçek yağı','Baharat karışımı','Tuz','Sirke']
for row, code, label in zip(range(6,14),codes,labels):
    recipe.append(dict(ingredient=code,label_tr=label,gross_kg_per_finished_kg=wb['RECETE'][f'B{row}'].value,price_try_per_kg=wb['RECETE'][f'C{row}'].value,cleaning_loss=None,roasting_loss=None,season_intake_days=None,status='ASSUMED',source=f'Legacy RECETE!B{row}:C{row}; not industrially validated'))
(ROOT/'config/recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2),encoding='utf-8')
assumptions=dict(report_date='2026-10-10',historical_start=2015,historical_end=2025,forecast_years=list(range(2026,2031)),forecast_date='2026-01-01',daily_tonnes=10,operating_days=250,jar_kg=0.5,horizon_years=10,capacity_scenarios=[5,10,25,50],price_basis='real',base_price_year=2026,discount_basis='real',real_discount_rate=0.12,tax_rate=0.25,utilization=1.0,demand_kg=None,selling_price_try_per_kg=135,packaging_try_per_jar=12,processing_try_per_kg=7,waste_try_per_kg=0.8,working_capital_try=20000000,depreciable_fraction=0.7,depreciation_years=10,salvage_fraction=0.2,replacement_capex_fraction=0.01,truck_payload_tonnes=20,freight_try_per_tonne_km=4,handling_try_per_tonne=250,empty_return_fraction=None,storage_try_per_tonne_month=None,storage_capacity_tonnes=None,finished_transport_mass_factor=None,supplier_participation_fraction=None,seed=401,monte_carlo_draws=500,monte_carlo_distributions={'price':[0.85,1,1.15],'demand':[0.7,1,1.1],'raw_cost':[0.85,1,1.2],'harvest':[0.7,1,1.1],'energy':[0.85,1,1.25],'freight':[0.85,1,1.25]},risk_penalty_fraction=0.25,status='ASSUMED',notes='Numeric legacy financial inputs are hypothetical; missing new inputs block appraisal. Triangular Monte Carlo distributions are uncalibrated expert assumptions, not empirical probabilities.')
sites=[]
for row, code, label, district in [(6,'BURSA_MKP','Bursa – Mustafakemalpaşa OSB','Mustafakemalpaşa'),(7,'MANISA_SALIHLI','Manisa – Salihli OSB','Salihli'),(8,'BALIKESIR_GONEN','Balıkesir – Gönen Deri İhtisas ve Karma OSB','Gönen')]:
    sites.append(dict(site=code,label_tr=label,district=district,capex_try=wb['LOKASYON'][f'I{row}'].value,labor_try=wb['LOKASYON'][f'F{row}'].value,administration_try=wb['LOKASYON'][f'G{row}'].value,fixed_overhead_try=wb['LOKASYON'][f'H{row}'].value,utilities_try_per_kg=wb['LOKASYON'][f'E{row}'].value,outbound_try_per_kg=None,maintenance_try=None,food_use='UNVERIFIED',water='UNVERIFIED',wastewater='UNVERIFIED',energy='UNVERIFIED',land_hazard='UNVERIFIED',status='ASSUMED',source=f'Legacy LOKASYON row {row}; no binding quotes'))
(ROOT/'config/assumptions.json').write_text(json.dumps(assumptions,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'config/sites.json').write_text(json.dumps(sites,ensure_ascii=False,indent=2),encoding='utf-8')
save('config/markets.csv',[dict(market=m,label_tr=l,demand_share='',annual_demand_kg='',net_price_try_per_kg='',source_url='',data_status='MISSING') for m,l in [('ISTANBUL','İstanbul'),('ANKARA','Ankara'),('IZMIR','İzmir'),('REGIONAL','Bölgesel dağıtıcılar'),('BANDIRMA_EXPORT','Bandırma limanı ihracat'),('IZMIR_EXPORT','İzmir limanı ihracat')]])
criteria=['Hammadde','Pazarlar','Enerji','İklim','Ulaşım','Su','Atık bertarafı','İşgücü','Vergiler ve yasal kısıtlar','Arazi özellikleri','Sel ve yangın koruması','Toplumsal faktörler']
save('config/fe401.csv',[dict(criterion=i+1,label_tr=l,weight=1/12,evidence_score='',expert_score='',source_url='',status='MISSING') for i,l in enumerate(criteria)])
print('Phase 1 metadata, import templates and preserved originals created.')
