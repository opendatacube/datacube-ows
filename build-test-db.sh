#!/usr/bin/env bash
# Convenience script for running Travis-like checks.
set -ex

# ensure db is ready
sh ./docker/ows/wait-for-db

# Initialise ODC schemas

datacube system init
datacube -E owspostgis system init

# Add extended metadata types

datacube metadata add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/product_metadata/eo3_landsat_ard.odc-type.yaml
datacube metadata add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/product_metadata/eo3_sentinel_ard.odc-type.yaml

datacube -E owspostgis metadata add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/product_metadata/eo3_landsat_ard.odc-type.yaml
datacube -E owspostgis metadata add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/product_metadata/eo3_sentinel_ard.odc-type.yaml

# Test products
datacube product add ./integration_tests/metadata/s2_l2a_prod.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/c3/ga_s2am_ard_3.odc-product.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/c3/ga_s2bm_ard_3.odc-product.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/land_and_vegetation/c3_fc/ga_ls_fc_3.odc-product.yaml

datacube -E owspostgis product add ./integration_tests/metadata/s2_l2a_prod.yaml
datacube -E owspostgis product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/c3/ga_s2am_ard_3.odc-product.yaml
datacube -E owspostgis product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/c3/ga_s2bm_ard_3.odc-product.yaml
datacube -E owspostgis product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/land_and_vegetation/c3_fc/ga_ls_fc_3.odc-product.yaml

# add flag masking products
datacube product add ./integration_tests/metadata/product_geodata_coast_100k.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/inland_water/c3_wo/ga_ls_wo_3.odc-product.yaml

datacube -E owspostgis product add ./integration_tests/metadata/product_geodata_coast_100k.yaml
datacube -E owspostgis product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/inland_water/c3_wo/ga_ls_wo_3.odc-product.yaml

# Geomedian for summary product testing

datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/geomedian-au/ga_ls8c_nbart_gm_cyear_3.odc-product.yaml
datacube -E owspostgis product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/geomedian-au/ga_ls8c_nbart_gm_cyear_3.odc-product.yaml

# S2 datasets from us-west-2 and eo3ified geodata_coast
MDL=./integration_tests/metadata
python ${MDL}/metadata_importer.py <<EOF
${MDL}/s2_l2a_ds_01.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XD/2021/12/S2B_51LXD_20211231_0_L2A/S2B_51LXD_20211231_0_L2A.json
${MDL}/s2_l2a_ds_02.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211231_0_L2A/S2B_51LYE_20211231_0_L2A.json
${MDL}/s2_l2a_ds_03.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XF/2021/12/S2B_51LXF_20211231_0_L2A/S2B_51LXF_20211231_0_L2A.json
${MDL}/s2_l2a_ds_04.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211231_0_L2A/S2B_51LXE_20211231_0_L2A.json
${MDL}/s2_l2a_ds_05.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WD/2021/12/S2B_51LWD_20211231_0_L2A/S2B_51LWD_20211231_0_L2A.json
${MDL}/s2_l2a_ds_06.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YF/2021/12/S2B_51LYF_20211231_0_L2A/S2B_51LYF_20211231_0_L2A.json
${MDL}/s2_l2a_ds_07.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211231_0_L2A/S2B_51LWE_20211231_0_L2A.json
${MDL}/s2_l2a_ds_08.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WF/2021/12/S2B_51LWF_20211231_0_L2A/S2B_51LWF_20211231_0_L2A.json
${MDL}/s2_l2a_ds_09.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YD/2021/12/S2B_51LYD_20211231_0_L2A/S2B_51LYD_20211231_0_L2A.json
${MDL}/s2_l2a_ds_10.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WF/2022/1/S2B_51LWF_20220110_0_L2A/S2B_51LWF_20220110_0_L2A.json
${MDL}/s2_l2a_ds_11.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YD/2022/1/S2B_51LYD_20220110_0_L2A/S2B_51LYD_20220110_0_L2A.json
${MDL}/s2_l2a_ds_12.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XD/2022/1/S2B_51LXD_20220110_0_L2A/S2B_51LXD_20220110_0_L2A.json
${MDL}/s2_l2a_ds_13.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WD/2022/1/S2B_51LWD_20220110_0_L2A/S2B_51LWD_20220110_0_L2A.json
${MDL}/s2_l2a_ds_14.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2022/1/S2A_51LXE_20220108_0_L2A/S2A_51LXE_20220108_0_L2A.json
${MDL}/s2_l2a_ds_15.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WD/2022/1/S2A_51LWD_20220105_0_L2A/S2A_51LWD_20220105_0_L2A.json
${MDL}/s2_l2a_ds_16.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2022/1/S2B_51LXE_20220110_0_L2A/S2B_51LXE_20220110_0_L2A.json
${MDL}/s2_l2a_ds_17.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2022/1/S2B_51LWE_20220110_0_L2A/S2B_51LWE_20220110_0_L2A.json
${MDL}/s2_l2a_ds_18.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2022/1/S2B_51LYE_20220110_0_L2A/S2B_51LYE_20220110_0_L2A.json
${MDL}/s2_l2a_ds_19.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XF/2022/1/S2B_51LXF_20220110_0_L2A/S2B_51LXF_20220110_0_L2A.json
${MDL}/s2_l2a_ds_20.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XF/2022/1/S2B_51LXF_20220103_0_L2A/S2B_51LXF_20220103_0_L2A.json
${MDL}/s2_l2a_ds_21.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YF/2022/1/S2B_51LYF_20220110_0_L2A/S2B_51LYF_20220110_0_L2A.json
${MDL}/s2_l2a_ds_22.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2022/1/S2A_51LWE_20220105_0_L2A/S2A_51LWE_20220105_0_L2A.json
${MDL}/s2_l2a_ds_23.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2022/1/S2A_51LWE_20220108_0_L2A/S2A_51LWE_20220108_0_L2A.json
${MDL}/s2_l2a_ds_24.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XD/2022/1/S2A_51LXD_20220105_0_L2A/S2A_51LXD_20220105_0_L2A.json
${MDL}/s2_l2a_ds_25.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XF/2022/1/S2A_51LXF_20220108_0_L2A/S2A_51LXF_20220108_0_L2A.json
${MDL}/s2_l2a_ds_26.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2022/1/S2A_51LYE_20220105_0_L2A/S2A_51LYE_20220105_0_L2A.json
${MDL}/s2_l2a_ds_27.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2022/1/S2B_51LXE_20220103_0_L2A/S2B_51LXE_20220103_0_L2A.json
${MDL}/s2_l2a_ds_28.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2A_51LXE_20211226_0_L2A/S2A_51LXE_20211226_0_L2A.json
${MDL}/s2_l2a_ds_29.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YD/2022/1/S2A_51LYD_20220105_0_L2A/S2A_51LYD_20220105_0_L2A.json
${MDL}/s2_l2a_ds_30.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2A_51LXE_20211229_0_L2A/S2A_51LXE_20211229_0_L2A.json
${MDL}/s2_l2a_ds_31.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XD/2021/12/S2A_51LXD_20211226_0_L2A/S2A_51LXD_20211226_0_L2A.json
${MDL}/s2_l2a_ds_32.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211224_0_L2A/S2B_51LXE_20211224_0_L2A.json
${MDL}/s2_l2a_ds_33.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WF/2022/1/S2A_51LWF_20220108_0_L2A/S2A_51LWF_20220108_0_L2A.json
${MDL}/s2_l2a_ds_34.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YF/2021/12/S2A_51LYF_20211226_0_L2A/S2A_51LYF_20211226_0_L2A.json
${MDL}/s2_l2a_ds_35.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YD/2021/12/S2B_51LYD_20211221_1_L2A/S2B_51LYD_20211221_1_L2A.json
${MDL}/s2_l2a_ds_36.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XF/2021/12/S2B_51LXF_20211221_0_L2A/S2B_51LXF_20211221_0_L2A.json
${MDL}/s2_l2a_ds_37.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YF/2022/1/S2A_51LYF_20220105_0_L2A/S2A_51LYF_20220105_0_L2A.json
${MDL}/s2_l2a_ds_38.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WF/2022/1/S2A_51LWF_20220105_0_L2A/S2A_51LWF_20220105_0_L2A.json
${MDL}/s2_l2a_ds_39.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2022/1/S2B_51LWE_20220103_0_L2A/S2B_51LWE_20220103_0_L2A.json
${MDL}/s2_l2a_ds_40.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WF/2021/12/S2A_51LWF_20211229_0_L2A/S2A_51LWF_20211229_0_L2A.json
${MDL}/s2_l2a_ds_41.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2022/1/S2A_51LXE_20220105_0_L2A/S2A_51LXE_20220105_0_L2A.json
${MDL}/s2_l2a_ds_42.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WF/2021/12/S2A_51LWF_20211226_0_L2A/S2A_51LWF_20211226_0_L2A.json
${MDL}/s2_l2a_ds_43.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XF/2021/12/S2B_51LXF_20211224_0_L2A/S2B_51LXF_20211224_0_L2A.json
${MDL}/s2_l2a_ds_44.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XF/2022/1/S2A_51LXF_20220105_0_L2A/S2A_51LXF_20220105_0_L2A.json
${MDL}/s2_l2a_ds_45.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WF/2022/1/S2B_51LWF_20220103_0_L2A/S2B_51LWF_20220103_0_L2A.json
${MDL}/s2_l2a_ds_46.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2A_51LYE_20211226_0_L2A/S2A_51LYE_20211226_0_L2A.json
${MDL}/s2_l2a_ds_47.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WF/2021/12/S2B_51LWF_20211221_0_L2A/S2B_51LWF_20211221_0_L2A.json
${MDL}/s2_l2a_ds_48.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YF/2021/12/S2B_51LYF_20211221_0_L2A/S2B_51LYF_20211221_0_L2A.json
${MDL}/s2_l2a_ds_49.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XF/2021/12/S2A_51LXF_20211229_0_L2A/S2A_51LXF_20211229_0_L2A.json
${MDL}/s2_l2a_ds_50.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2A_51LWE_20211229_0_L2A/S2A_51LWE_20211229_0_L2A.json
${MDL}/s2_l2a_ds_51.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2A_51LWE_20211226_0_L2A/S2A_51LWE_20211226_0_L2A.json
${MDL}/s2_l2a_ds_52.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YD/2021/12/S2A_51LYD_20211226_0_L2A/S2A_51LYD_20211226_0_L2A.json
${MDL}/s2_l2a_ds_53.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XD/2021/12/S2B_51LXD_20211221_0_L2A/S2B_51LXD_20211221_0_L2A.json
${MDL}/s2_l2a_ds_54.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WD/2021/12/S2A_51LWD_20211226_0_L2A/S2A_51LWD_20211226_0_L2A.json
${MDL}/s2_l2a_ds_55.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WD/2021/12/S2B_51LWD_20211221_0_L2A/S2B_51LWD_20211221_0_L2A.json
${MDL}/s2_l2a_ds_56.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XF/2021/12/S2A_51LXF_20211226_0_L2A/S2A_51LXF_20211226_0_L2A.json
${MDL}/s2_l2a_ds_57.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211224_0_L2A/S2B_51LWE_20211224_0_L2A.json
${MDL}/s2_l2a_ds_58.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WF/2021/12/S2B_51LWF_20211224_0_L2A/S2B_51LWF_20211224_0_L2A.json
${MDL}/s2_l2a_ds_59.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211221_0_L2A/S2B_51LYE_20211221_0_L2A.json
${MDL}/s2_l2a_ds_60.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211221_1_L2A/S2B_51LWE_20211221_1_L2A.json
${MDL}/s2_l2a_ds_61.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/WE/2021/12/S2B_51LWE_20211221_0_L2A/S2B_51LWE_20211221_0_L2A.json
${MDL}/s2_l2a_ds_62.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211221_1_L2A/S2B_51LXE_20211221_1_L2A.json
${MDL}/s2_l2a_ds_63.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/XE/2021/12/S2B_51LXE_20211221_0_L2A/S2B_51LXE_20211221_0_L2A.json
${MDL}/s2_l2a_ds_64.yaml https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/51/L/YE/2021/12/S2B_51LYE_20211221_1_L2A/S2B_51LYE_20211221_1_L2A.json
${MDL}/COAST_100K_8_-21.yaml https://data.dea.ga.gov.au/projects/geodata_coast_100k/v2004/x_8/y_-21/COAST_100K_8_-21.yaml
${MDL}/COAST_100K_15_-40.yaml https://data.dea.ga.gov.au/projects/geodata_coast_100k/v2004/x_15/y_-40/COAST_100K_15_-40.yaml
EOF

# S2 multiproduct datasets
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2bm_ard_3/52/LGM/2017/07/19/20170719T030622/ga_s2bm_ard_3-2-1_52LGM_2017-07-19_final.odc-metadata.yaml --ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2bm_ard_3/52/LGM/2017/07/29/20170729T081630/ga_s2bm_ard_3-2-1_52LGM_2017-07-29_final.odc-metadata.yaml --ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2bm_ard_3/52/LGM/2017/08/08/20170818T192649/ga_s2bm_ard_3-2-1_52LGM_2017-08-08_final.odc-metadata.yaml --ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2am_ard_3/52/LGM/2017/07/14/20170714T082022/ga_s2am_ard_3-2-1_52LGM_2017-07-14_final.odc-metadata.yaml --ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2am_ard_3/52/LGM/2017/07/24/20170724T030641/ga_s2am_ard_3-2-1_52LGM_2017-07-24_final.odc-metadata.yaml --ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2am_ard_3/52/LGM/2017/08/03/20170921T103758/ga_s2am_ard_3-2-1_52LGM_2017-08-03_final.odc-metadata.yaml --ignore-lineage

datacube -E owspostgis dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2bm_ard_3/52/LGM/2017/07/19/20170719T030622/ga_s2bm_ard_3-2-1_52LGM_2017-07-19_final.odc-metadata.yaml --ignore-lineage
datacube -E owspostgis dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2bm_ard_3/52/LGM/2017/07/29/20170729T081630/ga_s2bm_ard_3-2-1_52LGM_2017-07-29_final.odc-metadata.yaml --ignore-lineage
datacube -E owspostgis dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2bm_ard_3/52/LGM/2017/08/08/20170818T192649/ga_s2bm_ard_3-2-1_52LGM_2017-08-08_final.odc-metadata.yaml --ignore-lineage
datacube -E owspostgis dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2am_ard_3/52/LGM/2017/07/14/20170714T082022/ga_s2am_ard_3-2-1_52LGM_2017-07-14_final.odc-metadata.yaml --ignore-lineage
datacube -E owspostgis dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2am_ard_3/52/LGM/2017/07/24/20170724T030641/ga_s2am_ard_3-2-1_52LGM_2017-07-24_final.odc-metadata.yaml --ignore-lineage
datacube -E owspostgis dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2am_ard_3/52/LGM/2017/08/03/20170921T103758/ga_s2am_ard_3-2-1_52LGM_2017-08-03_final.odc-metadata.yaml --ignore-lineage

# flag masking datasets
datacube dataset add https://data.dea.ga.gov.au/derivative/ga_ls_wo_3/1-6-0/094/077/2018/02/08/ga_ls_wo_3_094077_2018-02-08_final.odc-metadata.yaml --ignore-lineage
datacube dataset add https://data.dea.ga.gov.au/derivative/ga_ls_fc_3/2-5-1/094/077/2018/02/08/ga_ls_fc_3_094077_2018-02-08_final.odc-metadata.yaml --ignore-lineage

datacube -E owspostgis dataset add https://data.dea.ga.gov.au/derivative/ga_ls_wo_3/1-6-0/094/077/2018/02/08/ga_ls_wo_3_094077_2018-02-08_final.odc-metadata.yaml --ignore-lineage
datacube -E owspostgis dataset add https://data.dea.ga.gov.au/derivative/ga_ls_fc_3/2-5-1/094/077/2018/02/08/ga_ls_fc_3_094077_2018-02-08_final.odc-metadata.yaml --ignore-lineage

# Geomedian datasets
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x17/y37/2019--P1Y/ga_ls8c_nbart_gm_cyear_3_x17y37_2019--P1Y_final.odc-metadata.yaml --ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x17/y37/2020--P1Y/ga_ls8c_nbart_gm_cyear_3_x17y37_2020--P1Y_final.odc-metadata.yaml --ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x17/y37/2021--P1Y/ga_ls8c_nbart_gm_cyear_3_x17y37_2021--P1Y_final.odc-metadata.yaml --ignore-lineage

datacube -E owspostgis dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x17/y37/2019--P1Y/ga_ls8c_nbart_gm_cyear_3_x17y37_2019--P1Y_final.odc-metadata.yaml --ignore-lineage
datacube -E owspostgis dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x17/y37/2020--P1Y/ga_ls8c_nbart_gm_cyear_3_x17y37_2020--P1Y_final.odc-metadata.yaml --ignore-lineage
datacube -E owspostgis dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/derivative/ga_ls8c_nbart_gm_cyear_3/3-0-0/x17/y37/2021--P1Y/ga_ls8c_nbart_gm_cyear_3_x17y37_2021--P1Y_final.odc-metadata.yaml --ignore-lineage

# create material view for ranges extents
datacube-ows-update --schema --write-role $DB_USERNAME --read-role $SERVER_DB_USERNAME
datacube-ows-update

datacube-ows-update -E owspostgis --schema --write-role $DB_USERNAME --read-role $SERVER_DB_USERNAME
datacube-ows-update -E owspostgis

set +x
