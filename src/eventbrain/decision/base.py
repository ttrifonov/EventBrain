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
    
    ::queue_type::    Base class for the queue. Should support
        obj.append method

    ::period:: Integer, the period to collect statistics
            in seconds
                
    ::threshold::    Threshold value to fire an event. 
            Depends on the aggregate_type

    ::eval_func:: Function for evaluation logic. 
            Should accept iterable values and return
            threshold-comparable value 
    """
    
    exchange_type = 'fanout'
     
    def __init__(self, period, threshold, eval_func, queue_type=dict,
                 **kwargs):
        self.period = int(period)
        self.threshold = float(threshold)
        self.eval_func = eval_func
        self.queue = queue_type()
        self.fired = False
        assert self.id, "Decision id not defined"
        self.channel = ChannelWrapper(self.id, 
                                      self.exchange_type, 
                                      self.on_update,
                                      publish=False,
                                      consume=True,
                                      **kwargs)
        
    def connect(self, **kwargs):
        """
        Connect to queue and start consuming
        """
        self.timer = RepeatingTimer(self.period, lambda: self.evaluate(**kwargs))
        self.timer.start()
        self.channel.connect(**kwargs)

    def disconnect(self, **kwargs):
        pass
        
    def evaluate(self, *args, **kwargs):
        self.clean_queue(**kwargs)
        eval_value = self.eval_func(self.queue.values()) 
        if eval_value >= self.threshold:
            if not self.fired:
                # Fire if not already fired
                self.fired = True
                self.fire(eval_value)
        else:
            self.fired = False

    def preprocess(self, data, **kwargs):
        return data

    def on_update(self, data, **kwargs):
        LOG.info("Received data %s" % data)
        self.queue[datetime.now()] = self.preprocess(data, **kwargs)

    def fire(self, eval_value, *args, **kwargs):
        raise NotImplementedError("This should be implemented in parent class")

    def clean_queue(self, **kwargs):
        """
        Performs a default clean, assuming the keys are timestamp values
        """
        timestamps = sorted(self.queue.keys())
        for timestamp in timestamps:
            if (datetime.now() - timestamp).seconds > self.period:
                self.queue.pop(timestamp)
            else:
                break
