from dataclasses import dataclass, field


@dataclass
class Coupon:
    """クーポン情報"""

    order: int = 0
    target: str = ""
    category: str = ""
    title: str = ""
    description: str = ""

    price: str = ""

    conditions: str = ""
    stylist: str = ""
    other: str = ""


@dataclass
class Shop:
    """店舗情報"""

    # 基本情報
    name: str = ""
    url: str = ""

    # HPBトップ情報
    review_score: float = 0.0
    review_count: int = 0

    blog_count: int = 0
    style_count: int = 0
    stylist_count: int = 0

    coupon_count: int = 0
    menu_count: int = 0

    coupons: list[Coupon] = field(default_factory=list)