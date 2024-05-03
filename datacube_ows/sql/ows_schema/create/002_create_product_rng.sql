-- Creating/replacing product ranges table

create table if not exists ows.layer_ranges (
    layer varchar(255) not null primary key,

    layer_type int not null,

    lat_min decimal not null,
    lat_max decimal not null,
    lon_min decimal not null,
    lon_max decimal not null,

    dates jsonb not null,

    bboxes jsonb not null,

    last_updated timestamp not null
);
