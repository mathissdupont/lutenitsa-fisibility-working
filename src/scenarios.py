"""Explicitly hypothetical legacy financial examples, isolated from genuine analysis."""
import copy
import pandas as pd
from openpyxl import load_workbook
from .common import ROOT,load_config,read_csv,write_csv,write_json
from .finance import appraise,monte_carlo,investment_break_even_price

def legacy_financial_demo():
    config=load_config('assumptions.json')
    config['demand_kg']=2500000
    workbook=load_workbook(ROOT/'data/raw/legacy/lutenitsa_tesis_yeri_fizibilite_lojistikli.xlsx',data_only=True)
    scenarios=[]
    annual=[]
    risk=[]
    sensitivity=[]
    for row,site in zip(range(6,9),load_config('sites.json')):
        site=copy.deepcopy(site)
        site['outbound_try_per_kg']=workbook['LOKASYON'][f'D{row}'].value
        site['maintenance_try']=0.0
        site['contract_supply_buffer']=1.0
        config_local=copy.deepcopy(config)
        # Demo cost aggregates original recipe + original inbound rate exactly once.
        raw_unit=sum(r['gross_kg_per_finished_kg']*r['price_try_per_kg'] for r in load_config('recipe.json'))
        inbound=workbook['LOKASYON'][f'C{row}'].value
        local=workbook['LOKASYON'][f'B{row}'].value
        landed=2500000*(raw_unit+inbound+local)
        site['inbound_cost_share']=inbound/(raw_unit+inbound+local)
        result=appraise(config_local,site,landed)
        summary=dict(site=site['site'],**{k:v for k,v in result['summary'].items() if k!='cashflows'},investment_break_even_price=investment_break_even_price(config_local,site,landed),status='ASSUMED',notes='Original legacy price/cost inputs; demand fixed at 2.5m kg; maintenance set to zero solely in demo. No industrial validation.')
        scenarios.append(summary)
        annual.append(result['cashflows'].assign(site=site['site'],status='ASSUMED'))
        draws,risk_summary=monte_carlo(config_local,site,landed)
        write_csv(draws,f'output/demo/monte_carlo_{site["site"]}.csv')
        risk.append(dict(site=site['site'],**risk_summary))
        for driver in ['selling_price_try_per_kg','demand_kg','raw_material_cost','utilities','freight']:
            for multiplier in [.8,1,1.2]:
                c=copy.deepcopy(config_local)
                s=copy.deepcopy(site)
                cost=landed
                if driver in c:
                    c[driver]*=multiplier
                elif driver=='raw_material_cost':
                    cost=2500000*(raw_unit*multiplier+inbound+local)
                elif driver=='utilities':
                    s['utilities_try_per_kg']*=multiplier
                else:
                    s['outbound_try_per_kg']*=multiplier
                    cost=2500000*(raw_unit+inbound*multiplier+local)
                evaluation=appraise(c,s,cost)
                sensitivity.append(dict(site=site['site'],driver=driver,multiplier=multiplier,npv=evaluation['summary']['npv'],status='ASSUMED'))
    write_csv(pd.DataFrame(scenarios),'output/demo/financial_scenarios.csv')
    write_csv(pd.concat(annual,ignore_index=True),'output/demo/annual_cashflows.csv')
    write_csv(pd.DataFrame(sensitivity),'output/demo/sensitivity.csv')
    write_json(risk,'output/demo/risk_summary.json')
    write_json(dict(status='ASSUMED',calibration='None',demand_kg=2500000,maintenance_try=0,harvest_policy='Buffer 1.0; shortfall draws infeasible; no emergency supply assumed',notes='These examples never feed the real report or site recommendation.'),'output/demo/demo_manifest.json')
