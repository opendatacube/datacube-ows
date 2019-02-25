-- Create wms schema

create schema if not exists wms;

-- Create wms ranges table

create table if not exists wms.product_ranges (
	-- ID PK and FK to dataset_type (product) table.
	id smallint not null primary key references agdc.dataset_type (id),

	-- Lat/Long ranges, for ExGeographicBoundingBox
	lat_min decimal not null,
	lat_max decimal not null,
	lon_min decimal not null,
	lon_max decimal not null,

	-- dates.  A JSON array of strings in 'YYYY-MM-DD' format.
	dates jsonb not null,

	-- bboxes. A JSON object of bounding boxes for all supported CRSs.
	-- Format:  {
	--             "CRS1": {
	--                  "left": 1.000,
	--                  "right": 2.000,
	--                  "bottom": 1.000,
	--                  "top": 2.000
	--             },
	--             "CRS2": { ... },
	--             ...
	--          }
        bboxes jsonb not null
);


create table if not exists wms.sub_product_ranges (
	-- ID PK and FK to dataset_type (product) table.
	product_id smallint not null references agdc.dataset_type (id),
  sub_product_id smallint not null,
	-- Lat/Long ranges, for ExGeographicBoundingBox
	lat_min decimal not null,
	lat_max decimal not null,
	lon_min decimal not null,
	lon_max decimal not null,

	-- dates.  A JSON array of strings in 'YYYY-MM-DD' format.
	dates jsonb not null,

	-- bboxes. A JSON object of bounding boxes for all supported CRSs.
	-- Format:  { 
	--             "CRS1": { 
	--                  "left": 1.000, 
	--                  "right": 2.000, 
	--                  "bottom": 1.000, 
	--                  "top": 2.000 
	--             }, 
	--             "CRS2": { ... },
	--             ... 
	--          }
  bboxes jsonb not null,

  constraint pk_sub_product_ranges primary key ( product_id, sub_product_id)
);

create table if not exists wms.multiproduct_ranges (
	-- ID PK and FK to dataset_type (product) table.
	wms_product_name varchar(128) not null primary key,

	-- Lat/Long ranges, for ExGeographicBoundingBox
	lat_min decimal not null,
	lat_max decimal not null,
	lon_min decimal not null,
	lon_max decimal not null,

	-- dates.  A JSON array of strings in 'YYYY-MM-DD' format.
	dates jsonb not null,

	-- bboxes. A JSON object of bounding boxes for all supported CRSs.
	-- Format:  {
	--             "CRS1": {
	--                  "left": 1.000,
	--                  "right": 2.000,
	--                  "bottom": 1.000,
	--                  "top": 2.000
	--             },
	--             "CRS2": { ... },
	--             ...
	--          }
  bboxes jsonb not null,
);


grant USAGE on schema wms to cube;

CREATE OR REPLACE FUNCTION wms_get_min(integer[], text) RETURNS numeric AS $$
DECLARE
    ret numeric;
    ul text[] DEFAULT array_append('{extent, coord, ul}', $2);
    ur text[] DEFAULT array_append('{extent, coord, ur}', $2);
    ll text[] DEFAULT array_append('{extent, coord, ll}', $2);
    lr text[] DEFAULT array_append('{extent, coord, lr}', $2);
BEGIN
    WITH m AS ( SELECT metadata FROM agdc.dataset WHERE dataset_type_ref in $1 AND archived IS NULL )
    SELECT MIN(LEAST((m.metadata#>>ul)::numeric, (m.metadata#>>ur)::numeric,
           (m.metadata#>>ll)::numeric, (m.metadata#>>lr)::numeric))
    INTO ret
    FROM m;
    RETURN ret;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION wms_get_max(integer[], text) RETURNS numeric AS $$
DECLARE
    ret numeric;
    ul text[] DEFAULT array_append('{extent, coord, ul}', $2);
    ur text[] DEFAULT array_append('{extent, coord, ur}', $2);
    ll text[] DEFAULT array_append('{extent, coord, ll}', $2);
    lr text[] DEFAULT array_append('{extent, coord, lr}', $2);
BEGIN
    WITH m AS ( SELECT metadata FROM agdc.dataset WHERE dataset_type_ref in $1 AND archived IS NULL )
    SELECT MAX(GREATEST((m.metadata#>>ul)::numeric, (m.metadata#>>ur)::numeric,
           (m.metadata#>>ll)::numeric, (m.metadata#>>lr)::numeric))
    INTO ret
    FROM m;
    RETURN ret;
END;
$$ LANGUAGE plpgsql;

