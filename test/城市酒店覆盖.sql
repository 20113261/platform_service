SELECT
  country.name,
  city.name,
  city_id,
  count(*)
FROM hotel_final_20171226a
  JOIN base_data.city ON hotel_final_20171226a.city_id = base_data.city.id
  JOIN base_data.country ON base_data.city.country_id = base_data.country.mid
WHERE source = 'holiday'
GROUP BY base_data.city.id;