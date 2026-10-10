"""Real-currency ten-year unlevered appraisal, sensitivity and reproducible risk scenarios."""
import copy
import math
import numpy as np
import numpy_financial as npf
import pandas as pd
from scipy.optimize import brentq
from .common import ROOT, load_config, read_csv, write_csv, write_json

def npv(cashflows, rate):
    if rate<=-1:
        raise ValueError('Discount rate must exceed -1')
    return float(sum(float(cf)/(1+rate)**t for t,cf in enumerate(cashflows)))

def irr(cashflows):
    signs=np.sign([v for v in cashflows if abs(v)>1e-12])
    changes=int(np.sum(signs[1:]!=signs[:-1]))
    if changes!=1:
        return None  # Multiple/no sign changes: uniqueness/definition not established.
    value=float(npf.irr(cashflows))
    return value if np.isfinite(value) else None

def payback(cashflows):
    balance=float(cashflows[0])
    if balance>=0:
        return 0.0
    for t,flow in enumerate(cashflows[1:],start=1):
        if balance+flow>=0 and flow>0:
            return float(t-1-balance/flow)
        balance+=flow
    return None

def appraise(config, site, annual_landed_cost, daily_tonnes=None):
    """Calculate produced and sold volume separately, including all production costs.

    Constant annual real inputs; unsold output has zero sales and no terminal recovery.
    No instant loss tax refund: tax losses carry forward. Terminal asset sale is
    taxed only on positive proceeds above book value; no assumed loss tax credit.
    Replacement investments enter service next year and depreciate over asset life.
    """
    if config['price_basis']!=config['discount_basis'] or config['price_basis']!='real':
        raise ValueError('Only a consistent real-price / real-discount-rate framework is supported')
    required_config=['demand_kg','selling_price_try_per_kg','working_capital_try','jar_kg','packaging_try_per_jar','processing_try_per_kg','waste_try_per_kg','real_discount_rate','tax_rate','utilization']
    required_site=['capex_try','labor_try','administration_try','fixed_overhead_try','utilities_try_per_kg','outbound_try_per_kg','maintenance_try']
    missing=[f'config.{k}' for k in required_config if config.get(k) is None]+[f'site.{k}' for k in required_site if site.get(k) is None]
    if annual_landed_cost is None:
        missing.append('annual_landed_cost')
    if missing:
        return dict(status='NOT_ESTIMABLE',missing=missing,summary={},cashflows=pd.DataFrame())
    for container,keys in [(config,required_config),(site,required_site)]:
        if any(not isinstance(container[k],(int,float)) or not math.isfinite(container[k]) or container[k]<0 for k in keys):
            raise ValueError('Financial inputs must be finite nonnegative values')
    if not 0<=config['tax_rate']<=1 or not 0<=config['utilization']<=1 or config['jar_kg']<=0 or config['depreciation_years']<=0 or config['horizon_years']<=0:
        raise ValueError('Invalid tax, utilization, jar size or horizon')
    if annual_landed_cost<0 or not math.isfinite(annual_landed_cost):
        raise ValueError('Invalid landed cost')
    if not 0<=config['depreciable_fraction']<=1 or not 0<=config['salvage_fraction']<=1 or config['replacement_capex_fraction']<0:
        raise ValueError('Invalid investment fractions')
    capacity=(daily_tonnes or config['daily_tonnes'])*1000*config['operating_days']
    produced=capacity*config['utilization']
    sold=min(produced,config['demand_kg'])
    capex=site['capex_try']
    horizon=int(config['horizon_years'])
    assets=[dict(cost=capex*config['depreciable_fraction'],start=1)]
    cash=[-capex-config['working_capital_try']]
    rows=[]
    loss_carry=0.0
    total_depreciation=0.0
    replacements=0.0
    for year in range(1,horizon+1):
        revenue=sold*config['selling_price_try_per_kg']
        ingredients=annual_landed_cost
        packaging=produced/config['jar_kg']*config['packaging_try_per_jar']
        processing=produced*config['processing_try_per_kg']
        waste=produced*config['waste_try_per_kg']
        utility=produced*site['utilities_try_per_kg']
        outbound=sold*site['outbound_try_per_kg']
        fixed=site['labor_try']+site['administration_try']+site['fixed_overhead_try']+site['maintenance_try']
        opex=ingredients+packaging+processing+waste+utility+outbound+fixed
        ebitda=revenue-opex
        depreciation=sum(asset['cost']/config['depreciation_years'] for asset in assets if asset['start']<=year<asset['start']+config['depreciation_years'])
        total_depreciation+=depreciation
        ebit=ebitda-depreciation
        opening_loss=loss_carry
        if ebit<0:
            loss_carry+=-ebit
            taxable=0.0
        else:
            offset=min(loss_carry,ebit)
            loss_carry-=offset
            taxable=ebit-offset
        tax=taxable*config['tax_rate']
        replacement=capex*config['replacement_capex_fraction'] if year<horizon else 0.0
        replacements+=replacement
        if replacement:
            assets.append(dict(cost=replacement,start=year+1))
        book_value=capex+replacements-total_depreciation
        salvage=capex*config['salvage_fraction'] if year==horizon else 0.0
        terminal_tax=max(salvage-book_value,0)*config['tax_rate'] if year==horizon else 0.0
        wc_recovery=config['working_capital_try'] if year==horizon else 0.0
        fcf=ebitda-tax-replacement+salvage-terminal_tax+wc_recovery
        cash.append(fcf)
        rows.append(dict(year=year,capacity_kg=capacity,produced_kg=produced,sold_kg=sold,unsold_kg=produced-sold,revenue=revenue,landed_ingredients=ingredients,packaging=packaging,processing=processing,waste=waste,utilities=utility,outbound=outbound,fixed_costs=fixed,operating_costs=opex,ebitda=ebitda,depreciation=depreciation,ebit=ebit,opening_tax_loss=opening_loss,closing_tax_loss=loss_carry,taxes=tax,replacement_capex=replacement,salvage=salvage,terminal_tax=terminal_tax,working_capital_recovery=wc_recovery,fcf=fcf,discounted_fcf=fcf/(1+config['real_discount_rate'])**year))
    contribution=config['selling_price_try_per_kg']-site['outbound_try_per_kg']-(annual_landed_cost/produced+config['packaging_try_per_jar']/config['jar_kg']+config['processing_try_per_kg']+config['waste_try_per_kg']+site['utilities_try_per_kg']) if produced>0 else None
    variable_cost=rows[0]['operating_costs']-fixed
    summary=dict(npv=npv(cash,config['real_discount_rate']),irr=irr(cash),payback_years=payback(cash),ebitda=rows[0]['ebitda'],break_even_selling_price=rows[0]['operating_costs']/sold if sold>0 else None,break_even_sales_volume=fixed/contribution if contribution is not None and contribution>0 else None,break_even_scope='EBITDA; break-even volume assumes production follows sales and excludes capital return',produced_kg=produced,sold_kg=sold,capacity_utilization=produced/capacity if capacity>0 else None,cashflows=cash)
    return dict(status='ASSUMED',missing=[],summary=summary,cashflows=pd.DataFrame(rows))

def investment_break_even_price(config,site,landed_cost):
    """Price yielding NPV zero for fixed production and demand; return None when undefined."""
    if config.get('demand_kg') is None or config['demand_kg']<=0:
        return None
    def objective(price):
        candidate=dict(config,selling_price_try_per_kg=price)
        result=appraise(candidate,site,landed_cost)
        if result['status']=='NOT_ESTIMABLE':
            raise ValueError('Missing appraisal inputs')
        return result['summary']['npv']
    if objective(0)>=0:
        return 0.0
    upper=max(1,config['selling_price_try_per_kg'])
    for _ in range(20):
        if objective(upper)>0:
            return float(brentq(objective,0,upper))
        upper*=2
    return None

def monte_carlo(config,site,base_landed_cost):
    """Uncalibrated triangular driver shocks; a failed harvest is a failed supply draw.

    Annual contract supply is fixed at baseline production. Harvest shock cannot
    silently be converted to a price shock. Site input must explicitly state the
    contract buffer; draws with insufficient supply are recorded as infeasible.
    """
    if site.get('contract_supply_buffer') is None or site.get('inbound_cost_share') is None:
        raise ValueError('Monte Carlo needs explicit contracted-supply buffer and inbound share of landed costs')
    if not 0<=site['inbound_cost_share']<=1:
        raise ValueError('Inbound cost share must be in [0,1]')
    rng=np.random.default_rng(config['seed'])
    rows=[]
    distributions=config['monte_carlo_distributions']
    for draw in range(config['monte_carlo_draws']):
        shocks={key:float(rng.triangular(*bounds)) for key,bounds in distributions.items()}
        c=copy.deepcopy(config)
        s=copy.deepcopy(site)
        c['selling_price_try_per_kg']*=shocks['price']
        c['demand_kg']*=shocks['demand']
        s['utilities_try_per_kg']*=shocks['energy']
        s['outbound_try_per_kg']*=shocks['freight']
        supplied=shocks['harvest']*site['contract_supply_buffer']
        feasible=supplied>=1
        shocked_landed=base_landed_cost*((1-site['inbound_cost_share'])*shocks['raw_cost']+site['inbound_cost_share']*shocks['freight'])
        result=appraise(c,s,shocked_landed) if feasible else None
        rows.append(dict(draw=draw,**shocks,contract_supply_ratio=supplied,status='ASSUMED_FEASIBLE' if feasible else 'INFEASIBLE_SUPPLY',npv=result['summary']['npv'] if feasible else None))
    frame=pd.DataFrame(rows)
    valid=frame[frame.status=='ASSUMED_FEASIBLE'].npv
    summary=dict(draws=len(frame),feasible_draws=len(valid),infeasible_supply_share=float((frame.status=='INFEASIBLE_SUPPLY').mean()),mean_npv=float(valid.mean()) if len(valid) else None,p05_npv=float(valid.quantile(.05)) if len(valid) else None,p50_npv=float(valid.quantile(.5)) if len(valid) else None,p95_npv=float(valid.quantile(.95)) if len(valid) else None,negative_npv_share_conditional=float((valid<0).mean()) if len(valid) else None,risk_adjusted_score=float(valid.mean()-config['risk_penalty_fraction']*max(valid.mean()-valid.quantile(.05),0)) if len(valid) else None,interpretation='Uncalibrated independent triangular assumptions; NPV statistics conditional on feasible supply. Infeasible draws are not dropped from feasibility reporting. No empirical probability claim.')
    return frame,summary

def run_finance():
    config=load_config('assumptions.json')
    sites=load_config('sites.json')
    summaries=[]
    capacities=[]
    landed=read_csv('data/processed/landed_costs.csv') if (ROOT/'data/processed/landed_costs.csv').exists() else pd.DataFrame(columns=['site','total_cost','status'])
    for site in sites:
        row=landed[(landed.site==site['site'])&(landed.status=='OPTIMAL')]
        cost=float(row.total_cost.iloc[0]) if len(row) else None
        result=appraise(config,site,cost)
        summaries.append(dict(site=site['site'],label_tr=site['label_tr'],status=result['status'],**({k:v for k,v in result['summary'].items() if k!='cashflows'} if result['summary'] else dict(npv=None,irr=None,payback_years=None)),missing=', '.join(result['missing'])))
        if not result['cashflows'].empty:
            write_csv(result['cashflows'],f'data/processed/cashflows_{site["site"]}.csv')
        for capacity in config['capacity_scenarios']:
            capacities.append(dict(site=site['site'],daily_tonnes=capacity,annual_capacity_kg=capacity*1000*config['operating_days'],planned_production_kg=capacity*1000*config['operating_days']*config['utilization'],demand_kg=config['demand_kg'],sold_kg=None,capex_try=site['capex_try'] if capacity==config['daily_tonnes'] else None,status='NOT_ESTIMABLE',reason='Capacity-specific equipment, utilities, supplier and demand quotations required'))
    write_csv(pd.DataFrame(summaries),'data/processed/profitability.csv')
    write_csv(pd.DataFrame(capacities),'data/processed/capacity_scenarios.csv')
    write_json(dict(status='NOT_ESTIMABLE',reason='Missing landed costs, demand, outbound cost, maintenance and capacity-specific investment. No fabricated NPV, IRR or risk distribution results.',required_inputs=summaries),'reports/finance_status.json')
    return summaries
