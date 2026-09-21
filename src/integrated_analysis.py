from __future__ import annotations
from typing import Any, Dict, List, Optional

VERSION = "v2.4.1"

class IntegratedAnalyzer:
    """価格・カテゴリ・確認候補・自店舗HPB詳細レポートを統合する分析エンジン。"""

    def analyze(self, primary_shop: Any, pricing_result: Optional[Dict[str, Any]] = None,
                category_analysis: Optional[Dict[str, Any]] = None,
                review_candidates: Optional[Dict[str, Any]] = None,
                improvement_result: Optional[Dict[str, Any]] = None,
                quantitative_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pricing_result = pricing_result or {}
        category_analysis = category_analysis or {}
        review_candidates = review_candidates or {}
        improvement_result = improvement_result or {}
        quantitative_result = quantitative_result or {}
        shop_name = (getattr(primary_shop, "display_name", None)
                     or getattr(primary_shop, "name", None) or "不明店舗")
        result = {"version": VERSION, "shop_name": shop_name, "summary": "",
                  "overall": [], "price": [], "category": [], "quality": [],
                  "quantitative": [], "cross_analysis": [], "check_points": [],
                  "source_status": {"pricing": bool(pricing_result),
                                    "category": bool(category_analysis),
                                    "quality": bool(review_candidates),
                                    "improvement": bool(improvement_result),
                                    "quantitative": bool(quantitative_result)}}
        result["price"] = self._price(pricing_result)
        result["category"] = self._categories(category_analysis)
        result["quality"] = self._quality(review_candidates)
        result["quantitative"] = self._quantitative(quantitative_result)
        result["cross_analysis"] = self._cross(pricing_result, quantitative_result, improvement_result)
        result["overall"] = (result["price"] + result["cross_analysis"] + result["quantitative"])[:6]
        result["check_points"] = self._checks(result)[:12]
        result["summary"] = self._summary(result)
        return result

    def _price(self, p):
        current = self._num(p.get("shop_median"))
        ref = self._num(p.get("market_reference_price"))
        if ref is None: ref = self._num(p.get("comparison_median"))
        if current is None: return []
        if ref is None:
            return [{"title":"店舗全体の価格","fact":f"自店舗のクーポン価格の中央値は{current:,.0f}円です。",
                     "meaning":"比較対象店舗の価格を確認できないため、市場との価格差は確認できません。",
                     "check":"クーポンの内容・利用条件・対象者条件を合わせて確認します。"}]
        ratio = self._num(p.get("ratio")) or (current / ref * 100)
        if ratio < 95: meaning = f"自店舗の中央値は比較基準より{abs(ratio-100):.1f}%低い位置です。"
        elif ratio > 105: meaning = f"自店舗の中央値は比較基準より{abs(ratio-100):.1f}%高い位置です。"
        else: meaning = "自店舗の中央値は比較基準に近い位置です。"
        return [{"title":"店舗全体の価格",
                 "fact":f"自店舗のクーポン価格の中央値は{current:,.0f}円、市場参考価格は{ref:,.0f}円です。",
                 "meaning":meaning,
                 "check":"価格だけで判断せず、主なクーポンの施術内容・利用条件・対象者条件を確認します。",
                 "shop_median":current,"market_reference_price":ref,"ratio":ratio}]

    def _categories(self, cats):
        out=[]
        for cat,d in cats.items():
            cur=self._num(d.get("shop_median")); ref=self._num(d.get("market_reference_price"))
            if cur is None: continue
            ratio=self._num(d.get("ratio"))
            if ratio is None and ref: ratio=cur/ref*100
            if ref is None: meaning="比較対象店舗に同カテゴリの十分な価格データがありません。"
            elif ratio < 95: meaning="比較対象店舗より低い価格帯です。"
            elif ratio > 105: meaning="比較対象店舗より高い価格帯です。"
            else: meaning="比較対象店舗に近い価格帯です。"
            out.append({"category":cat,
                        "fact":f"{cat}は自店舗の中央値が{cur:,.0f}円、"+(f"市場参考価格が{ref:,.0f}円です。" if ref is not None else "市場参考価格は比較できません。"),
                        "meaning":meaning,
                        "check":"価格差だけで判断せず、施術内容・所要時間・付帯メニュー・利用条件を確認します。",
                        "ratio":ratio})
        out.sort(key=lambda x: abs((x.get("ratio") or 100)-100), reverse=True)
        return out

    def _quality(self, c):
        out=[]; seen=set()
        for title,key in [("価格のばらつきから見た確認候補","outliers"),("カテゴリ別の確認候補","category_outliers"),
                          ("低価格の確認候補","low_price_attention"),("高価格の確認候補","high_price_attention")]:
            for item in c.get(key,[]):
                k=(item.get("coupon_name"),item.get("price"),item.get("category"),title)
                if k in seen: continue
                seen.add(k)
                out.append({"title":title,"coupon_name":item.get("coupon_name"),"category":item.get("category"),
                            "price":item.get("price"),"reason":item.get("reason","価格上の確認候補"),
                            "check":"価格だけで問題と判断せず、クーポン名・施術内容・利用条件・対象者条件を確認します。"})
        return out

    def _quantitative(self, q):
        if not q: return []
        m=q.get("metrics",{}); s=m.get("summary",{}); t=m.get("traffic",{}); r=m.get("reviews",{}); l=m.get("listing",{}); c=m.get("coupon",{})
        out=[]
        pv=self._first(s,"top_pv",t,"top_pv"); pvb=self._first(s,"area_plan_pv",t,"area_plan_pv")
        cvr=self._first(s,"cvr",t,"cvr"); cvrb=self._first(s,"area_plan_cvr",t,"area_plan_cvr")
        acr=self._first(s,"acr",t,"acr"); acrb=self._first(s,"area_plan_acr",t,"area_plan_acr")
        if pv is not None and cvr is not None and acr is not None:
            base=[]
            if pvb is not None: base.append(f"PVは比較基準{int(pvb):,}")
            if cvrb is not None: base.append(f"CVRは比較基準{cvrb:.1f}%")
            if acrb is not None: base.append(f"ACRは比較基準{acrb:.1f}%")
            out.append({"title":"PV・CVR・ACR",
                        "fact":f"PV {int(pv):,}、CVR {cvr:.1f}%、ACR {acr:.1f}%です。",
                        "meaning":"PVは検索結果から店舗ページを開いた回数、CVRは店舗ページから「クーポン・メニュー」を見た割合、ACRはそこから予約完了ページまで進んだ割合です。"+(" " + "、".join(base) if base else ""),
                        "check":"3つの数字を個別に見るだけでなく、予約までの流れのどの段階を確認するかをクーポン内容や掲載内容と合わせて確認します。"})
        sales=s.get("sales_man_yen"); reservations=s.get("reservations")
        if sales is not None or reservations is not None:
            out.append({"title":"売上・予約","fact":f"前月売上は{sales:.1f}万円、予約数は{reservations:,}件です。" if isinstance(sales,(int,float)) and isinstance(reservations,int) else "前月の売上・予約数を確認できます。",
                        "meaning":"売上と予約数を組み合わせることで、1予約あたりの売上も確認できます。",
                        "check":"HPB上の客単価や新規・再来の予約構成と合わせて確認します。"})
        if r.get("count") is not None:
            diff = r["count"]-r["comparison_count"] if r.get("comparison_count") is not None else None
            out.append({"title":"口コミ・評価","fact":f"口コミは{r['count']}件です。"+(f"比較サロン平均との差は{diff:+d}件です。" if diff is not None else ""),
                        "meaning":"口コミ数・評価は店舗ページ上の掲載情報と合わせて確認できます。",
                        "check":"口コミ数だけで判断せず、評価・返信状況・予約数などと合わせて確認します。"})
        if l.get("styles") is not None or l.get("coupons") is not None:
            out.append({"title":"掲載量","fact":f"掲載スタイルは{l.get('styles','—')}件、クーポンは{l.get('coupons',c.get('coupon_count','—'))}件です。",
                        "meaning":"掲載量をPV・CVR・ACRと合わせて確認できます。",
                        "check":"数量だけで判断せず、実際の掲載内容と予約までの数字を合わせて確認します。"})
        if c.get("new_label_count") is not None and c.get("repeat_label_count") is not None and c.get("all_label_count") is not None:
            out.append({"title":"クーポン構成","fact":f"掲載クーポンは{c.get('coupon_count','—')}件。新規{c['new_label_count']}件、再来{c['repeat_label_count']}件、全員{c['all_label_count']}件です。",
                        "meaning":"クーポンの対象構成を予約数の新規・再来構成と合わせて確認できます。",
                        "check":"予約構成や実際のクーポン内容と合わせて確認します。"})
        return out

    def _cross(self,p,q,improvement):
        out=[]; m=q.get("metrics",{}); s=m.get("summary",{}); t=m.get("traffic",{})
        price=self._num(p.get("shop_median")); ref=self._num(p.get("market_reference_price")) or self._num(p.get("comparison_median"))
        pv=self._first(s,"top_pv",t,"top_pv"); cvr=self._first(s,"cvr",t,"cvr"); acr=self._first(s,"acr",t,"acr")
        if None not in (price,ref,pv,cvr,acr):
            out.append({"title":"価格とHPB上の行動データ","fact":f"自店舗のクーポン中央値は{price:,.0f}円、市場参考価格は{ref:,.0f}円。PVは{int(pv):,}、CVRは{cvr:.1f}%、ACRは{acr:.1f}%です。",
                        "meaning":"価格とHPB上のお客様の行動データを同じ店舗について確認できます。",
                        "check":"価格だけ、またはPV・CVR・ACRだけで原因を決めず、クーポン内容・掲載内容・予約状況を合わせて確認します。"})
        if improvement.get("proposals"):
            out.append({"title":"改善検討候補とのつながり","fact":f"価格分析から{len(improvement['proposals'])}件の改善検討候補が整理されています。",
                        "meaning":"候補は価格差や価格のばらつきを確認する入口として利用できます。",
                        "check":"候補をそのまま変更判断にせず、クーポン内容・利用条件・対象者条件を確認します。"})
        return out

    def _checks(self,r):
        out=[]; seen=set()
        for g in ("price","category","quality","quantitative","cross_analysis"):
            for x in r.get(g,[]):
                text=x.get("check","")
                if text and text not in seen:
                    seen.add(text); out.append({"priority":g,"text":text,"coupon_name":x.get("coupon_name")})
        return out

    def _summary(self,r):
        parts=[]
        if r.get("price"): parts.append("価格")
        if r.get("category"): parts.append("カテゴリ")
        if r.get("quality"): parts.append("確認候補")
        if r.get("quantitative"): parts.append("HPB詳細レポート")
        if r.get("cross_analysis"): parts.append("データの組み合わせ")
        return "総合分析に使用できるデータが不足しています。" if not parts else "自店舗の"+"・".join(parts)+"を組み合わせて、数字上の事実と確認ポイントを整理しました。"

    @staticmethod
    def _num(v):
        if v is None: return None
        try: return float(str(v).replace(",","").replace("円","").replace("%",""))
        except (TypeError,ValueError): return None

    @classmethod
    def _first(cls,a,k1,b,k2): return cls._num(a.get(k1)) if a.get(k1) is not None else cls._num(b.get(k2))


def analyze_integrated(primary_shop: Any, pricing_result=None, category_analysis=None,
                       review_candidates=None, improvement_result=None, quantitative_result=None):
    return IntegratedAnalyzer().analyze(primary_shop, pricing_result, category_analysis,
                                        review_candidates, improvement_result, quantitative_result)
