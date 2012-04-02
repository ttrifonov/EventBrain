This example uses ampq-js tool(https://github.com/dansimpson/amqp-js) and shows how to display real-time CPU usage graph, using the CPU.CPU_usage actor class. First make sure to start the CPU.CPU_usage with launcher.py. Then follow these steps to display the graphics:

1. Make sure you run a policy server, as explained at https://github.com/dansimpson/amqp-js

2. Make the needed modifications in the html file for host/vhost/username/password(for some reason username/password doesn't seem to work in amqp-js, so use the default guest:guest).

3. Run this simple django site::
	``python manage.py runserver``

4. Load in browser test.html page, e.g. http://localhost:8000/test.html

