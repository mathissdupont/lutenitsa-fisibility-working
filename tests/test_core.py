"""Synthetic arithmetic fixtures are test-only; never research observations."""
import copy
import numpy as np
import pandas as pd
import pytest
from src.data import normalize_unit, normalize_observations, quality_report, deflate_prices
from src.materials import material_balance
from src.optimization import solve_supply
from src.finance import appraise,npv,irr,payback,monte_carlo
from src.statistics import metrics,make_panel
from src.decision import screen,weighted_score
from src.common import load_config,read_csv,ROOT,sha256

@pytest.mark.parametrize('value,unit,metric,expected',[(1000,'kg','production',1),(10,'da','area',1),(100,'kg_per_da','yield',1),(2,'thousand_t','production',2000),(1,'thousand_da','area',100)])
def test_unit_conversion(value,unit,metric,expected):
    assert normalize_unit(value,unit,metric)[0]==expected

def test_missing_not_zero():
    assert np.isnan(normalize_unit(None,'t','production')[0])
    with pytest.raises(ValueError):
        normalize_unit(2,'ha','production')

def test_material_balance_sequential():
    recipe=[dict(ingredient='TEST',label_tr='Test',gross_kg_per_finished_kg=2,price_try_per_kg=3,cleaning_loss=.1,roasting_loss=.2,season_intake_days=50,status='ASSUMED',source='test-only')]
    table,summary=material_balance(1000,recipe,250,.5)
    assert table.post_roasting_kg.iloc[0]==pytest.approx(1440)
    assert summary['evaporation_kg']==pytest.approx(440)
    assert summary['gross_input_kg']==pytest.approx(summary['finished_kg']+summary['evaporation_kg']+summary['cleaning_and_roasting_loss_kg'])
    assert summary['jars']==2000

def offer(supplier='A',period=1,quantity=20,price=10,loss=0,eligible=1):
    return dict(supplier_id=supplier,ingredient='TEST',period=period,available_tonnes=quantity,participation_limit=1,price=price,handling=2,freight_per_tonne=3,freight_per_truck=60,transport_loss=loss,quality_eligible=eligible)

def demand(period=1,quantity=10):
    return dict(ingredient='TEST',period=period,required_tonnes=quantity)

def test_lp_cost_and_loss():
    result=solve_supply(pd.DataFrame([offer(quantity=20,loss=.1)]),pd.DataFrame([demand(quantity=9)]),0,0)
    assert result['status']=='OPTIMAL'
    assert result['flows'].purchased_tonnes.iloc[0]==pytest.approx(10)
    assert result['total_cost']==pytest.approx(150)
    assert result['max_balance_error']<1e-7

def test_infeasible_supply_and_quality():
    assert solve_supply(pd.DataFrame([offer(quantity=5)]),pd.DataFrame([demand()]),0,0)['status']=='INFEASIBLE'
    assert solve_supply(pd.DataFrame([offer(eligible=0)]),pd.DataFrame([demand()]),0,0)['status']=='INFEASIBLE'

def test_seasonal_storage_and_participation():
    offers=pd.DataFrame([offer(period=1,quantity=20),offer(period=2,quantity=0)])
    requirements=pd.DataFrame([demand(1,10),demand(2,10)])
    result=solve_supply(offers,requirements,10,1)
    assert result['status']=='OPTIMAL'
    assert result['inventory'].closing_tonnes.tolist()==pytest.approx([10,0])
    assert result['total_cost']==pytest.approx(310)
    assert solve_supply(offers,requirements,9,1)['status']=='INFEASIBLE'
    offers['participation_limit']=.4
    assert solve_supply(offers,requirements,20,1)['status']=='INFEASIBLE'

def test_milp_whole_trucks_and_capacity():
    offers=pd.DataFrame([offer(quantity=30)])
    requirements=pd.DataFrame([demand(quantity=21)])
    result=solve_supply(offers,requirements,0,0,integer_trucks=True,payload=20)
    assert result['flows'].truckloads.iloc[0]==2
    assert result['total_cost']==pytest.approx(21*12+120)
    assert solve_supply(offers,requirements,0,0,integer_trucks=True,payload=20,max_trucks=1)['status']=='INFEASIBLE'

def financial_inputs():
    config=load_config('assumptions.json')
    config.update(daily_tonnes=1,operating_days=100,demand_kg=80000,selling_price_try_per_kg=10,utilization=1,jar_kg=.5,packaging_try_per_jar=.5,processing_try_per_kg=1,waste_try_per_kg=0,working_capital_try=10000,horizon_years=2,depreciation_years=2,depreciable_fraction=1,salvage_fraction=0,replacement_capex_fraction=0,tax_rate=.25,real_discount_rate=.1)
    site=dict(capex_try=100000,labor_try=10000,administration_try=0,fixed_overhead_try=0,utilities_try_per_kg=1,outbound_try_per_kg=1,maintenance_try=0,contract_supply_buffer=1,inbound_cost_share=.2)
    return config,site

def test_financial_arithmetic_sales_tax_working_capital():
    c,s=financial_inputs()
    result=appraise(c,s,200000)
    row=result['cashflows'].iloc[0]
    assert row.produced_kg==100000 and row.sold_kg==80000 and row.unsold_kg==20000
    assert row.revenue==800000
    assert row.operating_costs==590000
    assert row.ebitda==210000 and row.depreciation==50000 and row.taxes==40000
    assert result['summary']['cashflows']==pytest.approx([-110000,170000,180000])
    assert result['summary']['npv']==pytest.approx(-110000+170000/1.1+180000/1.1**2)

def test_no_tax_refund_and_real_framework():
    c,s=financial_inputs()
    c['selling_price_try_per_kg']=0
    result=appraise(c,s,200000)
    assert (result['cashflows'].taxes==0).all()
    assert result['cashflows'].closing_tax_loss.iloc[-1]>0
    c['discount_basis']='nominal'
    with pytest.raises(ValueError):
        appraise(c,s,200000)

def test_npv_irr_payback_missing():
    assert npv([-100,110],.1)==pytest.approx(0)
    assert irr([-100,110])==pytest.approx(.1)
    assert irr([-100,200,-50]) is None
    assert irr([-100,-10]) is None
    assert payback([-100,40,80])==pytest.approx(1.75)
    c,s=financial_inputs()
    c['demand_kg']=None
    assert appraise(c,s,0)['status']=='NOT_ESTIMABLE'

def test_monte_carlo_reproducible_harvest_failure():
    c,s=financial_inputs()
    c['monte_carlo_draws']=30
    left,summary=monte_carlo(c,s,200000)
    right,_=monte_carlo(c,s,200000)
    pd.testing.assert_frame_equal(left,right)
    assert summary['infeasible_supply_share']>0
    assert left[left.status=='INFEASIBLE_SUPPLY'].npv.isna().all()

def test_forecast_release_gate_no_future_feature():
    frame=pd.DataFrame([dict(metric='production',geographic_level='district',data_status='VERIFIED',province='Bursa',district='Karacabey',year=y,product_code='TEST',value=10,available_date=d) for y,d in [(2020,'2022-03-01'),(2021,'2022-03-01'),(2022,'2022-12-31'),(2023,'2024-01-01')]])
    panel=make_panel(frame)
    assert not panel[panel.year==2021].feature_eligible.iloc[0]
    assert not panel[panel.year==2022].feature_eligible.iloc[0]
    assert panel[panel.year==2023].feature_eligible.iloc[0]
    assert not any('yield' in c or 'climate' in c for c in panel.columns)

def test_metrics_zero_denominator_and_deflator():
    assert metrics([0,0],[1,2])['wape'] is None
    frame=pd.DataFrame([dict(metric='farm_gate_price',value=10,year=2020)])
    indices=pd.DataFrame([dict(year=2020,index=100,base='TEST',data_status='VERIFIED'),dict(year=2025,index=200,base='TEST',data_status='VERIFIED')])
    assert deflate_prices(frame,indices,2025).constant_price_try.iloc[0]==20
    assert deflate_prices(frame,indices,2026).constant_price_try.isna().all()

def test_screen_unknown_and_weights():
    assert screen({})=='UNVERIFIED'
    assert screen(dict(food_use='FAIL'))=='FAIL'
    assert weighted_score([5]*12,[1/12]*12)==pytest.approx(100)
    assert weighted_score([np.nan]*12,[1/12]*12) is None

def test_original_preservation():
    import json
    records=json.loads((ROOT/'reports/legacy_inventory.json').read_text(encoding='utf-8'))
    for record in records:
        assert sha256(ROOT/'data/raw/legacy'/record['file'])==record['sha256']
        # README is expanded, while its original preserved copy is immutable.
        if record['file']!='README.md':
            assert sha256(ROOT/record['file'])==record['sha256']

def test_verified_data_not_synthetic_or_mapped_pepper():
    observations=read_csv('data/processed/historical_observations.csv')
    assert len(observations)==38
    assert not (observations.geographic_level=='district').any()
    assert not (observations.product_code=='PEPPER_KAPYA').any()
    assert observations[observations.product_code=='PEPPER_PROCESSING'].value.tolist()==pytest.approx([202470,115903,120917])
    assert 'demo' not in '\n'.join(observations.raw_file.astype(str))

def test_duplicate_and_negative_quality_flags():
    frame=read_csv('data/processed/historical_observations.csv')
    duplicate=pd.concat([frame,frame.iloc[[0]]],ignore_index=True)
    report=quality_report(duplicate)
    assert report['duplicate_rows']==2
    assert any(issue['issue']=='DUPLICATE_OBSERVATION' for issue in report['issues'])
    negative=frame.copy()
    negative.loc[0,'value']=-1
    report=quality_report(negative)
    assert any(issue['issue']=='INVALID_VALUE' for issue in report['issues'])

def test_shared_storage_across_ingredients():
    rows=[offer(period=1,quantity=20),offer(period=2,quantity=0)]
    rows+= [dict(offer(period=1,quantity=20),ingredient='SECOND'),dict(offer(period=2,quantity=0),ingredient='SECOND')]
    requirements=[demand(1,10),demand(2,10),dict(demand(1,10),ingredient='SECOND'),dict(demand(2,10),ingredient='SECOND')]
    assert solve_supply(pd.DataFrame(rows),pd.DataFrame(requirements),20,1)['status']=='OPTIMAL'
    assert solve_supply(pd.DataFrame(rows),pd.DataFrame(requirements),15,1)['status']=='INFEASIBLE'

def test_tax_loss_offsets_future_profit():
    c,s=financial_inputs()
    c.update(selling_price_try_per_kg=8,depreciation_years=1)
    result=appraise(c,s,200000)
    assert result['cashflows'].ebit.tolist()==pytest.approx([-50000,50000])
    assert result['cashflows'].taxes.tolist()==pytest.approx([0,0])
    assert result['cashflows'].closing_tax_loss.tolist()==pytest.approx([50000,0])

def test_current_forecasts_require_observed_releases():
    import json
    report=json.loads((ROOT/'reports/data_quality.json').read_text(encoding='utf-8'))
    assert report['available_dates_missing']==38
    assert report['missing_district_records']==2904

def test_distance_proxies_and_source_links():
    roads=read_csv('data/processed/distance_matrix.csv')
    assert len(roads)==45
    assert (roads.data_status=='VERIFIED').all()
    assert (roads.distance_type=='DISTRICT_CENTER_PROXY').all()
    selected=roads[(roads.origin=='Karacabey')&(roads.destination=='BURSA_MKP')]
    assert selected.road_km.iloc[0]==23
    assert roads[roads.road_km==0].notes.str.contains('center-to-center').all()
