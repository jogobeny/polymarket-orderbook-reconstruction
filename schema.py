from datetime import datetime
from typing import Annotated, Literal

import orjson
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator


class PMXTDataBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition_id: str = Field(alias="market_id")
    position_id: str = Field(alias="token_id")
    side: Literal["YES", "NO"]
    best_bid: float | None
    best_ask: float | None
    timestamp: float


class PMXTDataSnapshot(PMXTDataBase):
    model_config = ConfigDict(extra="forbid")

    update_type: Literal["book_snapshot"]
    bids: list[tuple[float, float]]
    asks: list[tuple[float, float]]

    @model_validator(mode="before")
    @classmethod
    def parse_bids_asks(cls, v):
        if "bids" not in v or v["bids"] is None:
            v["bids"] = []
        else:
            v["bids"] = [(float(p), float(s)) for p, s in v["bids"]]
        if "asks" not in v or v["asks"] is None:
            v["asks"] = []
        else:
            v["asks"] = [(float(p), float(s)) for p, s in v["asks"]]
        return v


class PMXTDataPriceChange(PMXTDataBase):
    model_config = ConfigDict(extra="forbid")

    update_type: Literal["price_change"]
    change_price: float
    change_size: float
    change_side: Literal["BUY", "SELL"]

    @model_validator(mode="before")
    @classmethod
    def parse_floats(cls, v):
        for field in ("change_price", "change_size", "best_bid", "best_ask"):
            if field in v:
                v[field] = float(v[field])
        return v


PMXTData = Annotated[
    PMXTDataSnapshot | PMXTDataPriceChange,
    Field(discriminator="update_type"),
]


class PMXTRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp_received: datetime
    timestamp_created_at: datetime
    condition_id: str = Field(alias="market_id")
    update_type: Literal["book_snapshot", "price_change"]
    data: PMXTData

    @model_validator(mode="before")
    @classmethod
    def parse_data(cls, v):
        if isinstance(v.get("data"), str):
            v["data"] = orjson.loads(v["data"])
        return v


PMXTRowListAdapter = TypeAdapter(list[PMXTRow])


class Order(BaseModel):
    model_config = ConfigDict(extra="forbid")

    size: float
    price: float


class Orderbook(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hash: str
    timestamp: datetime
    asks: list[Order]
    bids: list[Order]


OrderbookListAdapter = TypeAdapter(list[Orderbook])
