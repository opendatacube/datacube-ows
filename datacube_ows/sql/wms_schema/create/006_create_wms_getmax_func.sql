-- Creating/replacing wms_get_max() function

CREATE OR REPLACE FUNCTION wms_get_max(integer[], text) RETURNS numeric AS $$
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
$$ LANGUAGE plpgsql;
