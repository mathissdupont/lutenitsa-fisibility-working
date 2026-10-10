"""Conservative chronological model evaluation with explicit ex-ante availability gates."""
import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .common import ROOT, read_csv, write_csv, write_json, load_config

MODELS=['naive','rolling_average','linear_trend','ols','ridge','panel_fixed_effects','random_forest']

def metrics(actual, predicted):
    actual=np.asarray(actual,dtype=float)
    predicted=np.asarray(predicted,dtype=float)
    return dict(mae=float(mean_absolute_error(actual,predicted)),rmse=float(np.sqrt(mean_squared_error(actual,predicted))),wape=float(np.abs(actual-predicted).sum()/np.abs(actual).sum()) if np.abs(actual).sum()>0 else None,r2=float(r2_score(actual,predicted)) if len(actual)>=2 and np.var(actual)>0 else None)

def make_panel(frame, metric='production'):
    """Exclude ambiguous observations and create only lagged, time-known features."""
    value_column='constant_price_try' if metric=='farm_gate_price' else 'value'
    frame=frame[(frame.metric==metric)&(frame.geographic_level=='district')&(frame.data_status=='VERIFIED')].copy()
    key=['province','district','year','product_code','metric']
    frame=frame[~frame.duplicated(key,keep=False)]
    frame['target']=pd.to_numeric(frame[value_column],errors='coerce')
    frame=frame[frame.target.notna()&(frame.target>=0)]
    frame['available_date']=pd.to_datetime(frame.available_date,errors='coerce')
    frame['district_key']=frame.province.astype(str)+'/'+frame.district.astype(str)
    frame=frame.sort_values(['product_code','district_key','year'])
    group=frame.groupby(['product_code','district_key'])
    frame['lag_target']=group.target.shift(1)
    frame['lag_available_date']=group.available_date.shift(1)
    frame['lag_year']=group.year.shift(1)
    frame['origin_date']=pd.to_datetime(frame.year.astype(int).astype(str)+'-01-01')
    frame['feature_eligible']=(frame.lag_year==frame.year-1)&(frame.lag_available_date<frame.origin_date)&frame.lag_target.notna()
    frame['log_target']=np.log1p(frame.target)
    frame['log_lag']=np.log1p(frame.lag_target)
    frame['trend']=frame.year-2015
    return frame

def fit_predict(train,test,model):
    if model=='linear_trend':
        estimator=LinearRegression().fit(train[['trend']],train.log_target)
        pred=estimator.predict(test[['trend']])
    elif model=='ols':
        estimator=smf.ols('log_target ~ log_lag + trend',data=train).fit(cov_type='HC3')
        pred=estimator.predict(test)
    elif model=='panel_fixed_effects':
        clusters=train.district_key.nunique()
        if clusters<8 or not set(test.district_key).issubset(set(train.district_key)):
            raise ValueError('At least eight district clusters and no unseen district required for panel inference')
        estimator=smf.ols('log_target ~ log_lag + trend + C(district_key)',data=train).fit(cov_type='cluster',cov_kwds={'groups':train.district_key})
        pred=estimator.predict(test)
    elif model=='ridge':
        # Fixed alpha declared in methodology; no tuning on held-out future periods.
        estimator=make_pipeline(StandardScaler(),Ridge(alpha=1.0)).fit(train[['log_lag','trend']],train.log_target)
        pred=estimator.predict(test[['log_lag','trend']])
    elif model=='random_forest':
        if len(train)<200 or train.district_key.nunique()<10:
            raise ValueError('Nonlinear benchmark needs at least 200 rows and ten districts')
        estimator=RandomForestRegressor(n_estimators=100,max_depth=3,min_samples_leaf=10,random_state=401,n_jobs=1).fit(train[['log_lag','trend']],train.log_target)
        pred=estimator.predict(test[['log_lag','trend']])
    else:
        raise ValueError(model)
    return np.maximum(0,np.expm1(np.asarray(pred))),estimator

def regress():
    frame=read_csv('data/processed/historical_observations.csv')
    assumptions=load_config('assumptions.json')
    results=[]
    predictions=[]
    coefficients=[]
    forecasts=[]
    diagnostics=[]
    for target_metric in ['production','farm_gate_price']:
        panel=make_panel(frame,target_metric)
        products=read_csv('config/products.csv').product_code.tolist()
        for product in products:
            rows=panel[panel.product_code==product]
            eligible=rows[rows.feature_eligible].copy()
            for model in MODELS:
                local=[]
                reason='Verified district history and dated releases required'
                for year in range(2020,2026):
                    cutoff=pd.Timestamp(f'{year}-01-01')
                    train=eligible[(eligible.year<year)&(eligible.available_date<cutoff)]
                    test=eligible[eligible.year==year]
                    if test.empty:
                        continue
                    if model in ['naive','rolling_average']:
                        values=[]
                        for row in test.itertuples():
                            history=rows[(rows.district_key==row.district_key)&(rows.year<year)&(rows.available_date<cutoff)].sort_values('year')
                            values.append(row.lag_target if model=='naive' else history.tail(3).target.mean())
                        predicted=np.asarray(values)
                    else:
                        if len(train)<30 or train.year.nunique()<5 or train.district_key.nunique()<3:
                            reason='At least 30 training rows, five years and three districts required for pooled regression'
                            continue
                        try:
                            predicted,_=fit_predict(train,test,model)
                        except ValueError as error:
                            reason=str(error)
                            continue
                    for row,value in zip(test.itertuples(),predicted):
                        if np.isfinite(value):
                            local.append(dict(product_code=product,metric=target_metric,model=model,province=row.province,district=row.district,year=int(year),actual=float(row.target),predicted=float(value),residual=float(row.target-value),validation='HOLDOUT' if year>=2023 else 'EXPANDING_BACKTEST',status='ESTIMATED'))
                holdout=[r for r in local if r['year']>=2023]
                if not holdout:
                    results.append(dict(product_code=product,metric=target_metric,model=model,status='NOT_ESTIMABLE',reason=reason,observations=len(rows),evaluation_rows=0,mae=None,rmse=None,wape=None,r2=None))
                else:
                    score=metrics([r['actual'] for r in holdout],[r['predicted'] for r in holdout])
                    results.append(dict(product_code=product,metric=target_metric,model=model,status='ESTIMATED',reason='One-step rolling origin; 2023-2025 evaluation',observations=len(rows),evaluation_rows=len(holdout),**score))
                predictions.extend(local)
            # Forecast only from complete eligible history known at configured origin.
            origin=pd.Timestamp(assumptions['forecast_date'])
            known=rows[(rows.available_date<origin)&(rows.year<origin.year)]
            comparisons=[r for r in results if r['product_code']==product and r['metric']==target_metric and r['status']=='ESTIMATED']
            best=min(comparisons,key=lambda r:r['mae'])['model'] if comparisons else None
            naive=next((r for r in comparisons if r['model']=='naive'),None)
            for comparison in comparisons:
                comparison['outperforms_naive']=comparison['mae']<naive['mae'] if naive else None
            for district in read_csv('config/geography.csv').itertuples():
                history=known[(known.province==district.province)&(known.district==district.district)].sort_values('year')
                state=history.target.tail(3).tolist()
                usable=best is not None and len(history)>0 and int(history.year.max())==2025
                for year in assumptions['forecast_years']:
                    value=None
                    if usable:
                        test=pd.DataFrame([dict(trend=year-2015,log_lag=np.log1p(state[-1]),district_key=district.province+'/'+district.district)])
                        if best=='naive':
                            value=state[-1]
                        elif best=='rolling_average':
                            value=float(np.mean(state[-3:]))
                        else:
                            training=eligible[(eligible.available_date<origin)&(eligible.year<=2025)]
                            value=float(fit_predict(training,test,best)[0][0])
                        state.append(value)
                    # Multi-year intervals require horizon-specific calibration; never reuse one-step residuals.
                    forecasts.append(dict(province=district.province,district=district.district,product_code=product,metric=target_metric,year=year,baseline=value,optimistic=None,pessimistic=None,pi_lower=None,pi_upper=None,interval_status='NOT_ESTIMABLE',scenario_status='MISSING',model=best,status='ESTIMATED' if value is not None else 'NOT_ESTIMABLE',reason='Horizon-specific uncertainty/scenario inputs missing' if value is not None else 'Validated model and 2025 observations available at forecast origin are required'))
            explanatory=eligible[(eligible.available_date<origin)&(eligible.year<=2025)]
            if len(explanatory)>=30 and explanatory.district_key.nunique()>=3 and explanatory.year.nunique()>=5:
                model='panel_fixed_effects' if explanatory.district_key.nunique()>=8 else 'ols'
                _,fitted=fit_predict(explanatory,explanatory,model)
                intervals=fitted.conf_int()
                for term,estimate in fitted.params.items():
                    coefficients.append(dict(product_code=product,metric=target_metric,model=model,term=term,coefficient=float(estimate),ci_lower=float(intervals.loc[term,0]),ci_upper=float(intervals.loc[term,1]),p_value=float(fitted.pvalues[term]),status='ESTIMATED'))
                diagnostics.append(dict(product_code=product,metric=target_metric,model=model,nobs=int(fitted.nobs),r2=float(fitted.rsquared),adjusted_r2=float(fitted.rsquared_adj),condition_number=float(fitted.condition_number),covariance='district-clustered' if model=='panel_fixed_effects' else 'HC3; insufficient clusters for reliable cluster inference',interpretation='Association only; district dependence unresolved for HC3; no causal inference'))
    tables={'model_validation':pd.DataFrame(results),'backtest_predictions':pd.DataFrame(predictions,columns=['product_code','metric','model','province','district','year','actual','predicted','residual','validation','status']),'regression_coefficients':pd.DataFrame(coefficients,columns=['product_code','metric','model','term','coefficient','ci_lower','ci_upper','p_value','status']),'forecasts':pd.DataFrame(forecasts)}
    for name,table in tables.items():
        write_csv(table,f'data/processed/{name}.csv')
    write_json(diagnostics,'reports/regression_diagnostics.json')
    write_json(dict(status='ESTIMATED' if predictions else 'NOT_ESTIMABLE',district_rows=len(panel),feature_policy='Lagged target available before January 1; no realized yield, current outcome or future weather predictors; no imputation; training-only scaling',interval_policy='Multi-year prediction intervals withheld pending horizon-specific calibration. Scenarios require editable external assumptions.'),'reports/statistics_status.json')
    if predictions:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plot=pd.DataFrame(predictions)
        fig,axes=plt.subplots(1,2,figsize=(11,4))
        axes[0].scatter(plot.actual,plot.predicted,alpha=.5)
        axes[0].set(xlabel='Gerçek değer',ylabel='Tahmin')
        axes[1].scatter(plot.predicted,plot.residual,alpha=.5)
        axes[1].axhline(0,color='grey')
        axes[1].set(xlabel='Tahmin',ylabel='Artık')
        fig.tight_layout()
        fig.savefig(ROOT/'output/model_diagnostics.png',dpi=160)
        plt.close(fig)
    return tables
