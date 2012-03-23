import logging

from eventbrain.decision.base import DecisionBase

LOG = logging.getLogger("CPU Peak")


class CPU_peak(DecisionBase):
    """
    A basic class to detect CPU peaks. Initial threshold is
    max 90% load over 5 min period.
    """

    id = "cpu_peak"
    
    def __init__(self, interval=5*60, threshold=90.0, **kwargs):
        super(CPU_peak, self).__init__(interval, 
                                       threshold, 
                                       self.calculate_peak, **kwargs)

    def calculate_peak(self, items):
        if not items:
            return 0
        return sum([float(item) for item in items]) / float(len(items))
        
    def fire(self, value, *args, **kwargs):
        LOG.info("Detected CPU Peak: %.2f%% average, "
                 "with threshold %.2f%% for %s seconds !!" % (value,
                                                           self.threshold,
                                                           self.period))
