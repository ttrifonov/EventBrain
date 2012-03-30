import pika
import logging

LOG = logging.getLogger(__name__)


class ChannelWrapper(object):
    def __init__(self, channel_id, exchange_type, callback=None, 
                 publish=False, manual_ack=False, **kwargs):
        (exch, rtg_key) = self._parse_id(channel_id)
        self.routing_wildcard_match = "match_all" in kwargs and \
                kwargs['match_all']
        self.channel_id = exch
        self.routing_key = rtg_key
        self.exchange_type = exchange_type
        self.callback = callback
        self.publish = publish
        self.manual_ack = manual_ack
        self._create(channel_id=self.channel_id, exchange_type=exchange_type,
                     callback=callback, publish=publish, 
                     manual_ack=manual_ack, **kwargs)

    def _parse_id(self, id):
        if (":" in id):
            # break to exchange and rtg key
            tokens = id.split(":")
        else:
            tokens = [id]

        return (tokens[0], ".".join(tokens[1:]))

    def _create(self, channel_id, exchange_type, callback,
                publish, manual_ack, **kwargs):
        self.queue = None
        
        def on_connected(connection):
            LOG.info("Connected to %s:%s" % (self.host,
                                             self.vhost))
            connection.channel(on_channel_open)

        def on_closed(frame):
            self.connection.ioloop.stop()

        def push(sender, data):
            LOG.debug("Pushing data from [%s]:%s to exc: %s" % \
                      (self.channel_id,
                       self.routing_key,
                       sender))
            try:
                self.channel.basic_publish(exchange=self.channel_id,
                           routing_key="%s%s" % (self.routing_key + "." if 
                                                 self.routing_key else "",
                                                 sender),
                                           body=data)
            except Exception, ex:
                LOG.exception(unicode(ex))
                self._reconnect()

        def on_channel_open(channel):
            LOG.info("Channel open")
            self.channel = channel
            self.queue = channel
            self.queue.push = push
            self.queue.escalate = self.publish_once  
            channel.exchange_declare(exchange=self.channel_id,
                                     type=exchange_type,
                                     callback=on_exchange_declared)

        def on_exchange_declared(frame):
            LOG.info("Exchange_declared: %s" % self.channel_id)
            if not publish:
                # We have a decision, or listener, bind a queue
                self.channel.queue_declare(durable=True,
                                      exclusive=False,
                                      auto_delete=False,
                                      callback=on_queue_declared)

        def on_queue_declared(frame):
            LOG.info("Queue declared on exchange %s:%s  [%s]" % (
                                                    self.channel_id,
                                                    self.routing_key,
                                                    exchange_type))
            if (self.routing_wildcard_match):
                if (self.routing_key):
                    routing_key = "%s.#" % self.routing_key
                else:
                    routing_key = "#" 
            else:
                routing_key = self.routing_key
            self.channel.queue_bind(exchange=self.channel_id,
                       queue=frame.method.queue,
                       routing_key=routing_key)
            self.channel.basic_consume(on_consume, no_ack=not manual_ack,
                                       queue=frame.method.queue)

        def on_consume(channel, method_frame, header_frame, body):
            if manual_ack:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            self.on_receive(self.channel_id, method_frame, header_frame, body)

        self.host = kwargs.get('host', "localhost")
        self.vhost = kwargs.get("vhost", "/")
        params = pika.ConnectionParameters(host=self.host,
                                           virtual_host=self.vhost)
        if "user" in kwargs.keys() and "password" in kwargs.keys():
            self.user = kwargs['user']
            self.password = kwargs['password']
            credentials = pika.PlainCredentials(self.user, self.password)
            params.credentials = credentials

        self.params = params

        self.connection = pika.SelectConnection(params,
                                                on_open_callback=on_connected)
        self.connection.add_on_close_callback(on_closed)

    def _reconnect(self):
        self.connection.ioloop.stop()
        self.connection.close()
        self._create(channel_id=self.channel_id,
                     exchange_type=self.exchange_type,
                     callback=self.callback, publish=self.publish, 
                     manual_ack=self.manual_ack, **self.connection_kwargs)
        self.connect(**self.connection_kwargs)

    def on_receive(self, channel, method, properties, body):
        if self.callback:
            self.callback(method.routing_key,
                          body,
                          method=method,
                          properties=properties)

    def connect(self, **kwargs):
        try:
            self.connection_kwargs = kwargs
            self.connection.ioloop.start()
        except Exception, ex:
            LOG.exception("Channel error: %r" % str(ex))
            # retry
            if not self.connection.closing:
                self._reconnect(**self.connection_kwargs)

    def stop(self, **kwargs):
        # connection.ioloop is blocking, this will stop and exit the app
        if (self.connection):
            LOG.info("Closing connection")
            self.connection.ioloop.stop()
            self.connection.close()

    def publish_once(self, sender, receiver, data):
        LOG.info("Escalating from %s to %s" % (sender, receiver))

        (exch, _) = self._parse_id(receiver)
        def on_exchange(frame):
            self.channel.basic_publish(exchange=exch,
                              routing_key=sender,
                              body=data)

        self.channel.exchange_declare(exchange=exch,
                                     type='topic',
                                     callback=on_exchange)
