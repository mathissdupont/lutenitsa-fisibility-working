#!/usr/bin/env python3
"""Lutenitsa district sourcing optimisation. Scenario inputs ARE NOT supplier offers.
Run: python optimize_logistics.py --folder .
Requires: scipy (pip install scipy)
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import argparse
import csv
from scipy.optimize import linprog

def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def save_csv(path, names, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=names)
        w.writeheader()
        w.writerows(rows)

def main(folder: Path, rate: float, handling: float):
    if rate < 0 or handling < 0:
        raise ValueError("Navlun ve ellecleme negatif olamaz.")
    offers=read_rows(folder/"tedarik_senaryosu.csv")
    roads=read_rows(folder/"rota_mesafeleri.csv")
    needs=read_rows(folder/"talep.csv")
    origins=sorted({r["origin"] for r in offers})
    sites=sorted({r["site"] for r in roads})
    roads_dict={(r["origin"],r["site"]):float(r["road_km"]) for r in roads}
    by_crop=defaultdict(list)
    for r in offers:
        by_crop[r["ingredient"]].append(r)
    out=[]
    totals=[]
    for site in sites:
        total_purchase=total_freight=total_handling=total_ton_km=0.0
        for need in needs:
            crop=need["ingredient"]
            demand=float(need["ton_year"])
            items=by_crop[crop]
            if not items: raise ValueError("Tedarikci yok: "+crop)
            avail=sum(float(x["capacity_ton_year"]) for x in items)
            if avail+1e-7<demand:
                raise ValueError(f"{crop} toplami {avail} ton, gerekli {demand} ton; senaryo fizibil DEGIL")
            unit=[]
            for item in items:
                key=(item["origin"],site)
                if key not in roads_dict: raise ValueError(f"Mesafe eksik: {key}")
                unit.append(float(item["price_tl_per_ton"])+rate*roads_dict[key]+handling)
            result=linprog(unit,A_eq=[[1]*len(items)],b_eq=[demand],
                bounds=[(0.0,float(x["capacity_ton_year"])) for x in items],method="highs")
            if not result.success: raise RuntimeError(f"{site}/{crop}: {result.message}")
            for i,item in enumerate(items):
                volume=float(result.x[i])
                dist=roads_dict[(item["origin"],site)]
                buy=volume*float(item["price_tl_per_ton"])
                freight=volume*dist*rate
                handle=volume*handling
                total_purchase+=buy
                total_freight+=freight
                total_handling+=handle
                total_ton_km+=volume*dist
                out.append(dict(site=site,ingredient=crop,origin=item["origin"],
                    allocated_ton_year=round(volume,3),road_km=dist,
                    purchase_tl=round(buy,2),freight_tl=round(freight,2),
                    handling_tl=round(handle,2),total_tl=round(buy+freight+handle,2)))
        totals.append(dict(site=site,purchase_tl=round(total_purchase,2),
            freight_tl=round(total_freight,2),handling_tl=round(total_handling,2),
            total_tl=round(total_purchase+total_freight+total_handling,2),
            ton_km=round(total_ton_km,2)))
    save_csv(folder/"optimum_akis.csv",list(out[0].keys()),out)
    save_csv(folder/"sonuclar.csv",list(totals[0].keys()),totals)
    for x in sorted(totals,key=lambda r:r["total_tl"]):
        print(f"{x['site']:<28} TL {x['total_tl']:,.0f}  "
              f"(alis TL {x['purchase_tl']:,.0f}; "
              f"navlun TL {x['freight_tl']:,.0f}; yukleme TL {x['handling_tl']:,.0f})")
    print("\nONEMLI: Sonuclar senaryo varsayimlaridir; piyasa fiyatlari degildir.")
    print("Excel LOJ_AKIS!D6:D41 icindeki tahsisler otomatik olarak degismez.")
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--folder",type=Path,default=Path("."))
    parser.add_argument("--rate",type=float,default=4.0,help="TL / ton-km (scenario)")
    parser.add_argument("--handling",type=float,default=250.0,help="TL / ton (scenario)")
    a=parser.parse_args()
    main(a.folder,a.rate,a.handling)
