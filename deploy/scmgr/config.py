import os
VERSION = '0.0.1'

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
STAGING_DB_NAME = "scmgr.db"
STAGING_DB_PATH = os.path.join(BASE_PATH, STAGING_DB_NAME)
LOG_PATH = os.path.join(BASE_PATH, 'extract.log')
LOG_TO_CONSOLE = True

# path to the SCMgr database
PRODUCTION_DB_PATH = r'Z:\media\Malawi_Central_Master.mdb'                                        

# RapidSMS server to submit to
SUBMIT_HOST = '192.168.47.1:8000'
SUBMIT_URL = '/malawi/scmgr/receiver/'
QUERY = """
SELECT CTF_Item.Closing_Bal, CTF_Item.Avg_mnthly_cons, CTF_Item.fStockedOut, CTF_Item.Fac_Code, CTF_Main.P_Date, Product.Prod_Name, Product.strProductID
FROM CTF_Main INNER JOIN (Product INNER JOIN CTF_Item ON Product.Pr_lngProductID = CTF_Item.lngProductID) ON (CTF_Main.P_Date = CTF_Item.P_Date) AND (CTF_Main.Fac_Code = CTF_Item.Fac_Code)
WHERE (((CTF_Item.Fac_Code) Like 'MHG%' Or (CTF_Item.Fac_Code) Like 'KK%' Or (CTF_Item.Fac_Code) Like 'KU%' Or (CTF_Item.Fac_Code) Like 'MJ%' Or (CTF_Item.Fac_Code) Like 'NE%' Or (CTF_Item.Fac_Code) Like 'NB%') AND ((CTF_Main.P_Date)>=DateValue('1/1/2011')) AND ((Product.strProductID) In ('A0451','A0452','A0296','E0006','A0405','A0995','E0325','B0614','CS0002','CS0006','C0036','C0035','GF0088','GF0090','GF0091','H0404','SM0242','K0018','E0014','M0427')) AND ((CTF_Main.CTF_Stat)=1))
ORDER BY CTF_Main.P_Date DESC;
"""

CHUNK_SIZE = 100 # Results per HTTP chunk
