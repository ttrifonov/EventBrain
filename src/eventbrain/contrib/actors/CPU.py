import logging
import psutil
from socket import gethostname

from eventbrain.actor.base import ActorBase

LOG = logging.getLogger(__name__)


class CPU_usage(ActorBase):
    """
    Detects CPU usage
    """

    id = "cpu"

    def on_update(self):
        sender = gethostname()
        LOG.info("On update %s:%s" % (self.id,
                                   sender))
        if self.channel.queue:
            cpu_usage = psutil.cpu_percent(interval=0)
            self.channel.queue.push(sender, str(cpu_usage))
        else:
            LOG.info("No queue available for: %s" % (self.id))


class CPU_user(ActorBase):
    """
    Detects User cpu usage
    """
    
    id = "cpu:times:user"

    def on_update(self):
        sender = gethostname()
        LOG.info("On update %s:%s" % (self.id,
                                   sender))
        if self.channel.queue:
            cpu_user = psutil.cpu_times().user
            self.channel.queue.push(sender, str(cpu_user))


class CPU_system(ActorBase):
    """
    Detects System cpu usage
    """
    
    id = "cpu"

    def on_update(self):
        sender = gethostname()
        LOG.info("On update %s:%s" % (self.id,
                                   sender))
        if self.channel.queue:
            cpu_sys = psutil.cpu_times().system
            self.channel.queue.push(sender, str(cpu_sys))
