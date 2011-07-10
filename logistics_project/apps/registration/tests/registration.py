from django import forms
from rapidsms.conf import settings
from rapidsms.tests.scripted import TestScript
from logistics_project.apps.registration.forms import IntlSMSContactForm
from logistics.models import Location, SupplyPoint, SupplyPointType 

class TestRegister(TestScript):
    fixtures = ["ghana_initial_data.json"] 
    def setUp(self):
        TestScript.setUp(self)
        location = Location.objects.get(code='de')
        facilitytype = SupplyPointType.objects.get(code='hc')
        rms = SupplyPoint.objects.get(code='garms')
        SupplyPoint.objects.get_or_create(code='dedh', name='Dangme East District Hospital',
                                       location=location, active=True,
                                       type=facilitytype, supplied_by=rms)

    def testWebPhoneRegistration(self):
        form = IntlSMSContactForm()
        idc = "%s%s" % (settings.INTL_DIALLING_CODE, settings.COUNTRY_DIALLING_CODE)
        self.assertEquals(form._clean_phone_number('16176023333'),'16176023333')
        self.assertEquals(form._clean_phone_number('1 617 602 3333'),'16176023333')
        self.assertEquals(form._clean_phone_number('1(617)6023333'),'16176023333')
        self.assertEquals(form._clean_phone_number('1-617-602-3333'),'16176023333')
        self.assertEquals(form._clean_phone_number('11-44-602-3333'),'11446023333')
        self.assertEquals(form._clean_phone_number('602-3333'),'6023333')
        # the following is considered poorly formatted, and not supported
        #self.assertEquals(form._clean_phone_number('+233(0)1234567'),'+2331234567')
        self.assertEquals(form._clean_phone_number('%s1234567' % idc),
                          '%s1234567' % idc)
        try:
            form._clean_phone_number('*01234567')
            self.fail('Cleaning "*01234567" should have raised a ValidationError, but it didn\'t')
        except forms.ValidationError:
            pass
        try:
            ddc = settings.DOMESTIC_DIALLING_CODE
            self.assertEquals(form._clean_phone_number('%s1234567' % ddc),'%s1234567' % idc)
        except NameError:
            # DOMESTIC_DIALLING_CODE not defined, no biggie
            pass
