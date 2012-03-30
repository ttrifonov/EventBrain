import logging

from eventbrain.decision.base import DecisionBase

LOG = logging.getLogger(__name__)


class Mailer(DecisionBase):
    """
    A basic class to send email notifications.
    """

    id = "notify-email"

    def __init__(self, interval=5, threshold=1.0, **kwargs):
        kwargs.update({'match_all': True})
        super(Mailer, self).__init__(interval, 
                                     threshold, 
                                     self.fake_func,
                                     **kwargs)

    def fake_func(self, items):
        return 0

    def fire(self, sender, value, *args, **kwargs):
        LOG.info("Mailer: [%s]" % sender)
