#!/usr/bin/env python
# file: launcher.py

import os
import sys
import logging
from optparse import OptionParser, OptionGroup
from eventbrain.util.daemon import Daemon

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

usage = "Usage: %prog [options] start|stop|restart"

def set_daemonize(option, opt_str, value, parser):
    parser.values.daemonize = True


parser = OptionParser(usage=usage)

parser.add_option("-t", "--type", dest="type",
                  help="type of object to process('actor', 'a' "
                  "or 'decision', 'd')")
parser.add_option("-i", "--id", dest="Id",
                  help="Id of the object to process")
parser.add_option("-p", "--pid-dir", dest="pid_dir", 
                  default="/var/run/eventbrain/",
                  help="Directory to store pid files for daemonized objects. "
                  "Default path is %default")
parser.add_option("-l", "--log-file", dest="logfile", default='/dev/null',
                  help="File to write logs. Default is %default")
parser.add_option("-d", "--daemonize", dest="daemonize", action="callback", 
                  callback=set_daemonize, default=False,
                  help="Start in daemon mode")
parser.add_option("-o", "--options", dest="opts", 
                  default=None,
                  help="Additional options to send to the class constructor")
parser.add_option("-c", "--config", dest="config", 
                  default=None,
                  help="Config file with initial settings. "
                  "If a config file is provided, "
                  "other parameters are ignored.")

server_opts = OptionGroup(parser, "RabbitMQ options")

server_opts.add_option("-s", "--server", dest="host", default='localhost',
                  help="RabbitMQ server. Default is %default")
server_opts.add_option("-u", "--user", dest="user", 
                 help="RabbitMQ credentials: username")
server_opts.add_option("-w", "--password", dest="password", 
                 help="RabbitMQ credentials: password")

parser.add_option_group(server_opts)

(options, args) = parser.parse_args()
commands = ('start', 'stop', 'restart')
types = ('actor', 'a', 'decision', 'd')
command = args[0]


class DaemonRunner(Daemon):
    def run(self):
        print "Run"
        if hasattr(options, "kwargs"):
            kwargs = options.kwargs
        else:
            kwargs = {}

        if options.opts:
            (k, v) = options.opts.split("=")
            kwargs[k] = v

        print "kwargs", kwargs

        if options.user and options.password:
            kwargs['user'] = options.user 
            kwargs['password'] = options.password
        if options.host:
            kwargs['host'] = options.host  
        inst = self.klass(**kwargs)
        try:
            inst.connect()
        except KeyboardInterrupt:
            inst.disconnect(reason="keyboard interruption")


def run_actor(obj_id):
    print "Starting actor %s" % obj_id
    klass = _import('actors', obj_id)
    print "Found actor with exchange %s" % klass.id
    if options.daemonize:
        daemon = DaemonRunner(pid_file('a', klass),
                              stdout=options.logfile,
                              stderr=options.logfile)
        daemon.klass = klass
        daemon.start()
    else:
        kwargs = {}
        if options.user and options.password:
            kwargs['user'] = options.user 
            kwargs['password'] = options.password
        if options.host:
            kwargs['host'] = options.host  
        if options.opts:
            (k, v) = options.opts.split("=")
            kwargs[k] = v
            print "kwargs", kwargs
        inst = klass(**kwargs)
        try:
            inst.connect()
        except KeyboardInterrupt:
            inst.disconnect(reason="keyboard interruption")
    print "Done"


def stop_actor(obj_id):
    print "Stopping actor %s" % obj_id
    klass = _import('actors', obj_id)
    daemon = DaemonRunner(pid_file('a', klass))
    daemon.stop()
    print "Done"


def run_decision(obj_id):
    print "Starting decision %s" % obj_id
    klass = _import('decisions', obj_id)
    print "Found decision with exchange %s" % klass.id

    if options.daemonize:
        daemon = DaemonRunner(pid_file('d', klass),
                              stdout=options.logfile,
                              stderr=options.logfile)
        daemon.klass = klass
        daemon.start()
    else:
        kwargs = {}
        if options.user and options.password:
            kwargs['user'] = options.user 
            kwargs['password'] = options.password
        if options.host:
            kwargs['host'] = options.host  
        if options.opts:
            (k, v) = options.opts.split("=")
            kwargs[k] = v
            print "kwargs", kwargs
        inst = klass(**kwargs)
        try:
            inst.connect()
        except KeyboardInterrupt:
            inst.disconnect(reason="keyboard interruption")
    print "Done"


def stop_decision(obj_id):
    print "Stopping decision %s" % obj_id
    klass = _import('decisions', obj_id)
    daemon = DaemonRunner(pid_file('d', klass))
    daemon.stop()
    print "Done"


def pid_file(prefix, klass):
    pidfile = os.path.join(options.pid_dir, "".join([prefix,
                                                     '-', 
                                                     klass.id, 
                                                     ".pid"]))
    pidfile = os.path.abspath(pidfile)
    print "PID file: %s" % pidfile
    return pidfile


def _import(scope, obj_id):
    try:
        (_mod, _klass) = obj_id.split('.')
        module = __import__('eventbrain.contrib.%s.%s' % (scope, 
                                                          _mod), 
                            fromlist=[_klass])
        klass = getattr(module, _klass)
    except Exception, ex:
        print "Cannot import class %s\n%r" % (obj_id, ex)
        exit(1)
    return klass


def from_config():
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.readfp(open(options.config))
    sections = config.sections()

    if config.has_section("Main"):
        if config.has_option("Main", "host"):
            parser.values.host = config.get("Main", "host")
        if config.has_option("Main", "user"):
            parser.values.user = config.get("Main", "user")
        if config.has_option("Main", "password"):
            parser.values.password = config.get("Main", "password")

    for section in sections:
        print ">>> Found section ", section
        if section == "Main":
            continue
        else:
            # Fork to avoid exiting from main thread after daemonizing
            fpid = os.fork()
            if fpid != 0:
                process_section(config, section)
                exit(0)
            else:
                continue
    return True


def process_section(config, section):
    if config.has_option(section, "type"):
        _type = config.get(section, "type")
        if _type not in types:
            print "Unrecognized type: %s" % _type
            return False
        kwargs = {}
        for item in config.items(section):
            if item[0] == "daemonize":
                parser.values.daemonize = config.getboolean(section,
                                                            "daemonize")
            elif item[0] == "pid_dir":
                parser.values.pid_dir = item[1]
            elif item[0] == "log_file":
                parser.values.logfile = item[1]
            else:
                kwargs[item[0]] = item[1]
        print "kwargs", kwargs
        parser.values.kwargs = kwargs

        if _type in ('actor', 'a'):
            if command == "start":
                run_actor(section)
            elif command == "stop":
                stop_actor(section)
            elif command == "restart":
                stop_actor(section)
                run_actor(section)
        elif _type in ('decision', 'd'):
            if command == "start":
                run_decision(section)
            elif command == "stop":
                stop_decision(section)
            elif command == "restart":
                stop_decision(section)
                run_decision(section)


if __name__ == "__main__":
    if options.config:
        if from_config():
            exit(0)
        else:
            exit(1)

    if not options.type:
        print "Type not specified"
        exit(1)

    if options.type not in types:
        print "Unrecognized type: %s" % options.type
        exit(1)

    if not options.Id:
        print "Id not specified"
        exit(1)

    if not args or args[0] not in commands:
        print "Unknown command %s" % ",".join(args)
        exit(1)

    if options.type in ('actor', 'a'):
        # Actor
        if command == "start":
            run_actor(options.Id)
        elif command == "stop":
            stop_actor(options.Id)
        elif command == "restart":
            stop_actor(options.Id)
            run_actor(options.Id)

    if options.type in ('decision', 'd'):
        # Decision
        if command == "start":
            run_decision(options.Id)
        elif command == "stop":
            stop_decision(options.Id)
        elif command == "restart":
            stop_decision(options.Id)
            run_decision(options.Id)
