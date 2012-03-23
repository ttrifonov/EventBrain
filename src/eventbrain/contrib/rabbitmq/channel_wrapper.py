import pika
import logging

LOG = logging.getLogger(__name__)


class ChannelWrapper(object):
    def __init__(self, channel_id, exchange_type, callback=None, 
                 publish=False, manual_ack=False, **kwargs):
        self.channel_id = channel_id
        self.exchange_type = exchange_type
        self.callback = callback
        self.publish = publish
        self.manual_ack = manual_ack
        self._create(channel_id=channel_id, exchange_type=exchange_type,
                     callback=callback, publish=publish, 
                     manual_ack=manual_ack, **kwargs)

    def _create(self, channel_id, exchange_type, callback,
                publish, manual_ack, **kwargs):
        self.queue = None
        
        def on_connected(connection):
            LOG.info("Connected")
            connection.channel(on_channel_open)

        def on_closed(frame):
            self.connection.ioloop.stop()

        def push(data):
            LOG.debug("Pushing data to %s" % channel_id)
            try:
                self.channel.basic_publish(exchange=channel_id,
                                           routing_key=channel_id,
                                           body=data)
            except Exception, ex:
                LOG.exception(unicode(ex))

        def on_channel_open(channel):
            LOG.info("Channel open")
            self.channel = channel
            self.queue = channel
            self.queue.push = push  
            channel.exchange_declare(exchange=channel_id,
                                     type=exchange_type,
                                     callback=on_exchange_declared)

        def on_exchange_declared(frame):
            LOG.info("Exchange_declared: got exchange")
            if not publish:
                # We have a decision, or listener, bind a queue
                self.channel.queue_declare(durable=True,
                                      exclusive=False,
                                      auto_delete=False,
                                      callback=on_queue_declared)

        def on_queue_declared(frame):
            LOG.info("Queue declared on exchange %s[%s]" % (
                                                            channel_id,
                                                            exchange_type))
            self.channel.queue_bind(exchange=channel_id,
                       queue=frame.method.queue,
                       routing_key="")
            self.channel.basic_consume(on_consume, no_ack=not manual_ack,
                                       queue=frame.method.queue)

        def on_consume(channel, method_frame, header_frame, body):
            if manual_ack:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            self.on_receive(channel_id, method_frame, header_frame, body)

        self.host = kwargs.get('host', "localhost")
        if "user" in kwargs.keys() and "password" in kwargs.keys():
            self.user = kwargs['user']
            self.password = kwargs['password']
            credentials = pika.PlainCredentials(self.user, self.password)
            params = pika.ConnectionParameters(host=self.host,
                                               credentials=credentials)
        else:
            params = pika.ConnectionParameters(host=self.host)
        self.connection = pika.SelectConnection(params,
                                                on_open_callback=on_connected)
        self.connection.add_on_close_callback(on_closed)

    def on_receive(self, channel, method, properties, body):
        if self.callback:
            self.callback(body,
                          method=method,
                          properties=properties)

    def connect(self, **kwargs):
        try:
            self.connection.ioloop.start()
        except Exception, ex:
            LOG.exception("Channel error: %r" % str(ex))
            # retry
            self.connection.ioloop.stop()
            self.connection.close()
            self.connection.ioloop.start()
            self._create(channel_id=self.channel_id,
                         exchange_type=self.exchange_type,
                         callback=self.callback, publish=self.publish, 
                         manual_ack=self.manual_ack, **kwargs)
            self.connect(**kwargs)

    def stop(self, **kwargs):
        # connection.ioloop is blocking, this will stop and exit the app
        if (self.connection):
            LOG.info("Closing connection")
            self.connection.close()
            # Loop until we're fully closed, will stop on its own
            #self.connection.ioloop.start()
