# Charger simulator

The WebSocket endpoint implements a simulator-oriented subset of OCPP 1.6J.
It supports BootNotification, StatusNotification, StartTransaction, MeterValues and StopTransaction.
The data path follows the Open Charge Alliance's [OCPP terminology](https://openchargealliance.org/protocols/ocpp-protocols/).

1. Run Alembic migrations and create a confirmed reservation whose start time is near the current time.
2. In the root environment file, set `OCPP_DEVICES` to a JSON object keyed by charger ID. Each entry has a random device password and maps RFID tags to existing customer IDs. For example, a charger with ID 1 and customer with ID 3 can use `{"1":{"password":"REPLACE_WITH_RANDOM_DEVICE_PASSWORD","driver_tags":{"driver-demo":3}}}`. Restart the API with the new setting.
3. Run `python -m database.simulator.charger ws://127.0.0.1:8000/ocpp/1 RESERVATION_ID driver-demo` and enter the device password when prompted. Use the Compose port 8080 when running through the proxy.

The selected reservation must belong to both the configured customer and the charger, and the device must negotiate the `ocpp1.6` WebSocket subprotocol. Each accepted reading is keyed by session ID and timestamp. Drivers and authorized staff can retrieve it with `GET /api/v1/sessions/{id}/meter-readings`. Use TLS with physical devices. This implementation handles one logical connector per charger, requires a reservation ID in StartTransaction and leaves maintenance clearance to operators.
