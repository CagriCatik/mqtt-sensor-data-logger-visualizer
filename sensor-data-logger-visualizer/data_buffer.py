import collections
import threading
import logging
from typing import Deque, Tuple

# Module-level logger
logger = logging.getLogger(__name__)

class CircularBuffer:
    """Thread-safe circular buffer for time-series data with debug logging."""
    def __init__(self, maxlen: int = 1000):
        self._lock = threading.Lock()
        self._times: Deque[float] = collections.deque(maxlen=maxlen)
        self._values: Deque[float] = collections.deque(maxlen=maxlen)
        logger.debug("CircularBuffer created with maxlen=%d", maxlen)

    def append(self, timestamp: float, value: float):
        with self._lock:
            self._times.append(timestamp)
            self._values.append(value)
        logger.debug("Appended value %s at time %s", value, timestamp)

    def get_series(self) -> Tuple[list[float], list[float]]:
        with self._lock:
            times_copy = list(self._times)
            values_copy = list(self._values)
        logger.debug("get_series returned %d entries", len(times_copy))
        return times_copy, values_copy
