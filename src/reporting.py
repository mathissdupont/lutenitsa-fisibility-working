"""Turkish presentation workbook with linked, guarded financial formulas."""
import json
import math
from pathlib import Path
import pandas as pd
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
from .common import ROOT,read_csv,load_config,write_json

SHEETS=['DASHBOARD','EXECUTIVE_SUMMARY','DATA_SOURCES','DATA_QUALITY','HISTORICAL_PRODUCTION','PRODUCT_TRENDS','REGRESSION_RESULTS','MODEL_VALIDATION','FORECASTS_2026_2030','RECIPE_MATERIAL_BALANCE','SUPPLIER_REGIONS','DISTANCE_MATRIX','OPTIMAL_SUPPLY_FLOWS','INGREDIENT_COSTS','UTILITIES','INVESTMENT_CAPEX','OPERATING_COSTS','PROFITABILITY_NPV','CAPACITY_SCENARIOS','SENSITIVITY_MONTE_CARLO','FE401_DECISION_MATRIX','FINAL_RECOMMENDATION','ASSUMPTIONS','METHODOLOGY']
TITLES=['Lütenitsa fabrikası yer seçimi','Yönetici özeti','Kaynak sicili','Veri kalitesi','Doğrulanmış tarihsel gözlemler','Ürün eğilimleri','Regresyon katsayıları','Zaman sıralı model doğrulama','2026–2030 projeksiyonları','Reçete ve kütle dengesi','Tedarik bölgeleri','Karayolu mesafe matrisi','En uygun tedarik akışları','Teslim alınan girdi maliyetleri','Enerji ve su','Yatırım bütçesi','İşletme giderleri ve nakit akışı','On yıllık yatırım değerlendirmesi','Kapasite senaryoları','Duyarlılık ve Monte Carlo','FE401 karar matrisi','Koşullu yer seçimi sonucu','Düzenlenebilir varsayımlar','Yöntem ve kullanım']
NAVY='#142D4E'
TEAL='#138A87'
LIGHT='#F2F5F8'
AMBER='#FFF2CC'
RED='#FCE5E5'

def report():
    config=load_config('assumptions.json')
    sites=load_config('sites.json')
    recipe=load_config('recipe.json')
    quality=json.loads((ROOT/'reports/data_quality.json').read_text(encoding='utf-8'))
    path=ROOT/'output/Lutenitsa_Factory_Feasibility_2015_2025.xlsx'
    path.parent.mkdir(exist_ok=True)
    wb=xlsxwriter.Workbook(path,{'strings_to_urls':False,'strings_to_formulas':False})
    wb.set_properties({'title':'Lütenitsa Fabrikası Fizibilitesi','subject':'FE401; resmî gözlemler, varsayımlar ve kanıt boşlukları','author':'FE401 Research Project','comments':'Hypothetical legacy inputs are not official statistics.'})
    wb.set_calc_mode('auto')
    body=wb.add_format({'font_name':'Arial','font_size':10,'font_color':NAVY,'valign':'vcenter'})
    number=wb.add_format({'font_name':'Arial','font_size':10,'num_format':'#,##0.00;(#,##0.00);–','font_color':NAVY})
    percent=wb.add_format({'font_name':'Arial','font_size':10,'num_format':'0.0%','font_color':NAVY})
    title=wb.add_format({'font_name':'Arial','font_size':16,'bold':True,'font_color':NAVY})
    header=wb.add_format({'font_name':'Arial','font_size':10,'bold':True,'font_color':'white','bg_color':NAVY,'text_wrap':True,'valign':'vcenter'})
    note=wb.add_format({'font_name':'Arial','font_size':10,'italic':True,'font_color':'#63758B','text_wrap':True,'valign':'top'})
    input_number=wb.add_format({'font_name':'Arial','font_size':10,'font_color':'#0000FF','bg_color':AMBER,'num_format':'#,##0.00;(#,##0.00);–'})
    input_percent=wb.add_format({'font_name':'Arial','font_size':10,'font_color':'#0000FF','bg_color':AMBER,'num_format':'0.0%'})
    input_ratio=wb.add_format({'font_name':'Arial','font_size':10,'font_color':'#0000FF','bg_color':AMBER,'num_format':'0.000'})
    link_number=wb.add_format({'font_name':'Arial','font_size':10,'font_color':'#008000','num_format':'#,##0.00;(#,##0.00);–'})
    missing_format=wb.add_format({'font_name':'Arial','font_size':10,'font_color':'#AC3030','bg_color':RED})
    verified=wb.add_format({'font_name':'Arial','font_size':10,'font_color':'#075E5A','bg_color':'#DEF3EF'})
    estimated=wb.add_format({'font_name':'Arial','font_size':10,'font_color':'#415D7C','bg_color':'#E7EDF5'})
    sheets={name:wb.add_worksheet(name) for name in SHEETS}
    for name,caption in zip(SHEETS,TITLES):
        ws=sheets[name]
        ws.hide_gridlines(2)
        ws.set_tab_color(TEAL if name=='ASSUMPTIONS' else NAVY if name in ['DASHBOARD','PROFITABILITY_NPV','FINAL_RECOMMENDATION'] else '#A8B7C8')
        ws.set_column('A:A',3)
        ws.set_column('B:B',30,body)
        ws.set_column('C:F',19,body)
        ws.set_column('G:Z',22,body)
        ws.write('B2',caption,title)
        ws.set_row(1,28)
        ws.set_landscape()
        ws.set_paper(9)
        ws.fit_to_pages(1,0)
        ws.set_margins(.3,.3,.4,.4)
        ws.set_footer('&CFE401   |   &P / &N')
        ws.repeat_rows(4,4)
        ws.freeze_panes(5,2)
        ws.set_zoom(90)
    def write_note(name,text,row=2):
        ws=sheets[name]
        ws.merge_range(row,1,row,9,text,note)
        ws.set_row(row,32)
    def table(name,headers,rows,start=4,widths=None):
        ws=sheets[name]
        rows=list(rows)
        if not rows:
            rows=[['Eksik veri; hesaplama yapılmadı']+[None]*(len(headers)-1)]
        clean=[]
        for row in rows:
            clean.append([None if value is None or (isinstance(value,float) and not math.isfinite(value)) else value for value in row])
        for i,h in enumerate(headers):
            ws.write(start,1+i,h,header)
        ws.set_row(start,34)
        for r,row in enumerate(clean,start+1):
            for c,value in enumerate(row,1):
                fmt=number if isinstance(value,(float,int)) and not isinstance(value,bool) else body
                if isinstance(value,str) and value.startswith(('https://','http://')):
                    ws.write_url(r,c,value,body,'Kaynağı aç')
                elif isinstance(value,str) and value=='VERIFIED':
                    ws.write(r,c,'DOĞRULANDI',verified)
                elif isinstance(value,str) and value in ['MISSING','NOT_ESTIMABLE','UNVERIFIED']:
                    ws.write(r,c,{'MISSING':'EKSİK','NOT_ESTIMABLE':'HESAPLANAMAZ','UNVERIFIED':'DOĞRULANMADI'}[value],missing_format)
                elif value=='ASSUMED':
                    ws.write(r,c,'VARSAYIM',input_number)
                elif value=='ESTIMATED':
                    ws.write(r,c,'TAHMİN',estimated)
                else:
                    ws.write(r,c,value,fmt)
        ws.add_table(start,1,start+len(clean),len(headers),{'name':name.replace('_','')+'Table','style':'Table Style Medium 2','columns':[{'header':h,'header_format':header} for h in headers]})
        if widths:
            for col,width in widths.items():
                ws.set_column(col,col,width,body)
        return len(clean)
    # One authoritative editable assumption area. Existing numbers remain labelled hypothetical.
    drivers=[('daily_tonnes','Günlük kapasite','ton/gün'),('operating_days','Çalışma günü','gün/yıl'),('jar_kg','Kavanoz net ürün','kg'),('horizon_years','Planlama süresi','yıl'),('base_price_year','Reel fiyat yılı','yıl'),('selling_price_try_per_kg','Net satış fiyatı','TL/kg'),('utilization','Planlanan kapasite kullanımı','oran'),('demand_kg','Yıllık müşteri talebi','kg/yıl'),('packaging_try_per_jar','Kavanoz, kapak, etiket, koli','TL/kavanoz'),('processing_try_per_kg','Diğer değişken işleme','TL/kg ürün'),('waste_try_per_kg','Atık ve fire yönetimi','TL/kg ürün'),('real_discount_rate','Reel iskonto oranı','oran'),('tax_rate','Vergi oranı varsayımı','oran'),('working_capital_try','Başlangıç işletme sermayesi','TL'),('depreciable_fraction','Amortismana tabi CAPEX payı','oran'),('depreciation_years','Amortisman süresi','yıl'),('salvage_fraction','Terminal varlık satış payı','oran'),('replacement_capex_fraction','Yenileme CAPEX payı','oran')]
    ws=sheets['ASSUMPTIONS']
    write_note('ASSUMPTIONS','Sarı hücreler düzenlenebilir varsayımdır. Eksik girdiler boş kalır. Reel 2026 TL ve reel iskonto birlikte kullanılır. Optimizasyon için JSON/CSV girdilerini de güncelleyip Python’u yeniden çalıştırın.')
    a={}
    for c,h in enumerate(['Varsayım','Değer','Birim','Durum','Kaynak / açıklama'],1):
        ws.write(4,c,h,header)
    for r,(key,label,unit) in enumerate(drivers,5):
        a[key]=f"ASSUMPTIONS!$C${r+1}"
        ws.write(r,1,label,body)
        ws.write(r,2,config[key],input_percent if unit=='oran' else input_number)
        ws.write(r,3,unit,body)
        ws.write(r,4,'EKSİK' if config[key] is None else 'VARSAYIM',missing_format if config[key] is None else body)
        ws.write(r,5,'Kullanıcı planı' if key in ['daily_tonnes','operating_days','jar_kg','horizon_years'] else 'Özgün dosya / planlama varsayımı; gerçek teklif değil',note)
    ws.set_column('B:B',36)
    ws.set_column('F:F',60)
    ws.data_validation('C12',{'validate':'decimal','criteria':'between','minimum':0,'maximum':1})
    ws.data_validation('C9',{'validate':'integer','criteria':'between','minimum':1,'maximum':config['horizon_years']})
    ws.data_validation('C18',{'validate':'decimal','criteria':'between','minimum':0,'maximum':1})
    site_row={}
    start=27
    headers=['Aday OSB','İşgücü TL/yıl','İdare TL/yıl','Sabit genel gider TL/yıl','Enerji ve su TL/kg','Giden lojistik TL/kg','Bakım TL/yıl','CAPEX TL','Durum']
    for c,h in enumerate(headers,1):
        ws.write(start,c,h,header)
    ws.set_row(start,42)
    for i,site in enumerate(sites):
        r=start+i+1
        site_row[site['site']]=r+1
        ws.write(r,1,site['label_tr'],body)
        for c,k in enumerate(['labor_try','administration_try','fixed_overhead_try','utilities_try_per_kg','outbound_try_per_kg','maintenance_try','capex_try'],2):
            ws.write(r,c,site[k],input_number)
        ws.write(r,9,'VARSAYIM; teklif gerekli',body)
    # Material recipe maintains the existing gross ratios; unmeasured stage losses remain blank.
    ws=sheets['RECIPE_MATERIAL_BALANCE']
    write_note('RECIPE_MATERIAL_BALANCE','Brüt reçete özgün dosyadan alınan varsayımdır. Temizlik/közleme kayıpları ve sezon günleri pilot çalışma ile girilmelidir. Buharlaşma, kalan girdi ile nihai ürün farkıdır.')
    headers=['Girdi','Brüt kg/kg ürün','Temizlik kaybı','Közleme kaybı','Sezon alım günü','Yıllık brüt ton','Temizlik sonrası ton','Közleme sonrası ton','Sezon ton/gün','Örnek TL/kg','Durum']
    for c,h in enumerate(headers,1):
        ws.write(4,c,h,header)
    produced=f"{a['daily_tonnes']}*1000*{a['operating_days']}*{a['utilization']}"
    for i,r in enumerate(recipe,5):
        ex=i+1
        ws.write(i,1,r['label_tr'],body)
        ws.write(i,2,r['gross_kg_per_finished_kg'],input_ratio)
        ws.write(i,3,r['cleaning_loss'],input_percent)
        ws.write(i,4,r['roasting_loss'],input_percent)
        ws.write(i,5,r['season_intake_days'],input_number)
        ws.write_formula(i,6,f'={produced}*C{ex}/1000',link_number,config['daily_tonnes']*config['operating_days']*config['utilization']*r['gross_kg_per_finished_kg'])
        ws.write_formula(i,7,f'=IF(ISNUMBER(D{ex}),G{ex}*(1-D{ex}),"Eksik")',number,'Eksik')
        ws.write_formula(i,8,f'=IF(AND(ISNUMBER(H{ex}),ISNUMBER(E{ex})),H{ex}*(1-E{ex}),"Eksik")',number,'Eksik')
        ws.write_formula(i,9,f'=IF(AND(ISNUMBER(F{ex}),F{ex}>0),G{ex}/F{ex},"Eksik")',number,'Eksik')
        ws.write(i,10,r['price_try_per_kg'],input_number)
        ws.write(i,11,'VARSAYIM',body)
    ws.data_validation('D6:E13',{'validate':'decimal','criteria':'between','minimum':0,'maximum':.999})
    ws.data_validation('F6:F13',{'validate':'decimal','criteria':'between','minimum':1,'maximum':365})
    ws.write('B16','Yıllık nihai ürün (ton)',body)
    ws.write_formula('C16',f'={produced}/1000',link_number,2500)
    ws.write('B17','Toplam brüt girdi (ton)',body)
    ws.write_formula('C17','=SUM(G6:G13)',number,6282.5)
    ws.write('B18','Temizlik / közleme kaybı (ton)',body)
    ws.write_formula('C18','=IF(COUNT(I6:I13)=8,C17-SUM(I6:I13),"Eksik")',number,'Eksik')
    ws.write('B19','Buharlaşma gereksinimi (ton)',body)
    ws.write_formula('C19','=IF(COUNT(I6:I13)=8,IF(SUM(I6:I13)>=C16,SUM(I6:I13)-C16,"Geçersiz reçete"),"Eksik")',number,'Eksik')
    ws.write('B20','Kütle dengesi farkı (ton)',body)
    ws.write_formula('C20','=IF(AND(ISNUMBER(C18),ISNUMBER(C19)),C17-C16-C18-C19,"Eksik")',number,'Eksik')
    ws.write('B21','Kavanoz gereksinimi (adet)',body)
    ws.write_formula('C21',f'=ROUNDUP(C16*1000/{a["jar_kg"]},0)',number,5000000)
    # Landed ingredient unit costs are the only inbound cost feed to finance.
    headers=['Aday OSB','Girdi','Brüt ton/yıl','Tüm teslim maliyeti TL/brüt ton','Yıllık maliyet TL','Durum']
    ws=sheets['INGREDIENT_COSTS']
    write_note('INGREDIENT_COSTS','Teslim maliyeti satın alma, gelen navlun, elleçleme, taşıma kaybı ve depolamayı kapsar. Finans modeline gelen navlun tekrar eklenmez. Miktar/fiyat değişince tahsis için Python optimizasyonunu yeniden çalıştırın.')
    for c,h in enumerate(headers,1):
        ws.write(4,c,h,header)
    ingredient_ranges={}
    for si,site in enumerate(sites):
        first=6+si*8
        ingredient_ranges[site['site']]=(first,first+7)
        for ri,ingredient in enumerate(recipe):
            r=first+ri
            ws.write(r-1,1,site['label_tr'],body)
            ws.write(r-1,2,ingredient['label_tr'],body)
            ws.write_formula(r-1,3,f'=RECIPE_MATERIAL_BALANCE!G{6+ri}',link_number,2500*ingredient['gross_kg_per_finished_kg'])
            ws.write_blank(r-1,4,None,input_number)
            ws.write_formula(r-1,5,f'=IF(ISNUMBER(E{r}),D{r}*E{r},"Eksik")',number,'Eksik')
            ws.write(r-1,6,'EKSİK; teklif ve optimizasyon gerekli',missing_format)
    ws.data_validation('E6:E29',{'validate':'decimal','criteria':'>=','value':0})
    # Operating schedule mirrors finance.appraise: depreciation, tax-loss carry and terminal book value.
    ws=sheets['OPERATING_COSTS']
    write_note('OPERATING_COSTS','Sabit reel yıllık girdiler. Üretilen fakat satılamayan ürüne gelir yazılmaz; üretim maliyetleri korunur. Vergi zararları sonraki yıla taşınır. Yenileme yatırımı ertesi yıl amortismana girer.')
    blocks={}
    fields=['Üretilen kg','Satılan kg','Satılamayan kg','Gelir TL','Teslim alınan girdiler TL','Ambalaj TL','İşleme ve atık TL','Enerji ve su TL','Giden dağıtım TL','Sabit giderler TL','Toplam işletme gideri TL','EBITDA TL','Amortisman TL','EBIT TL','Açılış vergi zararı TL','Kapanış vergi zararı TL','Vergi TL','Yenileme CAPEX TL','Terminal defter değeri TL','Terminal varlık satışı TL','Terminal satış vergisi TL','İşletme sermayesi geri dönüşü TL','Serbest nakit akışı TL','İskontolu nakit akışı TL']
    for si,site in enumerate(sites):
        sr=site_row[site['site']]
        first,last=ingredient_ranges[site['site']]
        top=5+si*29
        ws.write(top,1,site['label_tr'],header)
        blocks[site['site']]={label:top+3+i for i,label in enumerate(fields)}
        b=blocks[site['site']]
        ws.write(top+1,1,'Girdi durumu',body)
        gate=f'AND(COUNT(ASSUMPTIONS!C6:C23)=18,COUNT(ASSUMPTIONS!C{sr}:I{sr})=7,COUNT(INGREDIENT_COSTS!E{first}:E{last})=8,ASSUMPTIONS!C6>=0,ASSUMPTIONS!C7>0,ASSUMPTIONS!C8>0,ASSUMPTIONS!C9>=1,ASSUMPTIONS!C9<={config["horizon_years"]},ASSUMPTIONS!C12>=0,ASSUMPTIONS!C12<=1,ASSUMPTIONS!C18>=0,ASSUMPTIONS!C18<=1,ASSUMPTIONS!C20>=0,ASSUMPTIONS!C20<=1,ASSUMPTIONS!C21>0,ASSUMPTIONS!C22>=0,ASSUMPTIONS!C22<=1,MIN(ASSUMPTIONS!C6:C23)>=0,MIN(ASSUMPTIONS!C{sr}:I{sr})>=0,MIN(INGREDIENT_COSTS!E{first}:E{last})>=0)'
        ws.write_formula(top+1,2,f'=IF({gate},"VARSAYIM","Eksik / geçersiz")',body,'Eksik / geçersiz')
        gate_cell=f'$C${top+2}'
        for i,label in enumerate(fields):
            ws.write(top+2+i,1,label,body)
        for year in range(1,config['horizon_years']+1):
            col=2+year
            letter=xl_col_to_name(col)
            previous=xl_col_to_name(col-1)
            ws.write(top,col,year,header)
            def ref(label): return f'{letter}{b[label]}'
            capex=f'ASSUMPTIONS!$I${sr}'
            dep=f'({capex}*{a["depreciable_fraction"]}/{a["depreciation_years"]}*IF({year}<={a["depreciation_years"]},1,0)+{capex}*{a["replacement_capex_fraction"]}/{a["depreciation_years"]}*MIN({year}-1,{a["depreciation_years"]}))'
            formulas={
                'Üretilen kg':f'={produced}',
                'Satılan kg':f'=MIN({ref("Üretilen kg")},{a["demand_kg"]})',
                'Satılamayan kg':f'={ref("Üretilen kg")}-{ref("Satılan kg")}',
                'Gelir TL':f'={ref("Satılan kg")}*{a["selling_price_try_per_kg"]}',
                'Teslim alınan girdiler TL':f'=SUM(INGREDIENT_COSTS!F{first}:F{last})',
                'Ambalaj TL':f'={ref("Üretilen kg")}/{a["jar_kg"]}*{a["packaging_try_per_jar"]}',
                'İşleme ve atık TL':f'={ref("Üretilen kg")}*({a["processing_try_per_kg"]}+{a["waste_try_per_kg"]})',
                'Enerji ve su TL':f'={ref("Üretilen kg")}*ASSUMPTIONS!$F${sr}',
                'Giden dağıtım TL':f'={ref("Satılan kg")}*ASSUMPTIONS!$G${sr}',
                'Sabit giderler TL':f'=SUM(ASSUMPTIONS!$C${sr}:$E${sr})+ASSUMPTIONS!$H${sr}',
                'Toplam işletme gideri TL':f'=SUM({ref("Teslim alınan girdiler TL")}:{ref("Sabit giderler TL")})',
                'EBITDA TL':f'={ref("Gelir TL")}-{ref("Toplam işletme gideri TL")}',
                'Amortisman TL':'='+dep,
                'EBIT TL':f'={ref("EBITDA TL")}-{ref("Amortisman TL")}',
                'Açılış vergi zararı TL':'=0' if year==1 else f'={previous}{b["Kapanış vergi zararı TL"]}',
                'Kapanış vergi zararı TL':f'=MAX({ref("Açılış vergi zararı TL")}-{ref("EBIT TL")},0)',
                'Vergi TL':f'=MAX({ref("EBIT TL")}-{ref("Açılış vergi zararı TL")},0)*{a["tax_rate"]}',
                'Yenileme CAPEX TL':f'=IF({year}<{a["horizon_years"]},{capex}*{a["replacement_capex_fraction"]},0)',
                'Terminal defter değeri TL':f'={capex}+SUM($D${b["Yenileme CAPEX TL"]}:{ref("Yenileme CAPEX TL")})-SUM($D${b["Amortisman TL"]}:{ref("Amortisman TL")})',
                'Terminal varlık satışı TL':f'=IF({year}={a["horizon_years"]},{capex}*{a["salvage_fraction"]},0)',
                'Terminal satış vergisi TL':f'=IF({year}={a["horizon_years"]},MAX({ref("Terminal varlık satışı TL")}-{ref("Terminal defter değeri TL")},0)*{a["tax_rate"]},0)',
                'İşletme sermayesi geri dönüşü TL':f'=IF({year}={a["horizon_years"]},{a["working_capital_try"]},0)',
                'Serbest nakit akışı TL':f'={ref("EBITDA TL")}-{ref("Vergi TL")}-{ref("Yenileme CAPEX TL")}+{ref("Terminal varlık satışı TL")}-{ref("Terminal satış vergisi TL")}+{ref("İşletme sermayesi geri dönüşü TL")}',
                'İskontolu nakit akışı TL':f'={ref("Serbest nakit akışı TL")}/(1+{a["real_discount_rate"]})^{year}',
            }
            for label,formula in formulas.items():
                ws.write_formula(b[label]-1,col,f'=IF({gate_cell}="VARSAYIM",IF({year}<={a["horizon_years"]},{formula[1:]},0),"Eksik")',number,'Eksik')
    # One investment summary uses cash-flow schedule; initial outlay at t=0.
    ws=sheets['PROFITABILITY_NPV']
    write_note('PROFITABILITY_NPV','Sonuçlar düzenlenebilir varsayımların hesabıdır; gerçek tekliflerle doğrulanmış yatırım önerisi değildir. IRR tek negatif başlangıç ve pozitif sonraki akışlarda gösterilir. Başabaş göstergeleri EBITDA düzeyindedir.')
    headers=['Aday OSB','Başlangıç nakit çıkışı TL','NPV TL','IRR','EBITDA TL/yıl','Başabaş satış fiyatı TL/kg','Başabaş hacim kg/yıl','Durum']
    for c,h in enumerate(headers,1): ws.write(4,c,h,header)
    for i,site in enumerate(sites,5):
        sr=site_row[site['site']]
        b=blocks[site['site']]
        cashrow=12+i-5
        fcfrow=b['Serbest nakit akışı TL']
        gate=f'ISNUMBER(OPERATING_COSTS!D{fcfrow})'
        ws.write(i,1,site['label_tr'],body)
        ws.write_formula(i,2,f'=IF({gate},-ASSUMPTIONS!I{sr}-{a["working_capital_try"]},"Eksik")',link_number,'Eksik')
        ws.write_formula(i,3,f'=IF({gate},C{i+1}+SUM(OPERATING_COSTS!D{b["İskontolu nakit akışı TL"]}:M{b["İskontolu nakit akışı TL"]}),"Eksik")',number,'Eksik')
        ws.write_formula(i,4,f'=IF({gate},IF(AND(C{i+1}<0,MIN(OPERATING_COSTS!D{fcfrow}:M{fcfrow})>=0,MAX(OPERATING_COSTS!D{fcfrow}:M{fcfrow})>0),IRR(C{cashrow}:M{cashrow}),"Tanımsız"),"Eksik")',percent,'Eksik')
        ws.write_formula(i,5,f'=IF({gate},OPERATING_COSTS!D{b["EBITDA TL"]},"Eksik")',link_number,'Eksik')
        ws.write_formula(i,6,f'=IF({gate},IF(OPERATING_COSTS!D{b["Satılan kg"]}>0,OPERATING_COSTS!D{b["Toplam işletme gideri TL"]}/OPERATING_COSTS!D{b["Satılan kg"]},"Tanımsız"),"Eksik")',number,'Eksik')
        contribution=f'{a["selling_price_try_per_kg"]}-ASSUMPTIONS!G{sr}-(OPERATING_COSTS!D{b["Toplam işletme gideri TL"]}-OPERATING_COSTS!D{b["Sabit giderler TL"]}-OPERATING_COSTS!D{b["Giden dağıtım TL"]})/OPERATING_COSTS!D{b["Üretilen kg"]}'
        ws.write_formula(i,7,f'=IF({gate},IF(OPERATING_COSTS!D{b["Üretilen kg"]}>0,IF({contribution}>0,OPERATING_COSTS!D{b["Sabit giderler TL"]}/({contribution}),"Tanımsız"),"Tanımsız"),"Eksik")',number,'Eksik')
        ws.write_formula(i,8,f'=IF({gate},"VARSAYIM","HESAPLANAMAZ")',body,'HESAPLANAMAZ')
        ws.write(cashrow-1,1,site['label_tr']+' nakit akışı',body)
        ws.write_formula(cashrow-1,2,f'=C{i+1}',link_number,'Eksik')
        for year in range(1,11):
            col=2+year
            letter=xl_col_to_name(col)
            ws.write_formula(cashrow-1,col,f'=OPERATING_COSTS!{letter}{fcfrow}',link_number,'Eksik')
    ws.set_column('B:B',58,body)
    ws.write('B11','IRR için yıl 0–10 nakit akışları',body)
    # Factual observation tables and chart distinguish levels and classes.
    history=read_csv('data/processed/historical_observations.csv').fillna('')
    table('HISTORICAL_PRODUCTION',['Yıl','İl','İlçe','Ürün sınıfı','Ölçüm','Değer','Birim','Coğrafi düzey','Durum','Kaynak','Not'],[[int(r.year),r.province,r.district,{'TOMATO_PROCESSING':'Salçalık domates','PEPPER_PROCESSING':'Salçalık biber; kapya eşlenmedi','EGGPLANT':'Patlıcan'}.get(r.product_code,r.product_code),{'production':'Üretim','area':'Alan'}.get(r.metric,r.metric),r.value,r.unit,'İl toplamı',r.data_status,r.source_url,'İlçe arzı değildir; kaynak yuvarlaması korunmuştur'] for r in history.itertuples()])
    write_note('HISTORICAL_PRODUCTION','2019–2023 TEPGE serisi il toplamı ve yuvarlanmış değerlerdir. 2024 Bakanlık rehberleri ayrı kaynak/vintajdır. İlçe serisi veya sözleşmeli arz yerine kullanılamaz.')
    chartdata=history[(history.metric=='production')&(history.product_code=='TOMATO_PROCESSING')].pivot(index='year',columns='province',values='value').sort_index()
    table('PRODUCT_TRENDS',['Yıl','Bursa ton','Manisa ton','Balıkesir ton'],[[int(y),row.get('Bursa'),row.get('Manisa'),row.get('Balıkesir')] for y,row in chartdata.iterrows()])
    write_note('PRODUCT_TRENDS','Salçalık domates il toplamları. 2019–2023 bin ton yuvarlamasından dönüştürüldü; 2024 yeni kaynak/vintaj. Artış satın alınabilir arz veya tahmin değildir.')
    chart=wb.add_chart({'type':'line'})
    for i,label in enumerate(['Bursa','Manisa','Balıkesir'],2):
        chart.add_series({'name':label,'categories':['PRODUCT_TRENDS',5,1,10,1],'values':['PRODUCT_TRENDS',5,i,10,i],'line':{'color':[TEAL,NAVY,'#859DB8'][i-2],'width':2.25}})
    chart.set_title({'name':'Salçalık domates üretimi (il toplamı)'})
    chart.set_y_axis({'name':'ton','num_format':'#,##0'})
    chart.set_legend({'position':'bottom'})
    chart.set_style(13)
    sheets['PRODUCT_TRENDS'].insert_chart('G5',chart,{'x_scale':1.25,'y_scale':1.15})
    sources=read_csv('sources.csv').fillna('')
    table('DATA_SOURCES',['Kaynak kimliği','Kurum','Kaynak bağlantısı','Erişim tarihi','Yerel kaynak dosyası','Kullanım / eksik'],[[r.source_id,r.institution,r.url,r.access_date,r.raw_filename,'Resmî kaynak / sınıflandırma, dönem ve düzey kontrolü; ayrıntı sources.csv'] for r in sources.itertuples()],widths={2:38,5:28,6:56})
    table('DATA_QUALITY',['Kontrol','Sonuç','Açıklama'],[['Doğrulanmış gözlemler',quality['verified_count'],'Tamamı il düzeyinde'],['Doğrulanmış ilçe gözlemleri',quality['district_verified_count'],'İlçe regresyonu durduruldu'],['Eksik ilçe ölçümü',quality['missing_district_records'],'11 ilçe × 11 yıl × 6 ürün × 4 ölçüm'],['Yinelenen gözlem',quality['duplicate_rows'],'Çakışmalar otomatik birleştirilmez'],['Olası aykırı değer',len(quality['issues']),'İşaretlendi; silinmedi'],['Resmî deflatör','MISSING','Reel tarihsel fiyatlar hesaplanmadı'],['Resmî ilçe ve ürün kodları','MISSING','Proje kodları resmî kod değildir'],['Yayımlanma / erişilebilirlik tarihleri',38,'Dönemsel tahminlerde veri erişim tarihi zorunludur']],widths={1:38,3:67})
    table('REGRESSION_RESULTS',['Ürün','Model','Katsayı','Güven aralığı','Durum'],[['İlçe üretimi ve reel fiyat','OLS / panel',None,None,'NOT_ESTIMABLE']])
    write_note('REGRESSION_RESULTS','İlçe paneli ve erişilebilirlik tarihleri eksik. Katsayı, p-değeri, düzeltilmiş R² ve tanısal sonuç üretilmedi.')
    validation=read_csv('data/processed/model_validation.csv').fillna('')
    table('MODEL_VALIDATION',['Ürün kodu','Hedef','Model','Gözlem','Değerlendirme satırı','MAE','RMSE','WAPE','R²','Durum'],[[r.product_code,'Üretim' if r.metric=='production' else 'Reel çiftlik çıkış fiyatı',r.model,r.observations,r.evaluation_rows,r.mae,r.rmse,r.wape,r.r2,r.status] for r in validation.itertuples()])
    write_note('MODEL_VALIDATION','2015–2022 eğitim, 2023–2025 dönemsel değerlendirme ve uygun yıllarda genişleyen pencere. Başarılı sonuç olmadığından model üstünlüğü iddiası yok.')
    forecasts=read_csv('data/processed/forecasts.csv').fillna('')
    table('FORECASTS_2026_2030',['İl','İlçe','Ürün kodu','Hedef','Yıl','Baz','İyimser','Kötümser','Alt tahmin sınırı','Üst tahmin sınırı','Durum'],[[r.province,r.district,r.product_code,'Üretim' if r.metric=='production' else 'Reel fiyat',r.year,None,None,None,None,None,r.status] for r in forecasts.itertuples()])
    write_note('FORECASTS_2026_2030','Model çıktıları ve çok yıllı belirsizlik aralıkları veri olmadan doldurulmadı. İyimser/kötümser senaryo çarpanları da ayrıca kanıtlanmalı veya varsayım olarak tanımlanmalıdır.')
    geo=read_csv('config/geography.csv').fillna('')
    table('SUPPLIER_REGIONS',['İl','İlçe','İl kodu','Resmî ilçe kodu','Fabrikaya katılım oranı','Sözleşmeli miktar ton','Durum'],[[r.province,r.district,r.province_code,r.district_code,None,None,'MISSING'] for r in geo.itertuples()])
    distances=read_csv('data/processed/distance_matrix.csv').fillna('')
    table('DISTANCE_MATRIX',['Çıkış','Çıkış ili','Varış','Varış ilçe vekili','km','Mesafe niteliği','Durum','Kaynak'],[[r.origin,r.origin_province,r.destination,r.destination_district,r.road_km,'İlçe merkezi karayolu vekili',r.data_status,r.source_url] for r in distances.itertuples()])
    write_note('DISTANCE_MATRIX','33 gelen ve 12 giden rota. İstanbul: Fatih, Ankara: Çankaya, İzmir: Konak; ihracat: Bandırma ilçe merkezi. Aynı ilçe 0 km değeri OSB iç transferinin sıfır olduğu anlamına gelmez.')
    table('OPTIMAL_SUPPLY_FLOWS',['Aday OSB','Girdi','Tedarikçi','Ay','Brüt ton','Teslim ton','Durum'],[[s['label_tr'],'Tüm reçete',None,None,None,None,'NOT_ESTIMABLE'] for s in sites])
    write_note('OPTIMAL_SUPPLY_FLOWS','Gerçek teklifler, sezon, kalite, stok ve kamyon kapasitesi eksik. Varsayımsal eski LP sonuçları yalnız output/demo altında tutulur.')
    table('UTILITIES',['Aday OSB','Hizmet','Birim ihtiyaç','Tarife','Bağlantı kapasitesi','Durum'],[[s['label_tr'],service,None,None,None,'MISSING'] for s in sites for service in ['Elektrik','Isıl enerji / doğal gaz','Proses suyu','Atıksu']])
    write_note('UTILITIES','Altyapı varlığı ile kullanılabilir kapasite ayrıdır. Birim tüketim, gıda prosesine uygun su kalitesi ve bağlayıcı OSB tarifesi gereklidir.')
    ws=sheets['INVESTMENT_CAPEX']
    table('INVESTMENT_CAPEX',['Aday OSB','Örnek toplam CAPEX TL','Arazi','Bina','Proses ekipmanı','Yardımcı tesis','Durum'],[[s['label_tr'],s['capex_try'],None,None,None,None,'ASSUMED'] for s in sites])
    for i,s in enumerate(sites,5):
        ws.write_formula(i,2,f'=ASSUMPTIONS!I{site_row[s["site"]]}',link_number,s['capex_try'])
    write_note('INVESTMENT_CAPEX','Özgün toplamlar varsayımsaldır. Arazi ve ekipman ayrımı ile her kapasite için teklifler gerekir; yatırım bütçesi kısıtı uygulanmadı.')
    capacities=read_csv('data/processed/capacity_scenarios.csv').fillna('')
    table('CAPACITY_SCENARIOS',['Aday kodu','ton/gün','Teorik kg/yıl','Planlanan kg/yıl','Talep kg/yıl','Satılan kg/yıl','CAPEX TL','Durum'],[[r.site,r.daily_tonnes,r.annual_capacity_kg,r.planned_production_kg,None,None,r.capex_try,r.status] for r in capacities.itertuples()])
    ws=sheets['CAPACITY_SCENARIOS']
    for index,r in enumerate(capacities.itertuples(),5):
        ws.write_formula(index,3,f'=C{index+1}*1000*{a["operating_days"]}',link_number,r.annual_capacity_kg)
        ws.write_formula(index,4,f'=D{index+1}*{a["utilization"]}',link_number,r.planned_production_kg)
        ws.write_formula(index,5,f'=IF(ISNUMBER({a["demand_kg"]}),{a["demand_kg"]},"Eksik")',link_number,'Eksik')
        ws.write_formula(index,6,f'=IF(ISNUMBER(F{index+1}),MIN(E{index+1},F{index+1}),"Eksik")',number,'Eksik')
    write_note('CAPACITY_SCENARIOS','5, 10, 25 ve 50 ton/gün aynı talep varsayımında karşılaştırılır. Kapasiteye özel yatırım, enerji ve yeterli arz olmadan NPV hesaplanmaz.')
    table('SENSITIVITY_MONTE_CARLO',['Risk girdisi','Dağılım','Alt çarpan','Tepe çarpan','Üst çarpan','Durum'],[[{'price':'Satış fiyatı','demand':'Talep','raw_cost':'Hammadde maliyeti','harvest':'Hasat / sözleşmeli arz','energy':'Enerji','freight':'Navlun'}[k],'Üçgensel; ampirik kalibrasyon yok',*values,'ASSUMED'] for k,values in config['monte_carlo_distributions'].items()])
    write_note('SENSITIVITY_MONTE_CARLO','Gerçek NPV girdileri eksik olduğundan risk sonucu hesaplanmadı. Ayrı örnekte sabit tohumlu 500 çekiliş; hasat açığı olan çekilişler fizibil değil, başarı gibi raporlanmaz.')
    matrix=read_csv('config/fe401.csv')
    table('FE401_DECISION_MATRIX',['Kriter','Ağırlık','Bursa kanıt puanı','Salihli kanıt puanı','Gönen kanıt puanı','Bursa uzman puanı','Salihli uzman puanı','Gönen uzman puanı','Kaynak / gerekçe','Durum'],[[r.label_tr,r.weight,None,None,None,None,None,None,None,'MISSING'] for r in matrix.itertuples()])
    sheets['FE401_DECISION_MATRIX'].set_column('C:C',18,percent)
    ws=sheets['FE401_DECISION_MATRIX']
    ws.set_column('B:B',35,body)
    for r in range(5,17):
        ws.write(r,2,matrix.iloc[r-5].weight,input_percent)
        for c in range(3,9):
            ws.write_blank(r,c,None,input_number)
    ws.data_validation('D6:I17',{'validate':'decimal','criteria':'between','minimum':1,'maximum':5})
    ws.data_validation('C6:C17',{'validate':'decimal','criteria':'between','minimum':0,'maximum':1})
    ws.write('B19','Ağırlık toplamı',body)
    ws.write_formula('C19','=SUM(C6:C17)',percent,1)
    for col in range(3,9):
        letter=xl_col_to_name(col)
        ws.write_formula(18,col,f'=IF(AND(COUNT({letter}6:{letter}17)=12,ABS($C$19-1)<0.000001),SUMPRODUCT($C$6:$C$17,{letter}6:{letter}17)/5*100,"Eksik")',number,'Eksik')
    alternatives=[('Hammadde öncelikli',[.25,.15,.08,.04,.12,.08,.08,.05,.05,.04,.04,.02]),('Pazar öncelikli',[.15,.25,.08,.04,.15,.06,.06,.05,.05,.04,.04,.03])]
    ws.write('B22','Alternatif ağırlıklar',header)
    for index,(label,weights) in enumerate(alternatives,23):
        ws.write(index,1,label,body)
        for c,weight in enumerate(weights,2): ws.write(index,c,weight,input_percent)
        for c,scorecol in enumerate(['D','E','F'],14):
            weighted='+'.join(f'{xl_col_to_name(2+i)}{index+1}*{scorecol}{6+i}' for i in range(12))
            ws.write_formula(index,c,f'=IF(AND(COUNT({scorecol}6:{scorecol}17)=12,ABS(SUM(C{index+1}:N{index+1})-1)<0.000001),({weighted})/5*100,"Eksik")',number,'Eksik')
    write_note('FE401_DECISION_MATRIX','12 faktör kullanıcı metninden alınmıştır; FE401 PDF bulunamadı. Eşit ağırlık varsayımı ile hammadde/pazar öncelikli alternatifler ayrıdır. Öznel puanlar kârlılık kanıtı değildir.')
    table('FINAL_RECOMMENDATION',['Aday OSB','Gıda kullanım izni','Su','Atıksu','Enerji','Arazi / afet','Sonuç'],[[s['label_tr'],'UNVERIFIED','UNVERIFIED','UNVERIFIED','UNVERIFIED','UNVERIFIED','Koşullu; yer sıralaması yapılamaz'] for s in sites])
    write_note('FINAL_RECOMMENDATION','Önce parsel uygunluğu doğrulanmalı. Uygun adaylar arasında gerçek sözleşmeler, talep ve yatırım teklifleriyle risk düzeltilmiş reel NPV en yüksek olan seçilir.')
    summary=[['Karar','Kesin yer önerisi üretilemedi'],['Doğrulanmış tarım verisi','38 il düzeyi gözlem; 2019–2024 kısmi kapsam'],['İlçe tarihi','2015–2025 serisi eksik; sıfırla doldurulmadı'],['Lojistik kanıt','45 KGM ilçe merkezi mesafesi; parsel/liman kapısı değil'],['Reçete','2,513 kg brüt girdi / kg ürün; pilot doğrulama gerekli'],['Regresyon ve tahmin','Veri yetersiz; sonuçlar hesaplanamaz'],['Finans','Talep, gerçek teslim maliyeti, giden navlun ve bakım eksik'],['Ön eleme','Üç adayın parsel uygunluğu doğrulanmadı'],['Sonraki veri adımı','MEDAS ilçe ihracı; tedarik, pazar ve OSB teklifleri']]
    table('EXECUTIVE_SUMMARY',['Başlık','Bulgu'],summary,widths={1:29,2:100})
    table('METHODOLOGY',['Konu','Uygulama'],[['Gözlem','Kaynak, yıl, ürün sınıfı, birim, durum ve raw dosyası korunur.'],['Eksik veri','Sıfır yapılmaz; şablon ve kalite raporunda izlenir.'],['Tahmin tarihi',config['forecast_date']+'; veri bu tarihte erişilebilir olmalıdır.'],['İstatistik','Naif, üç yıllık ortalama, trend, OLS, Ridge, panel ve uygun örneklemde RF.'],['Ölçekleme','Yalnız eğitim verisinde; rastgele bölme ve gerçekleşmiş verim yok.'],['Belirsizlik','Çok yıllı aralık için tahmin ufkuna özel doğrulama gerekir.'],['Optimizasyon','Mevsimsel stok, kullanılabilir teklif, katılım, kalite, kayıp; tam kamyon için MILP.'],['Finans','Reel fiyat / reel iskonto; gelen navlun teslim maliyetinde bir kez.'],['Excel düzenleme','Sarı varsayımlar anında finans formüllerini değiştirir; tahsis için JSON/CSV ve CLI yeniden çalışmalı.'],['Dosya koruma','Özgün Excel değiştirilmedi; raw/legacy kopyaları SHA-256 ile kontrol edilir.'],['Çalıştırma','python -m src.pipeline all; yeni kaynak indirmek için collect --online.'],['Örnek senaryo','python -m src.pipeline demo; sonuçlar yalnız output/demo dizininde.']],widths={1:30,2:112})
    # Dashboard: factual progress, material planning and decision status; no fake profitability ranking.
    ws=sheets['DASHBOARD']
    ws.freeze_panes(0,0)
    ws.set_column('B:B',35)
    ws.set_column('C:F',19)
    ws.set_column('G:J',18)
    ws.merge_range('B4:J5','Kesin yatırım yeri seçimi için kanıt yetersiz',wb.add_format({'font_name':'Arial','font_size':16,'bold':True,'font_color':NAVY,'bg_color':LIGHT,'valign':'vcenter'}))
    ws.merge_range('B7:D7','Doğrulanmış gözlemler',header)
    ws.merge_range('E7:G7','Karayolu mesafeleri',header)
    ws.merge_range('H7:J7','Eksik ilçe ölçümleri',header)
    card=wb.add_format({'font_name':'Arial','font_size':26,'bold':True,'font_color':TEAL,'bg_color':'#F7FAFC','align':'center','valign':'vcenter','num_format':'#,##0'})
    ws.merge_range('B8:D9',quality['verified_count'],card)
    ws.merge_range('E8:G9',45,card)
    ws.merge_range('H8:J9',quality['missing_district_records'],card)
    ws.write('B11','Planlanan nihai ürün kg/yıl',body)
    ws.write_formula('C11',f'={produced}',number,2500000)
    ws.write('B12','500 g kavanoz gereksinimi',body)
    ws.write_formula('C12','=RECIPE_MATERIAL_BALANCE!C21',number,5000000)
    ws.write('B14','Aday OSB',header)
    ws.write('E14','Parsel uygunluğu',header)
    ws.write('G14','NPV (reel TL)',header)
    for i,s in enumerate(sites,14):
        ws.merge_range(i,1,i,3,s['label_tr'],body)
        ws.write(i,4,'DOĞRULANMADI',missing_format)
        ws.write_formula(i,6,f'=PROFITABILITY_NPV!D{i-8}',number,'Eksik')
        ws.set_row(i,30)
    ws.merge_range('B19:J20','İl toplamları ilçe arzına dağıtılmadı. Eski fiyatlar ve reçete varsayımdır. Veri eksikliği regresyon, tahmin ve gerçek kârlılık hesaplarını durdurur.',note)
    ws.merge_range('B22:D22','DOĞRULANDI: resmî gözlem',verified)
    ws.merge_range('E22:G22','VARSAYIM: sarı giriş hücresi',input_number)
    ws.merge_range('H22:J22','EKSİK: sonuç üretilemez',missing_format)
    ws.print_area('B2:J22')
    for name in SHEETS:
        if name not in ['DASHBOARD']:
            sheets[name].conditional_format('B6:Z1000',{'type':'text','criteria':'containing','value':'Eksik','format':missing_format})
    wb.close()
    write_markdown_report(quality)
    write_json(dict(workbook=str(path),sheet_count=len(SHEETS),language='Turkish',formula_policy='Guarded linked assumptions; real results unavailable until missing inputs supplied; native Excel recalculation recommended',demo_results_embedded=False),'reports/workbook_manifest.json')
    return path

def write_markdown_report(quality):
    text=f'''# Lütenitsa fabrikası: istatistiksel fizibilite ve yer seçimi

Rapor tarihi: 10 Ekim 2026. Çalışma FE401 akademik tasarım senaryosudur.

## Sonuç

Bursa–Mustafakemalpaşa OSB, Manisa–Salihli OSB ve Balıkesir–Gönen Deri İhtisas ve Karma OSB arasında doğrulanmış bir kârlılık sıralaması yapılamaz. Üç adayın gıda üretimine uygun parsel, tahsis edilebilir su/atıksu/enerji kapasitesi ve arazi/afet uygunluğu **DOĞRULANMADI** durumundadır. Kurumsal altyapı açıklaması parsel uygunluk onayı yerine geçmez.

Koşullu seçim kuralı: zorunlu uygunluk koşullarını sağlayan adaylar arasında, eşdeğer üretim ve talep koşullarında, gerçek sözleşmeler ve yatırım teklifleriyle hesaplanan risk düzeltilmiş 10 yıllık reel NPV en yüksek olan yer seçilmelidir. Mevcut kanıt hiçbir adayı kesin olarak desteklemiyor.

## Doğrulanan veri ve kapsam

Toplam {quality['verified_count']} resmî tarım gözlemi alındı. TEPGE Domates 2024 Ek Tablo 11 (PDF sayfa 34, basılı sayfa 26), Bursa, Manisa ve Balıkesir için 2019–2023 salçalık domates alanı ve üretimini içeriyor. Bin dekar ve bin ton değerleri hektar/tona dönüştürüldü; kaynağın yuvarlaması korundu. 2025 yatırım rehberlerindeki 2024 salçalık domates ve salçalık biber üretimleri, Bursa/Balıkesir patlıcan üretimleri özgün PDF’den doğrulandı. Manisa’da seçilmiş tabloda patlıcan yoktur; yokluğu sıfır kabul edilmedi.

Salçalık biber sınıfı kapya ile eşlenmedi. Tüm bu sayılar **il toplamıdır**; ilçelere paylaştırılmadı ve satın alınabilir arz sayılmadı. Kaynak/vintaj değişikliği 2023–2024 büyüme yorumunda dikkate alınmalıdır. Resmî ürün kodları, ilçe kodları ve kesin yayımlanma tarihleri eksiktir.

KGM’nin kendi sayfasında yayımladığı ilçe mesafe dosyasından 33 gelen ve 12 giden güzergâh çıkarıldı. İstanbul için Fatih, Ankara için Çankaya, İzmir için Konak, Bandırma ihracatı için Bandırma ilçe merkezi vekili kullanıldı. Bunlar karayolu **ilçe merkezi vekilleridir**. OSB kapısı, müşterinin deposu, liman terminali, ağır vasıta kısıtı ve son kilometre mesafesi ayrıca doğrulanmalıdır. Aynı ilçe için 0 km OSB iç transferi değildir. Bölgesel dağıtıcı ve İzmir liman terminali adresleri henüz eksiktir.

## İstatistiksel sonuçlar

Hedeflenen 11 ilçe × 11 yıl × 6 ürün × 4 ölçüm = {quality['expected_district_records']} kayıt eksiktir. 2015–2025 ilçe üretim, alan, verim ve çiftlik çıkış fiyat serileri alınamadı. İlgili regresyon/tahminler **NOT_ESTIMABLE** olarak kaydedildi. Katsayı, p-değeri, R² ve 2026–2030 miktarları uydurulmadı.

Kod; önceki yıl, üç yıllık ortalama, trend, OLS, Ridge, panel sabit etkiler ve örneklem uygunsa Random Forest seçeneklerini içeriyor. 2023–2025 değerlendirmesi ve genişleyen pencere kullanılıyor. Lag verisinin 1 Ocak tahmin tarihinde erişilebilir olması gerekiyor. Gerçekleşmiş aynı yıl verimi, hedef üretim ve gelecek iklim verileri özellik olarak kullanılmıyor. Ölçekleme yalnız eğitimde yapılıyor. OLS en az 30 eğitim satırı, beş yıl ve üç ilçe; panel çıkarımı en az sekiz ilçe kümesi; RF en az 200 satır ve on ilçe gerektiriyor. Bunlar proje güvenlik eşikleri olup yeterliliği tek başına kanıtlamaz. Model naif yöntemi geçmezse açıkça işaretlenir.

Çok yıllı belirsizlik aralıkları için tahmin ufkuna özgü kalibrasyon eksiktir. İyimser/kötümser arz senaryoları ve satın alınabilir üretim payları da veri/varsayım bekliyor. Bu nedenle boş değerler başarı sonucu gibi gösterilmedi.

## Reçete, lojistik ve ekonomi

Özgün reçete 1 kg ürün başına 2,513 kg brüt girdi varsayar. 10 ton/gün ve 250 gün için 2.500.000 kg ürün, 6.282,5 ton brüt girdi ve 5.000.000 adet 500 g kavanoz planlanır. Brüt girdi ile nihai ürün farkı 3.782,5 tondur. Bu farkın ne kadarının ayıklama, közleme veya buharlaşma olduğu bilinmiyor; tamamı buharlaşma diye etiketlenmedi. Pilot proses verimi, mevsimsel alım, raf ömrü ve depolama kapasitesi gerekli.

Mevsimsel LP/MILP; brüt satın alma, taşıma kaybı sonrası teslim, aylık stok dengesi, ortak depo kapasitesi, tedarikçi katılımı, kalite uygunluğu ve isteğe bağlı tam kamyon sayısını içeriyor. Tarımsal üretim tedarikçi teklifi yerine kullanılmıyor. Rafine yağ, baharat, tuz ve sirke ayrı tedarik ürünleridir. Ambalaj finans modelinde ayrı tutuluyor.

Finans hesapları üretim, talep ve satışı ayrı izler. Üretilip satılmayan ürünün üretim maliyeti korunur. Gelen navlun tüm teslim maliyetinde bir kez sayılır. Sabit reel fiyatlar ve reel iskonto birlikte kullanılır. Gerçek TÜFE endeks seviyeleri eksik olduğu için tarihsel reel fiyat dönüşümü yapılmadı; 2026 tam yıl TÜFE ortalaması rapor tarihinde henüz tamamlanmamıştır. Tarım-ÜFE yerel tedarikçi fiyatı sayılmadı.

Kod EBITDA, EBIT, amortisman, zarar devri, vergi, yenileme yatırımı, terminal defter değeri/satış vergisi, işletme sermayesi geri dönüşü, serbest nakit, NPV, uygun işaretlerde IRR, geri ödeme ve başabaş fiyat/hacim hesabını içerir. Vergi kaybına anlık nakit iadesi varsayılmaz. Başabaş hacim üretimin satışa uyduğu EBITDA eşiğidir; yatırım getirisini ölçmez. 5/10/25/50 ton kapasite tabloları var; kapasiteye özgü teklifler olmadan NPV ölçeklenmedi.

Gerçek finans girdileri eksik olduğundan gerçek NPV veya Monte Carlo sonucu yoktur. `output/demo/` altındaki açıkça varsayımsal örnekler eski maliyetleri kullanır. Bunlar ana Excel'e, resmî tarihsel veriye veya yer önerisine aktarılmaz. Üçgensel şoklar ampirik kalibre edilmemiş, bağımsız uzman varsayımlarıdır. Hasat nedeniyle sözleşmeli arz yetmediğinde çekiliş fizibil değil olarak sayılır; NPV istatistikleri fizibil çekilişlere koşulludur. Bu koşullu puan yatırım sıralaması olarak kullanılmaz.

## Kanıt boşlukları ve veri edinme

1. TÜİK/MEDAS: 2015–2025, belirtilen 11 ilçe, salçalık domates, kapya sınıfı, patlıcan, kuru sarımsak, yağlık ayçiçeği ve ayrıştırılmış baharatlar. Resmî ürün/ilçe kodları ve veri yayımlanma tarihleriyle CSV/Excel dışa aktarım.
2. MGM/MEVBİS: istasyon eşlemesi, yetişme dönemi yağış/sıcaklık ve erişilebilirlik tarihleri; üyelik/izinli sipariş. Gelecek gerçekleşmiş iklim gözlemleri tahmin girdisi olamaz.
3. Tedarikçiler: gerçek fiyat teklifi, kalite, aylık miktar, katılım sınırı, sezon, kayıp ve rafine yağ/ambalaj teslim noktaları.
4. Nakliyeciler: OSB/depo/liman adresleri, son kilometre, araç kapasitesi, boş dönüş, yükleme, navlun ve ağır vasıta uygunluğu.
5. OSB yönetimleri: gıda faaliyeti/parsel onayı, su kalitesi ve tahsis, deşarj kapasitesi, elektrik/ısı tahsis ve tarifeleri, arazi fiyatı ve zemin/sel/yangın etütleri.
6. Müşteriler: İstanbul, Ankara, İzmir, bölgesel dağıtım ve ihracat için fiyat, ürün/ambalaj, yıllık talep ve pazar payları.
7. Yatırım/işletme teklifleri: 5/10/25/50 ton ekipman, arazi, bina, yardımcı tesis, bakım ve su/enerji tüketim normları.
8. FE401 PDF: 12 faktör kullanıcı talebinden alınmıştır; özgün PDF sayfa ve yöntem kontrolü yapılamadı. Puanlar eksik, ağırlıklar varsayım, kârlılık ayrı hesap.

## Kaynak bağlantıları

- [TEPGE Domates 2024](https://arastirma.tarimorman.gov.tr/tepge/Belgeler/PDF%20%C3%9Cr%C3%BCn%20Raporlar%C4%B1/2024%20%C3%9Cr%C3%BCn%20Raporlar%C4%B1/Domates%20%C3%9Cr%C3%BCn%20Raporu%202024-396%20TEPGE.pdf)
- [KGM Mesafeler](https://www.kgm.gov.tr/Sayfalar/KGM/SiteTr/Root/Uzakliklar.aspx)
- [Mustafakemalpaşa OSB](https://www.mkposb.org.tr/tarihce), [Salihli OSB](https://salihliosb.org.tr/hizmetler/), [Gönen OSB](https://www.gonenosb.org.tr/)

Tam kayıt, erişim tarihi ve özgün dosyalar `sources.csv`, `reports/collection_log.json` ve `data/raw/` altında tutulur. Orijinal çalışma dosyaları değiştirilmemiştir.
'''
    (ROOT/'reports/final_report_tr.md').write_text(text,encoding='utf-8')
