Copy(
SELECT m.*, c.identity from messagelog_message m, rapidsms_connection c 
WHERE m.contact_id in (
    SELECT rapidsms_contact.id from rapidsms_contact 
    JOIN ilsgateway_contactdetail on rapidsms_contact.id = ilsgateway_contactdetail.contact_ptr_id 
    where service_delivery_point_id not in (275,276,277,278,279,280,281,282,283,284,285,286)) and m.connection_id = c.id order by m.id asc
) To 'e://messages.csv' with CSV;