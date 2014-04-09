import redis
import uuid
import json
import time
import threading

__name__ = "durable_channel"

class DurableChannel:

  def __init__(name, options):
    self.name = name
    self.stopping = False
    self.redis = redis.StrictRedis(host=options["host"], port=options["port"], db=0)
    self.timeoutMonitorFrequency = 1000
    if "timeoutMonitorFrequency" not in options:
      self.timeoutMonitorFrequency = options["timeoutMonitorFrequency"]
    
    self.timeoutMonitorThread = threading.Thread(target=self.__monitorTimeouts)
    self.timeoutMonitorThread.start()

  def __get_current_time():
    return int(round(time.time() * 1000))

  def __package(self, content, to, request_id=None, timeout):
    message = {
      "id": str(uuid.uuid4()),
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

      expiredMessages = self.redis.zrangebyscore(
        self.name + ".pending", 
        0, 
        self.__get_current_time()
      )
      if len(expiredMessages) == 0:
        continue

      for expiredMessageId in expiredMessageIds:
        expiredMessageTokens = expiredMessage.split("::")
        
        expiredMessage = self.redis.hdel(
          expiredMessageTokens[0] + ".messages", 
          expiredMessageTokens[1]
        )
        
        self.redis.zrem(
          self.name + ".pending", 
          expiredMessageId
        )

  def send(self, content, to, timeout):
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
    self.redis.lpush(
      to + ".queue", 
      message["id"]
    )
    self.redis.zadd(
      self.name + ".pending", 
      (self.__get_current_time() + timeout), 
      to + "::" + message["id"]
    )

  def receive(self):
    messageId = self.redis.brpop(
      self.name + ".queue"
    )
    messageId = messageId[1]
    
    message = self.redis.hget(
      self.name + ".messages", 
      messageId
    )

    if "requestId" in message and message["requestId"] != None:
      self.redis.zrem(
        self.name + ".pending", 
        message["from"] + "::" + message["requestId"]
      )
      self.redis.hdel(
        message["from"] + ".messages", 
        message["requestId"]
      )
    
    _message = {content: message.content}
    if "requestId" in message and message["requestId"] != None:
      _message["requestId"] = message["requestId"]
      _message["responseId"] = message["id"]
    else:
      _message["requestId"] = message["id"]

    return _message

  def reply(self, message, response, timeout):
    message = self.__package(
      content=response, 
      to=request["from"], 
      request_id=message["requestId"], 
      timeout=timeout
    )
    request = self.redis.hget(
      self.name + ".messages", 
      message["requestId"]
    )
    self.redis.hset(
      request["from"] + ".messages", 
      message["id"], 
      json.dumps(message)
    )
    self.redis.lpush(
      request["from"] + ".queue", 
      message["id"]
    )
    self.redis.zadd(
      self.name + ".pending", 
      (self.__get_current_time() + timeout), 
      request["from"] + "::" + message["id"]
    )

  def close(self, message):
    self.redis.hdel(
      self.name + ".messages", 
      message["responseId"]
    )

  def end(self):
    self.stopping = True