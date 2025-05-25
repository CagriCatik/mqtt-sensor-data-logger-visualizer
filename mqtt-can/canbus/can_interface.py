# canbus/can_interface.py

import can
import configparser
import os
import logging

# ——— Logger Setup ———————————————————————————————————————————————
logger = logging.getLogger("canbus.can_interface")

# ——— Compute Config Path ———————————————————————————————————————————
THIS_DIR    = os.path.dirname(__file__)
PROJECT_ROOT= os.path.abspath(os.path.join(THIS_DIR, os.pardir))
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'can_config.ini')

logger.debug(f"Looking for CAN config at: {CONFIG_PATH}")

# ——— Load CAN Bus Configuration ————————————————————————————————————
config = configparser.ConfigParser()
read_files = config.read(CONFIG_PATH)
if not read_files:
    logger.warning(f"No config file read. Checked paths: {read_files}")
if 'default' not in config:
    logger.warning(f"'default' section missing in CAN config; using defaults")
    iface, channel, bitrate = 'virtual', 'vcan0', 500000
else:
    sec = config['default']
    iface   = sec.get('interface', 'virtual')
    channel = sec.get('channel',   'vcan0')
    bitrate = int(sec.get('bitrate', 500000))
    logger.debug(f"Config loaded: interface={iface}, channel={channel}, bitrate={bitrate}")

# ——— Initialize Virtual CAN Bus —————————————————————————————————————
try:
    bus = can.Bus(interface=iface, channel=channel, bitrate=bitrate)
    logger.info(f"Initialized CAN bus on {iface}/{channel} @ {bitrate}bps")
except Exception as e:
    logger.error(f"Failed to initialize CAN bus: {e}")
    raise

# ——— API ———————————————————————————————————————————————————————
def read_can(timeout=1.0):
    try:
        msg = bus.recv(timeout)
        if msg:
            logger.debug(f"Received CAN: ID=0x{msg.arbitration_id:X}, data={msg.data.hex()}")
        return msg
    except can.CanError as e:
        logger.error(f"CAN read error: {e}")
        return None

def write_can(arbitration_id, data):
    try:
        msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
        bus.send(msg)
        logger.debug(f"Sent CAN: ID=0x{arbitration_id:X}, data={msg.data.hex()}")
    except can.CanError as e:
        logger.error(f"CAN write error: {e}")
