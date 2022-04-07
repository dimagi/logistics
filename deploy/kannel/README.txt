Setting up  kannel on a new machine:

Install kannel:

$ sudo apt-get install kannel

Turn off the wap box, turn on the smsbox:

edit: /etc/default/kannel and comment/uncomment START_xxxBOX.

Initialize Malawi config files:

$ sudo cp kannel.conf /etc/kannel/kannel.conf
 
Edit the /etc/kannel/kannel.conf files and fix relevant credentials.

Restart kannel:

$ sudo /etc/init.d/kannel restart

Send sms!
