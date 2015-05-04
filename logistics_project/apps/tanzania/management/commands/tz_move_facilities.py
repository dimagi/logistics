from optparse import make_option
from django.core.management import BaseCommand
from logistics.models import SupplyPoint


class Command(BaseCommand):
    help = "Move a part of locations to districts: CHEMBA DC, IKUNGI, MKALAMA"
    option_list = BaseCommand.option_list + (
        make_option(
            '--test',
            action='store_true',
            dest='test',
            default=False,
            help="Just print out test information but don't actually migrate anything"
        ),
    )

    def handle(self, *args, **options):
        moving_map = {
            'Chemba DC': [
                'D35907',
                'DM 520138',
                'DM 520140',
                'DM 520146',
                'DM510022',
                'DM510023',
                'DM510027',
                'DM520139',
                'DM520141',
                'DM520142',
                'DM520144',
                'DM520148',
                'DM520149',
                'DM520150',
                'DM520151',
                'DM520170',
                'DM520172',
                'DM520175',
                'DM520177',
                'DM520178',
                'DM520179',
                'DM520249',
                'DM520273',
                'DM520275',
                'DM520276',
                'DM520277',
                'DM520296',
                'DM520297',
                'DM520302',
                'DM520307',
                'DM520308',
                'DM521152',
                'DM620147'
            ],
            'IKUNGI DC': [
                'DM510033',
                'DM510041',
                'DM520333',
                'DM520403',
                'DM520404',
                'DM520406',
                'DM520407',
                'DM520414',
                'DM520415',
                'DM520416',
                'DM520417',
                'DM520419',
                'DM520420',
                'DM520422',
                'DM520424',
                'DM520425',
                'DM520429',
                'DM520430',
                'DM520431',
                'DM520432',
                'DM520434',
                'DM520436',
                'DM520437',
                'DM520438',
                'DM520439',
                'DM520451',
                'DM520472',
                'DM520499'
            ],

            'MKALAMA DC': [
                'DM510030',
                'DM510031',
                'DM510042',
                'DM520336',
                'DM520337',
                'DM520338',
                'DM520339',
                'DM520343',
                'DM520344',
                'DM520347',
                'DM520349',
                'DM520351',
                'DM520354',
                'DM520357',
                'DM520358',
                'DM520359',
                'DM520361',
                'DM520365',
                'DM520455',
                'DM520462',
                'DM520463',
                'DM520466',
                'DM520476',
                'DM520487',
            ]

        }

        for supply_point_name, codes in moving_map.iteritems():
            district = SupplyPoint.objects.get(name__iexact=supply_point_name)
            for code in codes:
                try:
                    facility_to_move = SupplyPoint.objects.get(code=code)
                    if options['test']:
                        t = (facility_to_move.name, facility_to_move.code,
                             facility_to_move.supplied_by, district.name)
                        print 'TEST - facility %s (%s) moved to from district %s to district %s' % t
                    else:
                        facility_to_move.supplied_by = district
                        facility_to_move.location.parent = district.location
                        facility_to_move.location.save()
                        facility_to_move.save()
                except SupplyPoint.DoesNotExist:
                    # Shouldn't happen
                    print "Facility with code %s doesn't exist!" % code

