"""Send a reservation-based charging session to the local OCPP endpoint."""

import argparse
import base64
import getpass
import json
from datetime import datetime, timezone
from uuid import uuid4

from websockets.sync.client import connect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Example: ws://127.0.0.1:8000/ocpp/1")
    parser.add_argument("reservation_id", type=int)
    parser.add_argument("driver_tag")
    parser.add_argument("--meter-start-wh", default=10000, type=int)
    args = parser.parse_args()
    charger_id = args.url.rstrip("/").rsplit("/", 1)[1]
    password = getpass.getpass("Charger password: ")
    basic = base64.b64encode(f"{charger_id}:{password}".encode()).decode()

    def now():
        return datetime.now(timezone.utc).isoformat()

    with connect(args.url, subprotocols=["ocpp1.6"], additional_headers={"Authorization": f"Basic {basic}"}) as socket:
        def call(action, payload):
            key = uuid4().hex
            socket.send(json.dumps([2, key, action, payload]))
            result = json.loads(socket.recv(timeout=10))
            if result[:2] != [3, key]:
                raise RuntimeError(f"{action} rejected: {result[2:4]}")
            return result[2]

        call("BootNotification", {"chargePointVendor": "EV Network", "chargePointModel": "Simulator"})
        call("StatusNotification", {"connectorId": 1, "status": "Available", "errorCode": "NoError"})
        start = call("StartTransaction", {
            "connectorId": 1, "idTag": args.driver_tag, "reservationId": args.reservation_id,
            "meterStart": args.meter_start_wh, "timestamp": now(),
        })
        transaction = start["transactionId"]
        if not transaction:
            raise RuntimeError("Driver tag or reservation was declined.")
        call("MeterValues", {
            "connectorId": 1, "transactionId": transaction,
            "meterValue": [{"timestamp": now(), "sampledValue": [
                {"value": str(args.meter_start_wh + 3000), "unit": "Wh"},
                {"value": "11000", "unit": "W", "measurand": "Power.Active.Import"},
            ]}],
        })
        call("StopTransaction", {"transactionId": transaction, "meterStop": args.meter_start_wh + 4000, "timestamp": now()})
        print(f"Session {transaction} completed with 4 kWh delivered.")


if __name__ == "__main__":
    main()
