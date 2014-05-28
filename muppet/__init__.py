from muppet.durable_channel import DurableChannel
from muppet.remote_channel import RemoteChannel

__version__ = "0.1.6"
VERSION = tuple(map(int, __version__.split('.')))

__all__ = [
  "DurableChannel", "RemoteChannel"
]