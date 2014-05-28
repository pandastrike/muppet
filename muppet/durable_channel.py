import string
import random
import json
import time
import threading
import redis

class DurableChannel:

  def __init__(self, name, options, timeoutCallback=None):
    if name == None or len(name) == 0:
      raise ValueError("Durable channels cannot be anonymous")

    self.name = name
    self.stopping = False
    self.redis = redis.StrictRedis(host=options["redis"]["host"], port=options["redis"]["port"], db=0)
    self.timeoutCallback = timeoutCallback
    self.timeoutMonitorFrequency = 1000
    if "timeoutMonitorFrequency" in options:
      self.timeoutMonitorFrequency = options["timeoutMonitorFrequency"]
    
    self.timeoutMonitorThread = threading.Thread(target=self.__monitorTimeouts)
    self.timeoutMonitorThread.daemon = True
    self.timeoutMonitorThread.start()

  def __get_current_time(self):
    return int(round(time.time() * 1000))

  def __package(self, content, to, request_id=None, timeout=None):
    newId = ''.join(random.choice(string.letters + string.digits) for _ in xrange(16))
    message = {
      "id": newId,
      "requestId": request_id,
      "from": self.name,
      "to": to,
      "timeout": timeout,
      "content": content
    }
    return message

  def __monitorTimeouts(self):
    while True:
      if self.stopping:
        break

      time.sleep(self.timeoutMonitorFrequency / 1000)

      expiredMessageIds = self.redis.zrangebyscore(
        self.name + ".pending", 
        0, 
        self.__get_current_time()
      )
      if len(expiredMessageIds) == 0:
        continue

      for expiredMessageId in expiredMessageIds:
        expiredMessageTokens = expiredMessageId.split("::")

        expiredMessage = self.redis.hget(
          expiredMessageTokens[0] + ".messages", 
          expiredMessageTokens[1]
        )

        self.redis.zrem(
          self.name + ".pending", 
          expiredMessageId
        )

        if expiredMessage == None:
          continue

        expiredMessage = json.loads(expiredMessage)
        
        self.redis.hdel(
          expiredMessageTokens[0] + ".messages", 
          expiredMessageTokens[1]
        )

        if self.timeoutCallback != None:
          _message = {"content": expiredMessage["content"]}
          if "requestId" in expiredMessage and expiredMessage["requestId"] != None:
            _message["requestId"] = expiredMessage["requestId"]
          self.timeoutCallback(_message)

  def send(self, content, to, timeout=None):
    message = self.__package(
      content=content, 
      to=to, 
      timeout=timeout
    )    

    self.redis.hset(
      to + ".messages", 
      message["id"], 
      json.dumps(message)
    )

    if timeout != None:
      self.redis.zadd(
        self.name + ".pending", 
        (self.__get_current_time() + timeout), 
        to + "::" + message["id"]
      )

    self.redis.lpush(
      to + ".queue", 
      message["id"]
    )

  def receive(self):
    message = None
    while message == None:
      messageId = self.redis.brpop(
        self.name + ".queue"
      )
      messageId = messageId[1]

      message = self.redis.hget(
        self.name + ".messages", 
        messageId
      )
    
    message = json.loads(message)

    if "requestId" in message and message["requestId"] != None:
      if message["timeout"] != None:
        self.redis.zrem(
          self.name + ".pending", 
          message["from"] + "::" + message["requestId"]
        )
      self.redis.hdel(
        message["from"] + ".messages", 
        message["requestId"]
      )
    
    _message = {"content": message["content"]}
    if "requestId" in message and message["requestId"] != None:
      _message["from"] = message["to"]
      _message["to"] = message["from"]
      _message["requestId"] = message["requestId"]
      _message["responseId"] = message["id"]
    else:
      _message["from"] = message["from"]
      _message["to"] = message["to"]
      _message["requestId"] = message["id"]

    return _message

  def reply(self, message, response, timeout=None):
    request = self.redis.hget(
      self.name + ".messages", 
      message["requestId"]
    )
    if request == None:
      # its possible that this is a reply to a message that already timed out
      return

    request = json.loads(request)
    message = self.__package(
      content=response, 
      to=request["from"], 
      request_id=message["requestId"], 
      timeout=timeout
    )

    self.redis.hset(
      request["from"] + ".messages", 
      message["id"], 
      json.dumps(message)
    )

    if timeout != None:
      self.redis.zadd(
        self.name + ".pending", 
        (self.__get_current_time() + timeout), 
        request["from"] + "::" + message["id"]
      )

    self.redis.lpush(
      request["from"] + ".queue", 
      message["id"]
    )

  def close(self, message):
    self.redis.hdel(
      self.name + ".messages", 
      message["responseId"]
    )
    self.redis.zrem(
      message["to"] + ".pending", 
      message["from"] + "::" + message["responseId"]
    )

  def end(self):
    self.stopping = True