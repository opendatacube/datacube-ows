from datacube_wms.product_ranges import update_all_ranges, get_sqlconn, add_product_range, add_multiproduct_range, add_all, update_range
from datacube import Datacube
import click

@click.command()
@click.option("--schema", is_flag=True, default=False, help="Create or update the OWS database schema.")
@click.option("--product", default=None, help="The name of a datacube product.")
@click.option("--multiproduct", default=None, help="The name of OWS multi-product." )
@click.option("--calculate-extent/--no-calculate-extent", default=True, help="no-calculate-extent uses database queries to maximise efficiency. calculate-extent calculates ranges directly and is the default.")
def main(product, multiproduct, calculate_extent, schema):
    """Manage datacube-ows range tables.

    A valid invocation should specify at most one of '--product', '--multiproduct' or '--schema'.
    If neither of these options are specified, then the ranges for all products and multiproducts
    are updated.
    """
    if product and multiproduct:
        print("Sorry, you specified both a product and multiproduct.  One at a time, please.")
        return 1
    elif schema and (product or multiproduct):
        print("Sorry, cannot update the schema and ranges in the same invocation.")
        return 1

    dc = Datacube(app="wms_update_ranges")
    if schema:
        print("Checking schema....")
        print("Creating or replacing WMS database schema...")
        create_schema(dc)
        print("Done")
    elif not calculate_extent:
        if product:
            print("Updating range for: ", product)
            add_product_range(dc, product)
        elif multiproduct:
            print("Updating range for: ", multiproduct)
            add_multiproduct_range(dc, multiproduct)
        else:
            print("Updating range for all, using SQL extent calculation")
            add_all(dc)
            print("Done")
    else:
        if product:
            print("Updating range for: ", product)
            p, u, i, sp, su, si = update_range(product, multi=False)
            if u:
                print("Ranges updated for", product)
            elif i:
                print("New ranges inserted for", product)
            else:
                print("Ranges up to date for", product)
            if sp or su or si:
                print ("Updated ranges for %d existing sub-products and inserted ranges for %d new sub-products (%d existing sub-products unchanged)" % (su, si, sp))
        elif multiproduct:
            print("Updating range for: ", multiproduct)
            p, u, i = update_range(product, multi=True)
            if u:
                print("Merged ranges updated for", product)
            elif i:
                print("Merged ranges inserted for", product)
            else:
                print("Merged ranges up to date for", product)
        else:
            print ("Updating ranges for all layers/products")
            p, u, i, sp, su, si, mp, mu, mi = update_all_ranges(dc)
            print ("Updated ranges for %d existing layers/products and inserted ranges for %d new layers/products (%d existing layers/products unchanged)" % (u, i, p))
            if sp or su or si:
                print ("Updated ranges for %d existing sub-products and inserted ranges for %d new sub-products (%d existing sub-products unchanged)" % (su, si, sp))
            if mp or mu or mi:
                print ("Updated ranges for %d existing multi-products and inserted ranges for %d new multi-products (%d existing multi-products unchanged)" % (su, si, sp))
    return 0


def create_schema(dc):
    commands = [
        ("Creating/replacing wms schema", "create schema if not exists wms"),

        ("Creating/replacing product ranges table", """
            create table if not exists wms.product_ranges (
                id smallint not null primary key references agdc.dataset_type (id),

                lat_min decimal not null,
                lat_max decimal not null,
                lon_min decimal not null,
                lon_max decimal not null,

                dates jsonb not null,

                bboxes jsonb not null)
        """),
        ("Creating/replacing sub-product ranges table", """
            create table if not exists wms.sub_product_ranges (
                product_id smallint not null references agdc.dataset_type (id),
                sub_product_id smallint not null,
                lat_min decimal not null,
                lat_max decimal not null,
                lon_min decimal not null,
                lon_max decimal not null,
                dates jsonb not null,
                bboxes jsonb not null,
                constraint pk_sub_product_ranges primary key (product_id, sub_product_id) )
        """),
        ("Creating/replacing multi-product ranges table", """
            create table if not exists wms.multiproduct_ranges (
                wms_product_name varchar(128) not null primary key,
                lat_min decimal not null,
                lat_max decimal not null,
                lon_min decimal not null,
                lon_max decimal not null,
                dates jsonb not null,
                bboxes jsonb not null)
        """),
        ("Granting schema permissions", "grant USAGE on schema wms to cube"),

        # Functions
        ("Creating/replacing wms_get_min() function", """
            CREATE OR REPLACE FUNCTION wms_get_min(integer[], text) RETURNS numeric AS $$
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
            $$ LANGUAGE plpgsql;
        """),
        ("Creating/replacing wms_get_max() function", """
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
        """),
    ]

    conn = get_sqlconn(dc)
    for msg, sql in commands:
        print(msg)
        conn.execute(sql)
    conn.close()

    return


if __name__ == '__main__':
    main()


