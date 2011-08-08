Copy(
SELECT sdp.id, sdp.name, sdp.active, sdp.msd_code, sdp2.name as parent_name, sdpt2.name as parent_type, pt.latitude, pt.longitude, dg.name as group, sdpt.name as type
FROM ilsgateway_servicedeliverypoint sdp
LEFT JOIN ilsgateway_deliverygroup dg on dg.id = sdp.delivery_group_id
LEFT JOIN ilsgateway_servicedeliverypointtype sdpt on sdp.service_delivery_point_type_id = sdpt.id
LEFT JOIN locations_point pt on sdp.point_id = pt.id
LEFT JOIN ilsgateway_servicedeliverypoint sdp2 on sdp.parent_id = sdp2.id
LEFT JOIN ilsgateway_servicedeliverypointtype sdpt2 on sdp2.service_delivery_point_type_id = sdpt2.id
ORDER BY sdp.id asc
) To 'e://all_facilities.csv' with CSV;
;