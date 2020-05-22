-- Creating/replacing product ranges table

create table if not exists wms.product_ranges (
    id smallint not null primary key references agdc.dataset_type (id),

    lat_min decimal not null,
    lat_max decimal not null,
    lon_min decimal not null,
    lon_max decimal not null,

    dates jsonb not null,

    bboxes jsonb not null);
