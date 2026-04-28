import uuid
from datetime import datetime, timedelta, timezone


def reconstruct_orderbooks(rows: list[PMXTRow]):
    state: dict[str, dict] = {}  # position_id -> {"bids": {price: size}, "asks": {price: size}}
    result: dict[str, list[Orderbook]] = {}
    last_saved: dict[str, datetime] = {}  # position_id -> last saved timestamp

    SNAPSHOT_INTERVAL = timedelta(minutes=1)

    for row in rows:
        position_id = row.data.position_id
        ts = datetime.fromtimestamp(row.data.timestamp, tz=timezone.utc)

        if position_id not in state:
            state[position_id] = {"bids": {}, "asks": {}}
        if position_id not in result:
            result[position_id] = []

        if isinstance(row.data, PMXTDataSnapshot):  # create new orderbook state
            state[position_id]["bids"] = dict(row.data.bids) if row.data.bids else {}
            state[position_id]["asks"] = dict(row.data.asks) if row.data.asks else {}
        elif isinstance(row.data, PMXTDataPriceChange):
            side = "bids" if row.data.change_side == "BUY" else "asks"
            if row.data.change_size == 0:  # remove price level
                state[position_id][side].pop(row.data.change_price, None)
            else:
                state[position_id][side][row.data.change_price] = row.data.change_size

        if not state[position_id]["bids"] and not state[position_id]["asks"]:
            continue

        if position_id not in last_saved or (ts - last_saved[position_id]) >= SNAPSHOT_INTERVAL:
            orderbook = Orderbook(
                hash=uuid.uuid4().hex,
                timestamp=ts,
                bids=[Order(price=p, size=s) for p, s in state[position_id]["bids"].items()],
                asks=[Order(price=p, size=s) for p, s in state[position_id]["asks"].items()],
            )
            result[position_id].append(orderbook)
            last_saved[position_id] = ts

    return result
