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
    
    exchange_type = 'fanout'

    def __init__(self, interval=5, **kwargs):
        self.interval = int(interval)
        assert self.id, "Actor 'id' property not set"
        self.channel = ChannelWrapper(self.id, 
                                      self.exchange_type,
                                      publish=True,
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
        self.timer.stop()
        self.channel.stop()

    def on_update(self, queue):
        raise NotImplementedError("This should be implemented in parent class")
