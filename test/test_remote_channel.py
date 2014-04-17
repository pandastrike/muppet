import time
from muppet.remote_channel import RemoteChannel

class TestRemoteChannel:

  def setup_class(self):
    self.redis_options = {"redis": {"host": "127.0.0.1", "port": 6379}}
    self.sender = None
    self.receiver = None
    self.calledbackChannel = ""
    self.calledbackMessage = ""

  def __callback(self, channel, message):
    self.calledbackChannel = channel
    self.calledbackMessage = message
    self.receiver.end()

  def test_messaging(self):
    self.sender = RemoteChannel("greeting", self.redis_options)
    self.receiver = RemoteChannel("greeting", self.redis_options)

    # listen for messages
    self.receiver.listen(self.__callback)

    # send message
    self.sender.send("hello")
    self.sender.end()

    # wait for timeout
    time.sleep(2)

    # assert to check we received the message
    assert self.calledbackChannel == "greeting"
    assert self.calledbackMessage == "hello"