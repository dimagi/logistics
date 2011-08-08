Copy(
SELECT contact.id, contact.name, contact.language, cd.email, cd.primary, cr.name as role, 
       cd.service_delivery_point_id, sdp.name as sdp_name, sdp.msd_code, sdpt.name as sdp_type, 
       be.name as backend, conn.identity as phone
FROM rapidsms_contact contact
LEFT JOIN ilsgateway_contactdetail cd on contact.id = cd.contact_ptr_id 
LEFT JOIN ilsgateway_contactrole cr on cr.id = cd.role_id
LEFT JOIN ilsgateway_servicedeliverypoint sdp on cd.service_delivery_point_id = sdp.id
LEFT JOIN ilsgateway_servicedeliverypointtype sdpt on sdp.service_delivery_point_type_id = sdpt.id
LEFT JOIN rapidsms_connection conn on conn.contact_id = contact.id
LEFT JOIN rapidsms_backend be on be.id = conn.backend_id
WHERE cd.service_delivery_point_id not in (275,276,277,278,279,280,281,282,283,284,285,286)
) To 'e://contacts.csv' with CSV;
;