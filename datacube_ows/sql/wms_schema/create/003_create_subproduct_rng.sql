-- Creating/replacing sub-product ranges table

create table if not exists wms.sub_product_ranges (
    product_id smallint not null references agdc.dataset_type (id),
    sub_product_id smallint not null,

    lat_min decimal not null,
    lat_max decimal not null,
    lon_min decimal not null,
    lon_max decimal not null,

    dates jsonb not null,

    bboxes jsonb not null,
    constraint pk_sub_product_ranges primary key (product_id, sub_product_id)
);
