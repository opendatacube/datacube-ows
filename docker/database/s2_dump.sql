--
-- PostgreSQL database dump
--

-- Dumped from database version 12.9 (Debian 12.9-1.pgdg110+1)
-- Dumped by pg_dump version 12.9 (Ubuntu 12.9-0ubuntu0.20.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: agdc; Type: SCHEMA; Schema: -; Owner: agdc_admin
--

CREATE SCHEMA agdc;


ALTER SCHEMA agdc OWNER TO agdc_admin;

--
-- Name: tiger; Type: SCHEMA; Schema: -; Owner: localuser
--

CREATE SCHEMA tiger;


ALTER SCHEMA tiger OWNER TO localuser;

--
-- Name: tiger_data; Type: SCHEMA; Schema: -; Owner: localuser
--

CREATE SCHEMA tiger_data;


ALTER SCHEMA tiger_data OWNER TO localuser;

--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: localuser
--

CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO localuser;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: localuser
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: wms; Type: SCHEMA; Schema: -; Owner: localuser
--

CREATE SCHEMA wms;


ALTER SCHEMA wms OWNER TO localuser;

--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: postgis_tiger_geocoder; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;


--
-- Name: EXTENSION postgis_tiger_geocoder; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_tiger_geocoder IS 'PostGIS tiger geocoder and reverse geocoder';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


--
-- Name: float8range; Type: TYPE; Schema: agdc; Owner: agdc_admin
--

CREATE TYPE agdc.float8range AS RANGE (
    subtype = double precision,
    subtype_diff = float8mi
);


ALTER TYPE agdc.float8range OWNER TO agdc_admin;

--
-- Name: common_timestamp(text); Type: FUNCTION; Schema: agdc; Owner: agdc_admin
--

CREATE FUNCTION agdc.common_timestamp(text) RETURNS timestamp with time zone
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$
select ($1)::timestamp at time zone 'utc';
$_$;


ALTER FUNCTION agdc.common_timestamp(text) OWNER TO agdc_admin;

--
-- Name: set_row_update_time(); Type: FUNCTION; Schema: agdc; Owner: agdc_admin
--

CREATE FUNCTION agdc.set_row_update_time() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  new.updated = now();
  return new;
end;
$$;


ALTER FUNCTION agdc.set_row_update_time() OWNER TO agdc_admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: dataset; Type: TABLE; Schema: agdc; Owner: agdc_admin
--

CREATE TABLE agdc.dataset (
    id uuid NOT NULL,
    metadata_type_ref smallint NOT NULL,
    dataset_type_ref smallint NOT NULL,
    metadata jsonb NOT NULL,
    archived timestamp with time zone,
    added timestamp with time zone DEFAULT now() NOT NULL,
    added_by name DEFAULT CURRENT_USER NOT NULL,
    updated timestamp with time zone
);


ALTER TABLE agdc.dataset OWNER TO agdc_admin;

--
-- Name: dataset_location; Type: TABLE; Schema: agdc; Owner: agdc_admin
--

CREATE TABLE agdc.dataset_location (
    id integer NOT NULL,
    dataset_ref uuid NOT NULL,
    uri_scheme character varying NOT NULL,
    uri_body character varying NOT NULL,
    added timestamp with time zone DEFAULT now() NOT NULL,
    added_by name DEFAULT CURRENT_USER NOT NULL,
    archived timestamp with time zone
);


ALTER TABLE agdc.dataset_location OWNER TO agdc_admin;

--
-- Name: dataset_location_id_seq; Type: SEQUENCE; Schema: agdc; Owner: agdc_admin
--

CREATE SEQUENCE agdc.dataset_location_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE agdc.dataset_location_id_seq OWNER TO agdc_admin;

--
-- Name: dataset_location_id_seq; Type: SEQUENCE OWNED BY; Schema: agdc; Owner: agdc_admin
--

ALTER SEQUENCE agdc.dataset_location_id_seq OWNED BY agdc.dataset_location.id;


--
-- Name: dataset_source; Type: TABLE; Schema: agdc; Owner: agdc_admin
--

CREATE TABLE agdc.dataset_source (
    dataset_ref uuid NOT NULL,
    classifier character varying NOT NULL,
    source_dataset_ref uuid NOT NULL
);


ALTER TABLE agdc.dataset_source OWNER TO agdc_admin;

--
-- Name: dataset_type; Type: TABLE; Schema: agdc; Owner: agdc_admin
--

CREATE TABLE agdc.dataset_type (
    id smallint NOT NULL,
    name character varying NOT NULL,
    metadata jsonb NOT NULL,
    metadata_type_ref smallint NOT NULL,
    definition jsonb NOT NULL,
    added timestamp with time zone DEFAULT now() NOT NULL,
    added_by name DEFAULT CURRENT_USER NOT NULL,
    updated timestamp with time zone,
    CONSTRAINT ck_dataset_type_alphanumeric_name CHECK (((name)::text ~* '^\w+$'::text))
);


ALTER TABLE agdc.dataset_type OWNER TO agdc_admin;

--
-- Name: dataset_type_id_seq; Type: SEQUENCE; Schema: agdc; Owner: agdc_admin
--

CREATE SEQUENCE agdc.dataset_type_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE agdc.dataset_type_id_seq OWNER TO agdc_admin;

--
-- Name: dataset_type_id_seq; Type: SEQUENCE OWNED BY; Schema: agdc; Owner: agdc_admin
--

ALTER SEQUENCE agdc.dataset_type_id_seq OWNED BY agdc.dataset_type.id;


--
-- Name: metadata_type; Type: TABLE; Schema: agdc; Owner: agdc_admin
--

CREATE TABLE agdc.metadata_type (
    id smallint NOT NULL,
    name character varying NOT NULL,
    definition jsonb NOT NULL,
    added timestamp with time zone DEFAULT now() NOT NULL,
    added_by name DEFAULT CURRENT_USER NOT NULL,
    updated timestamp with time zone,
    CONSTRAINT ck_metadata_type_alphanumeric_name CHECK (((name)::text ~* '^\w+$'::text))
);


ALTER TABLE agdc.metadata_type OWNER TO agdc_admin;

--
-- Name: dv_eo3_dataset; Type: VIEW; Schema: agdc; Owner: localuser
--

CREATE VIEW agdc.dv_eo3_dataset AS
 SELECT dataset.id,
    dataset.added AS indexed_time,
    dataset.added_by AS indexed_by,
    dataset_type.name AS product,
    dataset.dataset_type_ref AS dataset_type_id,
    metadata_type.name AS metadata_type,
    dataset.metadata_type_ref AS metadata_type_id,
    dataset.metadata AS metadata_doc,
    agdc.common_timestamp((dataset.metadata #>> '{properties,odc:processing_datetime}'::text[])) AS creation_time,
    (dataset.metadata #>> '{properties,odc:file_format}'::text[]) AS format,
    (dataset.metadata #>> '{label}'::text[]) AS label,
    agdc.float8range(((dataset.metadata #>> '{extent,lat,begin}'::text[]))::double precision, ((dataset.metadata #>> '{extent,lat,end}'::text[]))::double precision, '[]'::text) AS lat,
    agdc.float8range(((dataset.metadata #>> '{extent,lon,begin}'::text[]))::double precision, ((dataset.metadata #>> '{extent,lon,end}'::text[]))::double precision, '[]'::text) AS lon,
    tstzrange(LEAST(agdc.common_timestamp((dataset.metadata #>> '{properties,dtr:start_datetime}'::text[])), agdc.common_timestamp((dataset.metadata #>> '{properties,datetime}'::text[]))), GREATEST(agdc.common_timestamp((dataset.metadata #>> '{properties,dtr:end_datetime}'::text[])), agdc.common_timestamp((dataset.metadata #>> '{properties,datetime}'::text[]))), '[]'::text) AS "time",
    (dataset.metadata #>> '{properties,eo:platform}'::text[]) AS platform,
    (dataset.metadata #>> '{properties,eo:instrument}'::text[]) AS instrument,
    ((dataset.metadata #>> '{properties,eo:cloud_cover}'::text[]))::double precision AS cloud_cover,
    (dataset.metadata #>> '{properties,odc:region_code}'::text[]) AS region_code,
    (dataset.metadata #>> '{properties,odc:product_family}'::text[]) AS product_family,
    (dataset.metadata #>> '{properties,dea:dataset_maturity}'::text[]) AS dataset_maturity
   FROM ((agdc.dataset
     JOIN agdc.dataset_type ON ((dataset_type.id = dataset.dataset_type_ref)))
     JOIN agdc.metadata_type ON ((metadata_type.id = dataset_type.metadata_type_ref)))
  WHERE ((dataset.archived IS NULL) AND (dataset.metadata_type_ref = 1));


ALTER TABLE agdc.dv_eo3_dataset OWNER TO localuser;

--
-- Name: dv_eo_dataset; Type: VIEW; Schema: agdc; Owner: localuser
--

CREATE VIEW agdc.dv_eo_dataset AS
 SELECT dataset.id,
    dataset.added AS indexed_time,
    dataset.added_by AS indexed_by,
    dataset_type.name AS product,
    dataset.dataset_type_ref AS dataset_type_id,
    metadata_type.name AS metadata_type,
    dataset.metadata_type_ref AS metadata_type_id,
    dataset.metadata AS metadata_doc,
    agdc.common_timestamp((dataset.metadata #>> '{creation_dt}'::text[])) AS creation_time,
    (dataset.metadata #>> '{format,name}'::text[]) AS format,
    (dataset.metadata #>> '{ga_label}'::text[]) AS label,
    agdc.float8range(LEAST(((dataset.metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), GREATEST(((dataset.metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), '[]'::text) AS lat,
    agdc.float8range(LEAST(((dataset.metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), GREATEST(((dataset.metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((dataset.metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), '[]'::text) AS lon,
    tstzrange(LEAST(agdc.common_timestamp((dataset.metadata #>> '{extent,from_dt}'::text[])), agdc.common_timestamp((dataset.metadata #>> '{extent,center_dt}'::text[]))), GREATEST(agdc.common_timestamp((dataset.metadata #>> '{extent,to_dt}'::text[])), agdc.common_timestamp((dataset.metadata #>> '{extent,center_dt}'::text[]))), '[]'::text) AS "time",
    (dataset.metadata #>> '{platform,code}'::text[]) AS platform,
    (dataset.metadata #>> '{instrument,name}'::text[]) AS instrument,
    (dataset.metadata #>> '{product_type}'::text[]) AS product_type
   FROM ((agdc.dataset
     JOIN agdc.dataset_type ON ((dataset_type.id = dataset.dataset_type_ref)))
     JOIN agdc.metadata_type ON ((metadata_type.id = dataset_type.metadata_type_ref)))
  WHERE ((dataset.archived IS NULL) AND (dataset.metadata_type_ref = 2));


ALTER TABLE agdc.dv_eo_dataset OWNER TO localuser;

--
-- Name: dv_s2_l2a_dataset; Type: VIEW; Schema: agdc; Owner: localuser
--

CREATE VIEW agdc.dv_s2_l2a_dataset AS
 SELECT dataset.id,
    dataset.added AS indexed_time,
    dataset.added_by AS indexed_by,
    dataset_type.name AS product,
    dataset.dataset_type_ref AS dataset_type_id,
    metadata_type.name AS metadata_type,
    dataset.metadata_type_ref AS metadata_type_id,
    dataset.metadata AS metadata_doc,
    agdc.common_timestamp((dataset.metadata #>> '{properties,odc:processing_datetime}'::text[])) AS creation_time,
    (dataset.metadata #>> '{properties,odc:file_format}'::text[]) AS format,
    (dataset.metadata #>> '{label}'::text[]) AS label,
    agdc.float8range(((dataset.metadata #>> '{extent,lat,begin}'::text[]))::double precision, ((dataset.metadata #>> '{extent,lat,end}'::text[]))::double precision, '[]'::text) AS lat,
    agdc.float8range(((dataset.metadata #>> '{extent,lon,begin}'::text[]))::double precision, ((dataset.metadata #>> '{extent,lon,end}'::text[]))::double precision, '[]'::text) AS lon,
    tstzrange(LEAST(agdc.common_timestamp((dataset.metadata #>> '{properties,dtr:start_datetime}'::text[])), agdc.common_timestamp((dataset.metadata #>> '{properties,datetime}'::text[]))), GREATEST(agdc.common_timestamp((dataset.metadata #>> '{properties,dtr:end_datetime}'::text[])), agdc.common_timestamp((dataset.metadata #>> '{properties,datetime}'::text[]))), '[]'::text) AS "time",
    (dataset.metadata #>> '{properties,eo:platform}'::text[]) AS platform,
    (dataset.metadata #>> '{properties,eo:instrument}'::text[]) AS instrument,
    ((dataset.metadata #>> '{properties,eo:cloud_cover}'::text[]))::double precision AS cloud_cover,
    (dataset.metadata #>> '{properties,odc:region_code}'::text[]) AS region_code,
    (dataset.metadata #>> '{properties,odc:product_family}'::text[]) AS product_family,
    (dataset.metadata #>> '{properties,dea:dataset_maturity}'::text[]) AS dataset_maturity
   FROM ((agdc.dataset
     JOIN agdc.dataset_type ON ((dataset_type.id = dataset.dataset_type_ref)))
     JOIN agdc.metadata_type ON ((metadata_type.id = dataset_type.metadata_type_ref)))
  WHERE ((dataset.archived IS NULL) AND (dataset.dataset_type_ref = 1));


ALTER TABLE agdc.dv_s2_l2a_dataset OWNER TO localuser;

--
-- Name: dv_telemetry_dataset; Type: VIEW; Schema: agdc; Owner: localuser
--

CREATE VIEW agdc.dv_telemetry_dataset AS
 SELECT dataset.id,
    dataset.added AS indexed_time,
    dataset.added_by AS indexed_by,
    dataset_type.name AS product,
    dataset.dataset_type_ref AS dataset_type_id,
    metadata_type.name AS metadata_type,
    dataset.metadata_type_ref AS metadata_type_id,
    dataset.metadata AS metadata_doc,
    agdc.common_timestamp((dataset.metadata #>> '{creation_dt}'::text[])) AS creation_time,
    (dataset.metadata #>> '{format,name}'::text[]) AS format,
    (dataset.metadata #>> '{ga_label}'::text[]) AS label,
    (dataset.metadata #>> '{acquisition,groundstation,code}'::text[]) AS gsi,
    tstzrange(agdc.common_timestamp((dataset.metadata #>> '{acquisition,aos}'::text[])), agdc.common_timestamp((dataset.metadata #>> '{acquisition,los}'::text[])), '[]'::text) AS "time",
    ((dataset.metadata #>> '{acquisition,platform_orbit}'::text[]))::integer AS orbit,
    numrange((((dataset.metadata #>> '{image,satellite_ref_point_start,y}'::text[]))::integer)::numeric, (GREATEST(((dataset.metadata #>> '{image,satellite_ref_point_end,y}'::text[]))::integer, ((dataset.metadata #>> '{image,satellite_ref_point_start,y}'::text[]))::integer))::numeric, '[]'::text) AS sat_row,
    (dataset.metadata #>> '{platform,code}'::text[]) AS platform,
    numrange((((dataset.metadata #>> '{image,satellite_ref_point_start,x}'::text[]))::integer)::numeric, (GREATEST(((dataset.metadata #>> '{image,satellite_ref_point_end,x}'::text[]))::integer, ((dataset.metadata #>> '{image,satellite_ref_point_start,x}'::text[]))::integer))::numeric, '[]'::text) AS sat_path,
    (dataset.metadata #>> '{instrument,name}'::text[]) AS instrument,
    (dataset.metadata #>> '{product_type}'::text[]) AS product_type
   FROM ((agdc.dataset
     JOIN agdc.dataset_type ON ((dataset_type.id = dataset.dataset_type_ref)))
     JOIN agdc.metadata_type ON ((metadata_type.id = dataset_type.metadata_type_ref)))
  WHERE ((dataset.archived IS NULL) AND (dataset.metadata_type_ref = 3));


ALTER TABLE agdc.dv_telemetry_dataset OWNER TO localuser;

--
-- Name: metadata_type_id_seq; Type: SEQUENCE; Schema: agdc; Owner: agdc_admin
--

CREATE SEQUENCE agdc.metadata_type_id_seq
    AS smallint
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE agdc.metadata_type_id_seq OWNER TO agdc_admin;

--
-- Name: metadata_type_id_seq; Type: SEQUENCE OWNED BY; Schema: agdc; Owner: agdc_admin
--

ALTER SEQUENCE agdc.metadata_type_id_seq OWNED BY agdc.metadata_type.id;


--
-- Name: space_view; Type: MATERIALIZED VIEW; Schema: public; Owner: localuser
--

CREATE MATERIALIZED VIEW public.space_view AS
 WITH metadata_lookup AS (
         SELECT metadata_type.id,
            metadata_type.name
           FROM agdc.metadata_type
        ), ranges AS (
         SELECT dataset.id,
            (dataset.metadata #>> '{extent,lat,begin}'::text[]) AS lat_begin,
            (dataset.metadata #>> '{extent,lat,end}'::text[]) AS lat_end,
            (dataset.metadata #>> '{extent,lon,begin}'::text[]) AS lon_begin,
            (dataset.metadata #>> '{extent,lon,end}'::text[]) AS lon_end
           FROM agdc.dataset
          WHERE ((dataset.metadata_type_ref IN ( SELECT metadata_lookup.id
                   FROM metadata_lookup
                  WHERE ((metadata_lookup.name)::text = 'eo3'::text))) AND (dataset.archived IS NULL))
        ), corners AS (
         SELECT dataset.id,
            (dataset.metadata #>> '{extent,coord,ll,lat}'::text[]) AS ll_lat,
            (dataset.metadata #>> '{extent,coord,ll,lon}'::text[]) AS ll_lon,
            (dataset.metadata #>> '{extent,coord,lr,lat}'::text[]) AS lr_lat,
            (dataset.metadata #>> '{extent,coord,lr,lon}'::text[]) AS lr_lon,
            (dataset.metadata #>> '{extent,coord,ul,lat}'::text[]) AS ul_lat,
            (dataset.metadata #>> '{extent,coord,ul,lon}'::text[]) AS ul_lon,
            (dataset.metadata #>> '{extent,coord,ur,lat}'::text[]) AS ur_lat,
            (dataset.metadata #>> '{extent,coord,ur,lon}'::text[]) AS ur_lon
           FROM agdc.dataset
          WHERE ((dataset.metadata_type_ref IN ( SELECT metadata_lookup.id
                   FROM metadata_lookup
                  WHERE ((metadata_lookup.name)::text = ANY ((ARRAY['eo'::character varying, 'eo_s2_nrt'::character varying, 'gqa_eo'::character varying, 'eo_plus'::character varying, 'boku'::character varying])::text[])))) AND (dataset.archived IS NULL))
        )
 SELECT ranges.id,
    (format('POLYGON(( %s %s, %s %s, %s %s, %s %s, %s %s))'::text, ranges.lon_begin, ranges.lat_begin, ranges.lon_end, ranges.lat_begin, ranges.lon_end, ranges.lat_end, ranges.lon_begin, ranges.lat_end, ranges.lon_begin, ranges.lat_begin))::public.geometry AS spatial_extent
   FROM ranges
UNION
 SELECT corners.id,
    (format('POLYGON(( %s %s, %s %s, %s %s, %s %s, %s %s))'::text, corners.ll_lon, corners.ll_lat, corners.lr_lon, corners.lr_lat, corners.ur_lon, corners.ur_lat, corners.ul_lon, corners.ul_lat, corners.ll_lon, corners.ll_lat))::public.geometry AS spatial_extent
   FROM corners
UNION
 SELECT dataset.id,
    public.st_transform(public.st_setsrid(public.st_geomfromgeojson((dataset.metadata #>> '{geometry}'::text[])), (substr((dataset.metadata #>> '{crs}'::text[]), 6))::integer), 4326) AS spatial_extent
   FROM agdc.dataset
  WHERE ((dataset.metadata_type_ref IN ( SELECT metadata_lookup.id
           FROM metadata_lookup
          WHERE ((metadata_lookup.name)::text = 'eo3_landsat_ard'::text))) AND (dataset.archived IS NULL))
  WITH NO DATA;


ALTER TABLE public.space_view OWNER TO localuser;

--
-- Name: time_view; Type: MATERIALIZED VIEW; Schema: public; Owner: localuser
--

CREATE MATERIALIZED VIEW public.time_view AS
 WITH metadata_lookup AS (
         SELECT metadata_type.id,
            metadata_type.name
           FROM agdc.metadata_type
        )
 SELECT dataset.dataset_type_ref,
    dataset.id,
        CASE
            WHEN (((dataset.metadata -> 'extent'::text) ->> 'from_dt'::text) IS NULL) THEN tstzrange(((((dataset.metadata -> 'extent'::text) ->> 'center_dt'::text))::timestamp without time zone)::timestamp with time zone, ((((dataset.metadata -> 'extent'::text) ->> 'center_dt'::text))::timestamp without time zone)::timestamp with time zone, '[]'::text)
            ELSE tstzrange(((((dataset.metadata -> 'extent'::text) ->> 'from_dt'::text))::timestamp without time zone)::timestamp with time zone, ((((dataset.metadata -> 'extent'::text) ->> 'to_dt'::text))::timestamp without time zone)::timestamp with time zone, '[]'::text)
        END AS temporal_extent
   FROM agdc.dataset
  WHERE ((dataset.metadata_type_ref IN ( SELECT metadata_lookup.id
           FROM metadata_lookup
          WHERE ((metadata_lookup.name)::text = ANY ((ARRAY['eo'::character varying, 'eo_s2_nrt'::character varying, 'gqa_eo'::character varying, 'eo_plus'::character varying])::text[])))) AND (dataset.archived IS NULL))
UNION
 SELECT dataset.dataset_type_ref,
    dataset.id,
    tstzrange(((COALESCE(((dataset.metadata -> 'properties'::text) ->> 'dtr:start_datetime'::text), ((dataset.metadata -> 'properties'::text) ->> 'datetime'::text)))::timestamp without time zone)::timestamp with time zone, (COALESCE((((dataset.metadata -> 'properties'::text) ->> 'dtr:end_datetime'::text))::timestamp without time zone, (((dataset.metadata -> 'properties'::text) ->> 'datetime'::text))::timestamp without time zone))::timestamp with time zone, '[]'::text) AS temporal_extent
   FROM agdc.dataset
  WHERE ((dataset.metadata_type_ref IN ( SELECT metadata_lookup.id
           FROM metadata_lookup
          WHERE ((metadata_lookup.name)::text = ANY ((ARRAY['eo3_landsat_ard'::character varying, 'eo3'::character varying])::text[])))) AND (dataset.archived IS NULL))
  WITH NO DATA;


ALTER TABLE public.time_view OWNER TO localuser;

--
-- Name: space_time_view; Type: MATERIALIZED VIEW; Schema: public; Owner: localuser
--

CREATE MATERIALIZED VIEW public.space_time_view AS
 SELECT space_view.id,
    time_view.dataset_type_ref,
    space_view.spatial_extent,
    time_view.temporal_extent
   FROM (public.space_view
     JOIN public.time_view ON ((space_view.id = time_view.id)))
  WITH NO DATA;


ALTER TABLE public.space_time_view OWNER TO localuser;

--
-- Name: multiproduct_ranges; Type: TABLE; Schema: wms; Owner: localuser
--

CREATE TABLE wms.multiproduct_ranges (
    wms_product_name character varying(128) NOT NULL,
    lat_min numeric NOT NULL,
    lat_max numeric NOT NULL,
    lon_min numeric NOT NULL,
    lon_max numeric NOT NULL,
    dates jsonb NOT NULL,
    bboxes jsonb NOT NULL
);


ALTER TABLE wms.multiproduct_ranges OWNER TO localuser;

--
-- Name: product_ranges; Type: TABLE; Schema: wms; Owner: localuser
--

CREATE TABLE wms.product_ranges (
    id smallint NOT NULL,
    lat_min numeric NOT NULL,
    lat_max numeric NOT NULL,
    lon_min numeric NOT NULL,
    lon_max numeric NOT NULL,
    dates jsonb NOT NULL,
    bboxes jsonb NOT NULL
);


ALTER TABLE wms.product_ranges OWNER TO localuser;

--
-- Name: sub_product_ranges; Type: TABLE; Schema: wms; Owner: localuser
--

CREATE TABLE wms.sub_product_ranges (
    product_id smallint NOT NULL,
    sub_product_id smallint NOT NULL,
    lat_min numeric NOT NULL,
    lat_max numeric NOT NULL,
    lon_min numeric NOT NULL,
    lon_max numeric NOT NULL,
    dates jsonb NOT NULL,
    bboxes jsonb NOT NULL
);


ALTER TABLE wms.sub_product_ranges OWNER TO localuser;

--
-- Name: dataset_location id; Type: DEFAULT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_location ALTER COLUMN id SET DEFAULT nextval('agdc.dataset_location_id_seq'::regclass);


--
-- Name: dataset_type id; Type: DEFAULT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_type ALTER COLUMN id SET DEFAULT nextval('agdc.dataset_type_id_seq'::regclass);


--
-- Name: metadata_type id; Type: DEFAULT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.metadata_type ALTER COLUMN id SET DEFAULT nextval('agdc.metadata_type_id_seq'::regclass);


--
-- Data for Name: dataset; Type: TABLE DATA; Schema: agdc; Owner: agdc_admin
--

COPY agdc.dataset (id, metadata_type_ref, dataset_type_ref, metadata, archived, added, added_by, updated) FROM stdin;
fc1faf15-dcea-561f-907a-1e6c1a29bc63	1	1	{"id": "fc1faf15-dcea-561f-907a-1e6c1a29bc63", "crs": "epsg:32738", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 399960, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 399960, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 399960, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 399960, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2A_MSIL2A_20220101T072201_N0301_R063_T38LMK_20220101T081710", "extent": {"lat": {"end": -13.566748034152768, "begin": -14.56123045492476}, "lon": {"end": 45.09059297011045, "begin": 44.07137924326195}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[509759.0, 8390201.0], [399961.0, 8390201.0], [399961.0, 8499999.0], [509759.0, 8499999.0], [509759.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2022-01-01T11:03:30.690Z", "updated": "2022-01-01T11:03:30.690Z", "datetime": "2022-01-01T07:23:41Z", "proj:epsg": 32738, "eo:platform": "sentinel-2a", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 77.44, "odc:file_format": "GeoTIFF", "odc:region_code": "38LMK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 38, "sentinel:product_id": "S2A_MSIL2A_20220101T072201_N0301_R063_T38LMK_20220101T081710", "sentinel:grid_square": "MK", "sentinel:data_coverage": 100, "sentinel:latitude_band": "L", "odc:processing_datetime": "2022-01-01T11:03:30.690Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/38/L/MK/2022/1/1/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/38/L/MK/2022/1/1/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/38/L/MK/2022/1/1/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[509759.0, 8390201.0], [399961.0, 8390201.0], [399961.0, 8499999.0], [509759.0, 8499999.0], [509759.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 399960.0, "y": 8390200.0}, "lr": {"x": 509760.0, "y": 8390200.0}, "ul": {"x": 399960.0, "y": 8500000.0}, "ur": {"x": 509760.0, "y": 8500000.0}}, "spatial_reference": "epsg:32738"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:42.872334+00	localuser	\N
92595b50-144f-5b52-8b36-5937f5a8a361	1	1	{"id": "92595b50-144f-5b52-8b36-5937f5a8a361", "crs": "epsg:32750", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 799980, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 799980, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 799980, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 799980, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2A_MSIL2A_20220101T021351_N0301_R060_T50LRK_20220101T061221", "extent": {"lat": {"end": -13.539778272083733, "begin": -14.544692490688847}, "lon": {"end": 120.801003438928, "begin": 119.7715956828356}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[799981.0, 8390201.0], [799981.0, 8499999.0], [909779.0, 8499999.0], [909779.0, 8390201.0], [799981.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2022-01-01T09:14:00.522Z", "updated": "2022-01-01T09:14:00.522Z", "datetime": "2022-01-01T02:21:34Z", "proj:epsg": 32750, "eo:platform": "sentinel-2a", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 60.87, "odc:file_format": "GeoTIFF", "odc:region_code": "50LRK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 50, "sentinel:product_id": "S2A_MSIL2A_20220101T021351_N0301_R060_T50LRK_20220101T061221", "sentinel:grid_square": "RK", "sentinel:data_coverage": 100, "sentinel:latitude_band": "L", "odc:processing_datetime": "2022-01-01T09:14:00.522Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/RK/2022/1/1/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/RK/2022/1/1/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/50/L/RK/2022/1/1/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[799981.0, 8390201.0], [799981.0, 8499999.0], [909779.0, 8499999.0], [909779.0, 8390201.0], [799981.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 799980.0, "y": 8390200.0}, "lr": {"x": 909780.0, "y": 8390200.0}, "ul": {"x": 799980.0, "y": 8500000.0}, "ur": {"x": 909780.0, "y": 8500000.0}}, "spatial_reference": "epsg:32750"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:42.922387+00	localuser	\N
9a8c999a-727f-5200-a0e9-c21d89dfb7fb	1	1	{"id": "9a8c999a-727f-5200-a0e9-c21d89dfb7fb", "crs": "epsg:32750", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 600000, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 600000, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 600000, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 600000, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2A_MSIL2A_20220101T021351_N0301_R060_T50LPK_20220101T061221", "extent": {"lat": {"end": -13.560932176423318, "begin": -14.556697235931155}, "lon": {"end": 118.94716787178677, "begin": 118.45932654832203}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[657222.0, 8390201.0], [683281.0, 8499999.0], [709799.0, 8499999.0], [709799.0, 8390201.0], [657222.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2022-01-01T09:12:16.895Z", "updated": "2022-01-01T09:12:16.895Z", "datetime": "2022-01-01T02:21:41Z", "proj:epsg": 32750, "eo:platform": "sentinel-2a", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 93.49, "odc:file_format": "GeoTIFF", "odc:region_code": "50LPK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 50, "sentinel:product_id": "S2A_MSIL2A_20220101T021351_N0301_R060_T50LPK_20220101T061221", "sentinel:grid_square": "PK", "sentinel:data_coverage": 35.89, "sentinel:latitude_band": "L", "odc:processing_datetime": "2022-01-01T09:12:16.895Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/PK/2022/1/1/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/PK/2022/1/1/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/50/L/PK/2022/1/1/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[657222.0, 8390201.0], [683281.0, 8499999.0], [709799.0, 8499999.0], [709799.0, 8390201.0], [657222.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 600000.0, "y": 8390200.0}, "lr": {"x": 709800.0, "y": 8390200.0}, "ul": {"x": 600000.0, "y": 8500000.0}, "ur": {"x": 709800.0, "y": 8500000.0}}, "spatial_reference": "epsg:32750"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:42.935975+00	localuser	\N
7480b834-2d80-51ef-8d20-02474d3ac321	1	1	{"id": "7480b834-2d80-51ef-8d20-02474d3ac321", "crs": "epsg:32738", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 799980, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 799980, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 799980, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 799980, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211231T070049_N0301_R120_T38LRK_20211231T090304", "extent": {"lat": {"end": -13.539778272083733, "begin": -14.54236878508964}, "lon": {"end": 48.80100343892802, "begin": 47.972519450302755}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[820364.0, 8390201.0], [847224.0, 8499999.0], [909779.0, 8499999.0], [909779.0, 8390201.0], [820364.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-31T11:08:48.573Z", "updated": "2021-12-31T11:08:48.573Z", "datetime": "2021-12-31T07:03:31Z", "proj:epsg": 32738, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 36.54, "odc:file_format": "GeoTIFF", "odc:region_code": "38LRK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 38, "sentinel:product_id": "S2B_MSIL2A_20211231T070049_N0301_R120_T38LRK_20211231T090304", "sentinel:grid_square": "RK", "sentinel:data_coverage": 69.15, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-31T11:08:48.573Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/38/L/RK/2021/12/31/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/38/L/RK/2021/12/31/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/38/L/RK/2021/12/31/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[820364.0, 8390201.0], [847224.0, 8499999.0], [909779.0, 8499999.0], [909779.0, 8390201.0], [820364.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 799980.0, "y": 8390200.0}, "lr": {"x": 909780.0, "y": 8390200.0}, "ul": {"x": 799980.0, "y": 8500000.0}, "ur": {"x": 909780.0, "y": 8500000.0}}, "spatial_reference": "epsg:32738"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:42.927873+00	localuser	\N
090ee981-efb2-554c-96ab-86863459a876	1	1	{"id": "090ee981-efb2-554c-96ab-86863459a876", "crs": "epsg:32751", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 199980, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 199980, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 199980, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 199980, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2A_MSIL2A_20220101T021351_N0301_R060_T51LTE_20220101T061221", "extent": {"lat": {"end": -13.553072864934201, "begin": -14.554587278042646}, "lon": {"end": 121.24206804342543, "begin": 120.21608884980121}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[309779.0, 8390201.0], [199981.0, 8390201.0], [199981.0, 8499999.0], [309779.0, 8499999.0], [309779.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2022-01-01T09:14:51.937Z", "updated": "2022-01-01T09:14:51.937Z", "datetime": "2022-01-01T02:21:33Z", "proj:epsg": 32751, "eo:platform": "sentinel-2a", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 43.34, "odc:file_format": "GeoTIFF", "odc:region_code": "51LTE", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 51, "sentinel:product_id": "S2A_MSIL2A_20220101T021351_N0301_R060_T51LTE_20220101T061221", "sentinel:grid_square": "TE", "sentinel:data_coverage": 100, "sentinel:latitude_band": "L", "odc:processing_datetime": "2022-01-01T09:14:51.937Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/51/L/TE/2022/1/1/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/51/L/TE/2022/1/1/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/51/L/TE/2022/1/1/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[309779.0, 8390201.0], [199981.0, 8390201.0], [199981.0, 8499999.0], [309779.0, 8499999.0], [309779.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 199980.0, "y": 8390200.0}, "lr": {"x": 309780.0, "y": 8390200.0}, "ul": {"x": 199980.0, "y": 8500000.0}, "ur": {"x": 309780.0, "y": 8500000.0}}, "spatial_reference": "epsg:32751"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:42.929498+00	localuser	\N
89a69f26-6510-522d-859b-cca4fa13090f	1	1	{"id": "89a69f26-6510-522d-859b-cca4fa13090f", "crs": "epsg:32738", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 300000, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 300000, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 300000, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 300000, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2A_MSIL2A_20220101T072201_N0301_R063_T38LLK_20220101T081710", "extent": {"lat": {"end": -13.56175904707917, "begin": -14.559749838771705}, "lon": {"end": 44.166297697622156, "begin": 43.14375216553042}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[409799.0, 8390201.0], [300001.0, 8390201.0], [300001.0, 8490972.0], [302063.0, 8499999.0], [409799.0, 8499999.0], [409799.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2022-01-01T11:01:41.114Z", "updated": "2022-01-01T11:01:41.114Z", "datetime": "2022-01-01T07:23:45Z", "proj:epsg": 32738, "eo:platform": "sentinel-2a", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 37.16, "odc:file_format": "GeoTIFF", "odc:region_code": "38LLK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 38, "sentinel:product_id": "S2A_MSIL2A_20220101T072201_N0301_R063_T38LLK_20220101T081710", "sentinel:grid_square": "LK", "sentinel:data_coverage": 99.91, "sentinel:latitude_band": "L", "odc:processing_datetime": "2022-01-01T11:01:41.114Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/38/L/LK/2022/1/1/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/38/L/LK/2022/1/1/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/38/L/LK/2022/1/1/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[409799.0, 8390201.0], [300001.0, 8390201.0], [300001.0, 8490972.0], [302063.0, 8499999.0], [409799.0, 8499999.0], [409799.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 300000.0, "y": 8390200.0}, "lr": {"x": 409800.0, "y": 8390200.0}, "ul": {"x": 300000.0, "y": 8500000.0}, "ur": {"x": 409800.0, "y": 8500000.0}}, "spatial_reference": "epsg:32738"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:42.937279+00	localuser	\N
78be9cdf-c0b2-57a9-ab25-4beaafca6616	1	1	{"id": "78be9cdf-c0b2-57a9-ab25-4beaafca6616", "crs": "epsg:32739", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 199980, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 199980, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 199980, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 199980, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211231T070049_N0301_R120_T39LTE_20211231T090304", "extent": {"lat": {"end": -13.553072864934201, "begin": -14.554587278042646}, "lon": {"end": 49.24206804342543, "begin": 48.216088849801224}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[309779.0, 8390201.0], [199981.0, 8390201.0], [199981.0, 8499999.0], [309779.0, 8499999.0], [309779.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-31T11:09:58.602Z", "updated": "2021-12-31T11:09:58.602Z", "datetime": "2021-12-31T07:03:30Z", "proj:epsg": 32739, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 26.87, "odc:file_format": "GeoTIFF", "odc:region_code": "39LTE", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 39, "sentinel:product_id": "S2B_MSIL2A_20211231T070049_N0301_R120_T39LTE_20211231T090304", "sentinel:grid_square": "TE", "sentinel:data_coverage": 100, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-31T11:09:58.602Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/39/L/TE/2021/12/31/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/39/L/TE/2021/12/31/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/39/L/TE/2021/12/31/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[309779.0, 8390201.0], [199981.0, 8390201.0], [199981.0, 8499999.0], [309779.0, 8499999.0], [309779.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 199980.0, "y": 8390200.0}, "lr": {"x": 309780.0, "y": 8390200.0}, "ul": {"x": 199980.0, "y": 8500000.0}, "ur": {"x": 309780.0, "y": 8500000.0}}, "spatial_reference": "epsg:32739"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:43.02667+00	localuser	\N
4bc00074-bb56-5d82-b573-8372a0b8bc07	1	1	{"id": "4bc00074-bb56-5d82-b573-8372a0b8bc07", "crs": "epsg:32750", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 600000, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 600000, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 600000, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 600000, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211230T022319_N0301_R103_T50LPK_20211230T042426", "extent": {"lat": {"end": -13.560932176423318, "begin": -14.557094507840981}, "lon": {"end": 118.93978198197776, "begin": 117.92427299922686}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[650201.0, 8390201.0], [600001.0, 8403191.0], [600001.0, 8499999.0], [709799.0, 8499999.0], [709799.0, 8486572.0], [688032.0, 8390591.0], [687809.0, 8390201.0], [650201.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-30T06:43:43.256Z", "updated": "2021-12-30T06:43:43.256Z", "datetime": "2021-12-30T02:31:30Z", "proj:epsg": 32750, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 6.68, "odc:file_format": "GeoTIFF", "odc:region_code": "50LPK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 50, "sentinel:product_id": "S2B_MSIL2A_20211230T022319_N0301_R103_T50LPK_20211230T042426", "sentinel:grid_square": "PK", "sentinel:data_coverage": 88.17, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-30T06:43:43.256Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/PK/2021/12/30/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/PK/2021/12/30/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/50/L/PK/2021/12/30/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[650201.0, 8390201.0], [600001.0, 8403191.0], [600001.0, 8499999.0], [709799.0, 8499999.0], [709799.0, 8486572.0], [688032.0, 8390591.0], [687809.0, 8390201.0], [650201.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 600000.0, "y": 8390200.0}, "lr": {"x": 709800.0, "y": 8390200.0}, "ul": {"x": 600000.0, "y": 8500000.0}, "ur": {"x": 709800.0, "y": 8500000.0}}, "spatial_reference": "epsg:32750"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:43.0503+00	localuser	\N
4ea6faba-332d-5288-b05e-e9ec249d2ff1	1	1	{"id": "4ea6faba-332d-5288-b05e-e9ec249d2ff1", "crs": "epsg:32751", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 300000, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 300000, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 300000, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 300000, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2A_MSIL2A_20220101T021351_N0301_R060_T51LUE_20220101T061221", "extent": {"lat": {"end": -13.561618758927999, "begin": -14.554787228660402}, "lon": {"end": 121.48208005045798, "begin": 121.14375216553042}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[312657.0, 8390201.0], [300001.0, 8390201.0], [300001.0, 8499999.0], [335757.0, 8499999.0], [312657.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2022-01-01T09:06:43.779Z", "updated": "2022-01-01T09:06:43.779Z", "datetime": "2022-01-01T02:21:29Z", "proj:epsg": 32751, "eo:platform": "sentinel-2a", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 48.89, "odc:file_format": "GeoTIFF", "odc:region_code": "51LUE", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 51, "sentinel:product_id": "S2A_MSIL2A_20220101T021351_N0301_R060_T51LUE_20220101T061221", "sentinel:grid_square": "UE", "sentinel:data_coverage": 22.04, "sentinel:latitude_band": "L", "odc:processing_datetime": "2022-01-01T09:06:43.779Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/51/L/UE/2022/1/1/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/51/L/UE/2022/1/1/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/51/L/UE/2022/1/1/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[312657.0, 8390201.0], [300001.0, 8390201.0], [300001.0, 8499999.0], [335757.0, 8499999.0], [312657.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 300000.0, "y": 8390200.0}, "lr": {"x": 409800.0, "y": 8390200.0}, "ul": {"x": 300000.0, "y": 8500000.0}, "ur": {"x": 409800.0, "y": 8500000.0}}, "spatial_reference": "epsg:32751"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:42.949168+00	localuser	\N
0053ffe9-33cf-58c0-b61c-53b795c64702	1	1	{"id": "0053ffe9-33cf-58c0-b61c-53b795c64702", "crs": "epsg:32750", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 699960, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 699960, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 699960, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 699960, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2A_MSIL2A_20220101T021351_N0301_R060_T50LQK_20220101T061221", "extent": {"lat": {"end": -13.552058584450984, "begin": -14.553888007970453}, "lon": {"end": 119.87420997110434, "begin": 118.84791209279845}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[699961.0, 8390201.0], [699961.0, 8499999.0], [809759.0, 8499999.0], [809759.0, 8390201.0], [699961.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2022-01-01T08:56:56.856Z", "updated": "2022-01-01T08:56:56.856Z", "datetime": "2022-01-01T02:21:38Z", "proj:epsg": 32750, "eo:platform": "sentinel-2a", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 84, "odc:file_format": "GeoTIFF", "odc:region_code": "50LQK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 50, "sentinel:product_id": "S2A_MSIL2A_20220101T021351_N0301_R060_T50LQK_20220101T061221", "sentinel:grid_square": "QK", "sentinel:data_coverage": 100, "sentinel:latitude_band": "L", "odc:processing_datetime": "2022-01-01T08:56:56.856Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/QK/2022/1/1/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/QK/2022/1/1/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/50/L/QK/2022/1/1/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[699961.0, 8390201.0], [699961.0, 8499999.0], [809759.0, 8499999.0], [809759.0, 8390201.0], [699961.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 699960.0, "y": 8390200.0}, "lr": {"x": 809760.0, "y": 8390200.0}, "ul": {"x": 699960.0, "y": 8500000.0}, "ur": {"x": 809760.0, "y": 8500000.0}}, "spatial_reference": "epsg:32750"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:42.987259+00	localuser	\N
2010c062-ca58-5c0c-875b-91a1621d97f9	1	1	{"id": "2010c062-ca58-5c0c-875b-91a1621d97f9", "crs": "epsg:32739", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 399960, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 399960, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 399960, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 399960, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211231T070049_N0301_R120_T39LVE_20211231T090304", "extent": {"lat": {"end": -13.566748034152768, "begin": -14.56113869044314}, "lon": {"end": 50.99524906565659, "begin": 50.07137924326194}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[475637.0, 8390201.0], [399961.0, 8390201.0], [399961.0, 8499999.0], [499486.0, 8499999.0], [475637.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-31T11:08:42.364Z", "updated": "2021-12-31T11:08:42.364Z", "datetime": "2021-12-31T07:03:23Z", "proj:epsg": 32739, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 91.69, "odc:file_format": "GeoTIFF", "odc:region_code": "39LVE", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 39, "sentinel:product_id": "S2B_MSIL2A_20211231T070049_N0301_R120_T39LVE_20211231T090304", "sentinel:grid_square": "VE", "sentinel:data_coverage": 79.78, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-31T11:08:42.364Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/39/L/VE/2021/12/31/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/39/L/VE/2021/12/31/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/39/L/VE/2021/12/31/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[475637.0, 8390201.0], [399961.0, 8390201.0], [399961.0, 8499999.0], [499486.0, 8499999.0], [475637.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 399960.0, "y": 8390200.0}, "lr": {"x": 509760.0, "y": 8390200.0}, "ul": {"x": 399960.0, "y": 8500000.0}, "ur": {"x": 509760.0, "y": 8500000.0}}, "spatial_reference": "epsg:32739"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:42.991733+00	localuser	\N
0559e840-6372-55d3-83b3-4749e8c7afc6	1	1	{"id": "0559e840-6372-55d3-83b3-4749e8c7afc6", "crs": "epsg:32751", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 699960, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 699960, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 699960, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 699960, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211231T015619_N0301_R117_T51LYE_20211231T035247", "extent": {"lat": {"end": -13.552058584450984, "begin": -14.553888007970453}, "lon": {"end": 125.87420997110432, "begin": 124.84791209279844}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[699961.0, 8390201.0], [699961.0, 8499999.0], [809759.0, 8499999.0], [809759.0, 8390201.0], [699961.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-31T06:14:47.737Z", "updated": "2021-12-31T06:14:47.737Z", "datetime": "2021-12-31T02:01:20Z", "proj:epsg": 32751, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 33.54, "odc:file_format": "GeoTIFF", "odc:region_code": "51LYE", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 51, "sentinel:product_id": "S2B_MSIL2A_20211231T015619_N0301_R117_T51LYE_20211231T035247", "sentinel:grid_square": "YE", "sentinel:data_coverage": 100, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-31T06:14:47.737Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/51/L/YE/2021/12/31/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/51/L/YE/2021/12/31/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/51/L/YE/2021/12/31/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[699961.0, 8390201.0], [699961.0, 8499999.0], [809759.0, 8499999.0], [809759.0, 8390201.0], [699961.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 699960.0, "y": 8390200.0}, "lr": {"x": 809760.0, "y": 8390200.0}, "ul": {"x": 699960.0, "y": 8500000.0}, "ur": {"x": 809760.0, "y": 8500000.0}}, "spatial_reference": "epsg:32751"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:43.001502+00	localuser	\N
52ca63d9-41a6-54ea-8b88-ce6cb96785f1	1	1	{"id": "52ca63d9-41a6-54ea-8b88-ce6cb96785f1", "crs": "epsg:32739", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 300000, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 300000, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 300000, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 300000, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211231T070049_N0301_R120_T39LUE_20211231T090304", "extent": {"lat": {"end": -13.561618758927999, "begin": -14.559749838771705}, "lon": {"end": 50.166297697622134, "begin": 49.14375216553041}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[409799.0, 8390201.0], [300001.0, 8390201.0], [300001.0, 8499999.0], [409799.0, 8499999.0], [409799.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-31T11:14:04.086Z", "updated": "2021-12-31T11:14:04.086Z", "datetime": "2021-12-31T07:03:27Z", "proj:epsg": 32739, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 66.77, "odc:file_format": "GeoTIFF", "odc:region_code": "39LUE", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 39, "sentinel:product_id": "S2B_MSIL2A_20211231T070049_N0301_R120_T39LUE_20211231T090304", "sentinel:grid_square": "UE", "sentinel:data_coverage": 100, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-31T11:14:04.086Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/39/L/UE/2021/12/31/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/39/L/UE/2021/12/31/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/39/L/UE/2021/12/31/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[409799.0, 8390201.0], [300001.0, 8390201.0], [300001.0, 8499999.0], [409799.0, 8499999.0], [409799.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 300000.0, "y": 8390200.0}, "lr": {"x": 409800.0, "y": 8390200.0}, "ul": {"x": 300000.0, "y": 8500000.0}, "ur": {"x": 409800.0, "y": 8500000.0}}, "spatial_reference": "epsg:32739"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:42.996569+00	localuser	\N
c6ddc88a-5fe9-5acc-98f9-eb8f437d1b6f	1	1	{"id": "c6ddc88a-5fe9-5acc-98f9-eb8f437d1b6f", "crs": "epsg:32750", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 699960, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 699960, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 699960, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 699960, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211230T022319_N0301_R103_T50LQK_20211230T042426", "extent": {"lat": {"end": -13.560720610137741, "begin": -14.06501446545311}, "lon": {"end": 118.96584891927384, "begin": 118.84883588881569}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[700071.0, 8444297.0], [700061.0, 8499999.0], [712728.0, 8499999.0], [700071.0, 8444297.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-30T06:29:48.453Z", "updated": "2021-12-30T06:29:48.453Z", "datetime": "2021-12-30T02:31:22Z", "proj:epsg": 32750, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 4.12, "odc:file_format": "GeoTIFF", "odc:region_code": "50LQK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 50, "sentinel:product_id": "S2B_MSIL2A_20211230T022319_N0301_R103_T50LQK_20211230T042426", "sentinel:grid_square": "QK", "sentinel:data_coverage": 2.85, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-30T06:29:48.453Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/QK/2021/12/30/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/QK/2021/12/30/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/50/L/QK/2021/12/30/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[700071.0, 8444297.0], [700061.0, 8499999.0], [712728.0, 8499999.0], [700071.0, 8444297.0]]]}, "geo_ref_points": {"ll": {"x": 699960.0, "y": 8390200.0}, "lr": {"x": 809760.0, "y": 8390200.0}, "ul": {"x": 699960.0, "y": 8500000.0}, "ur": {"x": 809760.0, "y": 8500000.0}}, "spatial_reference": "epsg:32750"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:43.033077+00	localuser	\N
38ea6660-95fa-5089-97a7-ab43c7322f36	1	1	{"id": "38ea6660-95fa-5089-97a7-ab43c7322f36", "crs": "epsg:32750", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 399960, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 399960, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 399960, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 399960, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211230T022319_N0301_R103_T50LMK_20211230T042426", "extent": {"lat": {"end": -13.56709347955863, "begin": -14.253967104436134}, "lon": {"end": 117.09046903051538, "begin": 116.0734302529146}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[509759.0, 8424184.0], [400961.0, 8445188.0], [399961.0, 8445481.0], [399961.0, 8453120.0], [410621.0, 8499999.0], [509759.0, 8499999.0], [509759.0, 8424184.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-30T06:39:11.751Z", "updated": "2021-12-30T06:39:11.751Z", "datetime": "2021-12-30T02:31:34Z", "proj:epsg": 32750, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 11.76, "odc:file_format": "GeoTIFF", "odc:region_code": "50LMK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 50, "sentinel:product_id": "S2B_MSIL2A_20211230T022319_N0301_R103_T50LMK_20211230T042426", "sentinel:grid_square": "MK", "sentinel:data_coverage": 56.69, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-30T06:39:11.751Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/MK/2021/12/30/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/MK/2021/12/30/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/50/L/MK/2021/12/30/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[509759.0, 8424184.0], [400961.0, 8445188.0], [399961.0, 8445481.0], [399961.0, 8453120.0], [410621.0, 8499999.0], [509759.0, 8499999.0], [509759.0, 8424184.0]]]}, "geo_ref_points": {"ll": {"x": 399960.0, "y": 8390200.0}, "lr": {"x": 509760.0, "y": 8390200.0}, "ul": {"x": 399960.0, "y": 8500000.0}, "ur": {"x": 509760.0, "y": 8500000.0}}, "spatial_reference": "epsg:32750"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:43.052808+00	localuser	\N
64e807fd-63b7-5a50-b38f-1421c6f1bbf7	1	1	{"id": "64e807fd-63b7-5a50-b38f-1421c6f1bbf7", "crs": "epsg:32738", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 499980, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 499980, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 499980, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 499980, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2A_MSIL2A_20220101T072201_N0301_R063_T38LNK_20220101T081710", "extent": {"lat": {"end": -13.566615957490518, "begin": -14.561247992924196}, "lon": {"end": 45.95962264502696, "begin": 44.9998236225844}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[499981.0, 8390201.0], [499981.0, 8499999.0], [603826.0, 8499999.0], [579517.0, 8390201.0], [499981.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2022-01-01T10:59:25.798Z", "updated": "2022-01-01T10:59:25.798Z", "datetime": "2022-01-01T07:23:38Z", "proj:epsg": 32738, "eo:platform": "sentinel-2a", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 99.5, "odc:file_format": "GeoTIFF", "odc:region_code": "38LNK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 38, "sentinel:product_id": "S2A_MSIL2A_20220101T072201_N0301_R063_T38LNK_20220101T081710", "sentinel:grid_square": "NK", "sentinel:data_coverage": 83.51, "sentinel:latitude_band": "L", "odc:processing_datetime": "2022-01-01T10:59:25.798Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/38/L/NK/2022/1/1/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/38/L/NK/2022/1/1/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/38/L/NK/2022/1/1/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[499981.0, 8390201.0], [499981.0, 8499999.0], [603826.0, 8499999.0], [579517.0, 8390201.0], [499981.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 499980.0, "y": 8390200.0}, "lr": {"x": 609780.0, "y": 8390200.0}, "ul": {"x": 499980.0, "y": 8500000.0}, "ur": {"x": 609780.0, "y": 8500000.0}}, "spatial_reference": "epsg:32738"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:43.012183+00	localuser	\N
082027ee-135d-5610-849a-b3344ca9133a	1	1	{"id": "082027ee-135d-5610-849a-b3344ca9133a", "crs": "epsg:32751", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 499980, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 499980, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 499980, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 499980, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211231T015619_N0301_R117_T51LWE_20211231T035247", "extent": {"lat": {"end": -13.566398424069876, "begin": -14.56073221375927}, "lon": {"end": 124.0190234178553, "begin": 123.49128821317358}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[552924.0, 8390201.0], [578583.0, 8499999.0], [609779.0, 8499999.0], [609779.0, 8390201.0], [552924.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-31T06:06:05.445Z", "updated": "2021-12-31T06:06:05.445Z", "datetime": "2021-12-31T02:01:26Z", "proj:epsg": 32751, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 49.37, "odc:file_format": "GeoTIFF", "odc:region_code": "51LWE", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 51, "sentinel:product_id": "S2B_MSIL2A_20211231T015619_N0301_R117_T51LWE_20211231T035247", "sentinel:grid_square": "WE", "sentinel:data_coverage": 40.1, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-31T06:06:05.445Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/51/L/WE/2021/12/31/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/51/L/WE/2021/12/31/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/51/L/WE/2021/12/31/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[552924.0, 8390201.0], [578583.0, 8499999.0], [609779.0, 8499999.0], [609779.0, 8390201.0], [552924.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 499980.0, "y": 8390200.0}, "lr": {"x": 609780.0, "y": 8390200.0}, "ul": {"x": 499980.0, "y": 8500000.0}, "ur": {"x": 609780.0, "y": 8500000.0}}, "spatial_reference": "epsg:32751"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:43.015579+00	localuser	\N
b394a831-1818-5e89-be4b-4a5b77aff92c	1	1	{"id": "b394a831-1818-5e89-be4b-4a5b77aff92c", "crs": "epsg:32751", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 600000, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 600000, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 600000, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 600000, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211231T015619_N0301_R117_T51LXE_20211231T035247", "extent": {"lat": {"end": -13.560932176423318, "begin": -14.559406653491093}, "lon": {"end": 124.94716787178676, "begin": 123.92427299922684}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[600001.0, 8390201.0], [600001.0, 8499999.0], [709799.0, 8499999.0], [709799.0, 8390201.0], [600001.0, 8390201.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-31T06:10:10.523Z", "updated": "2021-12-31T06:10:10.523Z", "datetime": "2021-12-31T02:01:23Z", "proj:epsg": 32751, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 45.03, "odc:file_format": "GeoTIFF", "odc:region_code": "51LXE", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 51, "sentinel:product_id": "S2B_MSIL2A_20211231T015619_N0301_R117_T51LXE_20211231T035247", "sentinel:grid_square": "XE", "sentinel:data_coverage": 100, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-31T06:10:10.523Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/51/L/XE/2021/12/31/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/51/L/XE/2021/12/31/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/51/L/XE/2021/12/31/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[600001.0, 8390201.0], [600001.0, 8499999.0], [709799.0, 8499999.0], [709799.0, 8390201.0], [600001.0, 8390201.0]]]}, "geo_ref_points": {"ll": {"x": 600000.0, "y": 8390200.0}, "lr": {"x": 709800.0, "y": 8390200.0}, "ul": {"x": 600000.0, "y": 8500000.0}, "ur": {"x": 709800.0, "y": 8500000.0}}, "spatial_reference": "epsg:32751"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:43.019728+00	localuser	\N
70a65a1b-5c7a-5872-8be7-a903c1f6394e	1	1	{"id": "70a65a1b-5c7a-5872-8be7-a903c1f6394e", "crs": "epsg:32750", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 499980, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 499980, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 499980, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 499980, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211230T022319_N0301_R103_T50LNK_20211230T042426", "extent": {"lat": {"end": -13.566398424069876, "begin": -14.461006408360928}, "lon": {"end": 118.01857511082643, "begin": 116.99982387830885}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[609779.0, 8401044.0], [500381.0, 8425988.0], [499981.0, 8426241.0], [499981.0, 8499999.0], [609779.0, 8499999.0], [609779.0, 8401044.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-30T06:40:58.456Z", "updated": "2021-12-30T06:40:58.456Z", "datetime": "2021-12-30T02:31:32Z", "proj:epsg": 32750, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 15.04, "odc:file_format": "GeoTIFF", "odc:region_code": "50LNK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 50, "sentinel:product_id": "S2B_MSIL2A_20211230T022319_N0301_R103_T50LNK_20211230T042426", "sentinel:grid_square": "NK", "sentinel:data_coverage": 78.22, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-30T06:40:58.456Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/NK/2021/12/30/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/NK/2021/12/30/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/50/L/NK/2021/12/30/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[609779.0, 8401044.0], [500381.0, 8425988.0], [499981.0, 8426241.0], [499981.0, 8499999.0], [609779.0, 8499999.0], [609779.0, 8401044.0]]]}, "geo_ref_points": {"ll": {"x": 499980.0, "y": 8390200.0}, "lr": {"x": 609780.0, "y": 8390200.0}, "ul": {"x": 499980.0, "y": 8500000.0}, "ur": {"x": 609780.0, "y": 8500000.0}}, "spatial_reference": "epsg:32750"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:43.028691+00	localuser	\N
45791e7c-ab7c-552d-822f-d118c1cffd04	1	1	{"id": "45791e7c-ab7c-552d-822f-d118c1cffd04", "crs": "epsg:32750", "grids": {"g20m": {"shape": [5490, 5490], "transform": [20, 0, 300000, 0, -20, 8500000, 0, 0, 1]}, "g60m": {"shape": [1830, 1830], "transform": [60, 0, 300000, 0, -60, 8500000, 0, 0, 1]}, "g320m": {"shape": [343, 343], "transform": [320, 0, 300000, 0, -320, 8500000, 0, 0, 1]}, "default": {"shape": [10980, 10980], "transform": [10, 0, 300000, 0, -10, 8500000, 0, 0, 1]}}, "label": "S2B_MSIL2A_20211230T022319_N0301_R103_T50LLK_20211230T042426", "extent": {"lat": {"end": -13.60108174363115, "begin": -14.076248473634621}, "lon": {"end": 116.16617884779642, "begin": 116.0588652005831}}, "$schema": "https://schemas.opendatacube.org/dataset", "lineage": {"source_datasets": {}}, "product": {"name": "s2_l2a"}, "geometry": {"type": "Polygon", "coordinates": [[[409799.0, 8443681.0], [409512.0, 8443681.0], [399401.0, 8445488.0], [398387.0, 8445808.0], [409737.0, 8496160.0], [409799.0, 8496237.0], [409799.0, 8443681.0]]]}, "properties": {"eo:gsd": 10, "created": "2021-12-30T06:32:28.324Z", "updated": "2021-12-30T06:32:28.324Z", "datetime": "2021-12-30T02:31:37Z", "proj:epsg": 32750, "eo:platform": "sentinel-2b", "eo:off_nadir": 0, "eo:instrument": "MSI", "eo:cloud_cover": 1.98, "odc:file_format": "GeoTIFF", "odc:region_code": "50LLK", "eo:constellation": "sentinel-2", "sentinel:sequence": "0", "sentinel:utm_zone": 50, "sentinel:product_id": "S2B_MSIL2A_20211230T022319_N0301_R103_T50LLK_20211230T042426", "sentinel:grid_square": "LK", "sentinel:data_coverage": 2.44, "sentinel:latitude_band": "L", "odc:processing_datetime": "2021-12-30T06:32:28.324Z", "sentinel:valid_cloud_cover": true}, "accessories": {"info": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/LK/2021/12/30/0/tileInfo.json"}, "metadata": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l2a/tiles/50/L/LK/2021/12/30/0/metadata.xml"}, "thumbnail": {"path": "https://roda.sentinel-hub.com/sentinel-s2-l1c/tiles/50/L/LK/2021/12/30/0/preview.jpg"}}, "grid_spatial": {"projection": {"valid_data": {"type": "Polygon", "coordinates": [[[409799.0, 8443681.0], [409512.0, 8443681.0], [399401.0, 8445488.0], [398387.0, 8445808.0], [409737.0, 8496160.0], [409799.0, 8496237.0], [409799.0, 8443681.0]]]}, "geo_ref_points": {"ll": {"x": 300000.0, "y": 8390200.0}, "lr": {"x": 409800.0, "y": 8390200.0}, "ul": {"x": 300000.0, "y": 8500000.0}, "ur": {"x": 409800.0, "y": 8500000.0}}, "spatial_reference": "epsg:32750"}}, "measurements": {"AOT": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/AOT.tif"}, "B01": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B01.tif"}, "B02": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B02.tif"}, "B03": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B03.tif"}, "B04": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B04.tif"}, "B05": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B05.tif"}, "B06": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B06.tif"}, "B07": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B07.tif"}, "B08": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B08.tif"}, "B09": {"grid": "g60m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B09.tif"}, "B11": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B11.tif"}, "B12": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B12.tif"}, "B8A": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/B8A.tif"}, "SCL": {"grid": "g20m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/SCL.tif"}, "WVP": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/WVP.tif"}, "visual": {"path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/TCI.tif"}, "overview": {"grid": "g320m", "path": "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/L2A_PVI.tif"}}}	\N	2022-03-23 02:19:43.0532+00	localuser	\N
\.


--
-- Data for Name: dataset_location; Type: TABLE DATA; Schema: agdc; Owner: agdc_admin
--

COPY agdc.dataset_location (id, dataset_ref, uri_scheme, uri_body, added, added_by, archived) FROM stdin;
1	fc1faf15-dcea-561f-907a-1e6c1a29bc63	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/MK/2022/1/S2A_38LMK_20220101_0_L2A/S2A_38LMK_20220101_0_L2A.json	2022-03-23 02:19:42.872334+00	localuser	\N
2	92595b50-144f-5b52-8b36-5937f5a8a361	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/RK/2022/1/S2A_50LRK_20220101_0_L2A/S2A_50LRK_20220101_0_L2A.json	2022-03-23 02:19:42.922387+00	localuser	\N
3	7480b834-2d80-51ef-8d20-02474d3ac321	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/RK/2021/12/S2B_38LRK_20211231_0_L2A/S2B_38LRK_20211231_0_L2A.json	2022-03-23 02:19:42.927873+00	localuser	\N
4	9a8c999a-727f-5200-a0e9-c21d89dfb7fb	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2022/1/S2A_50LPK_20220101_0_L2A/S2A_50LPK_20220101_0_L2A.json	2022-03-23 02:19:42.935975+00	localuser	\N
5	090ee981-efb2-554c-96ab-86863459a876	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/TE/2022/1/S2A_51LTE_20220101_0_L2A/S2A_51LTE_20220101_0_L2A.json	2022-03-23 02:19:42.929498+00	localuser	\N
6	89a69f26-6510-522d-859b-cca4fa13090f	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/LK/2022/1/S2A_38LLK_20220101_0_L2A/S2A_38LLK_20220101_0_L2A.json	2022-03-23 02:19:42.937279+00	localuser	\N
7	4ea6faba-332d-5288-b05e-e9ec249d2ff1	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/UE/2022/1/S2A_51LUE_20220101_0_L2A/S2A_51LUE_20220101_0_L2A.json	2022-03-23 02:19:42.949168+00	localuser	\N
8	0053ffe9-33cf-58c0-b61c-53b795c64702	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2022/1/S2A_50LQK_20220101_0_L2A/S2A_50LQK_20220101_0_L2A.json	2022-03-23 02:19:42.987259+00	localuser	\N
9	0559e840-6372-55d3-83b3-4749e8c7afc6	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/S2B_51LYE_20211231_0_L2A.json	2022-03-23 02:19:43.001502+00	localuser	\N
10	2010c062-ca58-5c0c-875b-91a1621d97f9	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/VE/2021/12/S2B_39LVE_20211231_0_L2A/S2B_39LVE_20211231_0_L2A.json	2022-03-23 02:19:42.991733+00	localuser	\N
11	52ca63d9-41a6-54ea-8b88-ce6cb96785f1	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/UE/2021/12/S2B_39LUE_20211231_0_L2A/S2B_39LUE_20211231_0_L2A.json	2022-03-23 02:19:42.996569+00	localuser	\N
12	082027ee-135d-5610-849a-b3344ca9133a	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/S2B_51LWE_20211231_0_L2A.json	2022-03-23 02:19:43.015579+00	localuser	\N
13	64e807fd-63b7-5a50-b38f-1421c6f1bbf7	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/38/L/NK/2022/1/S2A_38LNK_20220101_0_L2A/S2A_38LNK_20220101_0_L2A.json	2022-03-23 02:19:43.012183+00	localuser	\N
14	78be9cdf-c0b2-57a9-ab25-4beaafca6616	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/39/L/TE/2021/12/S2B_39LTE_20211231_0_L2A/S2B_39LTE_20211231_0_L2A.json	2022-03-23 02:19:43.02667+00	localuser	\N
15	70a65a1b-5c7a-5872-8be7-a903c1f6394e	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/NK/2021/12/S2B_50LNK_20211230_0_L2A/S2B_50LNK_20211230_0_L2A.json	2022-03-23 02:19:43.028691+00	localuser	\N
16	b394a831-1818-5e89-be4b-4a5b77aff92c	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/S2B_51LXE_20211231_0_L2A.json	2022-03-23 02:19:43.019728+00	localuser	\N
17	c6ddc88a-5fe9-5acc-98f9-eb8f437d1b6f	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/QK/2021/12/S2B_50LQK_20211230_0_L2A/S2B_50LQK_20211230_0_L2A.json	2022-03-23 02:19:43.033077+00	localuser	\N
18	4bc00074-bb56-5d82-b573-8372a0b8bc07	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/PK/2021/12/S2B_50LPK_20211230_0_L2A/S2B_50LPK_20211230_0_L2A.json	2022-03-23 02:19:43.0503+00	localuser	\N
19	38ea6660-95fa-5089-97a7-ab43c7322f36	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/MK/2021/12/S2B_50LMK_20211230_0_L2A/S2B_50LMK_20211230_0_L2A.json	2022-03-23 02:19:43.052808+00	localuser	\N
20	45791e7c-ab7c-552d-822f-d118c1cffd04	https	//sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/50/L/LK/2021/12/S2B_50LLK_20211230_0_L2A/S2B_50LLK_20211230_0_L2A.json	2022-03-23 02:19:43.0532+00	localuser	\N
\.


--
-- Data for Name: dataset_source; Type: TABLE DATA; Schema: agdc; Owner: agdc_admin
--

COPY agdc.dataset_source (dataset_ref, classifier, source_dataset_ref) FROM stdin;
\.


--
-- Data for Name: dataset_type; Type: TABLE DATA; Schema: agdc; Owner: agdc_admin
--

COPY agdc.dataset_type (id, name, metadata, metadata_type_ref, definition, added, added_by, updated) FROM stdin;
1	s2_l2a	{"product": {"name": "s2_l2a"}}	1	{"name": "s2_l2a", "metadata": {"product": {"name": "s2_l2a"}}, "description": "Sentinel-2a and Sentinel-2b imagery, processed to Level 2A (Surface Reflectance) and converted to Cloud Optimized GeoTIFFs", "measurements": [{"name": "B01", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_01", "coastal_aerosol"]}, {"name": "B02", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_02", "blue"]}, {"name": "B03", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_03", "green"]}, {"name": "B04", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_04", "red"]}, {"name": "B05", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_05", "red_edge_1"]}, {"name": "B06", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_06", "red_edge_2"]}, {"name": "B07", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_07", "red_edge_3"]}, {"name": "B08", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_08", "nir", "nir_1"]}, {"name": "B8A", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_8a", "nir_narrow", "nir_2"]}, {"name": "B09", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_09", "water_vapour"]}, {"name": "B11", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_11", "swir_1", "swir_16"]}, {"name": "B12", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["band_12", "swir_2", "swir_22"]}, {"name": "SCL", "dtype": "uint8", "units": "1", "nodata": 0, "aliases": ["mask", "qa"], "flags_definition": {"qa": {"bits": [0, 1, 2, 3, 4, 5, 6, 7], "values": {"0": "no data", "1": "saturated or defective", "2": "dark area pixels", "3": "cloud shadows", "4": "vegetation", "5": "bare soils", "6": "water", "7": "unclassified", "8": "cloud medium probability", "9": "cloud high probability", "10": "thin cirrus", "11": "snow or ice"}, "description": "Sen2Cor Scene Classification"}}}, {"name": "AOT", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["aerosol_optical_thickness"]}, {"name": "WVP", "dtype": "uint16", "units": "1", "nodata": 0, "aliases": ["scene_average_water_vapour"]}], "metadata_type": "eo3"}	2022-03-23 02:19:38.213677+00	localuser	\N
\.


--
-- Data for Name: metadata_type; Type: TABLE DATA; Schema: agdc; Owner: agdc_admin
--

COPY agdc.metadata_type (id, name, definition, added, added_by, updated) FROM stdin;
1	eo3	{"name": "eo3", "dataset": {"id": ["id"], "label": ["label"], "format": ["properties", "odc:file_format"], "sources": ["lineage", "source_datasets"], "creation_dt": ["properties", "odc:processing_datetime"], "grid_spatial": ["grid_spatial", "projection"], "measurements": ["measurements"], "search_fields": {"lat": {"type": "double-range", "max_offset": [["extent", "lat", "end"]], "min_offset": [["extent", "lat", "begin"]], "description": "Latitude range"}, "lon": {"type": "double-range", "max_offset": [["extent", "lon", "end"]], "min_offset": [["extent", "lon", "begin"]], "description": "Longitude range"}, "time": {"type": "datetime-range", "max_offset": [["properties", "dtr:end_datetime"], ["properties", "datetime"]], "min_offset": [["properties", "dtr:start_datetime"], ["properties", "datetime"]], "description": "Acquisition time range"}, "platform": {"offset": ["properties", "eo:platform"], "indexed": false, "description": "Platform code"}, "instrument": {"offset": ["properties", "eo:instrument"], "indexed": false, "description": "Instrument name"}, "cloud_cover": {"type": "double", "offset": ["properties", "eo:cloud_cover"], "indexed": false, "description": "Cloud cover percentage [0, 100]"}, "region_code": {"offset": ["properties", "odc:region_code"], "description": "Spatial reference code from the provider. For Landsat region_code is a scene path row:\\n        '{:03d}{:03d}.format(path,row)'.\\nFor Sentinel it is MGRS code. In general it is a unique string identifier that datasets covering roughly the same spatial region share.\\n"}, "product_family": {"offset": ["properties", "odc:product_family"], "indexed": false, "description": "Product family code"}, "dataset_maturity": {"offset": ["properties", "dea:dataset_maturity"], "indexed": false, "description": "One of - final|interim|nrt  (near real time)"}}}, "description": "Default EO3 with no custom fields"}	2022-03-23 02:19:21.064478+00	localuser	\N
2	eo	{"name": "eo", "dataset": {"id": ["id"], "label": ["ga_label"], "format": ["format", "name"], "sources": ["lineage", "source_datasets"], "creation_dt": ["creation_dt"], "grid_spatial": ["grid_spatial", "projection"], "measurements": ["image", "bands"], "search_fields": {"lat": {"type": "double-range", "max_offset": [["extent", "coord", "ur", "lat"], ["extent", "coord", "lr", "lat"], ["extent", "coord", "ul", "lat"], ["extent", "coord", "ll", "lat"]], "min_offset": [["extent", "coord", "ur", "lat"], ["extent", "coord", "lr", "lat"], ["extent", "coord", "ul", "lat"], ["extent", "coord", "ll", "lat"]], "description": "Latitude range"}, "lon": {"type": "double-range", "max_offset": [["extent", "coord", "ul", "lon"], ["extent", "coord", "ur", "lon"], ["extent", "coord", "ll", "lon"], ["extent", "coord", "lr", "lon"]], "min_offset": [["extent", "coord", "ul", "lon"], ["extent", "coord", "ur", "lon"], ["extent", "coord", "ll", "lon"], ["extent", "coord", "lr", "lon"]], "description": "Longitude range"}, "time": {"type": "datetime-range", "max_offset": [["extent", "to_dt"], ["extent", "center_dt"]], "min_offset": [["extent", "from_dt"], ["extent", "center_dt"]], "description": "Acquisition time"}, "platform": {"offset": ["platform", "code"], "description": "Platform code"}, "instrument": {"offset": ["instrument", "name"], "description": "Instrument name"}, "product_type": {"offset": ["product_type"], "description": "Product code"}}}, "description": "Earth Observation datasets.\\n\\nExpected metadata structure produced by the eodatasets library, as used internally at GA.\\n\\nhttps://github.com/GeoscienceAustralia/eo-datasets\\n"}	2022-03-23 02:19:21.09946+00	localuser	\N
3	telemetry	{"name": "telemetry", "dataset": {"id": ["id"], "label": ["ga_label"], "sources": ["lineage", "source_datasets"], "creation_dt": ["creation_dt"], "search_fields": {"gsi": {"offset": ["acquisition", "groundstation", "code"], "indexed": false, "description": "Ground Station Identifier (eg. ASA)"}, "time": {"type": "datetime-range", "max_offset": [["acquisition", "los"]], "min_offset": [["acquisition", "aos"]], "description": "Acquisition time"}, "orbit": {"type": "integer", "offset": ["acquisition", "platform_orbit"], "description": "Orbit number"}, "sat_row": {"type": "integer-range", "max_offset": [["image", "satellite_ref_point_end", "y"], ["image", "satellite_ref_point_start", "y"]], "min_offset": [["image", "satellite_ref_point_start", "y"]], "description": "Landsat row"}, "platform": {"offset": ["platform", "code"], "description": "Platform code"}, "sat_path": {"type": "integer-range", "max_offset": [["image", "satellite_ref_point_end", "x"], ["image", "satellite_ref_point_start", "x"]], "min_offset": [["image", "satellite_ref_point_start", "x"]], "description": "Landsat path"}, "instrument": {"offset": ["instrument", "name"], "description": "Instrument name"}, "product_type": {"offset": ["product_type"], "description": "Product code"}}}, "description": "Satellite telemetry datasets.\\n\\nExpected metadata structure produced by telemetry datasets from the eodatasets library, as used internally at GA.\\n\\nhttps://github.com/GeoscienceAustralia/eo-datasets\\n"}	2022-03-23 02:19:21.131523+00	localuser	\N
\.


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: localuser
--

COPY public.spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Data for Name: geocode_settings; Type: TABLE DATA; Schema: tiger; Owner: localuser
--

COPY tiger.geocode_settings (name, setting, unit, category, short_desc) FROM stdin;
\.


--
-- Data for Name: pagc_gaz; Type: TABLE DATA; Schema: tiger; Owner: localuser
--

COPY tiger.pagc_gaz (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- Data for Name: pagc_lex; Type: TABLE DATA; Schema: tiger; Owner: localuser
--

COPY tiger.pagc_lex (id, seq, word, stdword, token, is_custom) FROM stdin;
\.


--
-- Data for Name: pagc_rules; Type: TABLE DATA; Schema: tiger; Owner: localuser
--

COPY tiger.pagc_rules (id, rule, is_custom) FROM stdin;
\.


--
-- Data for Name: topology; Type: TABLE DATA; Schema: topology; Owner: localuser
--

COPY topology.topology (id, name, srid, "precision", hasz) FROM stdin;
\.


--
-- Data for Name: layer; Type: TABLE DATA; Schema: topology; Owner: localuser
--

COPY topology.layer (topology_id, layer_id, schema_name, table_name, feature_column, feature_type, level, child_id) FROM stdin;
\.


--
-- Data for Name: multiproduct_ranges; Type: TABLE DATA; Schema: wms; Owner: localuser
--

COPY wms.multiproduct_ranges (wms_product_name, lat_min, lat_max, lon_min, lon_max, dates, bboxes) FROM stdin;
\.


--
-- Data for Name: product_ranges; Type: TABLE DATA; Schema: wms; Owner: localuser
--

COPY wms.product_ranges (id, lat_min, lat_max, lon_min, lon_max, dates, bboxes) FROM stdin;
1	-14.5612479929242	-13.5397782720837	43.1437521655304	125.874209971104	["2021-12-30", "2021-12-31", "2022-01-01"]	{"EPSG:3577": {"top": -1447930.7956246277, "left": -8983986.351965345, "right": -666655.3529028345, "bottom": -4774156.450446432}, "EPSG:3857": {"top": -1521468.747490163, "left": 4802740.521978038, "right": 14012252.957988894, "bottom": -1638686.8548411622}, "EPSG:4326": {"top": -13.5397782720837, "left": 43.1437521655304, "right": 125.874209971104, "bottom": -14.5612479929242}}
\.


--
-- Data for Name: sub_product_ranges; Type: TABLE DATA; Schema: wms; Owner: localuser
--

COPY wms.sub_product_ranges (product_id, sub_product_id, lat_min, lat_max, lon_min, lon_max, dates, bboxes) FROM stdin;
\.


--
-- Name: dataset_location_id_seq; Type: SEQUENCE SET; Schema: agdc; Owner: agdc_admin
--

SELECT pg_catalog.setval('agdc.dataset_location_id_seq', 20, true);


--
-- Name: dataset_type_id_seq; Type: SEQUENCE SET; Schema: agdc; Owner: agdc_admin
--

SELECT pg_catalog.setval('agdc.dataset_type_id_seq', 1, true);


--
-- Name: metadata_type_id_seq; Type: SEQUENCE SET; Schema: agdc; Owner: agdc_admin
--

SELECT pg_catalog.setval('agdc.metadata_type_id_seq', 3, true);


--
-- Name: dataset pk_dataset; Type: CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset
    ADD CONSTRAINT pk_dataset PRIMARY KEY (id);


--
-- Name: dataset_location pk_dataset_location; Type: CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_location
    ADD CONSTRAINT pk_dataset_location PRIMARY KEY (id);


--
-- Name: dataset_source pk_dataset_source; Type: CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_source
    ADD CONSTRAINT pk_dataset_source PRIMARY KEY (dataset_ref, classifier);


--
-- Name: dataset_type pk_dataset_type; Type: CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_type
    ADD CONSTRAINT pk_dataset_type PRIMARY KEY (id);


--
-- Name: metadata_type pk_metadata_type; Type: CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.metadata_type
    ADD CONSTRAINT pk_metadata_type PRIMARY KEY (id);


--
-- Name: dataset_location uq_dataset_location_uri_scheme; Type: CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_location
    ADD CONSTRAINT uq_dataset_location_uri_scheme UNIQUE (uri_scheme, uri_body, dataset_ref);


--
-- Name: dataset_source uq_dataset_source_source_dataset_ref; Type: CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_source
    ADD CONSTRAINT uq_dataset_source_source_dataset_ref UNIQUE (source_dataset_ref, dataset_ref);


--
-- Name: dataset_type uq_dataset_type_name; Type: CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_type
    ADD CONSTRAINT uq_dataset_type_name UNIQUE (name);


--
-- Name: metadata_type uq_metadata_type_name; Type: CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.metadata_type
    ADD CONSTRAINT uq_metadata_type_name UNIQUE (name);


--
-- Name: multiproduct_ranges multiproduct_ranges_pkey; Type: CONSTRAINT; Schema: wms; Owner: localuser
--

ALTER TABLE ONLY wms.multiproduct_ranges
    ADD CONSTRAINT multiproduct_ranges_pkey PRIMARY KEY (wms_product_name);


--
-- Name: sub_product_ranges pk_sub_product_ranges; Type: CONSTRAINT; Schema: wms; Owner: localuser
--

ALTER TABLE ONLY wms.sub_product_ranges
    ADD CONSTRAINT pk_sub_product_ranges PRIMARY KEY (product_id, sub_product_id);


--
-- Name: product_ranges product_ranges_pkey; Type: CONSTRAINT; Schema: wms; Owner: localuser
--

ALTER TABLE ONLY wms.product_ranges
    ADD CONSTRAINT product_ranges_pkey PRIMARY KEY (id);


--
-- Name: dix_s2_l2a_lat_lon_time; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_s2_l2a_lat_lon_time ON agdc.dataset USING gist (agdc.float8range(((metadata #>> '{extent,lat,begin}'::text[]))::double precision, ((metadata #>> '{extent,lat,end}'::text[]))::double precision, '[]'::text), agdc.float8range(((metadata #>> '{extent,lon,begin}'::text[]))::double precision, ((metadata #>> '{extent,lon,end}'::text[]))::double precision, '[]'::text), tstzrange(LEAST(agdc.common_timestamp((metadata #>> '{properties,dtr:start_datetime}'::text[])), agdc.common_timestamp((metadata #>> '{properties,datetime}'::text[]))), GREATEST(agdc.common_timestamp((metadata #>> '{properties,dtr:end_datetime}'::text[])), agdc.common_timestamp((metadata #>> '{properties,datetime}'::text[]))), '[]'::text)) WHERE ((archived IS NULL) AND (dataset_type_ref = 1));


--
-- Name: dix_s2_l2a_region_code; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_s2_l2a_region_code ON agdc.dataset USING btree (((metadata #>> '{properties,odc:region_code}'::text[]))) WHERE ((archived IS NULL) AND (dataset_type_ref = 1));


--
-- Name: dix_s2_l2a_time_lat_lon; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_s2_l2a_time_lat_lon ON agdc.dataset USING gist (tstzrange(LEAST(agdc.common_timestamp((metadata #>> '{properties,dtr:start_datetime}'::text[])), agdc.common_timestamp((metadata #>> '{properties,datetime}'::text[]))), GREATEST(agdc.common_timestamp((metadata #>> '{properties,dtr:end_datetime}'::text[])), agdc.common_timestamp((metadata #>> '{properties,datetime}'::text[]))), '[]'::text), agdc.float8range(((metadata #>> '{extent,lat,begin}'::text[]))::double precision, ((metadata #>> '{extent,lat,end}'::text[]))::double precision, '[]'::text), agdc.float8range(((metadata #>> '{extent,lon,begin}'::text[]))::double precision, ((metadata #>> '{extent,lon,end}'::text[]))::double precision, '[]'::text)) WHERE ((archived IS NULL) AND (dataset_type_ref = 1));


--
-- Name: ix_agdc_dataset_dataset_type_ref; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX ix_agdc_dataset_dataset_type_ref ON agdc.dataset USING btree (dataset_type_ref);


--
-- Name: ix_agdc_dataset_location_dataset_ref; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX ix_agdc_dataset_location_dataset_ref ON agdc.dataset_location USING btree (dataset_ref);


--
-- Name: space_time_view_ds_idx; Type: INDEX; Schema: public; Owner: localuser
--

CREATE INDEX space_time_view_ds_idx ON public.space_time_view USING btree (dataset_type_ref);


--
-- Name: space_time_view_geom_idx; Type: INDEX; Schema: public; Owner: localuser
--

CREATE INDEX space_time_view_geom_idx ON public.space_time_view USING gist (spatial_extent);


--
-- Name: space_time_view_idx; Type: INDEX; Schema: public; Owner: localuser
--

CREATE UNIQUE INDEX space_time_view_idx ON public.space_time_view USING btree (id);


--
-- Name: space_time_view_time_idx; Type: INDEX; Schema: public; Owner: localuser
--

CREATE INDEX space_time_view_time_idx ON public.space_time_view USING spgist (temporal_extent);


--
-- Name: dataset row_update_time_dataset; Type: TRIGGER; Schema: agdc; Owner: agdc_admin
--

CREATE TRIGGER row_update_time_dataset BEFORE UPDATE ON agdc.dataset FOR EACH ROW EXECUTE FUNCTION agdc.set_row_update_time();


--
-- Name: dataset_type row_update_time_dataset_type; Type: TRIGGER; Schema: agdc; Owner: agdc_admin
--

CREATE TRIGGER row_update_time_dataset_type BEFORE UPDATE ON agdc.dataset_type FOR EACH ROW EXECUTE FUNCTION agdc.set_row_update_time();


--
-- Name: metadata_type row_update_time_metadata_type; Type: TRIGGER; Schema: agdc; Owner: agdc_admin
--

CREATE TRIGGER row_update_time_metadata_type BEFORE UPDATE ON agdc.metadata_type FOR EACH ROW EXECUTE FUNCTION agdc.set_row_update_time();


--
-- Name: dataset fk_dataset_dataset_type_ref_dataset_type; Type: FK CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset
    ADD CONSTRAINT fk_dataset_dataset_type_ref_dataset_type FOREIGN KEY (dataset_type_ref) REFERENCES agdc.dataset_type(id);


--
-- Name: dataset_location fk_dataset_location_dataset_ref_dataset; Type: FK CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_location
    ADD CONSTRAINT fk_dataset_location_dataset_ref_dataset FOREIGN KEY (dataset_ref) REFERENCES agdc.dataset(id);


--
-- Name: dataset fk_dataset_metadata_type_ref_metadata_type; Type: FK CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset
    ADD CONSTRAINT fk_dataset_metadata_type_ref_metadata_type FOREIGN KEY (metadata_type_ref) REFERENCES agdc.metadata_type(id);


--
-- Name: dataset_source fk_dataset_source_dataset_ref_dataset; Type: FK CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_source
    ADD CONSTRAINT fk_dataset_source_dataset_ref_dataset FOREIGN KEY (dataset_ref) REFERENCES agdc.dataset(id);


--
-- Name: dataset_source fk_dataset_source_source_dataset_ref_dataset; Type: FK CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_source
    ADD CONSTRAINT fk_dataset_source_source_dataset_ref_dataset FOREIGN KEY (source_dataset_ref) REFERENCES agdc.dataset(id);


--
-- Name: dataset_type fk_dataset_type_metadata_type_ref_metadata_type; Type: FK CONSTRAINT; Schema: agdc; Owner: agdc_admin
--

ALTER TABLE ONLY agdc.dataset_type
    ADD CONSTRAINT fk_dataset_type_metadata_type_ref_metadata_type FOREIGN KEY (metadata_type_ref) REFERENCES agdc.metadata_type(id);


--
-- Name: product_ranges product_ranges_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: localuser
--

ALTER TABLE ONLY wms.product_ranges
    ADD CONSTRAINT product_ranges_id_fkey FOREIGN KEY (id) REFERENCES agdc.dataset_type(id);


--
-- Name: sub_product_ranges sub_product_ranges_product_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: localuser
--

ALTER TABLE ONLY wms.sub_product_ranges
    ADD CONSTRAINT sub_product_ranges_product_id_fkey FOREIGN KEY (product_id) REFERENCES agdc.dataset_type(id);


--
-- Name: SCHEMA agdc; Type: ACL; Schema: -; Owner: agdc_admin
--

GRANT USAGE ON SCHEMA agdc TO agdc_user;
GRANT CREATE ON SCHEMA agdc TO agdc_manage;


--
-- Name: FUNCTION common_timestamp(text); Type: ACL; Schema: agdc; Owner: agdc_admin
--

GRANT ALL ON FUNCTION agdc.common_timestamp(text) TO agdc_user;


--
-- Name: TABLE dataset; Type: ACL; Schema: agdc; Owner: agdc_admin
--

GRANT SELECT ON TABLE agdc.dataset TO agdc_user;
GRANT INSERT ON TABLE agdc.dataset TO agdc_ingest;


--
-- Name: TABLE dataset_location; Type: ACL; Schema: agdc; Owner: agdc_admin
--

GRANT SELECT ON TABLE agdc.dataset_location TO agdc_user;
GRANT INSERT ON TABLE agdc.dataset_location TO agdc_ingest;


--
-- Name: SEQUENCE dataset_location_id_seq; Type: ACL; Schema: agdc; Owner: agdc_admin
--

GRANT SELECT,USAGE ON SEQUENCE agdc.dataset_location_id_seq TO agdc_ingest;


--
-- Name: TABLE dataset_source; Type: ACL; Schema: agdc; Owner: agdc_admin
--

GRANT SELECT ON TABLE agdc.dataset_source TO agdc_user;
GRANT INSERT ON TABLE agdc.dataset_source TO agdc_ingest;


--
-- Name: TABLE dataset_type; Type: ACL; Schema: agdc; Owner: agdc_admin
--

GRANT SELECT ON TABLE agdc.dataset_type TO agdc_user;
GRANT INSERT,DELETE ON TABLE agdc.dataset_type TO agdc_manage;


--
-- Name: SEQUENCE dataset_type_id_seq; Type: ACL; Schema: agdc; Owner: agdc_admin
--

GRANT SELECT,USAGE ON SEQUENCE agdc.dataset_type_id_seq TO agdc_ingest;


--
-- Name: TABLE metadata_type; Type: ACL; Schema: agdc; Owner: agdc_admin
--

GRANT SELECT ON TABLE agdc.metadata_type TO agdc_user;
GRANT INSERT,DELETE ON TABLE agdc.metadata_type TO agdc_manage;


--
-- Name: SEQUENCE metadata_type_id_seq; Type: ACL; Schema: agdc; Owner: agdc_admin
--

GRANT SELECT,USAGE ON SEQUENCE agdc.metadata_type_id_seq TO agdc_ingest;


--
-- Name: TABLE space_time_view; Type: ACL; Schema: public; Owner: localuser
--

GRANT SELECT ON TABLE public.space_time_view TO PUBLIC;


--
-- Name: space_view; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: localuser
--

REFRESH MATERIALIZED VIEW public.space_view;


--
-- Name: time_view; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: localuser
--

REFRESH MATERIALIZED VIEW public.time_view;


--
-- Name: space_time_view; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: localuser
--

REFRESH MATERIALIZED VIEW public.space_time_view;


--
-- PostgreSQL database dump complete
--

