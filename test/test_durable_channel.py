import time
from muppet.durable_channel import DurableChannel

class TestDurableChannel:

  def setup_class(self):
    self.redis_options = {"redis": {"host": "127.0.0.1", "port": 6379}}
    self.dispatcher = None
    self.worker = None
    self.calledbackMessage = None

  def __timeout_callback(self, message):
    self.calledbackMessage = message
    self.worker.end()
    self.dispatcher.end()

  def test_messaging(self):
    self.dispatcher = DurableChannel("dispatcher.1", self.redis_options)
    self.worker = DurableChannel("worker.1", self.redis_options)

    # dispatch message
    self.dispatcher.send(content="task", to="worker.1")

    # receive message
    message = self.worker.receive()
    assert message["content"] == "task"
    self.worker.reply(message=message, response="reply", timeout=5000)

    # receive reply
    reply = self.dispatcher.receive()
    assert reply["content"] == "reply"
    self.dispatcher.close(reply)
    self.worker.end()
    self.worker = None
    self.dispatcher.end()
    self.dispatcher = None

  def test_timeout(self):
    self.dispatcher = DurableChannel("dispatcher.2", self.redis_options, self.__timeout_callback)
    self.worker = DurableChannel("worker.2", self.redis_options)

    # dispatch message
    self.dispatcher.send(content="task", to="worker.2", timeout=1000)

    # receive message
    message = self.worker.receive()
    assert message["content"] == "task"
    
    # wait for timeout
    time.sleep(2)

    # assert to check message timed out 
    assert self.calledbackMessage["content"] == "task"