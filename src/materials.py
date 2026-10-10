"""Editable gross recipe and explicit sequential process losses."""
import math
import pandas as pd
from .common import load_config, write_csv, write_json

def material_balance(finished_kg, recipe, operating_days, jar_kg):
    if not math.isfinite(finished_kg) or finished_kg<0 or operating_days<=0 or jar_kg<=0:
        raise ValueError('Production must be finite nonnegative; days and jar mass positive')
    rows=[]
    for ingredient in recipe:
        ratio=float(ingredient['gross_kg_per_finished_kg'])
        if ratio<0 or not math.isfinite(ratio):
            raise ValueError('Invalid gross ingredient ratio')
        gross=finished_kg*ratio
        clean=ingredient.get('cleaning_loss')
        roast=ingredient.get('roasting_loss')
        for loss in [clean,roast]:
            if loss is not None and not 0<=loss<1:
                raise ValueError('Stage loss must be in [0,1)')
        cleaned=gross*(1-clean) if clean is not None else None
        roasted=cleaned*(1-roast) if cleaned is not None and roast is not None else None
        season=ingredient.get('season_intake_days')
        if season is not None and not 0<season<=365:
            raise ValueError('Season intake days must be in (0,365]')
        rows.append(dict(ingredient=ingredient['ingredient'],label_tr=ingredient['label_tr'],gross_ratio=ratio,gross_kg=gross,gross_tonnes=gross/1000,cleaning_loss=clean,roasting_loss=roast,post_cleaning_kg=cleaned,post_roasting_kg=roasted,season_intake_days=season,season_daily_tonnes=gross/1000/season if season else None,average_daily_use_tonnes=gross/1000/operating_days,price_try_per_kg=ingredient['price_try_per_kg'],status='ASSUMED',source=ingredient['source']))
    gross_total=sum(r['gross_kg'] for r in rows)
    if gross_total<finished_kg:
        raise ValueError('Gross recipe cannot yield requested finished mass without explicit additional inputs')
    retained=sum(r['post_roasting_kg'] for r in rows) if all(r['post_roasting_kg'] is not None for r in rows) else None
    if retained is not None and retained<finished_kg-1e-6:
        raise ValueError('Stage losses leave less than finished product; revise recipe or yields')
    summary=dict(finished_kg=finished_kg,gross_input_kg=gross_total,total_loss_and_evaporation_kg=gross_total-finished_kg,evaporation_kg=retained-finished_kg if retained is not None else None,cleaning_and_roasting_loss_kg=gross_total-retained if retained is not None else None,jars=math.ceil(finished_kg/jar_kg),balance_status='ASSUMED' if retained is not None else 'MISSING_STAGE_LOSSES',storage_status='Monthly intake, shelf life and storage capacities required')
    return pd.DataFrame(rows),summary

def run_materials():
    assumptions=load_config('assumptions.json')
    frame,summary=material_balance(assumptions['daily_tonnes']*1000*assumptions['operating_days']*assumptions['utilization'],load_config('recipe.json'),assumptions['operating_days'],assumptions['jar_kg'])
    write_csv(frame,'data/processed/material_balance.csv')
    write_json(summary,'reports/material_balance.json')
    return frame,summary
