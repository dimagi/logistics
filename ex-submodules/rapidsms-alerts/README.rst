rapidsms-alerts
===============

Web-based configurable alerts.

This app currently supports two modes of alerts:

* "Alerts" -- these are alerts indicating conditions that exist at the
  given moment. The conditions are defined by custom logic. When the
  condition is satisfied, the alert is present; when the condition is
  resolved, the alert goes away automatically. These alerts are
  ephemeral and cannot be acted upon directly.

* "Notifications" -- these alerts are more akin to issue
  tracker. Notifications have triggering conditions (defined as custom
  code). Once triggered, they exist as a discrete event that can be
  'owned' by a user, followed-up upon, escalated to a supervisor, and
  resolved. Notifications can have priorities and
  comments. Notifications will not go away unless explicitly (or
  auto-) resolved.

Alerts
------

A simple alert consists of a notification message and an optional url
(which presumably takes you to a page to resolve the alert).

Alerts are produced via alert generators, and these generators are
registered via the LOGISTICS_ALERT_GENERATORS django settings.

::

  LOGISTICS_ALERT_GENERATORS = (
      'my_app.alerts.demo_alert',
  )

  def demo_alert(request):
      yield Alert('Mary\'s stock report is late', 'http://example.com/reports/stock/dashboard/')
      yield Alert('intruder alert! intruder alert!')

Note the 'request' parameter, which lets you tailor the list of alerts
generated.

Alerts can be displayed via the {% alerts %} template tag. The
generators will run EVERY time a page containing an alerts display is
rendered, so it is good to make sure they don't do anything too
intensive.

There are no database objects associated with simple alerts.

Notifications
-------------

Similar to simple alerts, notifications are also produced via
generators.

::

  LOGISTICS_NOTIF_GENERATORS = (
      'my_app.alerts.trigger_notifications',
  )

However, whereas for simple alerts the generators are invoked on page
render, notification generators must be called via cron or celery task.
The trigger_alerts management command facilitates this.

Notification objects contain:

* a text caption

* a url (links to a detail page or somewhere the user can act on the
  alert) (optional)

* a notification type (fully-qualified class name of a
  NotificationType class)

* an originating location (optional)

* a key that uniquely defines the alert condition

Since notifications are triggered via cron, the key is important to
keep the same alert from being triggered over and over. The key should
uniquely identify the source cause of the alert (e.g., late report;
report type 3; user 5; reporting period 27). You should not save() the
generated notifications yourself.

The NotificationType is a class containing custom logic that defines
the life-cycle of the notification, i.e., escalation levels, which
users can see the alert at each level, and the schedule for escalation.

::

  class DemoAlertType(NotificationType):
      # notification starts out at the first level, and can be
      # escalated to each subsequent level
      escalation_levels = ['district', 'region', 'moh']

      # which users can see the alert at each level
      def users_for_escalation_level(self, esc_level):
          if esc_level == 'district':
              # return all users with reporting_district = district
          elif esc_level == 'region':
              # return designated follow-up person at regional level
          elif esc_level == 'moh':
              # return all users with group 'moh'

      # how long the alert can be at the given level before it is
      # auto-escalated to the next level
      def auto_escalation_interval(self, esc_level):
          return timedelta(days=14)

      # return a human-readable name for each escalation level
      def escalation_level_name(self, esc_level):
          return {
              'district': 'district team',
              'moh': 'ministry of health',
          }[esc_level]

Active notifications are displayed with the {% notifications %}
template tag. Any user that can see the alert can take action on it,
or leave comments. Available actions are: follow up (i.e., take
ownership; only one person can own an alert), escalate to next level,
or resolve. Upon escalation, the 'ownership' flag is cleared, so
someone at the next escalation level must follow-up.

Notification events such as taking ownership, escalation, etc., are
indicated in the comments feed. Set the SYSTEM_USERNAME django setting
to configure what username is shown with these comment entries.

Auto-escalation must be triggered by a separate cron job. The
'alert_maintenance' management command handles this.

Wishlist
--------

* SMS subscription by alert type/priority

* Monthly aggregation and summaries


