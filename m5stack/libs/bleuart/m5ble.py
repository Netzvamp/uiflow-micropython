import bluetooth
from micropython import const
import struct

_ADV_APPEARANCE_GENERIC_COMPUTER = const(128)
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)
_IRQ_CONNECTION_UPDATE = const(27)
_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)

_ADV_IND = const(0x00)
_ADV_DIRECT_IND = const(0x01)
_ADV_SCAN_IND = const(0x02)
_ADV_NONCONN_IND = const(0x03)

_FLAG_BROADCAST = const(0x0001)
_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)
_FLAG_AUTHENTICATED_SIGNED_WRITE = const(0x0040)

_FLAG_AUX_WRITE = const(0x0100)
_FLAG_READ_ENCRYPTED = const(0x0200)
_FLAG_READ_AUTHENTICATED = const(0x0400)
_FLAG_READ_AUTHORIZED = const(0x0800)
_FLAG_WRITE_ENCRYPTED = const(0x1000)
_FLAG_WRITE_AUTHENTICATED = const(0x2000)
_FLAG_WRITE_AUTHORIZED = const(0x4000)

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_UUID16_MORE = const(0x2)
_ADV_TYPE_UUID32_MORE = const(0x4)
_ADV_TYPE_UUID128_MORE = const(0x6)
_ADV_TYPE_APPEARANCE = const(0x19)


# Generate a payload to be passed to gap_advertise(adv_data=...).
def advertising_payload(limited_disc=False, br_edr=False, name=None, services=None, appearance=0):
    payload = bytearray()

    def _append(adv_type, value):
        nonlocal payload
        payload += struct.pack("BB", len(value) + 1, adv_type) + value

    _append(
        _ADV_TYPE_FLAGS,
        struct.pack("B", (0x01 if limited_disc else 0x02) + (0x18 if br_edr else 0x04)),
    )

    if name:
        _append(_ADV_TYPE_NAME, name)

    if services:
        for uuid in services:
            b = bytes(uuid)
            if len(b) == 2:
                _append(_ADV_TYPE_UUID16_COMPLETE, b)
            elif len(b) == 4:
                _append(_ADV_TYPE_UUID32_COMPLETE, b)
            elif len(b) == 16:
                _append(_ADV_TYPE_UUID128_COMPLETE, b)

    # See org.bluetooth.characteristic.gap.appearance.xml
    if appearance:
        _append(_ADV_TYPE_APPEARANCE, struct.pack("<h", appearance))

    return payload


def decode_field(payload, adv_type):
    i = 0
    result = []
    while i + 1 < len(payload):
        if payload[i + 1] == adv_type:
            result.append(payload[i + 2 : i + payload[i] + 1])
        i += 1 + payload[i]
    return result


def decode_name(payload):
    n = decode_field(payload, _ADV_TYPE_NAME)
    return str(n[0], "utf-8") if n else ""


def decode_services(payload):
    services = []
    for u in decode_field(payload, _ADV_TYPE_UUID16_COMPLETE):
        services.append(bluetooth.UUID(struct.unpack("<h", u)[0]))
    for u in decode_field(payload, _ADV_TYPE_UUID32_COMPLETE):
        services.append(bluetooth.UUID(struct.unpack("<d", u)[0]))
    for u in decode_field(payload, _ADV_TYPE_UUID128_COMPLETE):
        services.append(bluetooth.UUID(u))
    return services


class M5BLEServer:
    def __init__(self, ble_handle, name, buf_size, verbose=False) -> None:
        self._verbose = verbose
        self._ble = ble_handle
        self._connected_devices = set()
        self._rx_buffer = bytearray()
        self._payload = advertising_payload(name=name, appearance=_ADV_APPEARANCE_GENERIC_COMPUTER)
        self._buf_size = buf_size
        self._services = []
        self._value_handles = ()
        self._value_handle_map = {}

    def clear_services(self):
        self._services.clear()

    def add_service(self, uuid, characteristics: list | tuple = None):
        self._services.append((bluetooth.UUID(uuid), characteristics))

    def create_characteristic(self, uuid, read=False, write=False, notify=False):
        return (
            bluetooth.UUID(uuid),
            bluetooth.FLAG_READ * read
            + bluetooth.FLAG_WRITE * write
            + bluetooth.FLAG_NOTIFY * notify,
        )

    def start(self, interval_us=500000):
        print(self._services)
        self._value_handles = self._ble.gatts_register_services(self._services)

        for i in range(len(self._services)):
            for j in range(len(self._services[i][1])):
                self._value_handle_map[self._services[i][1][j][0]] = self._value_handles[i][j]

        self._start_advertising(interval_us)

    def on_receive(self, callback):
        self._recv_cb = callback

    def on_connected(self, callback):
        self._connected_cb = callback

    def on_disconnected(self, callback):
        self._disconnected_cb = callback

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, addr_type, addr = data
            client = self.Client(self, conn_handle, addr_type, addr)
            self._connected_devices.add(client)
            if self._device_connected_cb:
                self._device_connected_cb(client)

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, addr_type, addr = data
            for client in self._connected_devices:
                if client.connect_handle == conn_handle:
                    self._connected_devices.remove(client)
                    if self._device_disconnected_cb:
                        self._device_disconnected_cb(client)
                    self._start_advertising()
                    break

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            for client in self._connected_devices:
                if client.connect_handle != conn_handle:
                    continue
                client._recv(value_handle)
                if self._recv_cb:
                    self._recv_cb(client)
                break

    def get_client(self, index):
        return self._connected_devices[index]

    def get_clients(self):
        return self._connected_devices

    def _start_advertising(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    class Client:
        def __init__(self, server, connect_handle, addr_type, addr) -> None:
            self.connect_handle = connect_handle
            self.addr_type = addr_type
            self.addr = addr
            self.rx_buffers = {}
            self._server = server

        def _recv(self, handle):
            self.rx_buffers[handle] = self.rx_buffers.get(
                handle, b""
            ) + self._server._ble.gatts_read(handle)

        def _get_value_handle(self, uuid):
            value_handle = self._server._value_handle_map[bluetooth.UUID(uuid)]
            if not value_handle:
                raise ValueError("Characteristic not found")
            return value_handle

        def any(self, uuid):
            value_handle = self._get_value_handle(uuid)
            return len(self.rx_buffers.get(value_handle, b""))

        def read(self, uuid, sz=None):
            value_handle = self._get_value_handle(uuid)
            if not self.rx_buffers[value_handle]:
                return b""
            if not sz:
                sz = len(self.rx_buffers[value_handle])
            result = self.rx_buffers[value_handle][0:sz]
            self.rx_buffers[value_handle] = self.rx_buffers[value_handle][sz:]
            return result

        def write(self, data, uuid):
            value_handle = self._get_value_handle(uuid)
            self._server._ble.gatts_notify(self.connect_handle, value_handle, data)

        def close(self):
            self._server._ble.gap_disconnect(self.connect_handle)


class M5BLEClient:
    def __init__(self, ble_handle, verbose=False) -> None:
        self._verbose = verbose
        self._ble = ble_handle
        self._scan_results = []
        self._reset()

    def _reset(self):
        self._server_conn_handle = None
        self._server_addr_type = None
        self._server_addr = None
        self._service_handle_map = {}
        self.rx_buffers = {}

    def on_connected(self, callback):
        self._connected_cb = callback

    def on_disconnected(self, callback):
        self._disconnected_cb = callback

    def on_server_found(self, callback):
        self._server_found_cb = callback

    def on_scan_finished(self, callback):
        self._scan_finished_cb = callback

    def on_read_complete(self, callback):
        self._read_complete_cb = callback

    def on_notify(self, callback):
        self._notify_cb = callback

    def scan(
        self,
        timeout=2000,
        connect_on_found=True,
        stop_on_found=True,
        target_name_prefix=None,
        target_uuid=None,
    ):
        self._target_name_prefix = target_name_prefix
        self._target_uuid = target_uuid
        self._stop_on_found = stop_on_found
        self._connect_on_found = connect_on_found
        self._scan_results = []
        self._ble.gap_scan(timeout, 30000, 30000)

    def connect(self, addr_type, addr):
        self._server_addr_type = addr_type
        self._server_addr = addr
        self._ble.gap_connect(addr_type, addr)

    def _irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            if adv_type in (_ADV_IND, _ADV_DIRECT_IND) and decode_name(adv_data).startswith(
                self._target_name_prefix
            ):
                self._scan_results.append(
                    (decode_name(adv_data), addr_type, addr, adv_type, rssi, adv_data)
                )
                if self._stop_on_found:
                    self._ble.gap_scan(None)
                if self._connect_on_found:
                    self._ble.gap_scan(None)
                    self.connect(addr_type, addr)
                if self._server_found_cb:
                    self._server_found_cb(self._scan_results[-1])

        elif event == _IRQ_SCAN_DONE:
            if self._scan_finished_cb:
                self._scan_finished_cb(self._scan_results)

        elif event == _IRQ_PERIPHERAL_CONNECT:
            # A successful gap_connect().
            conn_handle, addr_type, addr = data
            if addr_type == self._server_addr_type and addr == self._server_addr:
                self._server_conn_handle = conn_handle
                self._ble.gattc_discover_services(conn_handle)

        elif event == _IRQ_PERIPHERAL_DISCONNECT:
            # Disconnect (either initiated by us or the remote end).
            conn_handle, addr_type, addr = data
            if conn_handle == self._server_conn_handle:
                if self._disconnected_cb:
                    self._disconnected_cb(conn_handle, addr_type, addr)
                self._reset()

        elif event == _IRQ_GATTC_SERVICE_RESULT:
            self._verbose and print("GATTC service result")
            # Connected device returned a service.
            conn_handle, start_handle, end_handle, uuid = data
            if conn_handle == self._server_conn_handle:
                self._service_handle_map[uuid] = {
                    "start": start_handle,
                    "end": end_handle,
                }

        elif event == _IRQ_GATTC_SERVICE_DONE:
            self._verbose and print("GATTC service done")
            # Service query complete.
            for service in self._service_handle_map.values():
                self._ble.gattc_discover_characteristics(
                    self._server_conn_handle, service["start"], service["end"]
                )

        elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
            # Connected device returned a characteristic.
            conn_handle, def_handle, value_handle, properties, uuid = data
            self._service_handle_map[uuid]["value"] = value_handle

        elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
            if self._connected_cb:
                self._connected_cb()

        elif event == _IRQ_GATTC_READ_RESULT:
            # A read completed successfully.
            conn_handle, value_handle, char_data = data
            if conn_handle == self._server_conn_handle:
                if self._read_complete_cb:
                    self._read_complete_cb(conn_handle, value_handle, char_data)

        elif event == _IRQ_GATTC_READ_DONE:
            # Read completed (no-op).
            conn_handle, value_handle, status = data

        elif event == _IRQ_GATTC_NOTIFY:
            self._verbose and print("GATTC notify")
            # The ble_temperature.py demo periodically notifies its value.
            conn_handle, value_handle, notify_data = data
            if conn_handle == self._server_conn_handle:
                self.rx_buffers[value_handle] = (
                    self.rx_buffers.get(value_handle, b"") + notify_data
                )
                if self._notify_cb:
                    self._notify_cb(self)

    def _get_value_handle(self, uuid):
        value_handle = self._service_handle_map[bluetooth.UUID(uuid)]["value"]
        if not value_handle:
            raise ValueError("Characteristic not found")
        return value_handle

    def any(self, uuid):
        value_handle = self._get_value_handle(uuid)
        return len(self.rx_buffers.get(value_handle, b""))

    def read(self, uuid, sz=None):
        value_handle = self._get_value_handle(uuid)
        if not self.rx_buffers[value_handle]:
            return b""
        if not sz:
            sz = len(self.rx_buffers[value_handle])
        result = self.rx_buffers[value_handle][0:sz]
        self.rx_buffers[value_handle] = self.rx_buffers[value_handle][sz:]
        return result

    def write(self, data, uuid):
        value_handle = self._get_value_handle(uuid)
        self._ble.gattc_write(self._server_conn_handle, value_handle, data)

    def close(self):
        if not self._server_conn_handle:
            return
        self._ble.gap_disconnect(self._server_conn_handle)
        self._reset()


class M5BLE:
    def __init__(self, name="M5UiFlow", buf_size=100, verbose=False) -> None:
        self._verbose = verbose
        self._ble = self._ble = bluetooth.BLE()
        self.client = M5BLEClient(self._ble, verbose)
        self.server = M5BLEServer(self._ble, name, buf_size, verbose)
        self._ble.active(True)
        self._ble.irq(self._ble_irq)

    def _ble_irq(self, event, data):
        self._verbose and print("event: ", event)
        self.server._irq(event, data)
        self.client._irq(event, data)

    def deinit(self):
        self._ble.active(False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ble.active(False)


if __name__ == "__main__":
    ble = M5BLE()
    ble.server.add_service(
        0x1800,
        [
            ble.server.create_characteristic(0x2A00, read=True),
            ble.server.create_characteristic(0x2A01, read=True),
        ],
    )
    ble.server.start()
    while True:
        pass
