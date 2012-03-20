import pika
import logging

LOG = logging.getLogger(__name__)


class ChannelWrapper(object):
    def __init__(self, channel_id, exchange_type, callback=None, 
                 publish=False, consume=False, **kwargs):
        self.channel_id = channel_id
        self.exchange_type = exchange_type
        self.callback = callback
        self.publish = publish
        self.consume = consume
        self._create(channel_id=channel_id, exchange_type=exchange_type,
                     callback=callback, publish=publish, 
                     consume=consume, **kwargs)

    def _create(self, channel_id, exchange_type, callback,
                publish, consume, **kwargs):
        self.queue = None
        
        def on_connected(connection):
            LOG.info("On connected")
            connection.channel(on_channel_open)

        def push(data):
            LOG.debug("Pushing data to %s" % channel_id)
            try:
                self.channel.basic_publish(exchange=channel_id,
                                           routing_key=channel_id,
                                           body=data)
            except Exception, ex:
                LOG.exception(unicode(ex))

        def on_channel_open(channel):
            LOG.info("On channel open")
            self.channel = channel
            self.queue = channel
            self.queue.push = push
            if publish:
                channel.exchange_declare(exchange=channel_id,
                                     type=exchange_type,
                                     callback=on_exchange_declared)
            else:
                channel.queue_declare(queue=channel_id,
                                      durable=True,
                                      exclusive=False,
                                      auto_delete=False,
                                      callback=on_queue_declared)

        def on_exchange_declared(frame):
            LOG.info("on_exchange_declared: got exchange")

        def on_queue_declared(frame):
            LOG.info("On queue declared")
            self.channel.queue_bind(exchange=channel_id,
                       queue=frame.method.queue,
                       routing_key="")
            self.channel.basic_consume(on_consume, queue=frame.method.queue)

        def on_consume(channel, method_frame, header_frame, body):
            if consume:
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

    def on_receive(self, channel, method, properties, body):
        if self.callback:
            self.callback(body,
                          method=method,
                          properties=properties)

    def connect(self, **kwargs):
        try:
            self.connection.ioloop.start()
        except:
            # retry
            self.connection.ioloop.stop()
            self.connection.close()
            self.connection.ioloop.start()
            self._create(channel_id=self.channel_id,
                         exchange_type=self.exchange_type,
                         callback=self.callback, publish=self.publish, 
                         consume=self.consume, **kwargs)
            self.connect(**kwargs)

    def stop(self):
        # connection.ioloop is blocking, this will stop and exit the app
        self.connection.ioloop.stop()
        # Close our connection
        self.connection.close()
