from muppet.remote_channel import RemoteChannel

class TestRemoteChannel:

  def setup_class(self):
    self.redis_options = {"redis": {"host": "127.0.0.1", "port": 6379}}
    self.sender = None
    self.receiver = None

  def __callback(self, message):
    assert message == "hello"
    self.receiver.end()

  def test_messaging(self):
    self.sender = RemoteChannel("greeting", self.redis_options)
    self.receiver = RemoteChannel("greeting", self.redis_options)

    # listen for messages
    self.receiver.listen(self.__callback)

    # send message
    self.sender.send("hello")
    self.sender.end()