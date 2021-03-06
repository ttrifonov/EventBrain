import signal
import logging

#from eventbrain.contrib.rabbitmq.pika_wrapper import ChannelWrapper
from eventbrain.contrib.rabbitmq.kombu_wrapper import ChannelWrapper
from eventbrain.util.repeating_timer import RepeatingTimer

LOG = logging.getLogger(__name__)


class ActorBase(object):
    """
    Base class for Decision object. Defines common methods
    and properties, needed for a Decision class to operate
    with data, coming from the sources

    Arguments:

    .. interval::    Time in seconds between pushing data
                in the exchange/queue
    """

    exchange_type = 'topic'
    transport_class = ChannelWrapper

    def __init__(self, interval=5, **kwargs):
        self.interval = float(interval)
        assert self.id, "Actor 'id' property not set"
        self.channel = self.transport_class(self.id,
                                      self.exchange_type,
                                      publish=True,
                                      manual_ack=False,
                                      **kwargs)
        self._kwargs = kwargs
        self._create()

    def _create(self):
        """
        Called in the constructor, useful to be re-declared
        in a child classes to apply additional actions upon
        instance creation
        """
        pass

    def connect(self, **kwargs):
        """
        Connect to queue and start publishing data
        on the specified interval
        """
        signal.signal(signal.SIGTERM, self._on_signal_term)

        LOG.info("Starting ")
        self.timer = RepeatingTimer(self.interval, self.on_update)
        self.timer.start()
        self.channel.connect(**kwargs)

    def _on_signal_term(self, signum, frame):
        LOG.info('Received signal: %s' % signum)
        self.disconnect()

    def disconnect(self, **kwargs):
        if (hasattr(self, "timer") and self.timer):
            self.timer.stop()
        if (hasattr(self, "channel") and self.channel):
            if "reason" in kwargs.keys():
                LOG.info("Disconnected with reason: %s" % kwargs['reason'])
            self.channel.stop(**kwargs)

    def on_update(self):
        raise NotImplementedError("This should be implemented in parent class")
