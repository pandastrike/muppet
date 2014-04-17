******
muppet
******

`muppet`_ is Python implementation of `mutual`_. muppet provides RemoteChannel for simple messaging across process or machine boundaries and DurableChannel for durable messaging across process or machine boundaries. Both RemoteChannel and DurableChannel use Redis for message store.

.. _muppet: http://github.com/pandastrike/muppet
.. _mutual: http://github.com/pandastrike/mutual


Remote Channel
--------------
Remote Channel follows a pub-sub model where every message sent on a channel is broadcast to all the subscribers listening on the channel.

Usage:
^^^^^^

.. code-block:: python

   from muppet import RemoteChannel

   # define the callback to receive messages
   def callback(message):
     print("received:", message)
     # we are done with the receiver
     receiver.end()

   # redis server details
   redis_options = {"redis": {"host": "127.0.0.1", "port": 6379}}
   # create a remote channel to send messages
   sender = RemoteChannel("greeting", redis_options)
   # create a remote channel to receive messages
   receiver = RemoteChannel("greeting", redis_options)
   # listen for messages by passing the callback
   receiver.listen(callback)
   # send a message
   sender.send("hello")
   # we are done with the sender 
   sender.end()


Durable Channel
---------------
Durable Channel follows a queue model, where a message sent on a channel is picked up by any one of the receivers listening on the channel. Using DurableChannel, senders can send messages with a timeout, so they are informed when a message is not replied to within the specified timeout. Every message is guaranteed to be replied to within a specified timeout, if not, sender is informed via a callback.

Usage:
^^^^^^

.. code-block:: python

   from muppet import DurableChannel

   def timeout_callback(message):
     print "timed out:", message
     # we are done with the worker
     worker.end()
     # we are done with dispatcher
     dispatcher.end()

   # redis server details
   redis_options = {"redis": {"host": "127.0.0.1", "port": 6379}}
   # create a durable channel to dispatch messages
   dispatcher = DurableChannel("dispatcher.1", redis_options)
   # create a durable channel to receive messages, note the 3rd argument which is the callback for handling timeouts
   worker = DurableChannel("worker.1", redis_options, timeout_callback)

   # dispatch a message to worker.1
   dispatcher.send(content="task", to="worker.1")

   # receive the message
   message = worker.receive()
   print "received message:", message["content"]
   # reply to the message
   worker.reply(message=message, response="reply", timeout=5000)

   # receive the reply
   reply = dispatcher.receive()
   print "received reply:", reply["content"]
   
   # we are happy with the reply
   dispatcher.close(reply)

   # we are done with dispatcher and worker
   worker.end()
   dispatcher.end()
