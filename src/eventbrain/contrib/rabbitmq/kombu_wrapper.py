from kombu import BrokerConnection, Exchange, Queue
from kombu.messaging import Producer, Consumer
import logging

LOG = logging.getLogger(__name__)


class ChannelWrapper(object):
    """
    Wrapper for pika library for AMQP
    """
    reconnect_timeout = 3

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
        self.stopping = False

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

        self.protocol = kwargs.get('protocol', "amqplib")
        self.host = kwargs.get('host', "localhost")
        self.port = int(kwargs.get('port', 5672))
        self.vhost = kwargs.get("vhost", "/")
        self.use_ssl = kwargs.get('use_ssl', False)

        if "user" in kwargs.keys() and "password" in kwargs.keys():
            self.user = kwargs['user']
            self.password = kwargs['password']
            self.auth_str = "%s:%s@" % (self.user, self.password)
        else:
            self.auth_str = ""

    def _reconnect(self):
        LOG.info("Trying reconnect...")

    def connect(self, **kwargs):
        self.connection_kwargs = kwargs
        LOG.info("Connecting to %s://%s%s:%s/%s" % (self.protocol,
                                                    self.auth_str,
                                                    self.host,
                                                    self.port,
                                                    self.vhost))
        self.connection = BrokerConnection(hostname=self.host,
                                           userid=self.user,
                                           password=self.password,
                                           virtual_host=self.vhost,
                                           port=self.port,
                                           transport=self.protocol,
                                           ssl=self.use_ssl)
        self.connection.connect()
        self.channel = self.connection.channel()

        LOG.info("Declaring exchange %s of type %s" % (self.channel_id,
                                                       self.exchange_type))
        self.exchange = Exchange(self.channel_id,
                                 type=self.exchange_type,
                                 auto_declare=True,
                                 channel=self.channel)

        if self.publish:
            self.queue = self.channel
            self.producer = Producer(self.channel,
                                     self.exchange,
                                     self.routing_key)

            def push(sender, data):
                LOG.info("Pushing data from [%s]:%s to exc: %s" % \
                          (sender,
                           "%s%s" % (self.routing_key + "." if
                                     self.routing_key else "",
                                     sender),
                           self.channel_id))
                try:
                    self.producer.publish(data,
                                          "%s%s" % (self.routing_key + "." if
                                                    self.routing_key else "",
                                                    sender),
                                          exchange=self.channel_id)
                except Exception, ex:
                    LOG.exception(unicode(ex))
                    self._reconnect()
            self.channel.push = push
            self.producer.declare()

            self._loop()
        else:
            if (self.routing_wildcard_match):
                if (self.routing_key):
                    routing_key = "%s.#" % self.routing_key
                else:
                    routing_key = "#"
            else:
                routing_key = self.routing_key

            LOG.info("Declaring consumer on %s for %s" % (self.channel_id,
                                                          routing_key))

            self.queue = Queue("q", exchange=self.exchange,
                               channel=self.channel,
                               routing_key=routing_key)
            self.queue.queue_declare()

            def read_queue(body, message):
                if self.manual_ack:
                    message.ack()
                if self.callback:
                    self.callback(message.delivery_info.get("routing_key", ""),
                                  body)
            with Consumer(self.channel,
                          [self.queue],
                          no_ack=not self.manual_ack,
                          callbacks=[read_queue]):
                self._loop()

    def _loop(self):
        try:
            LOG.info("Entering loop")
            while True:
                self.connection.drain_events()
        except Exception, ex:
            LOG.exception("Channel error: %r" % str(ex))
            # retry
            if not self.stopping:
                self.connect(**self.connection_kwargs)

    def stop(self, **kwargs):
        self.stopping = True
        # connection.ioloop is blocking, this will stop and exit the app
        if (self.connection):
            LOG.info("Closing connection")
            self.connection.release()
            self.connection.close()

    def publish_once(self, sender, receiver, data):
        LOG.info("Escalating from %s to %s" % (sender, receiver))

        try:
            (exch, _) = self._parse_id(receiver)
            esc_channel = self.connection.channel()

            esc_exchange = Exchange(exch,
                                    type=self.exchange_type,
                                    auto_declare=True,
                                    channel=esc_channel)
            message = esc_exchange.Message(data)
            esc_exchange.publish(message, sender, exchange=exch)
        except Exception, ex:
            LOG.exception(ex)
