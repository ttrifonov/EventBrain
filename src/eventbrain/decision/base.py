import logging
from datetime import datetime, timedelta

from exceptions import NotImplementedError

from eventbrain.contrib.rabbitmq.channel_wrapper import ChannelWrapper
from eventbrain.util.repeating_timer import RepeatingTimer

LOG = logging.getLogger(__name__)


class DecisionBase(object):
    """
    Base class for Decision object. Defines common methods
    and properties, needed for a Decision class to operate
    with data, coming from the sources
    
    Arguments:
    
    ::period:: Integer, the period to collect statistics
            in seconds

    ::threshold::    Threshold value to fire an event. 
            Depends on the aggregate_type

    ::eval_func:: Function for evaluation logic. 
            Should accept iterable values and return
            threshold-comparable value 
    """
    
    exchange_type = 'topic'
     
    def __init__(self, period, threshold, eval_func,
                 **kwargs):
        self.period = int(period)
        self.threshold = float(threshold)
        self.eval_func = eval_func
        self.queue = dict()
        self.fired = False
        assert self.id, "Decision id not defined"
        self.channel = ChannelWrapper(self.id, 
                                      self.exchange_type, 
                                      self.on_update,
                                      publish=False,
                                      manual_ack=False,
                                      **kwargs)
        
    def connect(self, **kwargs):
        """
        Connect to queue and start consuming
        """
        if (hasattr(self, "channel") and self.channel):
            self.timer = RepeatingTimer(self.period, lambda: self.evaluate(**kwargs))
            self.timer.start()
            self.channel.connect(**kwargs)

    def disconnect(self, **kwargs):
        if (hasattr(self, "timer") and self.timer):
            self.timer.stop()
        if (hasattr(self, "channel") and self.channel):
            if "reason" in kwargs.keys():
                LOG.info("Disconnected with reason: %s" % kwargs['reason'])
            self.channel.stop(**kwargs)
        
    def evaluate(self, *args, **kwargs):
        for (sender, values) in self.queue.items():
            self.clean_queue_values(values, **kwargs)
            eval_value = self.eval_func(values.values())
            if eval_value >= self.threshold:
                if not self.fired:
                    # Fire if not already fired
                    self.fired = True
                    self.fire(sender, eval_value)
        else:
            self.fired = False

    def preprocess(self, data, **kwargs):
        return data

    def on_update(self, sender, data, **kwargs):
        LOG.info("Received data from %s:[%s] : %s" % (self.id,
                                                   sender,
                                                   data))
        self.queue.setdefault(sender, {})[datetime.now()] = self.preprocess(data, **kwargs)

    def fire(self, sender, eval_value, *args, **kwargs):
        raise NotImplementedError("This should be implemented in parent class")

    def clean_queue_values(self, values, **kwargs):
        """
        Performs a default clean, assuming the keys are timestamp values
        """
        keys = sorted(values.keys())
        for timestamp in keys:
            if (datetime.now() - timestamp).seconds > self.period:
                values.pop(timestamp)
            else:
                break

    def escalate(self, sender, receiver, data):
        # Used to escalate decision result to another queue
        pub_channel = ChannelWrapper(self.id,
                                      self.exchange_type,
                                      publish=True)
        pub_channel.publish_once(sender, receiver, data)
