#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.backends.http import RapidHttpBackend
from django.http import HttpResponse
import datetime
import urllib2

class PushBackend(RapidHttpBackend):
    """
    A RapidSMS backend for PUSH SMS
    
    Example POST:
    
    RemoteNetwork=celtel-tz&IsReceipt=NO&BSDate-tomorrow=20101009&Local=*15522&ReceiveDate=2010-10-08%2016:46:22%20%2B0000&BSDate-today=20101008&ClientID=1243&MessageID=336876061&ChannelID=9840&ReceiptStatus=&ClientName=OnPoint%20-%20TZ&Prefix=JSI&MobileDevice=&BSDate-yesterday=20101007&Remote=%2B255785000017&MobileNetwork=celtel-tz&State=11&ServiceID=124328&Text=test%203&MobileNumber=%2B255785000017&NewSubscriber=NO&RegType=1&Subscriber=%2B255785000017&ServiceName=JSI%20Demo&Parsed=&BSDate-thisweek=20101004&ServiceEndDate=2010-10-30%2023:29:00%20%2B0300&Now=2010-10-08%2016:46:22%20%2B0000
    
    """
    
    OUTBOUND_SMS_TEMPLATE = """
    <methodCall>
        <methodName>EAPIGateway.SendSMS</methodName>
        <params>
            <param>
                <value>
                    <struct>
                        <member>
                            <name>Password</name>
                            <value>%(password)s</value>
                        </member>
                        <member>
                            <name>Channel</name>
                            <value><int>%(channel)s</int></value>
                        </member>
                        <member>
                            <name>Service</name>
                            <value><int>%(service)s</int>
                            </value>
                        </member>
                        <member>
                            <name>SMSText</name>
                            <value>(text)s</value>
                        </member>
                        <member>
                            <name>Numbers</name>
                            <value>(number)s</value>
                        </member>                        
                    </struct>
                </value>
            </param>
        </params>
    </methodCall>    
    """
        
    def configure(self, host="localhost", port=8080, config={}, **kwargs):
        for key in ["url", "channel", "service", "password"]:
            if key not in config:
                raise ValueError("You are missing required config parameter: %s" % key)
        self.config = config
        super(PushBackend, self).configure(host, port, **kwargs)

    def handle_request(self, request):
        if request.method != 'POST':
            return HttpResponse('Not a post!')
        self.debug('This is the PUSH inbound POST data: %s' % request.raw_post_data)
        message = self.message(request.POST)
        if message:
            self.route(message)
        # We may need to return some XML here, but the current config 
        # is sending URL-encoded POST data and not XML, so we'll just 
        # send back a 200 OK
        return HttpResponse('OK')
    
    def get_url(self):
        return self.config["url"]
            
    def get_channel(self):
        return self.config["channel"]
        
    def get_service(self):
        return self.config["service"]
    
    def get_password(self):
        return self.config["password"]
    
    def message(self, data):
        text = data.get('Text', '')
        mobile_number = data.get('MobileNumber', '')
        if not text or not mobile_number:
            self.error('Missing mobile number or text: %s' % data)
            return None
        now = datetime.datetime.utcnow()
        return super(PushBackend, self).message(mobile_number, text, now)

    def send(self, message):
        number = message.connection.identity
        text = message.text
        
        # this is ghetto xml parsing but we control all the inputs so 
        # we're comfortable with that. 
        payload = self.OUTBOUND_SMS_TEMPLATE % {"password": self.get_password(),
                                                "channel": self.get_channel(),
                                                "service": self.get_service(),
                                                "text": text,
                                                "number": number}
        req = urllib2.Request(url=self.get_url(), 
                              data=payload, 
                              headers={'Content-Type': 'application/xml'})
        
        handle = urllib2.urlopen(req)
        resp = handle.read()
        self.debug("got push response: %s" % resp)
        return True
        