"""Refresh source registry and observations dictionary from preserved public assets."""
from src.common import ROOT,read_csv,write_csv
import pandas as pd

sources=read_csv('sources.csv').fillna('')
for idx,row in sources.iterrows():
    if row.raw_filename and (ROOT/'data/raw/official'/row.raw_filename).exists():
        sources.at[idx,'extraction_status']='PUBLIC_FILE_PRESERVED'
for sid,name in [('KGM_DISTRICT_XLSX','ilcemesafe.xlsx'),('KGM_PROVINCE_XLSX','ilmesafe.xlsx')]:
    if sid in sources.source_id.values:
        continue
    row=sources[sources.source_id=='KGM_DISTANCES'].iloc[0].to_dict()
    row.update(source_id=sid,url='https://www.kgm.gov.tr/SiteCollectionDocuments/KGMdocuments/Root/Uzakliklar/'+name,raw_filename=name,extraction_status='PUBLIC_FILE_PRESERVED',scope='Official road-distance table; district center proxy' if 'ilce' in name else 'Province center road-distance table',missing_information='OSB/customer gate and truck suitability')
    sources=pd.concat([sources,pd.DataFrame([row])],ignore_index=True)
write_csv(sources,'sources.csv')
dictionary=read_csv('data_dictionary.csv')
for field,definition in [('province_code','Province/plate identifier; normalization registry'),('district_code','Official district identifier; blank until source verified'),('constant_price_try','Farm-gate TRY/kg normalized by verified official annual index levels')]:
    if field not in dictionary.field.values:
        dictionary=pd.concat([dictionary,pd.DataFrame([dict(field=field,definition=definition,required=False)])],ignore_index=True)
# Import schema remains the original observation schema; processed-only columns are optional.
write_csv(dictionary,'data_dictionary.csv')
print('Registry and processed data definitions updated.')
