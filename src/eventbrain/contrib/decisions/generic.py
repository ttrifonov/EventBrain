import logging

from eventbrain.decision.base import DecisionBase

LOG = logging.getLogger(__name__)


class EchoListener(DecisionBase):
    """
    A basic class to detect CPU peaks. Initial threshold is
    max 90% load over 5 min period.
    """

    id = "echo-listener"

    def __init__(self, interval=10, threshold=90.0, **kwargs):
        if "id" not in kwargs:
            LOG.error("exchange parameter (id=...) not specified!")
            return

        self.id = kwargs['id']
        super(EchoListener, self).__init__(interval, 
                                       threshold, 
                                       self.fake_func, **kwargs)

    def fake_func(self, items):
        return 100

    def fire(self, sender, value, *args, **kwargs):
        LOG.info("Basic listener sender:[%s]" % sender)
        self.escalate(sender, "notify-email", value)
        self.fired = False
