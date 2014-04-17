import string
import random
import json
import threading
import redis

class RemoteChannel:

  def __init__(self, name, options):
    if name == None or len(name) == 0:
      raise ValueError("Remote channels cannot be anonymous")

    self.name = name
    self.id = ''.join(random.choice(string.letters + string.digits) for _ in xrange(16))
    self.redis = redis.StrictRedis(host=options["redis"]["host"], port=options["redis"]["port"], db=0)
    self.pubsub = self.redis.pubsub()
    self.listening = False

  def __startMessageLoop(self):
    for message in self.pubsub.listen():
      if message["type"] == "message":
        if message["data"] == self.id + "__kill__":
          self.pubsub.unsubscribe()
          break
        elif not message["data"].endswith("__kill__") :
          data = json.loads(message["data"])
          self.callback(message["channel"], data["content"])

  def send(self, content):
    message = {"content": content}
    self.redis.publish(self.name, json.dumps(message))

  def listen(self, callback):
    if not self.listening:
      self.listening = True
      self.callback = callback
      self.pubsub.subscribe([self.name])
      self.listenerThread = threading.Thread(target=self.__startMessageLoop)
      self.listenerThread.daemon = True
      self.listenerThread.start()

  def end(self):
    if self.listening:
      self.redis.publish(self.name, self.id + "__kill__")