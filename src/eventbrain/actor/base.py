import logging

from eventbrain.contrib.rabbitmq.channel_wrapper import ChannelWrapper
from eventbrain.util.repeating_timer import RepeatingTimer

LOG = logging.getLogger(__name__)


class ActorBase(object):
    """
    Base class for Decision object. Defines common methods
    and properties, needed for a Decision class to operate
    with data, coming from the sources
    
    Arguments:
    
    ::interval::    Time in seconds between pushing data 
                in the exchange/queue
    """
    
    exchange_type = 'topic'

    def __init__(self, interval=5, **kwargs):
        self.interval = int(interval)
        assert self.id, "Actor 'id' property not set"
        self.channel = ChannelWrapper(self.id, 
                                      self.exchange_type,
                                      publish=True,
                                      manual_ack=False,
                                      **kwargs)
        
    def connect(self, **kwargs):
        """
        Connect to queue and start publishing data
        on the specified interval
        """

        LOG.info("Starting ")
        self.timer = RepeatingTimer(self.interval, self.on_update)
        self.timer.start()
        self.channel.connect(**kwargs)

    def disconnect(self, **kwargs):
        if (hasattr(self, "timer") and self.timer):
            self.timer.stop()
        if (hasattr(self, "channel") and self.channel):
            if "reason" in kwargs.keys():
                LOG.info("Disconnected with reason: %s" % kwargs['reason'])
            self.channel.stop(**kwargs)

    def on_update(self):
        raise NotImplementedError("This should be implemented in parent class")
