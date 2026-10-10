"""Mandatory site screening precedes evidence/subjective scores and financial ranking."""
import numpy as np
import pandas as pd
from .common import load_config, read_csv, write_csv, write_json

GATES=['food_use','water','wastewater','energy','land_hazard']

def screen(site):
    values=[site.get(gate,'UNVERIFIED') for gate in GATES]
    if any(value not in ['PASS','FAIL','UNVERIFIED'] for value in values):
        raise ValueError('Screening status must be PASS, FAIL or UNVERIFIED')
    return 'FAIL' if 'FAIL' in values else ('PASS' if all(v=='PASS' for v in values) else 'UNVERIFIED')

def weighted_score(scores,weights):
    scores=np.asarray(scores,dtype=float)
    weights=np.asarray(weights,dtype=float)
    if len(scores)!=12 or len(weights)!=12 or np.any(weights<0) or not np.isclose(weights.sum(),1):
        raise ValueError('Twelve nonnegative criterion weights must sum to one')
    if not np.isfinite(scores).all():
        return None
    if np.any((scores<1)|(scores>5)):
        raise ValueError('Criterion scores must be between one and five')
    return float(scores@weights/5*100)

def decision():
    sites=load_config('sites.json')
    rows=[dict(site=s['site'],label_tr=s['label_tr'],**{k:s.get(k,'UNVERIFIED') for k in GATES},eligibility=screen(s),financial_rank=None,conclusion='Parsel uygunluğu ve ticari girdiler doğrulanmadan yatırım yeri seçilemez.') for s in sites]
    write_csv(pd.DataFrame(rows),'data/processed/site_screening.csv')
    criteria=read_csv('config/fe401.csv')
    out=[]
    base=criteria.weight.to_numpy()
    alternatives={'equal':base,'raw_material_priority':np.array([.25,.15,.08,.04,.12,.08,.08,.05,.05,.04,.04,.02]),'market_priority':np.array([.15,.25,.08,.04,.15,.06,.06,.05,.05,.04,.04,.03])}
    for site in sites:
        for name,weights in alternatives.items():
            out.append(dict(site=site['site'],weight_case=name,evidence_score=None,expert_score=None,status='MISSING',eligibility=screen(site),notes='Weights are editable assumptions. No scores invented. Financial ranking is separate.'))
    write_csv(pd.DataFrame(out),'data/processed/fe401_weight_sensitivity.csv')
    write_json(dict(status='CONDITIONAL_ONLY',preferred_site=None,reason='No site has verified parcel eligibility or complete commercial inputs. Provincial processing-tomato totals do not prove local supplier availability or profitability.',fe401_pdf_status='MISSING',conditional_rule='Select the eligible site maximizing risk-adjusted ten-year real NPV after dated supply, market, utility and investment evidence is supplied.'),'reports/recommendation.json')
    return rows
