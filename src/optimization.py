"""Seasonal landed-cost LP/MILP with purchase, inventory, quality and integer truck constraints."""
import numpy as np
import pandas as pd
from scipy.optimize import linprog, milp, Bounds, LinearConstraint
from .common import ROOT, load_config, read_csv, write_csv, write_json

def solve_supply(offers, requirements, storage_capacity, storage_rate, inventory_loss=0.0, integer_trucks=False, payload=20.0, max_trucks=None):
    """Solve one site over explicit ordered periods.

    Purchase x is gross shipped tonnes. Inventory receives x*(1-transport_loss).
    Costs include purchase+handling+variable freight once, and inventory holding.
    In truck mode freight is fixed per integer departure, not tonne-km again.
    Inputs must identify offered supply separately from agricultural production.
    """
    if not 0<=inventory_loss<1 or storage_capacity<0 or storage_rate<0 or payload<=0:
        raise ValueError('Invalid storage, shrinkage or payload parameter')
    required_offer={'supplier_id','ingredient','period','available_tonnes','participation_limit','price','handling','freight_per_tonne','transport_loss','quality_eligible'}
    if not required_offer.issubset(offers.columns):
        raise ValueError('Offer schema incomplete')
    if requirements.duplicated(['ingredient','period']).any() or (requirements.required_tonnes<0).any():
        raise ValueError('Demand must be unique and nonnegative')
    if requirements.empty:
        raise ValueError('At least one requirement is required')
    offers=offers.copy().reset_index(drop=True)
    if offers.duplicated(['supplier_id','ingredient','period']).any():
        raise ValueError('Duplicate supplier-period offers require adjudication')
    numeric=['available_tonnes','participation_limit','price','handling','freight_per_tonne','transport_loss']
    if not np.isfinite(offers[numeric].to_numpy(dtype=float)).all() or (offers[numeric]<0).any().any() or (offers.participation_limit>1).any() or (offers.transport_loss>=1).any():
        raise ValueError('Offer numeric inputs invalid')
    ingredients=sorted(requirements.ingredient.unique())
    periods=sorted(requirements.period.unique())
    if not set(offers.period).issubset(set(periods)) or not set(offers.ingredient).issubset(set(ingredients)):
        raise ValueError('Offers outside requirement horizon or ingredients')
    stock_keys=[(k,t) for k in ingredients for t in periods]
    n=len(offers)
    s=len(stock_keys)
    size=n+s+(n if integer_trucks else 0)
    costs=np.zeros(size)
    costs[:n]=offers.price+offers.handling+(0 if integer_trucks else offers.freight_per_tonne)
    costs[n:n+s]=storage_rate
    upper=np.full(size,np.inf)
    upper[:n]=offers.available_tonnes*np.where(offers.quality_eligible==1,1,0)
    upper[n:n+s]=storage_capacity
    # Participation caps apply across supplier/ingredient over the complete horizon.
    equality=[]
    rhs=[]
    for ki,k in enumerate(ingredients):
        for ti,t in enumerate(periods):
            row=np.zeros(size)
            selected=(offers.ingredient==k)&(offers.period==t)
            row[:n]=np.where(selected,1-offers.transport_loss,0)
            stock_index=n+stock_keys.index((k,t))
            row[stock_index]=-1
            if ti:
                row[n+stock_keys.index((k,periods[ti-1]))]=1-inventory_loss
            requirement=requirements[(requirements.ingredient==k)&(requirements.period==t)]
            demand=float(requirement.required_tonnes.iloc[0]) if len(requirement) else 0
            equality.append(row)
            rhs.append(demand)
            if ti==len(periods)-1:
                upper[stock_index]=0  # Explicit zero initial/terminal inventory policy.
    inequalities=[]
    limits=[]
    for (_,k),group in offers.groupby(['supplier_id','ingredient']):
        row=np.zeros(size)
        row[group.index]=1-group.transport_loss
        inequalities.append(row)
        limits.append(float(group.participation_limit.min()*requirements[requirements.ingredient==k].required_tonnes.sum()))
    # Shared storage capacity across ingredients, not capacity per crop.
    for t in periods:
        row=np.zeros(size)
        for k in ingredients:
            row[n+stock_keys.index((k,t))]=1
        inequalities.append(row)
        limits.append(storage_capacity)
    if integer_trucks:
        if 'freight_per_truck' not in offers or not np.isfinite(offers.freight_per_truck).all() or (offers.freight_per_truck<0).any():
            raise ValueError('Truck mode requires explicit nonnegative vehicle quote')
        costs[n+s:]=offers.freight_per_truck
        for i in range(n):
            row=np.zeros(size)
            row[i]=1
            row[n+s+i]=-payload
            inequalities.append(row)
            limits.append(0)
        if max_trucks is not None:
            if max_trucks<0:
                raise ValueError('Maximum truck count must be nonnegative')
            for t in periods:
                row=np.zeros(size)
                for i in offers.index[offers.period==t]:
                    row[n+s+i]=1
                inequalities.append(row)
                limits.append(max_trucks)
        integrality=np.zeros(size)
        integrality[n+s:]=1
        constraints=[LinearConstraint(np.asarray(equality),rhs,rhs),LinearConstraint(np.asarray(inequalities),-np.inf,limits)]
        result=milp(costs,integrality=integrality,bounds=Bounds(np.zeros(size),upper),constraints=constraints,options={'time_limit':60,'mip_rel_gap':0.0001})
    else:
        if max_trucks is not None:
            raise ValueError('Truck count constraints require integer_trucks=True')
        result=linprog(costs,A_eq=equality,b_eq=rhs,A_ub=inequalities,b_ub=limits,bounds=list(zip(np.zeros(size),upper)),method='highs')
    if not result.success:
        return dict(status='INFEASIBLE' if result.status==2 else 'SOLVER_FAILED',message=result.message,flows=pd.DataFrame(),inventory=pd.DataFrame(),total_cost=None)
    flows=offers.copy()
    flows['purchased_tonnes']=result.x[:n]
    flows['delivered_tonnes']=flows.purchased_tonnes*(1-flows.transport_loss)
    flows['truckloads']=np.rint(result.x[n+s:]).astype(int) if integer_trucks else np.nan
    flows['purchase_cost']=flows.purchased_tonnes*flows.price
    flows['handling_cost']=flows.purchased_tonnes*flows.handling
    flows['freight_cost']=flows.truckloads*flows.freight_per_truck if integer_trucks else flows.purchased_tonnes*flows.freight_per_tonne
    inventory=pd.DataFrame(stock_keys,columns=['ingredient','period'])
    inventory['closing_tonnes']=result.x[n:n+s]
    inventory['storage_cost']=inventory.closing_tonnes*storage_rate
    return dict(status='OPTIMAL',message=result.message,flows=flows,inventory=inventory,total_cost=float(result.fun),max_balance_error=float(np.max(np.abs(np.asarray(equality)@result.x-rhs))))

def optimize(demo=False):
    """Real-data run refuses missing quotes; optional legacy scenarios have isolated outputs."""
    prefix='output/demo' if demo else 'data/processed'
    if not demo:
        offers=read_csv('data/manual/supplier_offers_template.csv').dropna(how='all')
        configuration=load_config('assumptions.json')
        required=['monthly_production_fractions','storage_capacity_tonnes','storage_try_per_tonne_month','inventory_loss_fraction']
        absent=[k for k in required if configuration.get(k) is None]
        report=dict(status='NOT_ESTIMABLE',reason='Dated supplier offers, participation, quality, monthly seasonality, last-mile routes, losses, storage and truck quotes missing',missing_configuration=absent,agricultural_production_used_as_offer=False)
        if not offers.empty and not absent:
            if len(configuration['monthly_production_fractions'])!=12 or min(configuration['monthly_production_fractions'])<0 or not np.isclose(sum(configuration['monthly_production_fractions']),1):
                raise ValueError('Twelve nonnegative monthly production fractions must sum to one')
            required_columns=['supplier_id','site','ingredient','month','available_tonnes','participation_limit','price_try_per_tonne','handling_try_per_tonne','freight_try_per_tonne','transport_loss','quality_eligible','source_url','quote_date','price_year','price_basis','data_status']
            if not set(required_columns).issubset(offers.columns):
                raise ValueError('Supplier template requires full schema; see manual_import.md')
            if offers[required_columns].isna().any().any() or not (offers.data_status=='VERIFIED').all():
                raise ValueError('Production run requires complete dated VERIFIED supplier offers')
            if not (offers.price_basis=='real').all() or not (offers.price_year==configuration['base_price_year']).all():
                raise ValueError('Offers must be normalized to the configured real price year')
            from .materials import run_materials
            materials,_=run_materials()
            requirements=pd.DataFrame([dict(ingredient=r.ingredient,period=month+1,required_tonnes=r.gross_tonnes*fraction) for r in materials.itertuples() for month,fraction in enumerate(configuration['monthly_production_fractions'])])
            outcomes=[]
            output=[]
            for site in load_config('sites.json'):
                local=offers[offers.site==site['site']].copy()
                renamed=local.rename(columns={'month':'period','price_try_per_tonne':'price','handling_try_per_tonne':'handling','freight_try_per_tonne':'freight_per_tonne','freight_try_per_truck':'freight_per_truck'})
                if local.empty or set(materials.ingredient)-set(local.ingredient):
                    outcomes.append(dict(site=site['site'],status='NOT_ESTIMABLE',total_cost=None,reason='Missing one or more recipe ingredient offers'))
                    continue
                result=solve_supply(renamed,requirements,configuration['storage_capacity_tonnes'],configuration['storage_try_per_tonne_month'],inventory_loss=configuration['inventory_loss_fraction'],integer_trucks=configuration.get('integer_trucks',True),payload=configuration['truck_payload_tonnes'],max_trucks=configuration.get('max_trucks_per_month'))
                outcomes.append(dict(site=site['site'],status=result['status'],total_cost=result['total_cost'],reason=result['message']))
                if result['status']=='OPTIMAL':
                    output.append(result['flows'].assign(site=site['site'],status='ESTIMATED'))
                    write_csv(result['inventory'],f'data/processed/inventory_{site["site"]}.csv')
            write_csv(pd.DataFrame(outcomes),'data/processed/landed_costs.csv')
            write_csv(pd.concat(output,ignore_index=True) if output else pd.DataFrame(columns=['site','ingredient','supplier_id','period','purchased_tonnes','delivered_tonnes','total_cost','status']),f'{prefix}/optimal_supply_flows.csv')
            report=dict(status='ESTIMATED' if output else 'NOT_ESTIMABLE',sites=outcomes,agricultural_production_used_as_offer=False)
            write_json(report,'reports/optimization_status.json')
            return report
        write_json(report,'reports/optimization_status.json')
        write_csv(pd.DataFrame(columns=['site','ingredient','supplier_id','period','purchased_tonnes','delivered_tonnes','total_cost','status']),f'{prefix}/optimal_supply_flows.csv')
        write_csv(pd.DataFrame([dict(site=s['site'],status='NOT_ESTIMABLE',total_cost=None,reason=report['reason']) for s in load_config('sites.json')]),'data/processed/landed_costs.csv')
        return report
    source=read_csv('data/raw/legacy/tedarik_senaryosu.csv')
    roads=read_csv('data/raw/legacy/rota_mesafeleri.csv')
    needs=read_csv('data/raw/legacy/talep.csv')
    outcomes=[]
    flows=[]
    for site in sorted(roads.site.unique()):
        offers=[]
        for row in source.itertuples():
            distance=roads[(roads.origin==row.origin)&(roads.site==site)].road_km.iloc[0]
            offers.append(dict(supplier_id=row.origin,ingredient=row.ingredient,period=1,available_tonnes=row.capacity_ton_year,participation_limit=1.0,price=row.price_tl_per_ton,handling=250.0,freight_per_tonne=4.0*distance,freight_per_truck=4.0*distance*20,transport_loss=0.0,quality_eligible=1,road_km=distance,data_status='ASSUMED'))
        requirements=pd.DataFrame(dict(ingredient=needs.ingredient,period=1,required_tonnes=needs.ton_year))
        result=solve_supply(pd.DataFrame(offers),requirements,storage_capacity=0,storage_rate=0)
        outcomes.append(dict(site=site,status=result['status'],total_cost=result['total_cost'],data_status='ASSUMED',notes='Legacy annual three-vegetable scenario; assumed distances, zero transport losses, no seasonal storage. Not full feasibility.'))
        if result['status']=='OPTIMAL':
            f=result['flows'].assign(site=site,status='ASSUMED')
            flows.append(f)
    write_csv(pd.DataFrame(outcomes),f'{prefix}/legacy_logistics_scenario.csv')
    if flows:
        write_csv(pd.concat(flows,ignore_index=True),f'{prefix}/legacy_supply_flows.csv')
    return outcomes
