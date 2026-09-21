from __future__ import annotations

from typing import Any, Dict, List, Optional


VERSION = "v2.5.0"


class IntegratedAnalyzer:
    """
    v2.5.0 総合分析エンジン。

    価格・カテゴリ・営業確認候補・HPB詳細レポートを、
    「数字上の事実 → 分かること → 次に確認すること」
    の形で組み合わせる。

    重要:
    - 数字だけから原因を断定しない。
    - 比較対象店舗は市場・参考情報として扱う。
    - 自店舗のHPB詳細PDFだけを定量分析の対象にする。
    - 顧客向け文言では IQR / ファネル等の専門用語を使用しない。
    """

    def analyze(
        self,
        primary_shop: Any,
        pricing_result: Optional[Dict[str, Any]] = None,
        category_analysis: Optional[Dict[str, Any]] = None,
        review_candidates: Optional[Dict[str, Any]] = None,
        improvement_result: Optional[Dict[str, Any]] = None,
        quantitative_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        pricing_result = pricing_result or {}
        category_analysis = category_analysis or {}
        review_candidates = review_candidates or {}
        improvement_result = improvement_result or {}
        quantitative_result = quantitative_result or {}

        shop_name = (
            getattr(primary_shop, "display_name", None)
            or getattr(primary_shop, "name", None)
            or "不明店舗"
        )

        result: Dict[str, Any] = {
            "version": VERSION,
            "shop_name": shop_name,
            "summary": "",
            "overall": [],
            "price": [],
            "category": [],
            "quality": [],
            "quantitative": [],
            "cross_analysis": [],
            "check_points": [],
            "source_status": {
                "pricing": bool(pricing_result),
                "category": bool(category_analysis),
                "quality": bool(review_candidates),
                "improvement": bool(improvement_result),
                "quantitative": bool(quantitative_result),
            },
        }

        result["price"] = self._price(pricing_result)
        result["category"] = self._categories(category_analysis)
        result["quality"] = self._quality(review_candidates)
        result["quantitative"] = self._quantitative(quantitative_result)
        result["cross_analysis"] = self._cross(
            pricing_result,
            quantitative_result,
            improvement_result,
        )

        # 総合分析の中心にする情報。
        # 価格 → HPB行動 → 売上/予約 → 口コミ/掲載量 の順で、
        # 実際に読み手が店舗の状態を追いやすい順番にする。
        result["overall"] = (
            result["price"]
            + result["cross_analysis"]
            + result["quantitative"]
        )[:8]

        result["check_points"] = self._checks(result)[:10]
        result["summary"] = self._summary(result)

        return result

    # =========================================================
    # 価格
    # =========================================================

    def _price(self, pricing: Dict[str, Any]) -> List[Dict[str, Any]]:
        current = self._num(pricing.get("shop_median"))
        reference = self._num(
            pricing.get("market_reference_price")
        )

        if reference is None:
            reference = self._num(
                pricing.get("comparison_median")
            )

        if current is None:
            return []

        if reference is None:
            return [
                {
                    "section": "価格",
                    "title": "店舗全体の価格",
                    "fact": (
                        f"自店舗のクーポン価格の中央値は"
                        f"{current:,.0f}円です。"
                    ),
                    "meaning": (
                        "比較対象店舗から市場参考価格を確認できないため、"
                        "今回は市場との価格差は確認できません。"
                    ),
                    "check": (
                        "主なクーポンの施術内容・所要時間・利用条件・"
                        "対象者条件を確認します。"
                    ),
                }
            ]

        ratio = self._num(pricing.get("ratio"))
        if ratio is None and reference:
            ratio = current / reference * 100.0

        if ratio is None:
            meaning = "市場参考価格との比較データを確認できます。"
        elif ratio > 100:
            meaning = (
                f"自店舗の中央値は市場参考価格より"
                f"{ratio - 100:.1f}%高い位置です。"
            )
        elif ratio < 100:
            meaning = (
                f"自店舗の中央値は市場参考価格より"
                f"{100 - ratio:.1f}%低い位置です。"
            )
        else:
            meaning = "自店舗の中央値と市場参考価格は同じ水準です。"

        return [
            {
                "section": "価格",
                "title": "店舗全体の価格",
                "fact": (
                    f"自店舗のクーポン価格の中央値は"
                    f"{current:,.0f}円、市場参考価格は"
                    f"{reference:,.0f}円です。"
                ),
                "meaning": meaning,
                "check": (
                    "価格差だけで変更を決めず、主なクーポンの"
                    "施術内容・所要時間・利用条件・対象者条件を確認します。"
                ),
                "shop_median": current,
                "market_reference_price": reference,
                "ratio": ratio,
            }
        ]

    # =========================================================
    # カテゴリ
    # =========================================================

    def _categories(
        self,
        categories: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        out: List[Dict[str, Any]] = []

        for category, data in categories.items():
            current = self._num(data.get("shop_median"))
            reference = self._num(
                data.get("market_reference_price")
            )

            if current is None:
                continue

            ratio = self._num(data.get("ratio"))
            if ratio is None and reference:
                ratio = current / reference * 100.0

            if reference is None:
                meaning = (
                    "比較対象店舗に同じカテゴリの十分な価格データがなく、"
                    "市場参考価格との比較はできません。"
                )
            elif ratio is not None and ratio > 100:
                meaning = (
                    f"このカテゴリの中央値は市場参考価格より"
                    f"{ratio - 100:.1f}%高い位置です。"
                )
            elif ratio is not None and ratio < 100:
                meaning = (
                    f"このカテゴリの中央値は市場参考価格より"
                    f"{100 - ratio:.1f}%低い位置です。"
                )
            else:
                meaning = (
                    "このカテゴリの中央値は市場参考価格と"
                    "同じ水準です。"
                )

            out.append(
                {
                    "section": "カテゴリ",
                    "category": category,
                    "title": category,
                    "fact": (
                        f"{category}は自店舗の中央値が"
                        f"{current:,.0f}円、"
                        + (
                            f"市場参考価格が{reference:,.0f}円です。"
                            if reference is not None
                            else "市場参考価格は比較できません。"
                        )
                    ),
                    "meaning": meaning,
                    "check": (
                        "価格差だけで判断せず、施術内容・所要時間・"
                        "付帯メニュー・利用条件を確認します。"
                    ),
                    "ratio": ratio,
                }
            )

        # 差が大きいカテゴリを上にする。
        out.sort(
            key=lambda x: abs(
                (x.get("ratio") or 100.0) - 100.0
            ),
            reverse=True,
        )

        return out

    # =========================================================
    # 営業確認候補
    # =========================================================

    def _quality(
        self,
        candidates: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        out: List[Dict[str, Any]] = []
        seen = set()

        groups = [
            (
                "価格のばらつきから見た確認候補",
                "outliers",
            ),
            (
                "カテゴリ別の確認候補",
                "category_outliers",
            ),
            (
                "低価格の確認候補",
                "low_price_attention",
            ),
            (
                "高価格の確認候補",
                "high_price_attention",
            ),
        ]

        for title, key in groups:
            for item in candidates.get(key, []) or []:
                key_value = (
                    item.get("coupon_name"),
                    item.get("price"),
                    item.get("category"),
                    title,
                )

                if key_value in seen:
                    continue

                seen.add(key_value)

                reason = item.get("reason") or "価格上の確認候補です。"

                # 内部分析で IQR 等が入っていても、
                # 顧客向け総合分析には出さない。
                reason = self._customer_reason(reason)

                out.append(
                    {
                        "section": "確認候補",
                        "title": title,
                        "coupon_name": item.get("coupon_name"),
                        "category": item.get("category"),
                        "price": item.get("price"),
                        "reason": reason,
                        "fact": (
                            f"対象クーポンの価格は"
                            f"{self._money(item.get('price'))}です。"
                            if item.get("price") is not None
                            else "価格確認候補として抽出されています。"
                        ),
                        "meaning": (
                            "価格だけで良し悪しを決めるのではなく、"
                            "内容と価格のつり合いを確認する入口です。"
                        ),
                        "check": (
                            "クーポン名・施術内容・所要時間・"
                            "利用条件・対象者条件を確認します。"
                        ),
                    }
                )

        return out

    # =========================================================
    # HPB詳細レポート
    # =========================================================

    def _quantitative(
        self,
        quantitative: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        if not quantitative:
            return []

        metrics = quantitative.get("metrics", {})
        summary = metrics.get("summary", {})
        reviews = metrics.get("reviews", {})
        listing = metrics.get("listing", {})
        coupon = metrics.get("coupon", {})

        out: List[Dict[str, Any]] = []

        pv = self._first(summary, "top_pv")
        pv_base = self._first(summary, "area_plan_pv")
        cvr = self._first(summary, "cvr")
        cvr_base = self._first(summary, "area_plan_cvr")
        acr = self._first(summary, "acr")
        acr_base = self._first(summary, "area_plan_acr")

        # --- PV / CVR / ACR ---
        if pv is not None:
            meaning = self._comparison_meaning(
                pv,
                pv_base,
                "店舗ページを見てもらう機会",
            )
            out.append(
                {
                    "section": "予約までの流れ",
                    "title": "発見（PV）",
                    "fact": (
                        f"自店舗PVは{int(pv):,}です。"
                        + (
                            f"比較基準は{int(pv_base):,}です。"
                            if pv_base is not None
                            else ""
                        )
                    ),
                    "meaning": meaning,
                    "check": (
                        "検索される条件や店舗ページの掲載内容と"
                        "合わせて確認します。"
                    ),
                }
            )

        if cvr is not None:
            meaning = self._comparison_meaning(
                cvr,
                cvr_base,
                "「クーポン・メニュー」へ進む割合",
            )
            out.append(
                {
                    "section": "予約までの流れ",
                    "title": "興味喚起（CVR）",
                    "fact": (
                        f"自店舗CVRは{cvr:.1f}%です。"
                        + (
                            f"比較基準は{cvr_base:.1f}%です。"
                            if cvr_base is not None
                            else ""
                        )
                    ),
                    "meaning": meaning,
                    "check": (
                        "店舗ページの内容やクーポンの見せ方と"
                        "合わせて確認します。"
                    ),
                }
            )

        if acr is not None:
            meaning = self._comparison_meaning(
                acr,
                acr_base,
                "予約完了ページまで進む割合",
            )
            out.append(
                {
                    "section": "予約までの流れ",
                    "title": "アクション（ACR）",
                    "fact": (
                        f"自店舗ACRは{acr:.1f}%です。"
                        + (
                            f"比較基準は{acr_base:.1f}%です。"
                            if acr_base is not None
                            else ""
                        )
                    ),
                    "meaning": meaning,
                    "check": (
                        "クーポン内容・利用条件・予約可能枠・"
                        "予約状況と合わせて確認します。"
                    ),
                }
            )

        # --- 売上・予約 ---
        sales = self._num(summary.get("sales_man_yen"))
        reservations = self._num(summary.get("reservations"))

        if sales is not None or reservations is not None:
            fact_parts: List[str] = []

            if sales is not None:
                fact_parts.append(f"前月売上は{sales:.1f}万円")
            if reservations is not None:
                fact_parts.append(f"予約数は{int(reservations):,}件")

            ticket = None
            if sales is not None and reservations:
                ticket = sales * 10000 / reservations
                fact_parts.append(
                    f"1予約あたりの売上は約{ticket:,.0f}円"
                )

            out.append(
                {
                    "section": "売上・予約",
                    "title": "売上・予約",
                    "fact": "、".join(fact_parts) + "です。",
                    "meaning": (
                        "売上と予約数を組み合わせることで、"
                        "予約1件あたりの売上も確認できます。"
                    ),
                    "check": (
                        "HPB上の客単価、新規・再来の予約構成、"
                        "掲載クーポンと合わせて確認します。"
                    ),
                }
            )

        # --- 口コミ ---
        review_count = self._num(reviews.get("count"))
        comparison_review_count = self._num(
            reviews.get("comparison_count")
        )
        reply_rate = self._num(reviews.get("reply_rate"))
        overall_score = self._num(reviews.get("overall_score"))
        comparison_score = self._num(
            reviews.get("comparison_overall_score")
        )

        if review_count is not None:
            fact = f"口コミは{int(review_count):,}件です。"

            if comparison_review_count is not None:
                diff = review_count - comparison_review_count
                fact += (
                    f" 比較サロン平均との差は"
                    f"{diff:+.0f}件です。"
                )

            if reply_rate is not None:
                fact += f" 口コミ返信率は{reply_rate:.1f}%です。"

            if overall_score is not None:
                fact += f" 総合評点は{overall_score:.2f}です。"

            if (
                overall_score is not None
                and comparison_score is not None
            ):
                meaning = (
                    "総合評点は比較サロン平均と合わせて確認できます。"
                    + (
                        "自店舗の評点は比較サロン平均より高い水準です。"
                        if overall_score > comparison_score
                        else (
                            "自店舗の評点は比較サロン平均より低い水準です。"
                            if overall_score < comparison_score
                            else "自店舗の評点は比較サロン平均と同じ水準です。"
                        )
                    )
                )
            else:
                meaning = (
                    "口コミ数・返信率・評価を店舗ページの掲載内容と"
                    "合わせて確認できます。"
                )

            out.append(
                {
                    "section": "口コミ・評価",
                    "title": "口コミ・評価",
                    "fact": fact,
                    "meaning": meaning,
                    "check": (
                        "口コミ数だけで判断せず、評価・返信状況・"
                        "予約数などと合わせて確認します。"
                    ),
                }
            )

        # --- 掲載量 ---
        styles = self._num(listing.get("styles"))
        coupons = self._num(
            listing.get("coupons")
            if listing.get("coupons") is not None
            else coupon.get("coupon_count")
        )

        if styles is not None or coupons is not None:
            fact_parts = []
            if styles is not None:
                fact_parts.append(f"掲載スタイルは{int(styles):,}件")
            if coupons is not None:
                fact_parts.append(f"クーポンは{int(coupons):,}件")

            out.append(
                {
                    "section": "掲載内容",
                    "title": "掲載量",
                    "fact": "、".join(fact_parts) + "です。",
                    "meaning": (
                        "掲載量そのものだけでなく、PV・CVR・ACRと"
                        "合わせて店舗ページの状態を確認できます。"
                    ),
                    "check": (
                        "数量だけで判断せず、実際のスタイル・クーポンの"
                        "内容と予約までの数字を合わせて確認します。"
                    ),
                }
            )

        # --- クーポン構成 ---
        new_count = self._num(coupon.get("new_label_count"))
        repeat_count = self._num(coupon.get("repeat_label_count"))
        all_count = self._num(coupon.get("all_label_count"))
        coupon_count = self._num(coupon.get("coupon_count"))

        if (
            new_count is not None
            and repeat_count is not None
        ):
            fact = (
                f"掲載クーポンは{int(coupon_count):,}件です。"
                if coupon_count is not None
                else "掲載クーポンの構成を確認できます。"
            )
            fact += (
                f" 新規{int(new_count):,}件、"
                f"再来{int(repeat_count):,}件"
            )
            if all_count is not None:
                fact += f"、全員{int(all_count):,}件"
            fact += "です。"

            out.append(
                {
                    "section": "掲載内容",
                    "title": "クーポン構成",
                    "fact": fact,
                    "meaning": (
                        "クーポンの対象構成を、新規・再来の予約構成と"
                        "合わせて確認できます。"
                    ),
                    "check": (
                        "予約構成や実際のクーポン内容と合わせて確認します。"
                    ),
                }
            )

        return out

    # =========================================================
    # データを組み合わせた読み取り
    # =========================================================

    def _cross(
        self,
        pricing: Dict[str, Any],
        quantitative: Dict[str, Any],
        improvement: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        out: List[Dict[str, Any]] = []

        metrics = quantitative.get("metrics", {})
        summary = metrics.get("summary", {})

        price = self._num(pricing.get("shop_median"))
        reference = self._num(
            pricing.get("market_reference_price")
        )
        if reference is None:
            reference = self._num(
                pricing.get("comparison_median")
            )

        pv = self._first(summary, "top_pv")
        pv_base = self._first(summary, "area_plan_pv")
        cvr = self._first(summary, "cvr")
        cvr_base = self._first(summary, "area_plan_cvr")
        acr = self._first(summary, "acr")
        acr_base = self._first(summary, "area_plan_acr")

        # --- 価格 × PV/CVR/ACR ---
        if (
            price is not None
            and reference is not None
            and pv is not None
            and cvr is not None
            and acr is not None
        ):
            price_state = (
                "高い"
                if price > reference
                else "低い"
                if price < reference
                else "同じ"
            )

            flow = self._flow_state(
                pv,
                pv_base,
                cvr,
                cvr_base,
                acr,
                acr_base,
            )

            if flow:
                meaning = (
                    f"自店舗の価格は市場参考価格より{price_state}位置にあり、"
                    f"HPB上の数字は{flow}という組み合わせです。"
                )
                check = self._flow_check(
                    pv,
                    pv_base,
                    cvr,
                    cvr_base,
                    acr,
                    acr_base,
                    price,
                    reference,
                )
            else:
                meaning = (
                    f"自店舗の価格は市場参考価格より{price_state}位置にあり、"
                    "HPB上の行動データと合わせて確認できます。"
                )
                check = (
                    "価格とPV・CVR・ACRのどれか1つだけで原因を決めず、"
                    "クーポン内容・掲載内容・予約状況を合わせて確認します。"
                )

            out.append(
                {
                    "section": "価格 × HPB上の行動",
                    "title": "価格とHPB上の行動データ",
                    "fact": (
                        f"クーポン中央値は{price:,.0f}円、"
                        f"市場参考価格は{reference:,.0f}円です。"
                        f" PVは{int(pv):,}、CVRは{cvr:.1f}%、"
                        f"ACRは{acr:.1f}%です。"
                    ),
                    "meaning": meaning,
                    "check": check,
                }
            )

        # --- 改善検討候補とのつながり ---
        proposals = improvement.get("proposals") or []
        if proposals:
            out.append(
                {
                    "section": "改善検討候補",
                    "title": "改善検討候補とのつながり",
                    "fact": (
                        f"価格分析から{len(proposals)}件の"
                        "改善検討候補が整理されています。"
                    ),
                    "meaning": (
                        "価格差や価格のばらつきが見られる箇所を、"
                        "実際のクーポン内容と照らして確認する入口です。"
                    ),
                    "check": (
                        "候補をそのまま変更判断にせず、クーポン名・"
                        "施術内容・所要時間・利用条件・対象者条件を確認します。"
                    ),
                }
            )

        return out

    # =========================================================
    # 確認ポイント
    # =========================================================

    def _checks(
        self,
        result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        checks: List[Dict[str, Any]] = []
        seen = set()

        # 総合分析で出たチェックを優先。
        groups = (
            result.get("cross_analysis", [])
            + result.get("price", [])
            + result.get("quantitative", [])
            + result.get("quality", [])
            + result.get("category", [])
        )

        for item in groups:
            text = item.get("check", "")
            if not text or text in seen:
                continue

            seen.add(text)
            checks.append(
                {
                    "section": item.get("section", "確認ポイント"),
                    "text": text,
                }
            )

        return checks

    # =========================================================
    # 文言・補助
    # =========================================================

    @staticmethod
    def _customer_reason(reason: str) -> str:
        text = str(reason)

        replacements = {
            "IQR上限を上回っています": (
                "同じカテゴリの他のクーポンと比べて、価格の差が大きいため確認候補です。"
            ),
            "IQR下限を下回っています": (
                "同じカテゴリの他のクーポンと比べて、価格の差が大きいため確認候補です。"
            ),
            "統計的外れ値": (
                "同じカテゴリの他のクーポンと比べて、価格の差が大きいため確認候補です。"
            ),
            "統計的な外れ値": (
                "同じカテゴリの他のクーポンと比べて、価格の差が大きいため確認候補です。"
            ),
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    @staticmethod
    def _comparison_meaning(
        current: float,
        reference: Optional[float],
        label: str,
    ) -> str:

        if reference is None:
            return f"{label}は今回のPDF内の数字から確認できます。"

        if current > reference:
            return f"{label}は比較基準より高い数字です。"

        if current < reference:
            return f"{label}は比較基準より低い数字です。"

        return f"{label}は比較基準と同じ数字です。"

    @classmethod
    def _flow_state(
        cls,
        pv: float,
        pv_base: Optional[float],
        cvr: float,
        cvr_base: Optional[float],
        acr: float,
        acr_base: Optional[float],
    ) -> str:

        if None in (pv_base, cvr_base, acr_base):
            return ""

        states = [
            "PVは比較基準より高い"
            if pv > pv_base
            else "PVは比較基準より低い"
            if pv < pv_base
            else "PVは比較基準と同じ",
            "CVRは比較基準より高い"
            if cvr > cvr_base
            else "CVRは比較基準より低い"
            if cvr < cvr_base
            else "CVRは比較基準と同じ",
            "ACRは比較基準より高い"
            if acr > acr_base
            else "ACRは比較基準より低い"
            if acr < acr_base
            else "ACRは比較基準と同じ",
        ]

        return "、".join(states)

    @classmethod
    def _flow_check(
        cls,
        pv: float,
        pv_base: Optional[float],
        cvr: float,
        cvr_base: Optional[float],
        acr: float,
        acr_base: Optional[float],
        price: float,
        reference: float,
    ) -> str:

        if (
            pv_base is not None
            and cvr_base is not None
            and acr_base is not None
            and pv < pv_base
            and cvr > cvr_base
            and acr < acr_base
        ):
            return (
                "検索結果から店舗ページを見てもらう機会、"
                "クーポンを見てもらう割合、予約まで進む割合を分けて確認します。"
                "特にACRについては、クーポン内容・利用条件・予約可能枠を確認します。"
            )

        if (
            cvr_base is not None
            and acr_base is not None
            and cvr > cvr_base
            and acr < acr_base
        ):
            return (
                "クーポンを見てもらうところまでは比較基準より高い一方、"
                "予約完了まで進む割合は低い数字です。"
                "クーポン価格・内容・利用条件・予約可能枠を確認します。"
            )

        if (
            pv_base is not None
            and cvr_base is not None
            and pv < pv_base
            and cvr > cvr_base
        ):
            return (
                "店舗ページを見てもらう機会は比較基準より低い一方、"
                "店舗ページを見た後にクーポンを見る割合は高い数字です。"
                "検索される条件と店舗ページの掲載内容を確認します。"
            )

        if (
            pv_base is not None
            and cvr_base is not None
            and pv > pv_base
            and cvr < cvr_base
        ):
            return (
                "店舗ページを見てもらう機会は比較基準より高い一方、"
                "クーポンを見る割合は低い数字です。"
                "店舗ページの内容とクーポンの見せ方を確認します。"
            )

        if price > reference and acr_base is not None and acr < acr_base:
            return (
                "価格が市場参考価格より高く、ACRは比較基準より低い数字です。"
                "価格だけを原因と決めず、価格に対する施術内容・"
                "利用条件・予約可能枠を確認します。"
            )

        if price < reference and acr_base is not None and acr < acr_base:
            return (
                "価格が市場参考価格より低く、ACRは比較基準より低い数字です。"
                "価格だけで原因を決めず、クーポン内容・利用条件・"
                "予約可能枠を確認します。"
            )

        return (
            "価格とPV・CVR・ACRをそれぞれ確認し、"
            "クーポン内容・掲載内容・予約状況と合わせて読み取ります。"
        )

    def _summary(self, result: Dict[str, Any]) -> str:
        parts: List[str] = []

        if result.get("price"):
            parts.append("価格")
        if result.get("category"):
            parts.append("カテゴリ")
        if result.get("quality"):
            parts.append("確認候補")
        if result.get("quantitative"):
            parts.append("HPB詳細レポート")
        if result.get("cross_analysis"):
            parts.append("数字の組み合わせ")

        if not parts:
            return (
                "総合分析に使用できる主要データが不足しています。"
            )

        return (
            "自店舗の"
            + "・".join(parts)
            + "から、"
            "数字上の事実と次に確認するポイントを整理しました。"
        )

    @staticmethod
    def _num(value: Any) -> Optional[float]:
        if value is None:
            return None

        try:
            return float(
                str(value)
                .replace(",", "")
                .replace("円", "")
                .replace("%", "")
            )
        except (TypeError, ValueError):
            return None

    @classmethod
    def _first(
        cls,
        data: Dict[str, Any],
        key: str,
    ) -> Optional[float]:
        return cls._num(data.get(key))


    @classmethod
    def _money(cls, value: Any) -> str:
        if value is None:
            return "—"
        number = cls._num(value)
        if number is None:
            return "—"
        return f"{number:,.0f}円"


def analyze_integrated(
    primary_shop: Any,
    pricing_result: Optional[Dict[str, Any]] = None,
    category_analysis: Optional[Dict[str, Any]] = None,
    review_candidates: Optional[Dict[str, Any]] = None,
    improvement_result: Optional[Dict[str, Any]] = None,
    quantitative_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """互換用の簡易エントリーポイント。"""
    return IntegratedAnalyzer().analyze(
        primary_shop=primary_shop,
        pricing_result=pricing_result,
        category_analysis=category_analysis,
        review_candidates=review_candidates,
        improvement_result=improvement_result,
        quantitative_result=quantitative_result,
    )
