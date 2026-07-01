from dataclasses import dataclass, field


@dataclass
class Coupon:
    """クーポン情報"""

    order: int = 0                  # 掲載順
    target: str = ""                # 新規 / 再来 / 全員
    category: str = ""              # カット+カラー等
    title: str = ""                 # クーポン名
    description: str = ""           # クーポン内容

    regular_price: int = 0          # 通常価格（将来用）
    price: int = 0                  # 販売価格

    conditions: str = ""            # 来店条件
    stylist: str = ""               # 対象スタイリスト
    other: str = ""                 # その他条件


@dataclass
class Shop:
    """店舗情報"""

    name: str = ""
    url: str = ""
    coupons: list[Coupon] = field(default_factory=list)