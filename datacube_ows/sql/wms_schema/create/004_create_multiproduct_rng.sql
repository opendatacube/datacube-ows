-- Creating/replacing multi-product ranges table

create table if not exists wms.multiproduct_ranges (
    wms_product_name varchar(128) not null primary key,

    lat_min decimal not null,
    lat_max decimal not null,
    lon_min decimal not null,
    lon_max decimal not null,

    dates jsonb not null,

    bboxes jsonb not null
);
