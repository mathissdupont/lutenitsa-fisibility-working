"""Check delivered workbook structure and produce isolated financial recalculation fixtures."""
from pathlib import Path
import json
from openpyxl import load_workbook
from src.common import ROOT,load_config
from src.finance import appraise
from src.reporting import SHEETS

path=ROOT/'output/Lutenitsa_Factory_Feasibility_2015_2025.xlsx'
formulas=load_workbook(path,data_only=False)
values=load_workbook(path,data_only=True)
assert formulas.sheetnames==SHEETS
errors=[]
formula_count=0
for sheet in formulas:
    for row in sheet:
        for cell in row:
            if cell.data_type=='f':
                formula_count+=1
            if values[sheet.title][cell.coordinate].data_type=='e':
                errors.append(sheet.title+'!'+cell.coordinate)
assert not errors,errors
assert values['DASHBOARD']['C11'].value==2500000
assert values['DASHBOARD']['C12'].value==5000000
assert values['PROFITABILITY_NPV']['D6'].value=='Eksik'
assert formulas['ASSUMPTIONS']['C13'].value is None
assert len(formulas['PRODUCT_TRENDS']._charts)==1
assert sum(len(s.tables) for s in formulas)>=15
qa=ROOT/'output/qa'
qa.mkdir(exist_ok=True)
config=load_config('assumptions.json')
site=load_config('sites.json')[0]
recipe=load_config('recipe.json')
expected={}
for case,demand in [('base',2500000),('low_demand',1000000),('short_life',2000000)]:
    book=load_workbook(path)
    local=dict(config,demand_kg=demand)
    s=dict(site,outbound_try_per_kg=3.8,maintenance_try=0)
    book['ASSUMPTIONS']['C13']=demand
    book['ASSUMPTIONS']['G29']=3.8
    book['ASSUMPTIONS']['H29']=0
    if case=='short_life':
        local.update(depreciation_years=2,horizon_years=3)
        book['ASSUMPTIONS']['C21']=2
        book['ASSUMPTIONS']['C9']=3
    unit=sum(r['gross_kg_per_finished_kg']*r['price_try_per_kg'] for r in recipe)
    total_ratio=sum(r['gross_kg_per_finished_kg'] for r in recipe)
    for i,r in enumerate(recipe,6):
        book['INGREDIENT_COSTS'][f'E{i}']=r['price_try_per_kg']*1000+2.6*1000/total_ratio
    landed=2500000*(unit+2.6)
    result=appraise(local,s,landed)
    expected[case]=dict(summary=result['summary'],rows=json.loads(result['cashflows'].to_json(orient='records')))
    book.save(qa/f'finance_{case}.xlsx')
(qa/'finance_expected.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'reports/workbook_integrity.json').write_text(json.dumps(dict(status='PASS',sheets=len(formulas.sheetnames),formula_count=formula_count,formula_errors=0,tables=sum(len(s.tables) for s in formulas),charts=1,fixtures_created=list(expected)),indent=2),encoding='utf-8')
print('Workbook structure and cached values checked; isolated financial fixtures created.')
