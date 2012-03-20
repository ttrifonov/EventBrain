###################################################################
EventBrain
###################################################################

EventBrain is a Python library to provide an easy configurable framework
for creating and configuring multiple nodes accross multiple servers(or cluster)
that perform simple tasks(a.k.a. actor) like parsing logs, checking system status,
applying custom logic, and send some chunks of data to RabbitMQ (or other
AMPQ-compatible queue management system), with the ability to attach 
multiple listeners(a.k.a. decision) which apply some logic and redirect 
the output to another actors, like notifyers, notification services or other.
The whole system relies on the exchanges and queues from AMPQ to define the 
domains of application - i.e. if a decision listener waits for peak load of 
average 90% for 5 min period - when it detects such event - it will fire a new
event to another exchange, and all actors, attached to that event will be 
responsible to perform the needed notification or other actor. Each node(either 
actor or decision) can be started on one or more machines, with the only 
requirement to have access to the main AMPQ.

###################################################################
Install
###################################################################

Install using:

``python setup.py install``

###################################################################
Run
###################################################################

To run an actor or decision(or any combination of objects),
use the launcher executable:

``eventbrain/bin/launcher.py --help``

Usage: launcher.py [options] start|stop|restart

Options:
  -h, --help            show this help message and exit
  -t TYPE, --type=TYPE  type of object to process('actor', 'a' or 'decision',
                        'd')
  -i ID, --id=ID        Id of the object to process
  -p PID_DIR, --pid-dir=PID_DIR
                        Directory to store pid files for daemonized objects.
                        Default path is /var/run/eventbrain/
  -l LOGFILE, --log-file=LOGFILE
                        File to write logs. Default is /dev/null
  -d, --daemonize       Start in daemon mode
  -c CONFIG, --config=CONFIG
                        Config file with initial settings. If a config file is
                        provided, other parameters are ignored.

  RabbitMQ options:
    -s HOST, --server=HOST
                        RabbitMQ server. Default is localhost
    -u USER, --user=USER
                        RabbitMQ credentials: username
    -w PASSWORD, --password=PASSWORD
                        RabbitMQ credentials: password

To start a single actor, use the following command:

``eventbrain/bin/launcher.py --type=actor --id=CPU.CPU_usage --daemonize --pid-dir=/path/to/pid --log-file=/path/to/logs/some.log start``

The -d(--daemonize) option will start the actor in daemon mode, otherwise will be started in blocking mode.

You can see an example config file in eventbrain/bin/example.conf. Using a config file gives you the
ability to start multiple actors/decisions on a single server.

You can describe each actor/decision in a single section, having the name of the module.class to be executed.
Along with default options like type, log_file, pid_dir, you can pass various parameters, which will be
passed in the class constructor when initializing it.

Example config::
    [CPU.CPU_usage]

    type=actor
    
    log_file=/var/log/cpu_usage.log
    
    pid_dir=/var/run/
    
    interval=3
    
    daemonize=true
    
    
    [CPU.CPU_peak]
    
    type=decision
    
    log_file=/var/log/cpu_peak.log
    
    pid_dir=/var/run/
    
    interval=3
    
    threshold=10
    
    daemonize=true


Running launcher with a config file is simple:

``eventbrain/bin/launcher.py --config=/path/to/config.conf start``
