--
-- PostgreSQL database dump
--

-- Dumped from database version 11.7 (Debian 11.7-2.pgdg100+1)
-- Dumped by pg_dump version 11.7 (Debian 11.7-2.pgdg100+1)

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
-- Name: pg_cron; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS pg_cron WITH SCHEMA public;


--
-- Name: EXTENSION pg_cron; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_cron IS 'Job scheduler for PostgreSQL';


--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA topology;


ALTER SCHEMA topology OWNER TO postgres;

--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: wms; Type: SCHEMA; Schema: -; Owner: opendatacube
--

CREATE SCHEMA wms;


ALTER SCHEMA wms OWNER TO opendatacube;

--
-- Name: hstore; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS hstore WITH SCHEMA public;


--
-- Name: EXTENSION hstore; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION hstore IS 'data type for storing sets of (key, value) pairs';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry, geography, and raster spatial types and functions';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: 
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
-- Name: wms_get_max(integer[], text); Type: FUNCTION; Schema: agdc; Owner: opendatacube
--

CREATE FUNCTION agdc.wms_get_max(integer[], text) RETURNS numeric
    LANGUAGE plpgsql
    AS $_$
            DECLARE
                ret numeric;
                ul text[] DEFAULT array_append('{extent, coord, ul}', $2);
                ur text[] DEFAULT array_append('{extent, coord, ur}', $2);
                ll text[] DEFAULT array_append('{extent, coord, ll}', $2);
                lr text[] DEFAULT array_append('{extent, coord, lr}', $2);
            BEGIN
                WITH m AS ( SELECT metadata FROM agdc.dataset WHERE dataset_type_ref = ANY ($1) AND archived IS NULL )
                SELECT MAX(GREATEST((m.metadata#>>ul)::numeric, (m.metadata#>>ur)::numeric,
                       (m.metadata#>>ll)::numeric, (m.metadata#>>lr)::numeric))
                INTO ret
                FROM m;
                RETURN ret;
            END;
            $_$;


ALTER FUNCTION agdc.wms_get_max(integer[], text) OWNER TO opendatacube;

--
-- Name: wms_get_min(integer[], text); Type: FUNCTION; Schema: agdc; Owner: opendatacube
--

CREATE FUNCTION agdc.wms_get_min(integer[], text) RETURNS numeric
    LANGUAGE plpgsql
    AS $_$
            DECLARE
                ret numeric;
                ul text[] DEFAULT array_append('{extent, coord, ul}', $2);
                ur text[] DEFAULT array_append('{extent, coord, ur}', $2);
                ll text[] DEFAULT array_append('{extent, coord, ll}', $2);
                lr text[] DEFAULT array_append('{extent, coord, lr}', $2);
            BEGIN
                WITH m AS ( SELECT metadata FROM agdc.dataset WHERE dataset_type_ref = any($1) AND archived IS NULL )
                SELECT MIN(LEAST((m.metadata#>>ul)::numeric, (m.metadata#>>ur)::numeric,
                       (m.metadata#>>ll)::numeric, (m.metadata#>>lr)::numeric))
                INTO ret
                FROM m;
                RETURN ret;
            END;
            $_$;


ALTER FUNCTION agdc.wms_get_min(integer[], text) OWNER TO opendatacube;

--
-- Name: asbinary(public.geometry); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.asbinary(public.geometry) RETURNS bytea
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/postgis-2.5', 'LWGEOM_asBinary';


ALTER FUNCTION public.asbinary(public.geometry) OWNER TO postgres;

--
-- Name: asbinary(public.geometry, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.asbinary(public.geometry, text) RETURNS bytea
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/postgis-2.5', 'LWGEOM_asBinary';


ALTER FUNCTION public.asbinary(public.geometry, text) OWNER TO postgres;

--
-- Name: astext(public.geometry); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.astext(public.geometry) RETURNS text
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/postgis-2.5', 'LWGEOM_asText';


ALTER FUNCTION public.astext(public.geometry) OWNER TO postgres;

--
-- Name: estimated_extent(text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.estimated_extent(text, text) RETURNS public.box2d
    LANGUAGE c IMMUTABLE STRICT SECURITY DEFINER
    AS '$libdir/postgis-2.5', 'geometry_estimated_extent';


ALTER FUNCTION public.estimated_extent(text, text) OWNER TO postgres;

--
-- Name: estimated_extent(text, text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.estimated_extent(text, text, text) RETURNS public.box2d
    LANGUAGE c IMMUTABLE STRICT SECURITY DEFINER
    AS '$libdir/postgis-2.5', 'geometry_estimated_extent';


ALTER FUNCTION public.estimated_extent(text, text, text) OWNER TO postgres;

--
-- Name: geomfromtext(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.geomfromtext(text) RETURNS public.geometry
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$SELECT ST_GeomFromText($1)$_$;


ALTER FUNCTION public.geomfromtext(text) OWNER TO postgres;

--
-- Name: geomfromtext(text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.geomfromtext(text, integer) RETURNS public.geometry
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$SELECT ST_GeomFromText($1, $2)$_$;


ALTER FUNCTION public.geomfromtext(text, integer) OWNER TO postgres;

--
-- Name: ndims(public.geometry); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.ndims(public.geometry) RETURNS smallint
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/postgis-2.5', 'LWGEOM_ndims';


ALTER FUNCTION public.ndims(public.geometry) OWNER TO postgres;

--
-- Name: setsrid(public.geometry, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.setsrid(public.geometry, integer) RETURNS public.geometry
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/postgis-2.5', 'LWGEOM_set_srid';


ALTER FUNCTION public.setsrid(public.geometry, integer) OWNER TO postgres;

--
-- Name: srid(public.geometry); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.srid(public.geometry) RETURNS integer
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/postgis-2.5', 'LWGEOM_get_srid';


ALTER FUNCTION public.srid(public.geometry) OWNER TO postgres;

--
-- Name: st_asbinary(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.st_asbinary(text) RETURNS bytea
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$ SELECT ST_AsBinary($1::geometry);$_$;


ALTER FUNCTION public.st_asbinary(text) OWNER TO postgres;

--
-- Name: st_astext(bytea); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.st_astext(bytea) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$ SELECT ST_AsText($1::geometry);$_$;


ALTER FUNCTION public.st_astext(bytea) OWNER TO postgres;

--
-- Name: wms_get_max(integer[], text); Type: FUNCTION; Schema: public; Owner: opendatacube
--

CREATE FUNCTION public.wms_get_max(integer[], text) RETURNS numeric
    LANGUAGE plpgsql
    AS $_$
            DECLARE
                ret numeric;
                ul text[] DEFAULT array_append('{extent, coord, ul}', $2);
                ur text[] DEFAULT array_append('{extent, coord, ur}', $2);
                ll text[] DEFAULT array_append('{extent, coord, ll}', $2);
                lr text[] DEFAULT array_append('{extent, coord, lr}', $2);
            BEGIN
                WITH m AS ( SELECT metadata FROM agdc.dataset WHERE dataset_type_ref = ANY ($1) AND archived IS NULL )
                SELECT MAX(GREATEST((m.metadata#>>ul)::numeric, (m.metadata#>>ur)::numeric,
                       (m.metadata#>>ll)::numeric, (m.metadata#>>lr)::numeric))
                INTO ret
                FROM m;
                RETURN ret;
            END;
            $_$;


ALTER FUNCTION public.wms_get_max(integer[], text) OWNER TO opendatacube;

--
-- Name: wms_get_min(integer[], text); Type: FUNCTION; Schema: public; Owner: opendatacube
--

CREATE FUNCTION public.wms_get_min(integer[], text) RETURNS numeric
    LANGUAGE plpgsql
    AS $_$
            DECLARE
                ret numeric;
                ul text[] DEFAULT array_append('{extent, coord, ul}', $2);
                ur text[] DEFAULT array_append('{extent, coord, ur}', $2);
                ll text[] DEFAULT array_append('{extent, coord, ll}', $2);
                lr text[] DEFAULT array_append('{extent, coord, lr}', $2);
            BEGIN
                WITH m AS ( SELECT metadata FROM agdc.dataset WHERE dataset_type_ref = any($1) AND archived IS NULL )
                SELECT MIN(LEAST((m.metadata#>>ul)::numeric, (m.metadata#>>ur)::numeric,
                       (m.metadata#>>ll)::numeric, (m.metadata#>>lr)::numeric))
                INTO ret
                FROM m;
                RETURN ret;
            END;
            $_$;


ALTER FUNCTION public.wms_get_min(integer[], text) OWNER TO opendatacube;

--
-- Name: gist_geometry_ops; Type: OPERATOR FAMILY; Schema: public; Owner: postgres
--

CREATE OPERATOR FAMILY public.gist_geometry_ops USING gist;


ALTER OPERATOR FAMILY public.gist_geometry_ops USING gist OWNER TO postgres;

--
-- Name: gist_geometry_ops; Type: OPERATOR CLASS; Schema: public; Owner: postgres
--

CREATE OPERATOR CLASS public.gist_geometry_ops
    FOR TYPE public.geometry USING gist FAMILY public.gist_geometry_ops AS
    STORAGE public.box2df ,
    OPERATOR 1 public.<<(public.geometry,public.geometry) ,
    OPERATOR 2 public.&<(public.geometry,public.geometry) ,
    OPERATOR 3 public.&&(public.geometry,public.geometry) ,
    OPERATOR 4 public.&>(public.geometry,public.geometry) ,
    OPERATOR 5 public.>>(public.geometry,public.geometry) ,
    OPERATOR 6 public.~=(public.geometry,public.geometry) ,
    OPERATOR 7 public.~(public.geometry,public.geometry) ,
    OPERATOR 8 public.@(public.geometry,public.geometry) ,
    OPERATOR 9 public.&<|(public.geometry,public.geometry) ,
    OPERATOR 10 public.<<|(public.geometry,public.geometry) ,
    OPERATOR 11 public.|>>(public.geometry,public.geometry) ,
    OPERATOR 12 public.|&>(public.geometry,public.geometry) ,
    OPERATOR 13 public.<->(public.geometry,public.geometry) FOR ORDER BY pg_catalog.float_ops ,
    OPERATOR 14 public.<#>(public.geometry,public.geometry) FOR ORDER BY pg_catalog.float_ops ,
    FUNCTION 1 (public.geometry, public.geometry) public.geometry_gist_consistent_2d(internal,public.geometry,integer) ,
    FUNCTION 2 (public.geometry, public.geometry) public.geometry_gist_union_2d(bytea,internal) ,
    FUNCTION 3 (public.geometry, public.geometry) public.geometry_gist_compress_2d(internal) ,
    FUNCTION 4 (public.geometry, public.geometry) public.geometry_gist_decompress_2d(internal) ,
    FUNCTION 5 (public.geometry, public.geometry) public.geometry_gist_penalty_2d(internal,internal,internal) ,
    FUNCTION 6 (public.geometry, public.geometry) public.geometry_gist_picksplit_2d(internal,internal) ,
    FUNCTION 7 (public.geometry, public.geometry) public.geometry_gist_same_2d(public.geometry,public.geometry,internal) ,
    FUNCTION 8 (public.geometry, public.geometry) public.geometry_gist_distance_2d(internal,public.geometry,integer);


ALTER OPERATOR CLASS public.gist_geometry_ops USING gist OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

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
    added_by name DEFAULT CURRENT_USER NOT NULL
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
    CONSTRAINT ck_metadata_type_alphanumeric_name CHECK (((name)::text ~* '^\w+$'::text))
);


ALTER TABLE agdc.metadata_type OWNER TO agdc_admin;

--
-- Name: dv_eo_dataset; Type: VIEW; Schema: agdc; Owner: opendatacube
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
  WHERE ((dataset.archived IS NULL) AND (dataset.metadata_type_ref = 1));


ALTER TABLE agdc.dv_eo_dataset OWNER TO opendatacube;

--
-- Name: dv_ls5_usgs_level1_scene_dataset; Type: VIEW; Schema: agdc; Owner: opendatacube
--

CREATE VIEW agdc.dv_ls5_usgs_level1_scene_dataset AS
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
  WHERE ((dataset.archived IS NULL) AND (dataset.dataset_type_ref = 3));


ALTER TABLE agdc.dv_ls5_usgs_level1_scene_dataset OWNER TO opendatacube;

--
-- Name: dv_ls7_usgs_level1_scene_dataset; Type: VIEW; Schema: agdc; Owner: opendatacube
--

CREATE VIEW agdc.dv_ls7_usgs_level1_scene_dataset AS
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
  WHERE ((dataset.archived IS NULL) AND (dataset.dataset_type_ref = 2));


ALTER TABLE agdc.dv_ls7_usgs_level1_scene_dataset OWNER TO opendatacube;

--
-- Name: dv_ls8_l1_pc_usgs_dataset; Type: VIEW; Schema: agdc; Owner: opendatacube
--

CREATE VIEW agdc.dv_ls8_l1_pc_usgs_dataset AS
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
  WHERE ((dataset.archived IS NULL) AND (dataset.dataset_type_ref = 4));


ALTER TABLE agdc.dv_ls8_l1_pc_usgs_dataset OWNER TO opendatacube;

--
-- Name: dv_ls8_usgs_level1_scene_dataset; Type: VIEW; Schema: agdc; Owner: opendatacube
--

CREATE VIEW agdc.dv_ls8_usgs_level1_scene_dataset AS
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
  WHERE ((dataset.archived IS NULL) AND (dataset.dataset_type_ref = 1));


ALTER TABLE agdc.dv_ls8_usgs_level1_scene_dataset OWNER TO opendatacube;

--
-- Name: dv_telemetry_dataset; Type: VIEW; Schema: agdc; Owner: opendatacube
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
  WHERE ((dataset.archived IS NULL) AND (dataset.metadata_type_ref = 2));


ALTER TABLE agdc.dv_telemetry_dataset OWNER TO opendatacube;

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
-- Name: multiproduct_ranges; Type: TABLE; Schema: wms; Owner: opendatacube
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


ALTER TABLE wms.multiproduct_ranges OWNER TO opendatacube;

--
-- Name: product_ranges; Type: TABLE; Schema: wms; Owner: opendatacube
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


ALTER TABLE wms.product_ranges OWNER TO opendatacube;

--
-- Name: sub_product_ranges; Type: TABLE; Schema: wms; Owner: opendatacube
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


ALTER TABLE wms.sub_product_ranges OWNER TO opendatacube;

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

COPY agdc.dataset (id, metadata_type_ref, dataset_type_ref, metadata, archived, added, added_by) FROM stdin;
ecc38ae4-5e00-56d3-96a3-8a8d9feb35d9	1	1	{"id": "ecc38ae4-5e00-56d3-96a3-8a8d9feb35d9", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019365LGN00", "extent": {"coord": {"ll": {"lat": -44.24807464861568, "lon": 145.73871923644134}, "lr": {"lat": -44.24239455045583, "lon": 148.69949366724586}, "ul": {"lat": -42.11443640852102, "lon": 145.7818996737607}, "ur": {"lat": -42.10916220129073, "lon": 148.6413253937152}}, "to_dt": "2019-12-31 23:52:54.9000300Z", "from_dt": "2019-12-31 23:52:54.9000300Z", "center_dt": "2019-12-31 23:52:54.9000300Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-12-31", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 399300.0, "y": -4900200.0}, "lr": {"x": 635700.0, "y": -4900200.0}, "ul": {"x": 399300.0, "y": -4663200.0}, "ur": {"x": 635700.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:14.967231+00	opendatacube
d1c6cfdf-a733-5bad-aff6-c655092e069f	1	1	{"id": "d1c6cfdf-a733-5bad-aff6-c655092e069f", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80910902019356LGN00", "extent": {"coord": {"ll": {"lat": -44.21465373360978, "lon": 144.17345194769433}, "lr": {"lat": -44.249590101327925, "lon": 147.1027089474793}, "ul": {"lat": -42.10730495957889, "lon": 144.26903999396603}, "ur": {"lat": -42.13977286754249, "lon": 147.09923019048784}}, "to_dt": "2019-12-22 23:59:08.5011710Z", "from_dt": "2019-12-22 23:59:08.5011710Z", "center_dt": "2019-12-22 23:59:08.5011710Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-12-22", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 274200.0, "y": -4899600.0}, "lr": {"x": 508200.0, "y": -4899600.0}, "ul": {"x": 274200.0, "y": -4665300.0}, "ur": {"x": 508200.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:15.006945+00	opendatacube
6968ce4c-b645-58ce-80f4-10ac59cf0ecb	1	1	{"id": "6968ce4c-b645-58ce-80f4-10ac59cf0ecb", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80910902019340LGN00", "extent": {"coord": {"ll": {"lat": -44.214560791500325, "lon": 144.16970111151326}, "lr": {"lat": -44.24959341800632, "lon": 147.0989513087264}, "ul": {"lat": -42.10721858090196, "lon": 144.26541561135187}, "ur": {"lat": -42.13977594975431, "lon": 147.09559982265046}}, "to_dt": "2019-12-06 23:59:11.3132560Z", "from_dt": "2019-12-06 23:59:11.3132560Z", "center_dt": "2019-12-06 23:59:11.3132560Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-12-06", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 273900.0, "y": -4899600.0}, "lr": {"x": 507900.0, "y": -4899600.0}, "ul": {"x": 273900.0, "y": -4665300.0}, "ur": {"x": 507900.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:15.050386+00	opendatacube
c23926f9-c2ff-58f0-8506-db92a10a4cb6	1	1	{"id": "c23926f9-c2ff-58f0-8506-db92a10a4cb6", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019349LGN00", "extent": {"coord": {"ll": {"lat": -44.24794964146216, "lon": 145.7274493649566}, "lr": {"lat": -44.24256165735517, "lon": 148.6882270260159}, "ul": {"lat": -42.11432033493224, "lon": 145.77101539085845}, "ur": {"lat": -42.109317367986094, "lon": 148.63044394859878}}, "to_dt": "2019-12-15 23:52:59.2829260Z", "from_dt": "2019-12-15 23:52:59.2829260Z", "center_dt": "2019-12-15 23:52:59.2829260Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-12-15", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 398400.0, "y": -4900200.0}, "lr": {"x": 634800.0, "y": -4900200.0}, "ul": {"x": 398400.0, "y": -4663200.0}, "ur": {"x": 634800.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.06925+00	opendatacube
226df188-700f-503a-970b-e8ddc12d1e88	1	1	{"id": "226df188-700f-503a-970b-e8ddc12d1e88", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019324LGN00", "extent": {"coord": {"ll": {"lat": -44.21465373360978, "lon": 144.17345194769433}, "lr": {"lat": -44.24959341800632, "lon": 147.0989513087264}, "ul": {"lat": -42.10730495957889, "lon": 144.26903999396603}, "ur": {"lat": -42.13977594975431, "lon": 147.09559982265046}}, "to_dt": "2019-11-20 23:59:11.6198170Z", "from_dt": "2019-11-20 23:59:11.6198170Z", "center_dt": "2019-11-20 23:59:11.6198170Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-11-20", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 274200.0, "y": -4899600.0}, "lr": {"x": 507900.0, "y": -4899600.0}, "ul": {"x": 274200.0, "y": -4665300.0}, "ur": {"x": 507900.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.195046+00	opendatacube
280a5f94-95ef-5709-a450-1dce13ad0cfe	1	1	{"id": "280a5f94-95ef-5709-a450-1dce13ad0cfe", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019333LGN00", "extent": {"coord": {"ll": {"lat": -44.24794964146216, "lon": 145.7274493649566}, "lr": {"lat": -44.24256165735517, "lon": 148.6882270260159}, "ul": {"lat": -42.11432033493224, "lon": 145.77101539085845}, "ur": {"lat": -42.109317367986094, "lon": 148.63044394859878}}, "to_dt": "2019-11-29 23:53:00.8813289Z", "from_dt": "2019-11-29 23:53:00.8813289Z", "center_dt": "2019-11-29 23:53:00.8813289Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-11-29", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 398400.0, "y": -4900200.0}, "lr": {"x": 634800.0, "y": -4900200.0}, "ul": {"x": 398400.0, "y": -4663200.0}, "ur": {"x": 634800.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.201128+00	opendatacube
bbf7b384-76e1-56dd-b558-6ce5abe3ce97	1	1	{"id": "bbf7b384-76e1-56dd-b558-6ce5abe3ce97", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019317LGN00", "extent": {"coord": {"ll": {"lat": -44.24786568583852, "lon": 145.71993615798468}, "lr": {"lat": -44.242672444900855, "lon": 148.6807158778222}, "ul": {"lat": -42.114242379130296, "lon": 145.7637592379975}, "ur": {"lat": -42.10942023945261, "lon": 148.62318960437858}}, "to_dt": "2019-11-13 23:53:02.8315650Z", "from_dt": "2019-11-13 23:53:02.8315650Z", "center_dt": "2019-11-13 23:53:02.8315650Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-11-13", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 397800.0, "y": -4900200.0}, "lr": {"x": 634200.0, "y": -4900200.0}, "ul": {"x": 397800.0, "y": -4663200.0}, "ur": {"x": 634200.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.264582+00	opendatacube
8c4fcc58-6b7b-55e8-a0b8-241eb4dabec4	1	1	{"id": "8c4fcc58-6b7b-55e8-a0b8-241eb4dabec4", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019285LGN00", "extent": {"coord": {"ll": {"lat": -44.247653635497244, "lon": 145.70115328435165}, "lr": {"lat": -44.24294725402083, "lon": 148.66193781959473}, "ul": {"lat": -42.11404548272987, "lon": 145.7456189821676}, "ur": {"lat": -42.10967541258017, "lon": 148.60505357889122}}, "to_dt": "2019-10-12 23:53:04.9355130Z", "from_dt": "2019-10-12 23:53:04.9355130Z", "center_dt": "2019-10-12 23:53:04.9355130Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-10-12", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 396300.0, "y": -4900200.0}, "lr": {"x": 632700.0, "y": -4900200.0}, "ul": {"x": 396300.0, "y": -4663200.0}, "ur": {"x": 632700.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.456443+00	opendatacube
340513d4-546c-582f-9c18-b9c430ce9c0a	1	1	{"id": "340513d4-546c-582f-9c18-b9c430ce9c0a", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019253LGN00", "extent": {"coord": {"ll": {"lat": -44.24778123620461, "lon": 145.71242298378456}, "lr": {"lat": -44.24278273879451, "lon": 148.67320468661987}, "ul": {"lat": -42.1141639646068, "lon": 145.75650311392587}, "ur": {"lat": -42.10952265251364, "lon": 148.6159352223743}}, "to_dt": "2019-09-10 23:52:56.6020800Z", "from_dt": "2019-09-10 23:52:56.6020800Z", "center_dt": "2019-09-10 23:52:56.6020800Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-09-10", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 397200.0, "y": -4900200.0}, "lr": {"x": 633600.0, "y": -4900200.0}, "ul": {"x": 397200.0, "y": -4663200.0}, "ur": {"x": 633600.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.653582+00	opendatacube
68832511-490e-5ddd-b237-a20b4cf7d8f0	1	1	{"id": "68832511-490e-5ddd-b237-a20b4cf7d8f0", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80900902019221LGN00", "extent": {"coord": {"ll": {"lat": -44.24773882613563, "lon": 145.70866640903395}, "lr": {"lat": -44.24283770061945, "lon": 148.6694490749504}, "ul": {"lat": -42.11412458532606, "lon": 145.75287506273878}, "ur": {"lat": -42.109573687139985, "lon": 148.61230801725574}}, "to_dt": "2019-08-09 23:52:48.1197129Z", "from_dt": "2019-08-09 23:52:48.1197129Z", "center_dt": "2019-08-09 23:52:48.1197129Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-08-09", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 396900.0, "y": -4900200.0}, "lr": {"x": 633300.0, "y": -4900200.0}, "ul": {"x": 396900.0, "y": -4663200.0}, "ur": {"x": 633300.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:15.837377+00	opendatacube
9f8dc1ed-8224-596b-9b79-919feaab0d52	1	1	{"id": "9f8dc1ed-8224-596b-9b79-919feaab0d52", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019189LGN00", "extent": {"coord": {"ll": {"lat": -44.247653635497244, "lon": 145.70115328435165}, "lr": {"lat": -44.24294725402083, "lon": 148.66193781959473}, "ul": {"lat": -42.11404548272987, "lon": 145.7456189821676}, "ur": {"lat": -42.10967541258017, "lon": 148.60505357889122}}, "to_dt": "2019-07-08 23:52:37.4689560Z", "from_dt": "2019-07-08 23:52:37.4689560Z", "center_dt": "2019-07-08 23:52:37.4689560Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-07-08", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 396300.0, "y": -4900200.0}, "lr": {"x": 632700.0, "y": -4900200.0}, "ul": {"x": 396300.0, "y": -4663200.0}, "ur": {"x": 632700.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.020739+00	opendatacube
b59946ec-abaa-5bc7-b3e5-978978c1ccb3	1	1	{"id": "b59946ec-abaa-5bc7-b3e5-978978c1ccb3", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019148LGN00", "extent": {"coord": {"ll": {"lat": -44.21343589274039, "lon": 144.12469249315507}, "lr": {"lat": -44.2496235771426, "lon": 147.05385960115333}, "ul": {"lat": -42.106173119346394, "lon": 144.22192426590277}, "ur": {"lat": -42.13980397684405, "lon": 147.05203537118055}}, "to_dt": "2019-05-28 23:58:34.6547040Z", "from_dt": "2019-05-28 23:58:34.6547040Z", "center_dt": "2019-05-28 23:58:34.6547040Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-05-28", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 270300.0, "y": -4899600.0}, "lr": {"x": 504300.0, "y": -4899600.0}, "ul": {"x": 270300.0, "y": -4665300.0}, "ur": {"x": 504300.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.222003+00	opendatacube
fe2e3e74-eb00-5724-bfca-4c186757d5d0	1	1	{"id": "fe2e3e74-eb00-5724-bfca-4c186757d5d0", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80910902019308LGN00", "extent": {"coord": {"ll": {"lat": -44.21428122718561, "lon": 144.15844871145077}, "lr": {"lat": -44.24960544869494, "lon": 147.0839207476197}, "ul": {"lat": -42.10695875888925, "lon": 144.25454255897253}, "ur": {"lat": -42.13978712995502, "lon": 147.08107834593886}}, "to_dt": "2019-11-04 23:59:15.3711020Z", "from_dt": "2019-11-04 23:59:15.3711020Z", "center_dt": "2019-11-04 23:59:15.3711020Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-11-04", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 273000.0, "y": -4899600.0}, "lr": {"x": 506700.0, "y": -4899600.0}, "ul": {"x": 273000.0, "y": -4665300.0}, "ur": {"x": 506700.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:15.264621+00	opendatacube
7a980882-5967-5e1e-84aa-63b82937a980	1	1	{"id": "7a980882-5967-5e1e-84aa-63b82937a980", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80910902019276LGN00", "extent": {"coord": {"ll": {"lat": -44.2140942360032, "lon": 144.15094720204758}, "lr": {"lat": -44.24961072242359, "lon": 147.07640546374597}, "ul": {"lat": -42.1067849725767, "lon": 144.24729393714827}, "ur": {"lat": -42.1397920308668, "lon": 147.0738176046622}}, "to_dt": "2019-10-03 23:59:14.3671139Z", "from_dt": "2019-10-03 23:59:14.3671139Z", "center_dt": "2019-10-03 23:59:14.3671139Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-10-03", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 272400.0, "y": -4899600.0}, "lr": {"x": 506100.0, "y": -4899600.0}, "ul": {"x": 272400.0, "y": -4665300.0}, "ur": {"x": 506100.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:15.499671+00	opendatacube
3636043f-c8e2-5180-b08d-8f21f983a522	1	1	{"id": "3636043f-c8e2-5180-b08d-8f21f983a522", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019244LGN00", "extent": {"coord": {"ll": {"lat": -44.21428122718561, "lon": 144.15844871145077}, "lr": {"lat": -44.249602626426636, "lon": 147.08767838876253}, "ul": {"lat": -42.10695875888925, "lon": 144.25454255897253}, "ur": {"lat": -42.13978450720193, "lon": 147.08470871587872}}, "to_dt": "2019-09-01 23:59:04.6581430Z", "from_dt": "2019-09-01 23:59:04.6581430Z", "center_dt": "2019-09-01 23:59:04.6581430Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-09-01", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 273000.0, "y": -4899600.0}, "lr": {"x": 507000.0, "y": -4899600.0}, "ul": {"x": 273000.0, "y": -4665300.0}, "ur": {"x": 507000.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.707418+00	opendatacube
664a80b8-68dc-5873-9fb6-02ad35a1ef8a	1	1	{"id": "664a80b8-68dc-5873-9fb6-02ad35a1ef8a", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80910902019212LGN00", "extent": {"coord": {"ll": {"lat": -44.2140942360032, "lon": 144.15094720204758}, "lr": {"lat": -44.24960814736062, "lon": 147.08016310593948}, "ul": {"lat": -42.1067849725767, "lon": 144.24729393714827}, "ur": {"lat": -42.13978963784333, "lon": 147.0774479755263}}, "to_dt": "2019-07-31 23:58:55.6212950Z", "from_dt": "2019-07-31 23:58:55.6212950Z", "center_dt": "2019-07-31 23:58:55.6212950Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-07-31", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 272400.0, "y": -4899600.0}, "lr": {"x": 506400.0, "y": -4899600.0}, "ul": {"x": 272400.0, "y": -4665300.0}, "ur": {"x": 506400.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.922774+00	opendatacube
fd0b1849-484e-55ba-89da-6c1d046cd949	1	1	{"id": "fd0b1849-484e-55ba-89da-6c1d046cd949", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019173LGN00", "extent": {"coord": {"ll": {"lat": -44.24752492329971, "lon": 145.68988365973578}, "lr": {"lat": -44.24311065848746, "lon": 148.65067085687897}, "ul": {"lat": -42.11392596875847, "lon": 145.73473491613464}, "ur": {"lat": -42.10982714119671, "lon": 148.59417185134177}}, "to_dt": "2019-06-22 23:52:33.7530019Z", "from_dt": "2019-06-22 23:52:33.7530019Z", "center_dt": "2019-06-22 23:52:33.7530019Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-06-22", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 395400.0, "y": -4900200.0}, "lr": {"x": 631800.0, "y": -4900200.0}, "ul": {"x": 395400.0, "y": -4663200.0}, "ur": {"x": 631800.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.121746+00	opendatacube
16b91827-f8ba-5845-b308-84d60dee738f	1	1	{"id": "16b91827-f8ba-5845-b308-84d60dee738f", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019141LGN00", "extent": {"coord": {"ll": {"lat": -44.247438497683326, "lon": 145.68237061854364}, "lr": {"lat": -44.24321897769732, "lon": 148.64315949555998}, "ul": {"lat": -42.11384571940042, "lon": 145.72747890890804}, "ur": {"lat": -42.1099277205689, "lon": 148.5869173198862}}, "to_dt": "2019-05-21 23:52:20.1047020Z", "from_dt": "2019-05-21 23:52:20.1047020Z", "center_dt": "2019-05-21 23:52:20.1047020Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-05-21", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 394800.0, "y": -4900200.0}, "lr": {"x": 631200.0, "y": -4900200.0}, "ul": {"x": 394800.0, "y": -4663200.0}, "ur": {"x": 631200.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.323966+00	opendatacube
8c654b0a-0512-58a5-82e9-ab5129253d7c	1	1	{"id": "8c654b0a-0512-58a5-82e9-ab5129253d7c", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80910902019292LGN00", "extent": {"coord": {"ll": {"lat": -44.2140942360032, "lon": 144.15094720204758}, "lr": {"lat": -44.24961072242359, "lon": 147.07640546374597}, "ul": {"lat": -42.1067849725767, "lon": 144.24729393714827}, "ur": {"lat": -42.1397920308668, "lon": 147.0738176046622}}, "to_dt": "2019-10-19 23:59:16.2345630Z", "from_dt": "2019-10-19 23:59:16.2345630Z", "center_dt": "2019-10-19 23:59:16.2345630Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-10-19", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 272400.0, "y": -4899600.0}, "lr": {"x": 506100.0, "y": -4899600.0}, "ul": {"x": 272400.0, "y": -4665300.0}, "ur": {"x": 506100.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:15.40613+00	opendatacube
c20c3d4f-93e8-5d0a-baf0-108ab5c8281a	1	1	{"id": "c20c3d4f-93e8-5d0a-baf0-108ab5c8281a", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019269LGN00", "extent": {"coord": {"ll": {"lat": -44.24769629256625, "lon": 145.70490984254832}, "lr": {"lat": -44.242892539028546, "lon": 148.66569345260072}, "ul": {"lat": -42.114085091366874, "lon": 145.74924701881233}, "ur": {"lat": -42.10962460716244, "lon": 148.60868080275438}}, "to_dt": "2019-09-26 23:53:01.9585310Z", "from_dt": "2019-09-26 23:53:01.9585310Z", "center_dt": "2019-09-26 23:53:01.9585310Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-09-26", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 396600.0, "y": -4900200.0}, "lr": {"x": 633000.0, "y": -4900200.0}, "ul": {"x": 396600.0, "y": -4663200.0}, "ur": {"x": 633000.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.62506+00	opendatacube
27247a17-537f-51a0-afad-3159cfac5349	1	1	{"id": "27247a17-537f-51a0-afad-3159cfac5349", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019228LGN00", "extent": {"coord": {"ll": {"lat": -44.214187793090595, "lon": 144.15469794766946}, "lr": {"lat": -44.24960814736062, "lon": 147.08016310593948}, "ul": {"lat": -42.10687192289577, "lon": 144.25091824007023}, "ur": {"lat": -42.13978963784333, "lon": 147.0774479755263}}, "to_dt": "2019-08-16 23:59:01.1157820Z", "from_dt": "2019-08-16 23:59:01.1157820Z", "center_dt": "2019-08-16 23:59:01.1157820Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-08-16", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 272700.0, "y": -4899600.0}, "lr": {"x": 506400.0, "y": -4899600.0}, "ul": {"x": 272700.0, "y": -4665300.0}, "ur": {"x": 506400.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.821468+00	opendatacube
e5058524-c785-551a-af81-baede63fcbaf	1	1	{"id": "e5058524-c785-551a-af81-baede63fcbaf", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80910902019196LGN00", "extent": {"coord": {"ll": {"lat": -44.2140942360032, "lon": 144.15094720204758}, "lr": {"lat": -44.24960814736062, "lon": 147.08016310593948}, "ul": {"lat": -42.1067849725767, "lon": 144.24729393714827}, "ur": {"lat": -42.13978963784333, "lon": 147.0774479755263}}, "to_dt": "2019-07-15 23:58:49.2838210Z", "from_dt": "2019-07-15 23:58:49.2838210Z", "center_dt": "2019-07-15 23:58:49.2838210Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-07-15", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 272400.0, "y": -4899600.0}, "lr": {"x": 506400.0, "y": -4899600.0}, "ul": {"x": 272400.0, "y": -4665300.0}, "ur": {"x": 506400.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:16.00528+00	opendatacube
a1b2d6de-f2e1-5a12-a1b7-0f405646f20c	1	1	{"id": "a1b2d6de-f2e1-5a12-a1b7-0f405646f20c", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019157LGN00", "extent": {"coord": {"ll": {"lat": -44.247438497683326, "lon": 145.68237061854364}, "lr": {"lat": -44.24321897769732, "lon": 148.64315949555998}, "ul": {"lat": -42.11384571940042, "lon": 145.72747890890804}, "ur": {"lat": -42.1099277205689, "lon": 148.5869173198862}}, "to_dt": "2019-06-06 23:52:28.0464200Z", "from_dt": "2019-06-06 23:52:28.0464200Z", "center_dt": "2019-06-06 23:52:28.0464200Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-06-06", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 394800.0, "y": -4900200.0}, "lr": {"x": 631200.0, "y": -4900200.0}, "ul": {"x": 394800.0, "y": -4663200.0}, "ur": {"x": 631200.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.196149+00	opendatacube
90659d3d-b27c-5be5-b343-b271d811e9f1	1	1	{"id": "90659d3d-b27c-5be5-b343-b271d811e9f1", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019125LGN00", "extent": {"coord": {"ll": {"lat": -44.24752492329971, "lon": 145.68988365973578}, "lr": {"lat": -44.24305631375123, "lon": 148.6544265217099}, "ul": {"lat": -42.11392596875847, "lon": 145.73473491613464}, "ur": {"lat": -42.109776679598134, "lon": 148.59779910316388}}, "to_dt": "2019-05-05 23:52:09.7704610Z", "from_dt": "2019-05-05 23:52:09.7704610Z", "center_dt": "2019-05-05 23:52:09.7704610Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-05-05", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 395400.0, "y": -4900200.0}, "lr": {"x": 632100.0, "y": -4900200.0}, "ul": {"x": 395400.0, "y": -4663200.0}, "ur": {"x": 632100.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.385711+00	opendatacube
e86659de-aa87-58a0-9eec-fd7c41505093	1	1	{"id": "e86659de-aa87-58a0-9eec-fd7c41505093", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019301LGN00", "extent": {"coord": {"ll": {"lat": -44.24773882613563, "lon": 145.70866640903395}, "lr": {"lat": -44.24283770061945, "lon": 148.6694490749504}, "ul": {"lat": -42.11412458532606, "lon": 145.75287506273878}, "ur": {"lat": -42.109573687139985, "lon": 148.61230801725574}}, "to_dt": "2019-10-28 23:53:05.3338799Z", "from_dt": "2019-10-28 23:53:05.3338799Z", "center_dt": "2019-10-28 23:53:05.3338799Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-10-28", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 396900.0, "y": -4900200.0}, "lr": {"x": 633300.0, "y": -4900200.0}, "ul": {"x": 396900.0, "y": -4663200.0}, "ur": {"x": 633300.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.407637+00	opendatacube
0f7118e3-9746-54ee-aaf7-767c18c9b4cb	1	1	{"id": "0f7118e3-9746-54ee-aaf7-767c18c9b4cb", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019260LGN00", "extent": {"coord": {"ll": {"lat": -44.214187793090595, "lon": 144.15469794766946}, "lr": {"lat": -44.24960544869494, "lon": 147.0839207476197}, "ul": {"lat": -42.10687192289577, "lon": 144.25091824007023}, "ur": {"lat": -42.13978712995502, "lon": 147.08107834593886}}, "to_dt": "2019-09-17 23:59:10.0308660Z", "from_dt": "2019-09-17 23:59:10.0308660Z", "center_dt": "2019-09-17 23:59:10.0308660Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-09-17", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 272700.0, "y": -4899600.0}, "lr": {"x": 506700.0, "y": -4899600.0}, "ul": {"x": 272700.0, "y": -4665300.0}, "ur": {"x": 506700.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.62446+00	opendatacube
3857627d-b42f-5962-8a39-03b36ebc31a5	1	1	{"id": "3857627d-b42f-5962-8a39-03b36ebc31a5", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019237LGN00", "extent": {"coord": {"ll": {"lat": -44.24773882613563, "lon": 145.70866640903395}, "lr": {"lat": -44.24278273879451, "lon": 148.67320468661987}, "ul": {"lat": -42.11412458532606, "lon": 145.75287506273878}, "ur": {"lat": -42.10952265251364, "lon": 148.6159352223743}}, "to_dt": "2019-08-25 23:52:52.5131420Z", "from_dt": "2019-08-25 23:52:52.5131420Z", "center_dt": "2019-08-25 23:52:52.5131420Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-08-25", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 396900.0, "y": -4900200.0}, "lr": {"x": 633600.0, "y": -4900200.0}, "ul": {"x": 396900.0, "y": -4663200.0}, "ur": {"x": 633600.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:15.805258+00	opendatacube
4a843b23-e0ab-5bbc-8f9c-004cb08db9f9	1	1	{"id": "4a843b23-e0ab-5bbc-8f9c-004cb08db9f9", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80900902019205LGN00", "extent": {"coord": {"ll": {"lat": -44.24773882613563, "lon": 145.70866640903395}, "lr": {"lat": -44.24278273879451, "lon": 148.67320468661987}, "ul": {"lat": -42.11412458532606, "lon": 145.75287506273878}, "ur": {"lat": -42.10952265251364, "lon": 148.6159352223743}}, "to_dt": "2019-07-24 23:52:41.7654270Z", "from_dt": "2019-07-24 23:52:41.7654270Z", "center_dt": "2019-07-24 23:52:41.7654270Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-07-24", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 396900.0, "y": -4900200.0}, "lr": {"x": 633600.0, "y": -4900200.0}, "ul": {"x": 396900.0, "y": -4663200.0}, "ur": {"x": 633600.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:16.001153+00	opendatacube
f1455031-02b8-5356-b70b-e2584008bbde	1	1	{"id": "f1455031-02b8-5356-b70b-e2584008bbde", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019164LGN00", "extent": {"coord": {"ll": {"lat": -44.213530310729226, "lon": 144.1284431109953}, "lr": {"lat": -44.2496235771426, "lon": 147.05385960115333}, "ul": {"lat": -42.106260869904666, "lon": 144.2255484563761}, "ur": {"lat": -42.13980397684405, "lon": 147.05203537118055}}, "to_dt": "2019-06-13 23:58:41.5973970Z", "from_dt": "2019-06-13 23:58:41.5973970Z", "center_dt": "2019-06-13 23:58:41.5973970Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-06-13", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 270600.0, "y": -4899600.0}, "lr": {"x": 504300.0, "y": -4899600.0}, "ul": {"x": 270600.0, "y": -4665300.0}, "ur": {"x": 504300.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.190623+00	opendatacube
98a38e95-86d7-5513-8585-53bb27e65462	1	1	{"id": "98a38e95-86d7-5513-8585-53bb27e65462", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019132LGN00", "extent": {"coord": {"ll": {"lat": -44.21362460573701, "lon": 144.1321937471614}, "lr": {"lat": -44.24961978664774, "lon": 147.0613748903203}, "ul": {"lat": -42.10634850614734, "lon": 144.22917266297634}, "ur": {"lat": -42.13980045431159, "lon": 147.05929611711372}}, "to_dt": "2019-05-12 23:58:25.4297690Z", "from_dt": "2019-05-12 23:58:25.4297690Z", "center_dt": "2019-05-12 23:58:25.4297690Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-05-12", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 270900.0, "y": -4899600.0}, "lr": {"x": 504900.0, "y": -4899600.0}, "ul": {"x": 270900.0, "y": -4665300.0}, "ur": {"x": 504900.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.375507+00	opendatacube
356eb1bd-32dc-568a-bd5b-c4051debcb41	1	1	{"id": "356eb1bd-32dc-568a-bd5b-c4051debcb41", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80910902019116LGN00", "extent": {"coord": {"ll": {"lat": -44.213718777762104, "lon": 144.1359444016296}, "lr": {"lat": -44.24961770599594, "lon": 147.06513253432635}, "ul": {"lat": -42.10643602807299, "lon": 144.23279688568255}, "ur": {"lat": -42.139798520747824, "lon": 147.0629264895723}}, "to_dt": "2019-04-26 23:58:16.0670509Z", "from_dt": "2019-04-26 23:58:16.0670509Z", "center_dt": "2019-04-26 23:58:16.0670509Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-04-26", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 271200.0, "y": -4899600.0}, "lr": {"x": 505200.0, "y": -4899600.0}, "ul": {"x": 271200.0, "y": -4665300.0}, "ur": {"x": 505200.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:16.415619+00	opendatacube
4c37e317-cfa7-50c3-8893-51264641950b	1	1	{"id": "4c37e317-cfa7-50c3-8893-51264641950b", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019084LGN00", "extent": {"coord": {"ll": {"lat": -44.21493182192942, "lon": 144.1847045643853}, "lr": {"lat": -44.24958309716408, "lon": 147.110224222988}, "ul": {"lat": -42.10756340960803, "lon": 144.27991323697825}, "ur": {"lat": -42.13976635852522, "lon": 147.1064909244059}}, "to_dt": "2019-03-25 23:58:26.4003490Z", "from_dt": "2019-03-25 23:58:26.4003490Z", "center_dt": "2019-03-25 23:58:26.4003490Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-03-25", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 275100.0, "y": -4899600.0}, "lr": {"x": 508800.0, "y": -4899600.0}, "ul": {"x": 275100.0, "y": -4665300.0}, "ur": {"x": 508800.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.615669+00	opendatacube
15a2b4f8-08b5-52e6-8474-f958f9a516f0	1	1	{"id": "15a2b4f8-08b5-52e6-8474-f958f9a516f0", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80900902019061LGN00", "extent": {"coord": {"ll": {"lat": -44.248116070655456, "lon": 145.74247587644737}, "lr": {"lat": -44.242338601338346, "lon": 148.70324919261046}, "ul": {"lat": -42.11447487035099, "lon": 145.78552778227325}, "ur": {"lat": -42.10911024986351, "lon": 148.6449525230127}}, "to_dt": "2019-03-02 23:52:22.0057970Z", "from_dt": "2019-03-02 23:52:22.0057970Z", "center_dt": "2019-03-02 23:52:22.0057970Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-03-02", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 399600.0, "y": -4900200.0}, "lr": {"x": 636000.0, "y": -4900200.0}, "ul": {"x": 399600.0, "y": -4663200.0}, "ur": {"x": 636000.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:16.822353+00	opendatacube
55708aeb-be6e-510c-8d2d-0d676e009a09	1	1	{"id": "55708aeb-be6e-510c-8d2d-0d676e009a09", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019029LGN00", "extent": {"coord": {"ll": {"lat": -44.248116070655456, "lon": 145.74247587644737}, "lr": {"lat": -44.242338601338346, "lon": 148.70324919261046}, "ul": {"lat": -42.11447487035099, "lon": 145.78552778227325}, "ur": {"lat": -42.10911024986351, "lon": 148.6449525230127}}, "to_dt": "2019-01-29 23:52:28.1566690Z", "from_dt": "2019-01-29 23:52:28.1566690Z", "center_dt": "2019-01-29 23:52:28.1566690Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-01-29", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 399600.0, "y": -4900200.0}, "lr": {"x": 636000.0, "y": -4900200.0}, "ul": {"x": 399600.0, "y": -4663200.0}, "ur": {"x": 636000.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.988407+00	opendatacube
5e9dcb87-5d11-5500-9e34-fe7b865a4bd1	1	1	{"id": "5e9dcb87-5d11-5500-9e34-fe7b865a4bd1", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019004LGN00", "extent": {"coord": {"ll": {"lat": -44.214560791500325, "lon": 144.16970111151326}, "lr": {"lat": -44.24959341800632, "lon": 147.0989513087264}, "ul": {"lat": -42.10721858090196, "lon": 144.26541561135187}, "ur": {"lat": -42.13977594975431, "lon": 147.09559982265046}}, "to_dt": "2019-01-04 23:58:44.4887789Z", "from_dt": "2019-01-04 23:58:44.4887789Z", "center_dt": "2019-01-04 23:58:44.4887789Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-01-04", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 273900.0, "y": -4899600.0}, "lr": {"x": 507900.0, "y": -4899600.0}, "ul": {"x": 273900.0, "y": -4665300.0}, "ur": {"x": 507900.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:17.195481+00	opendatacube
ea3105ea-920c-57f1-bb62-5645bac9ef0d	1	1	{"id": "ea3105ea-920c-57f1-bb62-5645bac9ef0d", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019109LGN00", "extent": {"coord": {"ll": {"lat": -44.24794964146216, "lon": 145.7274493649566}, "lr": {"lat": -44.24256165735517, "lon": 148.6882270260159}, "ul": {"lat": -42.11432033493224, "lon": 145.77101539085845}, "ur": {"lat": -42.109317367986094, "lon": 148.63044394859878}}, "to_dt": "2019-04-19 23:52:07.3171620Z", "from_dt": "2019-04-19 23:52:07.3171620Z", "center_dt": "2019-04-19 23:52:07.3171620Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-04-19", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 398400.0, "y": -4900200.0}, "lr": {"x": 634800.0, "y": -4900200.0}, "ul": {"x": 398400.0, "y": -4663200.0}, "ur": {"x": 634800.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.498993+00	opendatacube
a0c23e3d-fa17-550b-b4f7-d2d183a853ca	1	1	{"id": "a0c23e3d-fa17-550b-b4f7-d2d183a853ca", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019077LGN00", "extent": {"coord": {"ll": {"lat": -44.248116070655456, "lon": 145.74247587644737}, "lr": {"lat": -44.242338601338346, "lon": 148.70324919261046}, "ul": {"lat": -42.11447487035099, "lon": 145.78552778227325}, "ur": {"lat": -42.10911024986351, "lon": 148.6449525230127}}, "to_dt": "2019-03-18 23:52:16.8245270Z", "from_dt": "2019-03-18 23:52:16.8245270Z", "center_dt": "2019-03-18 23:52:16.8245270Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-03-18", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 399600.0, "y": -4900200.0}, "lr": {"x": 636000.0, "y": -4900200.0}, "ul": {"x": 399600.0, "y": -4663200.0}, "ur": {"x": 636000.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.718646+00	opendatacube
bc7c6bcf-05f1-5435-8b56-b1848c41de71	1	1	{"id": "bc7c6bcf-05f1-5435-8b56-b1848c41de71", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80910902019052LGN00", "extent": {"coord": {"ll": {"lat": -44.21493182192942, "lon": 144.1847045643853}, "lr": {"lat": -44.24958309716408, "lon": 147.110224222988}, "ul": {"lat": -42.10756340960803, "lon": 144.27991323697825}, "ur": {"lat": -42.13976635852522, "lon": 147.1064909244059}}, "to_dt": "2019-02-21 23:58:35.4835830Z", "from_dt": "2019-02-21 23:58:35.4835830Z", "center_dt": "2019-02-21 23:58:35.4835830Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-02-21", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 275100.0, "y": -4899600.0}, "lr": {"x": 508800.0, "y": -4899600.0}, "ul": {"x": 275100.0, "y": -4665300.0}, "ur": {"x": 508800.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1GT"}	\N	2020-04-07 23:23:16.888115+00	opendatacube
13a02aed-9ec5-57dc-a6e4-7b2b9f73b4af	1	1	{"id": "13a02aed-9ec5-57dc-a6e4-7b2b9f73b4af", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019020LGN00", "extent": {"coord": {"ll": {"lat": -44.214839248825925, "lon": 144.18095367415415}, "lr": {"lat": -44.24958666104716, "lon": 147.10646658557448}, "ul": {"lat": -42.107477373933335, "lon": 144.27628880680015}, "ur": {"lat": -42.13976967046611, "lon": 147.1028605577467}}, "to_dt": "2019-01-20 23:58:41.2170730Z", "from_dt": "2019-01-20 23:58:41.2170730Z", "center_dt": "2019-01-20 23:58:41.2170730Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-01-20", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 274800.0, "y": -4899600.0}, "lr": {"x": 508500.0, "y": -4899600.0}, "ul": {"x": 274800.0, "y": -4665300.0}, "ur": {"x": 508500.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:17.068802+00	opendatacube
0396656a-231c-5b52-8117-87b9c372b15c	1	1	{"id": "0396656a-231c-5b52-8117-87b9c372b15c", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019100LGN00", "extent": {"coord": {"ll": {"lat": -44.21465373360978, "lon": 144.17345194769433}, "lr": {"lat": -44.249590101327925, "lon": 147.1027089474793}, "ul": {"lat": -42.10730495957889, "lon": 144.26903999396603}, "ur": {"lat": -42.13977286754249, "lon": 147.09923019048784}}, "to_dt": "2019-04-10 23:58:21.8610849Z", "from_dt": "2019-04-10 23:58:21.8610849Z", "center_dt": "2019-04-10 23:58:21.8610849Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-04-10", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 274200.0, "y": -4899600.0}, "lr": {"x": 508200.0, "y": -4899600.0}, "ul": {"x": 274200.0, "y": -4665300.0}, "ur": {"x": 508200.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.552904+00	opendatacube
8c5bee41-1f00-5df4-afc3-0d98385fdc49	1	1	{"id": "8c5bee41-1f00-5df4-afc3-0d98385fdc49", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_B1.TIF", "layer": 1}}}, "label": "LC80910902019068LGN00", "extent": {"coord": {"ll": {"lat": -44.21502427202773, "lon": 144.1884554725856}, "lr": {"lat": -44.24957559859118, "lon": 147.11773949567365}, "ul": {"lat": -42.10764933094582, "lon": 144.28353768296913}, "ur": {"lat": -42.13975939005015, "lon": 147.11375165584047}}, "to_dt": "2019-03-09 23:58:30.1830530Z", "from_dt": "2019-03-09 23:58:30.1830530Z", "center_dt": "2019-03-09 23:58:30.1830530Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-03-09", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 275400.0, "y": -4899600.0}, "lr": {"x": 509400.0, "y": -4899600.0}, "ul": {"x": 275400.0, "y": -4665300.0}, "ur": {"x": 509400.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.773782+00	opendatacube
087d8d60-6d09-52cc-ad83-ff8fb66a6505	1	1	{"id": "087d8d60-6d09-52cc-ad83-ff8fb66a6505", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019045LGN00", "extent": {"coord": {"ll": {"lat": -44.24807464861568, "lon": 145.73871923644134}, "lr": {"lat": -44.24239455045583, "lon": 148.69949366724586}, "ul": {"lat": -42.11443640852102, "lon": 145.7818996737607}, "ur": {"lat": -42.10916220129073, "lon": 148.6413253937152}}, "to_dt": "2019-02-14 23:52:26.1880890Z", "from_dt": "2019-02-14 23:52:26.1880890Z", "center_dt": "2019-02-14 23:52:26.1880890Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-02-14", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 399300.0, "y": -4900200.0}, "lr": {"x": 635700.0, "y": -4900200.0}, "ul": {"x": 399300.0, "y": -4663200.0}, "ur": {"x": 635700.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.999796+00	opendatacube
5ce6e081-3e22-5b2b-b8ce-a4a78d993dd6	1	1	{"id": "5ce6e081-3e22-5b2b-b8ce-a4a78d993dd6", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019093LGN00", "extent": {"coord": {"ll": {"lat": -44.2479914340183, "lon": 145.73120598067194}, "lr": {"lat": -44.24250607846521, "lon": 148.6919825839246}, "ul": {"lat": -42.11435914081101, "lon": 145.7746434780322}, "ur": {"lat": -42.10926576035286, "lon": 148.63407110648714}}, "to_dt": "2019-04-03 23:52:13.3733560Z", "from_dt": "2019-04-03 23:52:13.3733560Z", "center_dt": "2019-04-03 23:52:13.3733560Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-04-03", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 398700.0, "y": -4900200.0}, "lr": {"x": 635100.0, "y": -4900200.0}, "ul": {"x": 398700.0, "y": -4663200.0}, "ur": {"x": 635100.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.586433+00	opendatacube
7c73294b-6d68-5d75-a7c0-1d00b467ff84	1	1	{"id": "7c73294b-6d68-5d75-a7c0-1d00b467ff84", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019068LGN00", "extent": {"coord": {"ll": {"lat": -44.21502427202773, "lon": 144.1884554725856}, "lr": {"lat": -44.24957559859118, "lon": 147.11773949567365}, "ul": {"lat": -42.10764933094582, "lon": 144.28353768296913}, "ur": {"lat": -42.13975939005015, "lon": 147.11375165584047}}, "to_dt": "2019-03-09 23:58:30.1830530Z", "from_dt": "2019-03-09 23:58:30.1830530Z", "center_dt": "2019-03-09 23:58:30.1830530Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-03-09", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 275400.0, "y": -4899600.0}, "lr": {"x": 509400.0, "y": -4899600.0}, "ul": {"x": 275400.0, "y": -4665300.0}, "ur": {"x": 509400.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.777578+00	opendatacube
3c36cf24-9439-55a9-937d-a4739db5e7f2	1	1	{"id": "3c36cf24-9439-55a9-937d-a4739db5e7f2", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80910902019036LGN00", "extent": {"coord": {"ll": {"lat": -44.21493182192942, "lon": 144.1847045643853}, "lr": {"lat": -44.249579409678724, "lon": 147.1139818596957}, "ul": {"lat": -42.10756340960803, "lon": 144.27991323697825}, "ur": {"lat": -42.139762931719886, "lon": 147.1101212904442}}, "to_dt": "2019-02-05 23:58:38.2559600Z", "from_dt": "2019-02-05 23:58:38.2559600Z", "center_dt": "2019-02-05 23:58:38.2559600Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-02-05", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 275100.0, "y": -4899600.0}, "lr": {"x": 509100.0, "y": -4899600.0}, "ul": {"x": 275100.0, "y": -4665300.0}, "ur": {"x": 509100.0, "y": -4665300.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:16.967055+00	opendatacube
77d41e67-7b17-5038-b5d0-4c7f2955655d	1	1	{"id": "77d41e67-7b17-5038-b5d0-4c7f2955655d", "image": {"bands": {"nir": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B5.TIF", "layer": 1}, "red": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B4.TIF", "layer": 1}, "blue": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B2.TIF", "layer": 1}, "green": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B3.TIF", "layer": 1}, "lwir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B10.TIF", "layer": 1}, "lwir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B11.TIF", "layer": 1}, "swir1": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B6.TIF", "layer": 1}, "swir2": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B7.TIF", "layer": 1}, "cirrus": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B9.TIF", "layer": 1}, "quality": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_BQA.TIF", "layer": 1}, "panchromatic": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B8.TIF", "layer": 1}, "coastal_aerosol": {"path": "s3://landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_B1.TIF", "layer": 1}}}, "label": "LC80900902019013LGN00", "extent": {"coord": {"ll": {"lat": -44.2479914340183, "lon": 145.73120598067194}, "lr": {"lat": -44.24250607846521, "lon": 148.6919825839246}, "ul": {"lat": -42.11435914081101, "lon": 145.7746434780322}, "ur": {"lat": -42.10926576035286, "lon": 148.63407110648714}}, "to_dt": "2019-01-13 23:52:32.1435860Z", "from_dt": "2019-01-13 23:52:32.1435860Z", "center_dt": "2019-01-13 23:52:32.1435860Z"}, "format": {"name": "GeoTiff"}, "lineage": {"source_datasets": {}}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "creation_dt": "2019-01-13", "grid_spatial": {"projection": {"geo_ref_points": {"ll": {"x": 398700.0, "y": -4900200.0}, "lr": {"x": 635100.0, "y": -4900200.0}, "ul": {"x": 398700.0, "y": -4663200.0}, "ur": {"x": 635100.0, "y": -4663200.0}}, "spatial_reference": "EPSG:32655"}}, "product_type": "L1TP", "processing_level": "L1TP"}	\N	2020-04-07 23:23:17.152915+00	opendatacube
\.


--
-- Data for Name: dataset_location; Type: TABLE DATA; Schema: agdc; Owner: agdc_admin
--

COPY agdc.dataset_location (id, dataset_ref, uri_scheme, uri_body, added, added_by, archived) FROM stdin;
1	ecc38ae4-5e00-56d3-96a3-8a8d9feb35d9	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191231_20200111_01_T1/LC08_L1TP_090090_20191231_20200111_01_T1_MTL.txt	2020-04-07 23:23:14.967231+00	opendatacube	\N
2	d1c6cfdf-a733-5bad-aff6-c655092e069f	s3	//landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191222_20191223_01_RT/LC08_L1GT_091090_20191222_20191223_01_RT_MTL.txt	2020-04-07 23:23:15.006945+00	opendatacube	\N
3	6968ce4c-b645-58ce-80f4-10ac59cf0ecb	s3	//landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191206_20191207_01_RT/LC08_L1GT_091090_20191206_20191207_01_RT_MTL.txt	2020-04-07 23:23:15.050386+00	opendatacube	\N
4	c23926f9-c2ff-58f0-8506-db92a10a4cb6	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191215_20191226_01_T1/LC08_L1TP_090090_20191215_20191226_01_T1_MTL.txt	2020-04-07 23:23:15.06925+00	opendatacube	\N
5	226df188-700f-503a-970b-e8ddc12d1e88	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20191120_20191203_01_T1/LC08_L1TP_091090_20191120_20191203_01_T1_MTL.txt	2020-04-07 23:23:15.195046+00	opendatacube	\N
6	280a5f94-95ef-5709-a450-1dce13ad0cfe	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191129_20191216_01_T1/LC08_L1TP_090090_20191129_20191216_01_T1_MTL.txt	2020-04-07 23:23:15.201128+00	opendatacube	\N
7	bbf7b384-76e1-56dd-b558-6ce5abe3ce97	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191113_20191202_01_T1/LC08_L1TP_090090_20191113_20191202_01_T1_MTL.txt	2020-04-07 23:23:15.264582+00	opendatacube	\N
8	fe2e3e74-eb00-5724-bfca-4c186757d5d0	s3	//landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191104_20191105_01_RT/LC08_L1GT_091090_20191104_20191105_01_RT_MTL.txt	2020-04-07 23:23:15.264621+00	opendatacube	\N
9	8c654b0a-0512-58a5-82e9-ab5129253d7c	s3	//landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191019_20191020_01_RT/LC08_L1GT_091090_20191019_20191020_01_RT_MTL.txt	2020-04-07 23:23:15.40613+00	opendatacube	\N
10	e86659de-aa87-58a0-9eec-fd7c41505093	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191028_20191114_01_T1/LC08_L1TP_090090_20191028_20191114_01_T1_MTL.txt	2020-04-07 23:23:15.407637+00	opendatacube	\N
11	8c4fcc58-6b7b-55e8-a0b8-241eb4dabec4	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20191012_20191018_01_T1/LC08_L1TP_090090_20191012_20191018_01_T1_MTL.txt	2020-04-07 23:23:15.456443+00	opendatacube	\N
12	7a980882-5967-5e1e-84aa-63b82937a980	s3	//landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20191003_20191004_01_RT/LC08_L1GT_091090_20191003_20191004_01_RT_MTL.txt	2020-04-07 23:23:15.499671+00	opendatacube	\N
13	0f7118e3-9746-54ee-aaf7-767c18c9b4cb	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190917_20190926_01_T1/LC08_L1TP_091090_20190917_20190926_01_T1_MTL.txt	2020-04-07 23:23:15.62446+00	opendatacube	\N
14	c20c3d4f-93e8-5d0a-baf0-108ab5c8281a	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190926_20191017_01_T1/LC08_L1TP_090090_20190926_20191017_01_T1_MTL.txt	2020-04-07 23:23:15.62506+00	opendatacube	\N
15	340513d4-546c-582f-9c18-b9c430ce9c0a	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190910_20190917_01_T1/LC08_L1TP_090090_20190910_20190917_01_T1_MTL.txt	2020-04-07 23:23:15.653582+00	opendatacube	\N
16	3636043f-c8e2-5180-b08d-8f21f983a522	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190901_20190916_01_T1/LC08_L1TP_091090_20190901_20190916_01_T1_MTL.txt	2020-04-07 23:23:15.707418+00	opendatacube	\N
17	3857627d-b42f-5962-8a39-03b36ebc31a5	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190825_20190903_01_T1/LC08_L1TP_090090_20190825_20190903_01_T1_MTL.txt	2020-04-07 23:23:15.805258+00	opendatacube	\N
18	27247a17-537f-51a0-afad-3159cfac5349	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190816_20190902_01_T1/LC08_L1TP_091090_20190816_20190902_01_T1_MTL.txt	2020-04-07 23:23:15.821468+00	opendatacube	\N
19	68832511-490e-5ddd-b237-a20b4cf7d8f0	s3	//landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190809_20190810_01_RT/LC08_L1GT_090090_20190809_20190810_01_RT_MTL.txt	2020-04-07 23:23:15.837377+00	opendatacube	\N
20	664a80b8-68dc-5873-9fb6-02ad35a1ef8a	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190731_20190801_01_RT/LC08_L1TP_091090_20190731_20190801_01_RT_MTL.txt	2020-04-07 23:23:15.922774+00	opendatacube	\N
21	4a843b23-e0ab-5bbc-8f9c-004cb08db9f9	s3	//landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190724_20190725_01_RT/LC08_L1GT_090090_20190724_20190725_01_RT_MTL.txt	2020-04-07 23:23:16.001153+00	opendatacube	\N
22	e5058524-c785-551a-af81-baede63fcbaf	s3	//landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190715_20190716_01_RT/LC08_L1GT_091090_20190715_20190716_01_RT_MTL.txt	2020-04-07 23:23:16.00528+00	opendatacube	\N
23	9f8dc1ed-8224-596b-9b79-919feaab0d52	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190708_20190719_01_T1/LC08_L1TP_090090_20190708_20190719_01_T1_MTL.txt	2020-04-07 23:23:16.020739+00	opendatacube	\N
24	fd0b1849-484e-55ba-89da-6c1d046cd949	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190622_20190704_01_T1/LC08_L1TP_090090_20190622_20190704_01_T1_MTL.txt	2020-04-07 23:23:16.121746+00	opendatacube	\N
25	f1455031-02b8-5356-b70b-e2584008bbde	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190613_20190619_01_T1/LC08_L1TP_091090_20190613_20190619_01_T1_MTL.txt	2020-04-07 23:23:16.190623+00	opendatacube	\N
26	a1b2d6de-f2e1-5a12-a1b7-0f405646f20c	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190606_20190619_01_T1/LC08_L1TP_090090_20190606_20190619_01_T1_MTL.txt	2020-04-07 23:23:16.196149+00	opendatacube	\N
27	b59946ec-abaa-5bc7-b3e5-978978c1ccb3	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190528_20190605_01_T1/LC08_L1TP_091090_20190528_20190605_01_T1_MTL.txt	2020-04-07 23:23:16.222003+00	opendatacube	\N
28	16b91827-f8ba-5845-b308-84d60dee738f	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190521_20190604_01_T1/LC08_L1TP_090090_20190521_20190604_01_T1_MTL.txt	2020-04-07 23:23:16.323966+00	opendatacube	\N
29	98a38e95-86d7-5513-8585-53bb27e65462	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190512_20190521_01_T1/LC08_L1TP_091090_20190512_20190521_01_T1_MTL.txt	2020-04-07 23:23:16.375507+00	opendatacube	\N
30	90659d3d-b27c-5be5-b343-b271d811e9f1	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190505_20190520_01_T1/LC08_L1TP_090090_20190505_20190520_01_T1_MTL.txt	2020-04-07 23:23:16.385711+00	opendatacube	\N
31	356eb1bd-32dc-568a-bd5b-c4051debcb41	s3	//landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190426_20190427_01_RT/LC08_L1GT_091090_20190426_20190427_01_RT_MTL.txt	2020-04-07 23:23:16.415619+00	opendatacube	\N
32	ea3105ea-920c-57f1-bb62-5645bac9ef0d	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190419_20190507_01_T1/LC08_L1TP_090090_20190419_20190507_01_T1_MTL.txt	2020-04-07 23:23:16.498993+00	opendatacube	\N
33	0396656a-231c-5b52-8117-87b9c372b15c	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190410_20190422_01_T1/LC08_L1TP_091090_20190410_20190422_01_T1_MTL.txt	2020-04-07 23:23:16.552904+00	opendatacube	\N
34	5ce6e081-3e22-5b2b-b8ce-a4a78d993dd6	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190403_20190421_01_T1/LC08_L1TP_090090_20190403_20190421_01_T1_MTL.txt	2020-04-07 23:23:16.586433+00	opendatacube	\N
38	7c73294b-6d68-5d75-a7c0-1d00b467ff84	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190325_01_T1/LC08_L1TP_091090_20190309_20190325_01_T1_MTL.txt	2020-04-07 23:23:16.777578+00	opendatacube	\N
41	3c36cf24-9439-55a9-937d-a4739db5e7f2	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190205_20190221_01_T1/LC08_L1TP_091090_20190205_20190221_01_T1_MTL.txt	2020-04-07 23:23:16.967055+00	opendatacube	\N
45	77d41e67-7b17-5038-b5d0-4c7f2955655d	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190113_20190131_01_T1/LC08_L1TP_090090_20190113_20190131_01_T1_MTL.txt	2020-04-07 23:23:17.152915+00	opendatacube	\N
35	4c37e317-cfa7-50c3-8893-51264641950b	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190325_20190403_01_T1/LC08_L1TP_091090_20190325_20190403_01_T1_MTL.txt	2020-04-07 23:23:16.615669+00	opendatacube	\N
39	15a2b4f8-08b5-52e6-8474-f958f9a516f0	s3	//landsat-pds/c1/L8/090/090/LC08_L1GT_090090_20190302_20190303_01_RT/LC08_L1GT_090090_20190302_20190303_01_RT_MTL.txt	2020-04-07 23:23:16.822353+00	opendatacube	\N
42	55708aeb-be6e-510c-8d2d-0d676e009a09	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190129_20190206_01_T1/LC08_L1TP_090090_20190129_20190206_01_T1_MTL.txt	2020-04-07 23:23:16.988407+00	opendatacube	\N
46	5e9dcb87-5d11-5500-9e34-fe7b865a4bd1	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190104_20190130_01_T1/LC08_L1TP_091090_20190104_20190130_01_T1_MTL.txt	2020-04-07 23:23:17.195481+00	opendatacube	\N
36	a0c23e3d-fa17-550b-b4f7-d2d183a853ca	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190318_20190325_01_T1/LC08_L1TP_090090_20190318_20190325_01_T1_MTL.txt	2020-04-07 23:23:16.718646+00	opendatacube	\N
40	bc7c6bcf-05f1-5435-8b56-b1848c41de71	s3	//landsat-pds/c1/L8/091/090/LC08_L1GT_091090_20190221_20190222_01_RT/LC08_L1GT_091090_20190221_20190222_01_RT_MTL.txt	2020-04-07 23:23:16.888115+00	opendatacube	\N
44	13a02aed-9ec5-57dc-a6e4-7b2b9f73b4af	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190120_20190201_01_T1/LC08_L1TP_091090_20190120_20190201_01_T1_MTL.txt	2020-04-07 23:23:17.068802+00	opendatacube	\N
37	8c5bee41-1f00-5df4-afc3-0d98385fdc49	s3	//landsat-pds/c1/L8/091/090/LC08_L1TP_091090_20190309_20190310_01_RT/LC08_L1TP_091090_20190309_20190310_01_RT_MTL.txt	2020-04-07 23:23:16.773782+00	opendatacube	\N
43	087d8d60-6d09-52cc-ad83-ff8fb66a6505	s3	//landsat-pds/c1/L8/090/090/LC08_L1TP_090090_20190214_20190222_01_T1/LC08_L1TP_090090_20190214_20190222_01_T1_MTL.txt	2020-04-07 23:23:16.999796+00	opendatacube	\N
\.


--
-- Data for Name: dataset_source; Type: TABLE DATA; Schema: agdc; Owner: agdc_admin
--

COPY agdc.dataset_source (dataset_ref, classifier, source_dataset_ref) FROM stdin;
\.


--
-- Data for Name: dataset_type; Type: TABLE DATA; Schema: agdc; Owner: agdc_admin
--

COPY agdc.dataset_type (id, name, metadata, metadata_type_ref, definition, added, added_by) FROM stdin;
1	ls8_usgs_level1_scene	{"format": {"name": "GeoTiff"}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "product_type": "L1TP"}	1	{"name": "ls8_usgs_level1_scene", "metadata": {"format": {"name": "GeoTiff"}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "product_type": "L1TP"}, "description": "Landsat 8 USGS Level 1 Collection-1 OLI-TIRS", "measurements": [{"name": "coastal_aerosol", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_1", "coastal_aerosol"]}, {"name": "blue", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_2", "blue"]}, {"name": "green", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_3", "green"]}, {"name": "red", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_4", "red"]}, {"name": "nir", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_5", "nir"]}, {"name": "swir1", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_6", "swir1"]}, {"name": "swir2", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_7", "swir2"]}, {"name": "panchromatic", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_8", "panchromatic"]}, {"name": "cirrus", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_9", "cirrus"]}, {"name": "lwir1", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_10", "lwir1"]}, {"name": "lwir2", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_11", "lwir2"]}, {"name": "quality", "dtype": "int16", "units": "1", "nodata": 0, "aliases": ["QUALITY", "quality"], "flags_definition": {"cloud": {"bits": [4], "values": {"0": false, "1": true}, "description": "Cloud"}, "snow_ice_conf": {"bits": [9, 10], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Snow/Ice Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "designated_fill": {"bits": [0], "values": {"0": false, "1": true}, "description": "Used to identify fill values"}, "cloud_confidence": {"bits": [5, 6], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Cloud Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "cirrus_confidence": {"bits": [11, 12], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Cirrus Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "cloud_shadow_conf": {"bits": [7, 8], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Cloud Shadow Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "terrain_occlusion": {"bits": [1], "values": {"0": false, "1": true}, "description": "Terrain Occlusion"}, "radiometric_saturation": {"bits": [2, 3], "values": {"0": "none", "1": "1-2", "2": "3-4", "3": "<=5"}, "description": "Radiometric saturation bits, represents how many bands contains saturation"}}}], "metadata_type": "eo"}	2020-04-07 04:07:59.051324+00	opendatacube
2	ls7_usgs_level1_scene	{"format": {"name": "GeoTiff"}, "platform": {"code": "LANDSAT_7"}, "instrument": {"name": "ETM"}, "product_type": "L1TP"}	1	{"name": "ls7_usgs_level1_scene", "metadata": {"format": {"name": "GeoTiff"}, "platform": {"code": "LANDSAT_7"}, "instrument": {"name": "ETM"}, "product_type": "L1TP"}, "description": "Landsat 7 USGS Level 1 Collection-1 OLI-TIRS", "measurements": [{"name": "blue", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_1", "blue"]}, {"name": "green", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_2", "green"]}, {"name": "red", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_3", "red"]}, {"name": "nir", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_4", "nir"]}, {"name": "swir1", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_5", "swir1"]}, {"name": "swir2", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_7", "swir2"]}, {"name": "quality", "dtype": "int16", "units": "1", "nodata": 0, "aliases": ["QUALITY", "quality"], "flags_definition": {"cloud": {"bits": [4], "values": {"0": false, "1": true}, "description": "Cloud"}, "dropped_pixel": {"bits": [1], "values": {"0": false, "1": true}, "description": "Dropped Pixel"}, "snow_ice_conf": {"bits": [9, 10], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Snow/Ice Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "designated_fill": {"bits": [0], "values": {"0": false, "1": true}, "description": "Used to identify fill values"}, "cloud_confidence": {"bits": [5, 6], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Cloud Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "cloud_shadow_conf": {"bits": [7, 8], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Cloud Shadow Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "radiometric_saturation": {"bits": [2, 3], "values": {"0": "none", "1": "1-2", "2": "3-4", "3": "<=5"}, "description": "Radiometric saturation bits, represents how many bands contains saturation"}}}], "metadata_type": "eo"}	2020-04-07 04:07:59.124654+00	opendatacube
3	ls5_usgs_level1_scene	{"format": {"name": "GeoTiff"}, "platform": {"code": "LANDSAT_5"}, "instrument": {"name": "TM"}, "product_type": "L1TP"}	1	{"name": "ls5_usgs_level1_scene", "metadata": {"format": {"name": "GeoTiff"}, "platform": {"code": "LANDSAT_5"}, "instrument": {"name": "TM"}, "product_type": "L1TP"}, "description": "Landsat 5 USGS Level 1 Collection-1 OLI-TIRS", "measurements": [{"name": "blue", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_1", "blue"]}, {"name": "green", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_2", "green"]}, {"name": "red", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_3", "red"]}, {"name": "nir", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_4", "nir"]}, {"name": "swir1", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_5", "swir1"]}, {"name": "swir2", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_7", "swir2"]}, {"name": "quality", "dtype": "int16", "units": "1", "nodata": 0, "aliases": ["QUALITY", "quality"], "flags_definition": {"cloud": {"bits": [4], "values": {"0": false, "1": true}, "description": "Cloud"}, "dropped_pixel": {"bits": [1], "values": {"0": false, "1": true}, "description": "Dropped Pixel"}, "snow_ice_conf": {"bits": [9, 10], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Snow/Ice Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "designated_fill": {"bits": [0], "values": {"0": false, "1": true}, "description": "Used to identify fill values"}, "cloud_confidence": {"bits": [5, 6], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Cloud Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "cloud_shadow_conf": {"bits": [7, 8], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Cloud Shadow Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "radiometric_saturation": {"bits": [2, 3], "values": {"0": "none", "1": "1-2", "2": "3-4", "3": "<=5"}, "description": "Radiometric saturation bits, represents how many bands contains saturation"}}}], "metadata_type": "eo"}	2020-04-07 04:07:59.19368+00	opendatacube
4	ls8_l1_pc_usgs	{"format": {"name": "GeoTiff"}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "product_type": "L1T"}	1	{"name": "ls8_l1_pc_usgs", "metadata": {"format": {"name": "GeoTiff"}, "platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}, "product_type": "L1T"}, "description": "Landsat 8 USGS Level 1 Pre-Collection OLI-TIRS", "measurements": [{"name": "coastal_aerosol", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_1", "coastal_aerosol"]}, {"name": "blue", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_2", "blue"]}, {"name": "green", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_3", "green"]}, {"name": "red", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_4", "red"]}, {"name": "nir", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_5", "nir"]}, {"name": "swir1", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_6", "swir1"]}, {"name": "swir2", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_7", "swir2"]}, {"name": "panchromatic", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_8", "panchromatic"]}, {"name": "cirrus", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_9", "cirrus"]}, {"name": "lwir1", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_10", "lwir1"]}, {"name": "lwir2", "dtype": "int16", "units": "1", "nodata": -9999, "aliases": ["band_11", "lwir2"]}, {"name": "quality", "dtype": "int16", "units": "1", "nodata": 0, "aliases": ["QUALITY", "quality"], "flags_definition": {"water": {"bits": [4, 5], "values": {"0": false, "2": true}, "description": "water condition 0 - not exist, 2 -condition exist"}, "dropped_frame": {"bits": [1], "values": {"0": false, "1": true}, "description": "Dropped Frame"}, "snow_ice_conf": {"bits": [10, 11], "values": {"0": false, "3": true}, "description": "Snow/Ice Confidence with 0- condition doesn't exist, 3 - condition exist"}, "designated_fill": {"bits": [0], "values": {"0": false, "1": true}, "description": "Used to identify fill values"}, "cloud_confidence": {"bits": [14, 15], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Cloud Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "cirrus_confidence": {"bits": [12, 13], "values": {"0": "Not Determined", "1": "Low", "2": "Medium", "3": "High"}, "description": "Cirrus Confidence with low =(0-33)%, medium =(34-66)% and high =(67-100)%"}, "terrain_occlusion": {"bits": [2], "values": {"0": false, "1": true}, "description": "Terrain Occlusion"}}}], "metadata_type": "eo"}	2020-04-07 04:07:59.265598+00	opendatacube
\.


--
-- Data for Name: metadata_type; Type: TABLE DATA; Schema: agdc; Owner: agdc_admin
--

COPY agdc.metadata_type (id, name, definition, added, added_by) FROM stdin;
1	eo	{"name": "eo", "dataset": {"id": ["id"], "label": ["ga_label"], "format": ["format", "name"], "sources": ["lineage", "source_datasets"], "creation_dt": ["creation_dt"], "grid_spatial": ["grid_spatial", "projection"], "measurements": ["image", "bands"], "search_fields": {"lat": {"type": "double-range", "max_offset": [["extent", "coord", "ur", "lat"], ["extent", "coord", "lr", "lat"], ["extent", "coord", "ul", "lat"], ["extent", "coord", "ll", "lat"]], "min_offset": [["extent", "coord", "ur", "lat"], ["extent", "coord", "lr", "lat"], ["extent", "coord", "ul", "lat"], ["extent", "coord", "ll", "lat"]], "description": "Latitude range"}, "lon": {"type": "double-range", "max_offset": [["extent", "coord", "ul", "lon"], ["extent", "coord", "ur", "lon"], ["extent", "coord", "ll", "lon"], ["extent", "coord", "lr", "lon"]], "min_offset": [["extent", "coord", "ul", "lon"], ["extent", "coord", "ur", "lon"], ["extent", "coord", "ll", "lon"], ["extent", "coord", "lr", "lon"]], "description": "Longitude range"}, "time": {"type": "datetime-range", "max_offset": [["extent", "to_dt"], ["extent", "center_dt"]], "min_offset": [["extent", "from_dt"], ["extent", "center_dt"]], "description": "Acquisition time"}, "platform": {"offset": ["platform", "code"], "description": "Platform code"}, "instrument": {"offset": ["instrument", "name"], "description": "Instrument name"}, "product_type": {"offset": ["product_type"], "description": "Product code"}}}, "description": "Earth Observation datasets.\\n\\nExpected metadata structure produced by the eodatasets library, as used internally at GA.\\n\\nhttps://github.com/GeoscienceAustralia/eo-datasets\\n"}	2020-04-07 04:23:57.980404+00	opendatacube
2	telemetry	{"name": "telemetry", "dataset": {"id": ["id"], "label": ["ga_label"], "sources": ["lineage", "source_datasets"], "creation_dt": ["creation_dt"], "search_fields": {"gsi": {"offset": ["acquisition", "groundstation", "code"], "indexed": false, "description": "Ground Station Identifier (eg. ASA)"}, "time": {"type": "datetime-range", "max_offset": [["acquisition", "los"]], "min_offset": [["acquisition", "aos"]], "description": "Acquisition time"}, "orbit": {"type": "integer", "offset": ["acquisition", "platform_orbit"], "description": "Orbit number"}, "sat_row": {"type": "integer-range", "max_offset": [["image", "satellite_ref_point_end", "y"], ["image", "satellite_ref_point_start", "y"]], "min_offset": [["image", "satellite_ref_point_start", "y"]], "description": "Landsat row"}, "platform": {"offset": ["platform", "code"], "description": "Platform code"}, "sat_path": {"type": "integer-range", "max_offset": [["image", "satellite_ref_point_end", "x"], ["image", "satellite_ref_point_start", "x"]], "min_offset": [["image", "satellite_ref_point_start", "x"]], "description": "Landsat path"}, "instrument": {"offset": ["instrument", "name"], "description": "Instrument name"}, "product_type": {"offset": ["product_type"], "description": "Product code"}}}, "description": "Satellite telemetry datasets.\\n\\nExpected metadata structure produced by telemetry datasets from the eodatasets library, as used internally at GA.\\n\\nhttps://github.com/GeoscienceAustralia/eo-datasets\\n"}	2020-04-07 04:23:58.009294+00	opendatacube
\.


--
-- Data for Name: job; Type: TABLE DATA; Schema: cron; Owner: postgres
--

COPY cron.job (jobid, schedule, command, nodename, nodeport, database, username, active) FROM stdin;
\.


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Data for Name: topology; Type: TABLE DATA; Schema: topology; Owner: postgres
--

COPY topology.topology (id, name, srid, "precision", hasz) FROM stdin;
\.


--
-- Data for Name: layer; Type: TABLE DATA; Schema: topology; Owner: postgres
--

COPY topology.layer (topology_id, layer_id, schema_name, table_name, feature_column, feature_type, level, child_id) FROM stdin;
\.


--
-- Data for Name: multiproduct_ranges; Type: TABLE DATA; Schema: wms; Owner: opendatacube
--

COPY wms.multiproduct_ranges (wms_product_name, lat_min, lat_max, lon_min, lon_max, dates, bboxes) FROM stdin;
\.


--
-- Data for Name: product_ranges; Type: TABLE DATA; Schema: wms; Owner: opendatacube
--

COPY wms.product_ranges (id, lat_min, lat_max, lon_min, lon_max, dates, bboxes) FROM stdin;
1	-44.2496235771426	-42.106173119346394	144.12469249315507	148.70324919261046	["2019-01-05", "2019-01-14", "2019-01-21", "2019-01-30", "2019-02-06", "2019-02-15", "2019-02-22", "2019-03-03", "2019-03-10", "2019-03-19", "2019-03-26", "2019-04-04", "2019-04-11", "2019-04-20", "2019-04-27", "2019-05-06", "2019-05-13", "2019-05-22", "2019-05-29", "2019-06-07", "2019-06-14", "2019-06-23", "2019-07-09", "2019-07-16", "2019-07-25", "2019-08-01", "2019-08-10", "2019-08-17", "2019-08-26", "2019-09-02", "2019-09-11", "2019-09-18", "2019-09-27", "2019-10-04", "2019-10-13", "2019-10-20", "2019-10-29", "2019-11-05", "2019-11-14", "2019-11-21", "2019-11-30", "2019-12-07", "2019-12-16", "2019-12-23", "2020-01-01"]	{"EPSG:3577": {"top": -4652810.970521015, "left": 1006608.0662815507, "right": 1409444.2074511466, "bottom": -4923487.213918506}, "EPSG:3857": {"top": -5176896.954504759, "left": 16043887.379075164, "right": 16553569.97942667, "bottom": -5504945.321572271}, "EPSG:4326": {"top": -42.10617311934641, "left": 144.1246924931551, "right": 148.7032491926105, "bottom": -44.2547177031693}}
\.


--
-- Data for Name: sub_product_ranges; Type: TABLE DATA; Schema: wms; Owner: opendatacube
--

COPY wms.sub_product_ranges (product_id, sub_product_id, lat_min, lat_max, lon_min, lon_max, dates, bboxes) FROM stdin;
\.


--
-- Name: dataset_location_id_seq; Type: SEQUENCE SET; Schema: agdc; Owner: agdc_admin
--

SELECT pg_catalog.setval('agdc.dataset_location_id_seq', 46, true);


--
-- Name: dataset_type_id_seq; Type: SEQUENCE SET; Schema: agdc; Owner: agdc_admin
--

SELECT pg_catalog.setval('agdc.dataset_type_id_seq', 4, true);


--
-- Name: metadata_type_id_seq; Type: SEQUENCE SET; Schema: agdc; Owner: agdc_admin
--

SELECT pg_catalog.setval('agdc.metadata_type_id_seq', 2, true);


--
-- Name: jobid_seq; Type: SEQUENCE SET; Schema: cron; Owner: postgres
--

SELECT pg_catalog.setval('cron.jobid_seq', 1, false);


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
-- Name: multiproduct_ranges multiproduct_ranges_pkey; Type: CONSTRAINT; Schema: wms; Owner: opendatacube
--

ALTER TABLE ONLY wms.multiproduct_ranges
    ADD CONSTRAINT multiproduct_ranges_pkey PRIMARY KEY (wms_product_name);


--
-- Name: sub_product_ranges pk_sub_product_ranges; Type: CONSTRAINT; Schema: wms; Owner: opendatacube
--

ALTER TABLE ONLY wms.sub_product_ranges
    ADD CONSTRAINT pk_sub_product_ranges PRIMARY KEY (product_id, sub_product_id);


--
-- Name: product_ranges product_ranges_pkey; Type: CONSTRAINT; Schema: wms; Owner: opendatacube
--

ALTER TABLE ONLY wms.product_ranges
    ADD CONSTRAINT product_ranges_pkey PRIMARY KEY (id);


--
-- Name: dix_ls5_usgs_level1_scene_lat_lon_time; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_ls5_usgs_level1_scene_lat_lon_time ON agdc.dataset USING gist (agdc.float8range(LEAST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), '[]'::text), tstzrange(LEAST(agdc.common_timestamp((metadata #>> '{extent,from_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), GREATEST(agdc.common_timestamp((metadata #>> '{extent,to_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), '[]'::text)) WHERE ((archived IS NULL) AND (dataset_type_ref = 3));


--
-- Name: dix_ls5_usgs_level1_scene_time_lat_lon; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_ls5_usgs_level1_scene_time_lat_lon ON agdc.dataset USING gist (tstzrange(LEAST(agdc.common_timestamp((metadata #>> '{extent,from_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), GREATEST(agdc.common_timestamp((metadata #>> '{extent,to_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), '[]'::text)) WHERE ((archived IS NULL) AND (dataset_type_ref = 3));


--
-- Name: dix_ls7_usgs_level1_scene_lat_lon_time; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_ls7_usgs_level1_scene_lat_lon_time ON agdc.dataset USING gist (agdc.float8range(LEAST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), '[]'::text), tstzrange(LEAST(agdc.common_timestamp((metadata #>> '{extent,from_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), GREATEST(agdc.common_timestamp((metadata #>> '{extent,to_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), '[]'::text)) WHERE ((archived IS NULL) AND (dataset_type_ref = 2));


--
-- Name: dix_ls7_usgs_level1_scene_time_lat_lon; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_ls7_usgs_level1_scene_time_lat_lon ON agdc.dataset USING gist (tstzrange(LEAST(agdc.common_timestamp((metadata #>> '{extent,from_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), GREATEST(agdc.common_timestamp((metadata #>> '{extent,to_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), '[]'::text)) WHERE ((archived IS NULL) AND (dataset_type_ref = 2));


--
-- Name: dix_ls8_l1_pc_usgs_lat_lon_time; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_ls8_l1_pc_usgs_lat_lon_time ON agdc.dataset USING gist (agdc.float8range(LEAST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), '[]'::text), tstzrange(LEAST(agdc.common_timestamp((metadata #>> '{extent,from_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), GREATEST(agdc.common_timestamp((metadata #>> '{extent,to_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), '[]'::text)) WHERE ((archived IS NULL) AND (dataset_type_ref = 4));


--
-- Name: dix_ls8_l1_pc_usgs_time_lat_lon; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_ls8_l1_pc_usgs_time_lat_lon ON agdc.dataset USING gist (tstzrange(LEAST(agdc.common_timestamp((metadata #>> '{extent,from_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), GREATEST(agdc.common_timestamp((metadata #>> '{extent,to_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), '[]'::text)) WHERE ((archived IS NULL) AND (dataset_type_ref = 4));


--
-- Name: dix_ls8_usgs_level1_scene_lat_lon_time; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_ls8_usgs_level1_scene_lat_lon_time ON agdc.dataset USING gist (agdc.float8range(LEAST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), '[]'::text), tstzrange(LEAST(agdc.common_timestamp((metadata #>> '{extent,from_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), GREATEST(agdc.common_timestamp((metadata #>> '{extent,to_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), '[]'::text)) WHERE ((archived IS NULL) AND (dataset_type_ref = 1));


--
-- Name: dix_ls8_usgs_level1_scene_time_lat_lon; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX dix_ls8_usgs_level1_scene_time_lat_lon ON agdc.dataset USING gist (tstzrange(LEAST(agdc.common_timestamp((metadata #>> '{extent,from_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), GREATEST(agdc.common_timestamp((metadata #>> '{extent,to_dt}'::text[])), agdc.common_timestamp((metadata #>> '{extent,center_dt}'::text[]))), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ur,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ul,lat}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lat}'::text[]))::double precision), '[]'::text), agdc.float8range(LEAST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), GREATEST(((metadata #>> '{extent,coord,ul,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ur,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,ll,lon}'::text[]))::double precision, ((metadata #>> '{extent,coord,lr,lon}'::text[]))::double precision), '[]'::text)) WHERE ((archived IS NULL) AND (dataset_type_ref = 1));


--
-- Name: ix_agdc_dataset_dataset_type_ref; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX ix_agdc_dataset_dataset_type_ref ON agdc.dataset USING btree (dataset_type_ref);


--
-- Name: ix_agdc_dataset_location_dataset_ref; Type: INDEX; Schema: agdc; Owner: agdc_admin
--

CREATE INDEX ix_agdc_dataset_location_dataset_ref ON agdc.dataset_location USING btree (dataset_ref);


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
-- Name: product_ranges product_ranges_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: opendatacube
--

ALTER TABLE ONLY wms.product_ranges
    ADD CONSTRAINT product_ranges_id_fkey FOREIGN KEY (id) REFERENCES agdc.dataset_type(id);


--
-- Name: sub_product_ranges sub_product_ranges_product_id_fkey; Type: FK CONSTRAINT; Schema: wms; Owner: opendatacube
--

ALTER TABLE ONLY wms.sub_product_ranges
    ADD CONSTRAINT sub_product_ranges_product_id_fkey FOREIGN KEY (product_id) REFERENCES agdc.dataset_type(id);


--
-- Name: job cron_job_policy; Type: POLICY; Schema: cron; Owner: postgres
--

CREATE POLICY cron_job_policy ON cron.job USING ((username = (CURRENT_USER)::text));


--
-- Name: job; Type: ROW SECURITY; Schema: cron; Owner: postgres
--

ALTER TABLE cron.job ENABLE ROW LEVEL SECURITY;

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
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: opendatacube
--

ALTER DEFAULT PRIVILEGES FOR ROLE opendatacube IN SCHEMA public REVOKE ALL ON TABLES  FROM opendatacube;
ALTER DEFAULT PRIVILEGES FOR ROLE opendatacube IN SCHEMA public GRANT SELECT ON TABLES  TO replicator;


--
-- PostgreSQL database dump complete
--

