from __future__ import annotations
from typing import Any, Dict, List, Optional

VERSION = "v2.4.2"

class ImprovementAnalyzer:
    """第6章。第4章の確認候補を重複掲載するのではなく、改善検討の入口として整理する。"""
    POSITION_THRESHOLD = 5.0

    def _num(self,v):
        if v is None: return None
        if isinstance(v,(int,float)): return float(v)
        try: return float(str(v).replace(",","").replace("円","").replace("￥","").replace("¥","").replace("%",""))
        except (TypeError,ValueError): return None

    def _text(self,v): return "" if v is None else str(v).strip()

    def _customer_reason(self, value):
        text = self._text(value)
        replacements = {
            "IQR上限": "同じカテゴリの他のクーポンと比べて価格の差が大きい範囲",
            "IQR下限": "同じカテゴリの他のクーポンと比べて価格の差が大きい範囲",
            "IQR": "価格のばらつき",
            "統計的外れ値": "価格の差が大きい確認候補",
            "統計的な外れ値": "価格の差が大きい確認候補",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    def _price(self,v):
        n=self._num(v); return "—" if n is None else f"{n:,.0f}円"

    def _level(self,d): return self._text(d.get("reference_level") or d.get("reference_confidence") or "比較不可")

    def _base(self,title,category,reason,current,reference,detail,action,priority="確認候補"):
        return {"title":title,"category":category,"priority":priority,"reason":reason,
                "current_price":current,"reference_price":reference,
                "current_price_display":self._price(current),"reference_price_display":self._price(reference),
                "detail":detail,"action":action}

    def _overall(self,p):
        current=self._num(p.get("shop_median")); ref=self._num(p.get("market_reference_price"))
        if ref is None: ref=self._num(p.get("comparison_median"))
        if current is None or ref is None or ref<=0: return None
        ratio=self._num(p.get("ratio")) or current/ref*100
        if self._level(p) not in {"高","中"}:
            return self._base("市場参考価格の確認","全体価格","比較基準の参考度が低いため、価格差だけで判断しない確認が必要です。",current,ref,
                              "比較対象店舗数・有効価格データ数を確認します。","主なクーポンの内容・利用条件と合わせて確認します。","参考情報")
        if abs(ratio-100)<=self.POSITION_THRESHOLD: return None
        direction="低い" if ratio<100 else "高い"
        reason=f"自店舗中央値が市場参考価格より{abs(ratio-100):.1f}%{direction}位置です。"
        return self._base("店舗全体の価格確認","全体価格",reason,current,ref,"店舗全体の中央値を比較した確認候補です。","価格だけで判断せず、主なクーポンの内容・利用条件・対象者条件を確認します。")

    def _categories(self,cats):
        out=[]
        for cat,d in cats.items():
            cur=self._num(d.get("shop_median")); ref=self._num(d.get("market_reference_price"))
            if cur is None or ref is None or ref<=0: continue
            ratio=self._num(d.get("ratio")) or cur/ref*100
            if self._level(d) not in {"高","中"} or abs(ratio-100)<=self.POSITION_THRESHOLD: continue
            direction="低い" if ratio<100 else "高い"
            out.append(self._base("カテゴリ価格の確認",cat,f"自店舗中央値が市場参考価格より{abs(ratio-100):.1f}%{direction}位置です。",cur,ref,
                                   "カテゴリ別中央値を比較した確認候補です。","施術内容・所要時間・付帯メニュー・利用条件を確認します。"))
        return out

    def _quality(self,p):
        q=p.get("price_quality",{}); out=[]; seen=set()
        groups=[("outliers","価格のばらつきから見た確認候補"),("category_outliers","カテゴリ別の確認候補"),
                ("low_price_attention","低価格の確認候補"),("high_price_attention","高価格の確認候補")]
        for key,title in groups:
            for item in q.get(key,[]):
                name=self._text(item.get("coupon_name")); price=self._num(item.get("price")); cat=self._text(item.get("category")); unique=(name,price,cat,title)
                if unique in seen: continue
                seen.add(unique)
                out.append({"title":title,"category":cat or "クーポン","priority":"確認候補","coupon_name":name,
                            "reason":self._customer_reason(item.get("reason","価格上の確認候補です。")),"current_price":price,"reference_price":None,
                            "current_price_display":self._price(price),"reference_price_display":"—",
                            "detail":"第4章の価格確認候補を、改善を検討する際の入口として整理しています。",
                            "action":"価格だけで問題と判断せず、クーポン名・施術内容・利用条件・対象者条件を確認します。"})
        return out

    def analyze(self,primary_shop:Any,pricing_result:Optional[Dict[str,Any]]=None,category_analysis:Optional[Dict[str,Any]]=None):
        p=pricing_result if isinstance(pricing_result,dict) else {}; c=category_analysis if isinstance(category_analysis,dict) else {}
        proposals=[]
        overall=self._overall(p)
        if overall: proposals.append(overall)
        proposals.extend(self._categories(c)); proposals.extend(self._quality(p))
        overall_candidates=[x for x in proposals if x.get("category")=="全体価格" and not x.get("coupon_name")]
        coupon_candidates=[x for x in proposals if x.get("coupon_name")]
        category_candidates=[x for x in proposals if not x.get("coupon_name") and x.get("category")!="全体価格"][:6]
        final=overall_candidates+coupon_candidates+category_candidates
        return {"version":VERSION,"shop_name":getattr(primary_shop,"name","自店舗"),
                "chapter_title":"6. 自店舗への改善検討候補","proposal_count":len(final),"proposals":final,
                "summary":self._summary(final),
                "source_note":"第4章の価格確認候補と重複する内容は、改善を検討する入口として整理しています。",
                "limitations":["本章は価格分析・カテゴリ比較・価格品質分析から機械的に生成した改善検討候補です。",
                               "クーポン内容・利用条件・対象者条件を確認せず、変更を断定するものではありません。",
                               "市場参考価格の参考度が低い場合は、価格変更を強く提案しない設計です。"]}

    def _summary(self,ps):
        if not ps: return "今回の分析では、価格・カテゴリ・クーポン内容から特に改善を検討する候補は抽出されませんでした。"
        oc=sum(1 for p in ps if p.get("category")=="全体価格"); cc=sum(1 for p in ps if not p.get("coupon_name") and p.get("category")!="全体価格"); qc=sum(1 for p in ps if p.get("coupon_name"))
        parts=[]
        if oc: parts.append("店舗全体の価格に関する確認候補")
        if cc: parts.append(f"カテゴリ価格に関する検討候補{cc}件")
        if qc: parts.append(f"クーポン内容の確認候補{qc}件")
        return "今回の分析では、"+"、".join(parts)+"を整理しました。"


def analyze_improvements(primary_shop:Any,pricing_result=None,category_analysis=None):
    return ImprovementAnalyzer().analyze(primary_shop,pricing_result,category_analysis)
