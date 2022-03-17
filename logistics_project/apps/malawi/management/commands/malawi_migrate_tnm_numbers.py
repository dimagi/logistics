from __future__ import print_function
from datetime import datetime
from optparse import make_option
from django.core.management.base import LabelCommand
from logistics_project.apps.malawi import loader
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Backend, Connection


class Command(LabelCommand):
    help = "Migrate TNM accounts after they changed the format of the messages."

    option_list = LabelCommand.option_list + (
        make_option('--dry-run', action='store_true', dest='dry_run', default=False,
                    help='Just print what would happen but do not save any changes.'),
    )

    def handle(self, *args, **options):
        tnm_backend = Backend.objects.get(name='tnm-smpp')
        connections = Connection.objects.filter(backend=tnm_backend, identity__startswith='+')
        dry_run = options['dry_run']
        unmigrated_numbers = []
        migrated = skipped = 0
        for conn in connections:
            if conn.identity.startswith('+'):
                migrated += 1
                new_identity = conn.identity.replace('+', '')
                print('migrating {0} --> {1}'.format(conn.identity, new_identity))
                try:
                    old_conn = Connection.objects.get(backend=tnm_backend, identity=new_identity)
                except Connection.DoesNotExist:
                    # no need to migrate new number
                    pass
                else:
                    # migrate old number to prevent integrity conflicts
                    msg_qs = Message.objects.filter(connection=old_conn)
                    last_msg_time = msg_qs.order_by('-date')[0].date if msg_qs.exists() else None
                    print('> found old connection - most recent message is: {0}'.format(last_msg_time))
                    if last_msg_time is None or last_msg_time > datetime(2014, 10, 30):
                        print('>> migrating existing connection')
                        if not dry_run:
                            old_conn.identity = old_conn.identity + '-deprecated'
                            old_conn.save()
                    else:
                        print('>> not migrating because last message is too far in the past')
                        unmigrated_numbers.append(old_conn.identity)

                if not dry_run:
                    conn.identity = new_identity
                    conn.save()
            else:
                skipped += 1

        print('migration finished. migrated {0} numbers and skipped {1}'.format(migrated, skipped))
        if unmigrated_numbers:
            print('the following numbers were not migrated due to conflicts:')
            print('\n'.join(unmigrated_numbers))
