###################################################################
EventBrain
###################################################################

EventBrain is a Python library to provide an easy configurable framework
for creating and configuring multiple nodes accross multiple servers(or cluster)
that perform simple tasks(a.k.a. action) like parsing logs, checking system status,
applying custom logic, and send some chunks of data to RabbitMQ (or other
AMPQ-compatible queue management system), with the ability to attach 
multiple listeners(a.k.a. decision) which apply some logic and redirect 
the output to another actions, like notifyers, notification services or other.
The whole system relies on the exchanges and queues from AMPQ to define the 
domains of application - i.e. if a decision listener waits for peak load of 
average 90% for 5 min period - when it detects such event - it will fire a new
event to another exchange, and all actions, attached to that event will be 
responsible to perform the needed notification or other action. Each node(either 
action or decision) can be started on one or more machines, with the only 
requirement to have access to the main AMPQ.
