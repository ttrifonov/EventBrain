import logging
import psutil

from eventbrain.actor.base import ActorBase

LOG = logging.getLogger(__name__)


class CPU_usage(ActorBase):
    """
    Detects CPU usage
    """

    id = "cpu_peak"

    def on_update(self):
        LOG.info("On update %s" % (self.id))
        if self.channel.queue:
            cpu_usage = psutil.cpu_percent(interval=0)
            self.channel.queue.push(str(cpu_usage))


class CPU_user(ActorBase):
    """
    Detects User cpu usage
    """
    
    id = "cpu_user"

    def on_update(self):
        LOG.info("On update %s" % (self.id))
        if self.channel.queue:
            cpu_user = psutil.cpu_times().user
            self.channel.queue.push(str(cpu_user))


class CPU_system(ActorBase):
    """
    Detects System cpu usage
    """
    
    id = "cpu_sys"

    def on_update(self):
        LOG.info("On update %s" % (self.id))
        if self.channel.queue:
            cpu_sys = psutil.cpu_times().system
            self.channel.queue.push(str(cpu_sys))
