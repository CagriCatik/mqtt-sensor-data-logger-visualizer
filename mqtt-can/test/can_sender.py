import time
import logging
import can
import configparser

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("test.sender")

# Load configuration
config = configparser.ConfigParser()
config.read('../can_config.ini')
iface   = config['default']['interface']
channel = config['default']['channel']
bitrate = int(config['default'].get('bitrate', 500000))

# Create a python-can Bus
bus = can.Bus(interface=iface, channel=channel, bitrate=bitrate)
logger.debug(f"Test sender initialized on {iface}, channel={channel}, bitrate={bitrate}")

def send_test_frames(count=5, base_id=0x123):
    for i in range(count):
        data = [(i + j) & 0xFF for j in range(4)]
        msg = can.Message(arbitration_id=base_id, data=data, is_extended_id=False)
        bus.send(msg)
        logger.info(f"Sent test CAN frame: ID=0x{base_id:X}, data={msg.data.hex()}")
        time.sleep(1.0)
    bus.shutdown()
    logger.info("Test sender shutdown complete")

if __name__ == "__main__":
    send_test_frames()
