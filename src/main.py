from __future__ import annotations
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Optional

from scraper import HotPepperScraper
from pricing_analysis import PricingAnalyzer
from report_pdf import generate_pdf_report
from hpb_quantitative_analysis import HPBDetailReportParser, QuantitativeAnalyzer, OptionalAIAnalyzer
from improvement_analysis import ImprovementAnalyzer
from integrated_analysis import IntegratedAnalyzer

VERSION="v2.4.1"

def print_separator(): print("\n"+"="*70)

def get_valid_price(coupon:Any)->Optional[int]:
    p=getattr(coupon,"price",None)
    if p is None:return None
    if isinstance(p,str):
        p=p.replace(",","").replace("円","").replace("￥","").replace("¥","").strip()
        if not p:return None
        try:p=int(float(p))
        except ValueError:return None
    try:p=int(p)
    except (TypeError,ValueError):return None
    return p if p>0 else None

def normalize_category(analyzer,category):
    try:return analyzer._normalize_category(category)
    except Exception:
        parts=[]
        for p in str(category or "").split("+"):
            p=p.strip()
            if p and p not in parts:parts.append(p)
        parts=[p for p in parts if p!="その他"] or parts
        return " + ".join(parts)

def get_shop_prices(shop): return [p for c in getattr(shop,"coupons",[]) for p in [get_valid_price(c)] if p is not None]

def get_shop_summary(shop):
    prices=get_shop_prices(shop)
    return {"name":getattr(shop,"name","不明店舗"),"coupon_count":len(getattr(shop,"coupons",[])),"valid_price_count":len(prices),"average":round(sum(prices)/len(prices)) if prices else None,"median":float(median(prices)) if prices else None,"min":min(prices) if prices else None,"max":max(prices) if prices else None}

def get_category_shop_summary(analyzer,shop):
    result={}
    for c in getattr(shop,"coupons",[]):
        cat=normalize_category(analyzer,getattr(c,"category","")); p=get_valid_price(c)
        if not cat or p is None:continue
        result.setdefault(cat,{"prices":[],"coupon_count":0}); result[cat]["prices"].append(p); result[cat]["coupon_count"]+=1
    for cat,d in result.items():
        ps=d["prices"]; d["average"]=round(sum(ps)/len(ps)); d["median"]=float(median(ps)); d["min"]=min(ps); d["max"]=max(ps); del d["prices"]
    return result

def build_comparison_shop_rows(analyzer,shops):
    out=[]
    for shop in shops:
        s=get_shop_summary(shop); cats=get_category_shop_summary(analyzer,shop); out.append({**s,"category_count":len(cats),"categories":cats})
    return out

def build_category_rows(analyzer,primary,comparisons,analysis):
    maps=[get_category_shop_summary(analyzer,s) for s in comparisons]; out=[]
    for cat,d in analysis.items():
        stores=[]
        for shop,m in zip(comparisons,maps):
            x=m.get(cat)
            if x and x.get("median") is not None: stores.append({"shop_name":getattr(shop,"name","不明店舗"),"coupon_count":x["coupon_count"],"median":x["median"],"average":x["average"]})
        out.append({"category":cat,"primary_coupon_count":d.get("shop_coupon_count",0),"primary_average":d.get("shop_average"),"primary_median":d.get("shop_median"),"comparison_shop_count":d.get("comparison_shop_count",0),"comparison_coupon_count":d.get("comparison_coupon_count",0),"market_reference_price":d.get("market_reference_price"),"reference_price_min":d.get("reference_price_min"),"reference_price_max":d.get("reference_price_max"),"position":d.get("position","比較不可"),"reference_level":d.get("reference_level","比較不可"),"difference":d.get("difference"),"ratio":d.get("ratio"),"comparison_stores":stores})
    return out

def extract_review_candidates(pricing):
    q=pricing.get("price_quality",{}); return {"outliers":q.get("outliers",[]),"category_outliers":q.get("category_outliers",[]),"low_price_attention":q.get("low_price_attention",[]),"high_price_attention":q.get("high_price_attention",[])}

def main():
    print("="*70); print(f"ちゃぴおHPB Toolkit {VERSION}"); print("自店舗を主役にしたクーポン価格分析・市場参考価格・営業確認候補・自店舗定量分析・総合分析・PDFレポート"); print("="*70)
    scraper=HotPepperScraper(); analyzer=PricingAnalyzer()
    print("\n【1】分析対象となる自店舗URLを入力してください。"); primary_url=input("自店舗URL: ").strip()
    if not primary_url: print("\n自店舗URLが入力されていません。"); return
    print("\n【2】比較対象店舗URLを入力してください。"); print("複数入力できます。比較店舗の入力終了は空Enterです。\n")
    comparison_urls=[]
    while True:
        u=input("比較店舗URL: ").strip()
        if not u:break
        comparison_urls.append(u)
    print("\n【3】自店舗のHPB詳細レポートPDFを指定してください。")
    print("エクスプローラーからPDFファイルをこの画面へドラッグ＆ドロップできます。")
    print("PDFを使用しない場合は空Enterで進められます。\n")
    pdf_path=input("自店舗詳細レポートPDF: ").strip().strip('"')
    print_separator(); print("店舗データの取得を開始します。"); print("="*70)
    try: primary=scraper.scrape(primary_url)
    except Exception as e: print(f"自店舗の取得に失敗しました: {e}"); return
    if primary is None: print("自店舗データを取得できませんでした。"); return
    print(f"取得完了: {getattr(primary,'name','不明店舗')} / クーポン{len(getattr(primary,'coupons',[]))}件")
    comparisons=[]
    for i,u in enumerate(comparison_urls,1):
        print(f"\n[比較店舗 {i}/{len(comparison_urls)}] データ取得中...")
        try:
            shop=scraper.scrape(u)
            if shop is None: print("取得できなかったためスキップします。"); continue
            comparisons.append(shop); print(f"取得完了: {getattr(shop,'name','不明店舗')} / クーポン{len(getattr(shop,'coupons',[]))}件")
        except Exception as e: print(f"取得に失敗しました: {e}")
    print_separator(); print("自店舗を主対象として価格分析を実行します。"); print("="*70)
    try: pricing=analyzer.analyze_summary(primary,[primary]+comparisons)
    except Exception as e: print(f"全体価格分析でエラーが発生しました: {e}"); return
    try: cats=analyzer.analyze_category_summary(primary,{},[primary]+comparisons)
    except Exception as e: print(f"カテゴリ別価格分析でエラーが発生しました: {e}"); cats={}
    primary_summary=get_shop_summary(primary); comparison_rows=build_comparison_shop_rows(analyzer,comparisons); category_rows=build_category_rows(analyzer,primary,comparisons,cats); candidates=extract_review_candidates(pricing)
    print_separator(); print("【第6章】改善検討候補を整理しています。")
    try: improvement=ImprovementAnalyzer().analyze(primary,pricing,cats)
    except Exception as e: print(f"改善提案分析でエラーが発生しました: {e}"); improvement={"version":VERSION,"shop_name":getattr(primary,"name","自店舗"),"chapter_title":"6. 自店舗への改善検討候補","proposal_count":0,"proposals":[],"summary":"改善提案分析を実行できませんでした。","limitations":[]}
    quantitative=None
    if pdf_path:
        print_separator(); print("【第7章】自店舗HPB詳細レポートを解析中...")
        try:
            metrics=HPBDetailReportParser().parse(pdf_path); base=QuantitativeAnalyzer().analyze(metrics); ai=OptionalAIAnalyzer().analyze(metrics,base); quantitative={"source_file":metrics.get("source_file"),"page_count":metrics.get("page_count"),"metrics":metrics,"analysis":base,"ai_analysis":ai}; print(f"解析完了: {metrics.get('source_file','PDF')} / {metrics.get('page_count','—')}ページ"); print(base.get("summary",""))
        except Exception as e: print(f"HPB詳細レポートの解析に失敗しました: {e}"); print("PDFなしとして価格分析を続行します。")
    else: print_separator(); print("HPB詳細レポートPDFは指定されていません。")
    print_separator(); print("【v2.4.1 総合分析】")
    try: integrated=IntegratedAnalyzer().analyze(primary,pricing,cats,candidates,improvement,quantitative); print(integrated.get("summary","総合分析が完了しました。"))
    except Exception as e: print(f"総合分析でエラーが発生しました: {e}"); integrated={"version":VERSION,"shop_name":getattr(primary,"name","自店舗"),"summary":"総合分析を実行できませんでした。","overall":[],"price":[],"category":[],"quality":[],"quantitative":[],"cross_analysis":[],"check_points":[],"source_status":{}}
    report_data={"version":VERSION,"created_at":datetime.now(),"primary_shop":{"name":getattr(primary,"display_name",None) or getattr(primary,"name","不明店舗"),"url":primary_url,"summary":primary_summary,"pricing":pricing,"category_analysis":cats,"category_rows":category_rows,"review_candidates":candidates,"improvement":improvement,"quantitative":quantitative,"integrated":integrated},"comparison_shops":comparison_rows,"comparison_urls":comparison_urls,"integrated":integrated,"notes":["本レポートは自店舗を主対象として、比較対象店舗を市場・参考情報として扱います。","市場参考価格は比較店舗ごとの価格中央値を同じ重みで比較して算出しています。","市場参考価格は100円単位に統一して表示しています。","営業確認候補は機械的な統計・価格閾値による候補抽出であり、異常価格と断定するものではありません。","第6章は第4章の確認候補を再掲するのではなく、改善を検討するための候補として整理しています。","クーポンの内容・利用条件・対象者条件などは営業担当者による確認を前提とします。","数字だけから原因を断定せず、掲載内容・クーポン内容・予約状況などと合わせて確認します。"]}
    print_separator(); print("PDFレポートを生成しています...")
    try:
        out=Path("output"); out.mkdir(parents=True,exist_ok=True); path=out/f"HPB_自店舗分析レポート_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"; generate_pdf_report(report_data,path); print("\n"+"="*70); print("PDFレポートを生成しました。"); print(f"保存先: {path}"); print("="*70)
    except Exception as e: print("\nPDF生成でエラーが発生しました。"); print(f"エラー内容: {e}")

if __name__=="__main__": main()
