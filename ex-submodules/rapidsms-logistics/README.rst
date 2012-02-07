rapidsms-logistics
==================

The logistics app is meant to provide all the bells and whistles needed to provide SMS support to logistics management systems.

Web Reports
-----------

By default, the logistics app comes with a series of built-in reports:

* Aggregate Stock Report -- Displays the number of stockouts, low stocks, adequate stock, and overstocks for a given geographic region in a table
* Aggregate Reporting Rates - Displays the reporting rates (how many facilities reported at all?) and reporting completeness rates (of the total number of commodities required for reporting, how many actually were reported?)
* District Dashboard - Includes district-specific alerts, reporting rates, and a product availability summary chart so that district administrators can get a snapshot view of the stock levels of a given product within their region
* Facilities by Product - For a given product, show a list of facilities within a given geographic region and display their absolutey stock rates as well as months in a way which will make it easy for administrators to manage internal transfers (adjustments).
* Facility Input Stock Page - For a given facility, manually update the stock levels and receipts through a web UI
* Facility Stock on Hand - For a given facility, display the stock on hand with user-friendly colour codes and icons

Other Functionality
-------------------
* Automatic Consumption Calculation: the app can be configured to use a sophisticated algorithm for calculating consumption levels by product and facility automatically on the basis of historical stock reports and receipts. 
* Data Export: there are hooks for exporting message logs and facility information via Excel.

All the individual pieces (graphs, tables, charts, etc.) have been broken down into individual templatetags for easy re-use in other deployment-specific reports. 

Configuration
-------------
For details of some of the different settings which can be configured for the logistics app, check out 'settings.py' within the logistic

Wishlist
--------

* Save 'location' in session variables so that all views are narrowed down to the area of interest. This has been implemented for some views but not all. 
