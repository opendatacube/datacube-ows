-- Create wms schema

create schema wms;

-- Create wms ranges table

create table wms.product_ranges (
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


create table wms.sub_product_ranges (
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

grant USAGE on schema wms to cube;

