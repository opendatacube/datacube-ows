=======
History
=======

1.9.x Releases
==============

Datacube-ows version 1.9.x releases are designed to work with datacube-core versions 1.9.x.

1.9.7 (2025-12-21)
------------------

Mostly addressing issues in the previous release.

If upgrading, we recommend upgrading to `datacube>=1.9.12` first.

Schema updates are recommended, especially if using the postgis driver.  Only perform the schema updates once all
processes accessing your index have been upgraded to datacube>=1.9.11. Update ODC and OWS schemas as follows:

(NB: use an ODC database environment with database superuser privileges)::

    # Update ODC schema:
    datacube system init
    # Update OWS schema:
    datacube-ows-update --schema

Note that this release drops the separate OWS users - all permissions default to the user (c.f. old read-role),
manage (c.f. old ows write-role), and admin (manage the OWS schema - new feature).

Use::
    datacube user grant [user|manage|admin] <db_username>

instead of the old::
    datacube-ows --read-role <db_username> --write-role <db_username>

If you no longer run OWS 1.8.x versions, now would be a good time to also run::

    # Cleanup OWS 1.8 range tables and materialised views
    datacube-ows-update --cleanup

These schema changes only affects database user permissions and schema management.  A datacube-1.9.12/ows-1.9.7
schema is backwards compatible with earlier versions of datacube and ows. (Note this was advised for the previous
releases as well, but was unfortunately not actually the case for postgis indexes).


What's Changed
++++++++++++++

* Improve error reporting from get_ranges. by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1377
* dependabot: add 10 day cooldown by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1379
* uv.lock: update to urllib3 2.6.0 by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1378
* postgis: fix comment typo by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1385
* uv.lock: update to rasterio 1.4.4 by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1391
* datacube-ows-update: fix help output by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1390
* Replace assert with RuntimeError by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1392
* ogc: log unexpected exceptions by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1393
* Doc string fixes by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1394
* datacube-ows-update: detect OperationalError by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1395
* psycopg3: install c extras by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1398
* datacube-ows-update: print exception by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1396
* Connection handling cleanup by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1399
* Name datacube connection by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1401
* api: re-use existing datacube by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1400
* Refactor to support thread-safe Flask initialisation. by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1403
* Bump version numbers and update HISTORY.rst for 1.9.7 release by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1406

Automated Updates
+++++++++++++++++

* build(deps): bump astral-sh/uv from 0.9.15 to 0.9.16 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1382
* build(deps): bump the actions-deps group with 3 updates by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1380
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1384
* build(deps): bump mambaorg/micromamba from `4037bec` to `b505801` by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1381
* dependabot: fix syntax error by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1383
* build(deps): bump astral-sh/uv from 0.9.16 to 0.9.17 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1389
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1397
* build(deps): bump astral-sh/uv from 0.9.17 to 0.9.18 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1402

**Full Changelog**: https://github.com/opendatacube/datacube-ows/compare/1.9.6...1.9.7


1.9.6 (2025-12-04)
------------------

If upgrading, we recommend upgrading to `datacube>=1.9.11` first.  Update ODC and OWS schemas as follows:

(NB: use an ODC database environment with database superuser privileges)::

    # Update ODC schema:
    datacube system init
    # Update OWS schema:
    datacube-ows-update --schema

Note that this release drops the separate OWS users - all permissions default to the user (c.f. old read-role),
manage (c.f. old ows write-role), and admin (manage the OWS schema - new feature).

Use::
    datacube user grant [user|manage|admin] <db_username>

instead of the old::
    datacube-ows --read-role <db_username> --write-role <db_username>

If you no longer run OWS 1.8.x versions, now would be a good time to also run::

    # Cleanup OWS 1.8 range tables and materialised views
    datacube-ows-update --cleanup

These schema changes only affects database user permissions and schema management.  A datacube-1.9.11/ows-1.9.6
schema is backwards compatible with earlier versions of datacube and ows.

What's Changed
++++++++++++++

* GetFeatureInfo cleanup and bugfix by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1322
* CI: fetch tags for release by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1320
* Combine weekly Dependabot updates to GitHub Actions into a single PR by @omad in https://github.com/opendatacube/datacube-ows/pull/1316
* readthedocs: fix uv warning by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1334
* Update to latest Sphinx by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1335
* Update to owslib 0.35.0 by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1337
* pyproject: use datacube < 1.10.0 by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1340
* CI: use anchors for branches & paths by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1344
* uv.lock: update dependencies by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1352
* update_ranges_impl: catch OWSConfigNotReady by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1348
* Db user perms cleanup by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1343
* Updates fail cleanly on misconfigured layers. by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1356
* config_utils: fix typo in doc string by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1357
* compose: use a single db container by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1358
* Include psycopg3 in dependencies by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1359
* tests: sync po files by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1360
* Move lxml from main dependency to test dependency. by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1366
* Add psycopg3 support by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1364
* Adjust some type annotations by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1367
* Fix mosaic date stacking order by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1363
* Update to lxml 6 by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1368
* CI: do not fail fast by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1370
* Update to datacube 1.9.11 by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1371
* Prepare for 1.9.6 release by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1372

Autoupdates
+++++++++++

* build(deps): bump astral-sh/uv from 0.9.4 to 0.9.5 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1321
* build(deps): bump mambaorg/micromamba from 2.3.2 to 2.3.3 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1326
* build(deps): bump astral-sh/setup-uv from 7.1.1 to 7.1.2 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1324
* build(deps): bump actions/upload-artifact from 4.6.2 to 5.0.0 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1325
* build(deps): bump github/codeql-action from 4.30.9 to 4.31.0 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1323
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1327
* build(deps): bump mambaorg/micromamba from `e4ef56b` to `800e7ad` by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1328
* build(deps): bump astral-sh/uv from 0.9.5 to 0.9.6 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1329
* build(deps): bump astral-sh/uv from 0.9.6 to 0.9.7 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1330
* build(deps): bump github/codeql-action from 4.31.0 to 4.31.2 in the actions-deps group by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1331
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1332
* build(deps): bump docker/metadata-action from 5.8.0 to 5.9.0 in the actions-deps group by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1338
* build(deps): bump astral-sh/uv from 0.9.7 to 0.9.8 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1339
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1341
* build(deps): bump astral-sh/uv from 0.9.8 to 0.9.9 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1342
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1345
* build(deps): bump astral-sh/uv from 0.9.9 to 0.9.10 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1346
* build(deps): bump astral-sh/uv from 0.9.10 to 0.9.11 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1347
* build(deps): bump mambaorg/micromamba from 2.3.3 to 2.4.0 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1350
* build(deps): bump the actions-deps group with 3 updates by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1349
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1351
* build(deps): bump astral-sh/uv from 0.9.11 to 0.9.12 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1353
* build(deps): bump astral-sh/uv from 0.9.12 to 0.9.13 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1355
* build(deps): bump the actions-deps group with 2 updates by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1361
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1362
* build(deps): bump astral-sh/uv from 0.9.13 to 0.9.14 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1365
* build(deps): bump astral-sh/uv from 0.9.14 to 0.9.15 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1369

Includes contributions from @pjonsson, @omad, and @SpacemanPaul, with thanks to supporting organisations
RISE, CSIRO and Geoscience Australia.

**Full Changelog**: https://github.com/opendatacube/datacube-ows/compare/1.9.5...1.9.6

1.9.5 (2025-10-21)
------------------

What's Changed
++++++++++++++

Significant changes include:

- Bug fix to CRS handling.  We still prefer upper case CRSs in config, but can now
  handle lower case CRSs in ODC metadata.  A more major overhaul of OWS's CRS handling is still needed.
- Update to latest version of datacube core.
- HTTP requests (e.g. for forwarded logo images) are now retried on failure.

All included updates:

* Manual dependency updates by @pjonsson (#1272, #1284, #1297,  #1313,
* Auto-dependency updates (#1262-#1264, #1268-#1271, #1275-#1278, #1280-#1281, #1283, #1286-#1291, #1293-#1296,
  #1300-#1306, #1309-#1311, #1314-#1315, #1317-#1318)
* Improvements to CA actions by @pjonsson (#1265, #1273, #1312)
* Misc code cleanup by @pjonsson (#1261, #1299)
* Improvements to default docker behaviour (#1274, #1279)
* Retry HTTP requests (e.g. for forwarded images) by @pjonsson in #1266
* Wrap to_netcdf in bytes() for latest xarray versions by @pjonsson in #1285
* Normalise native spec CRS by @Ariana-B in #1298
* Update HISTORY.txt and default version number for release by @SpacemanPaul in #1319.

**Full Changelog**: https://github.com/opendatacube/datacube-ows/compare/1.9.4...1.9.5

1.9.4 (2025-08-08)
------------------

What's Changed
++++++++++++++

* Fix PyPI push on release automation by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1202
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1204
* docs: fix docker compose name by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1205
* CI: pin remaining actions by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1206
* CI: attest docker image by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1207
* Assorted lint fixes by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1209
* Fix some type signatures by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1210
* update_ranges_impl: import psycopg2 locally by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1211
* docs: unpin docutils version by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1212
* Avoid timezonefinder 6.6.0 by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1213
* CI: fix attestation permissions by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1214
* Enable some more Ruff rules by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1215
* Convert setup.py to pyproject.toml by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1216
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1218
* Fix Ruff configuration by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1217
* CI: use uv for lint jobs by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1219
* Require setuptools_scm >= 8 by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1220
* cfg_parser_impl: respect depth parameter by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1221
* cfg_parser_impl: report error on failure by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1222
* mv_index: remove dead code by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1223
* wcs2_utils: fix type error by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1224
* Make methods static by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1226
* CI: make curl retry more by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1227
* CI: shorten job timeout by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1228
* docs: fix doc build by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1229
* build(deps): bump astral-sh/setup-uv from 6.4.1 to 6.4.3 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1230
* build(deps): bump github/codeql-action from 3.29.2 to 3.29.4 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1231
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1232
* docs: fix some warnings by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1208
* build(deps): bump mambaorg/micromamba from 2.3.0 to 2.3.1 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1233
* CI: cache docker layers by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1234
* readthedocs: use uv for building by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1236
* Dockerfile: use uv for build by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1238
* conf: autogenerate version by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1237
* CI: cache in pyspy workflow by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1239
* HTML and JavaScript updates by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1242
* CI: reduce workflow permissions by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1240
* dockerignore: update with more patterns by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1245
* pre-commit: update ruff hook name by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1247
* build(deps): bump github/codeql-action from 3.29.4 to 3.29.5 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1248
* build(deps): bump docker/metadata-action from 5.7.0 to 5.8.0 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1249
* CI: use OIDC for CodeCov by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1250
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1251
* CI: build Docker with full history by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1252
* CI: fixate time stamp for image layers (towards reproducible docker builds) by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1253
* Add more type signatures by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1241
* uv.lock: update dependencies by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1254
* Dockerfile: remove proj specials by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1246
* Drop deprecated Image.fromarray() mode parameter. by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1257
* Check top level config is a dictionary. by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1258
* Dockerfile: upgrade to uv 0.8.6 by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1259
* Remove pytz by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1255
* Read native product specs from load section in preference to storage section by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1256
* Update fallback version numbers and HISTORY.rst for release by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1260

Includes contributions from @pjonsson and @SpacemanPaul

The ODC Steering Council recognises the ongoing support of Geoscience Australia and RISE.

**Full Changelog**: https://github.com/opendatacube/datacube-ows/compare/1.9.3...1.9.4


1.9.3 (2025-07-11)
------------------

Includes bug-fixes and cleanup.

This version of OWS can be installed without psycopg2 (e.g. for installations that only use the rendering API).
Operational web services will still require psycopg2, which can be installed with e.g. ``pip install datacube-ows[ops]``

What's Changed
++++++++++++++

* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1177
* build(deps): bump mambaorg/micromamba from 2.1.1 to 2.2.0 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1179
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1180
* Update pypi action runner to ubuntu 24.04. by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1181
* Dockerfile: use a single base image by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1182
* build(deps): bump mambaorg/micromamba from 2.2.0 to 2.3.0 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1183
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1184
* Fix GetCaps when some layers are broken by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1185
* Pin lxml<6 as 6.0.0 seems buggy by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1187
* build(deps): bump igsekor/pyspelling-any from 1.0.4 to 1.0.5 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1188
* pytest: output test runtimes by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1186
* feature_info: fix deprecation warning by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1194
* CI: mount source directory by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1195
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1191
* utils: fix deprecation warnings by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1192
* CI: pin actions by hash by @pjonsson in https://github.com/opendatacube/datacube-ows/pull/1197
* build(deps): bump aquasecurity/trivy-action from 0.31.0 to 0.32.0 by @dependabot[bot] in https://github.com/opendatacube/datacube-ows/pull/1198
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci[bot] in https://github.com/opendatacube/datacube-ows/pull/1199
* Make psycopg2 an optional dependency. by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1200
* Update fallback version number and HISTORY.rst for 1.9.3 release. by @SpacemanPaul in https://github.com/opendatacube/datacube-ows/pull/1201

Includes contributions from @pjonsson and @SpacemanPaul, with thanks to supporting organisations Geoscience Australia and RISE.

**Full Changelog**: https://github.com/opendatacube/datacube-ows/compare/1.9.2...1.9.3

1.9.2 (2025-05-29)
------------------

* Type-hint cleanups (#1148, #1149, #1151)
* CI improvements (#1152, #1153, #1156, #1162, #1161, #1167)
* dependency updates and cleanups (#1154, #1163, #1169, #1166, #1165, #1168, #1172, #1173, #1174)
* Replace dockerhub push with GHCR. (#1170)
* Other misc cleanup (#1150, #1155, #1157, #1160, #1159, #1164)
* Prepare for 1.9.2 release (#1175)

1.9.1 (2025-04-16)
------------------

* CI fixes and automatic updates (#1101, #1102, #1107, #1106, #1097, #1105, #1117, #1124, #1114, #1121, #1125, #1129, #1136)
* wsgi: use 1.9 config variable name (#1110)
* Misc code cleanup and updates (#1118, #1119, #1111, #1115, #1120, #1123, #1128, #1116, #1130, #1131, #1134, #1141,
  #1142, #1143, #1144, #1145, #1146)
* Docker cleanups and improvements (#1122)
* Documentation cleanup (#1113)
* Properly close db connections in schema management ops (#1133)
* Refactor styling engine to remove dependency on orphaned colour library (#1140)
* Make ping multi-db aware (#1139)
* Update HISTORY.rst and default version number ready for release (#1147)

Featuring contributions from @pjonsson and @SpacemanPaul.  Thanks to supporting organisations Geoscience Australia
and RISE.

1.9.0 (2024-12-23)
------------------

This is the first OWS release compatible with the 1.9.x series datacube-core releases.

New features from the 1.8.x series releases include:

* Full support for the postgis index driver
* Support for multi-database environment (Can serve data out of multiple indexes)
* Seamless rendering around the antimeridian for most wms and wmts clients.

Changes from 1.9.0-rc2:

* Update HISTORY.rst and default version number ready for release
* Active CI jobs are now cancelled on PR update (#1091)
* Auto upstream library bumps (#1093, #1095)

1.9.0-rc2 (2024-11-15)
----------------------

Now supports seamless rendering across the antimeridian for most wms clients.

* Antimeridian handling (#1076, #1083, #1086,
* Fix bug in resource limiting defaults (#1077)
* Add support for proxy fix header handling (#1085)
* Cherry pick recent updates from mainline (#1087)

This release includes contributions from @SpacemanPaul, @alexgleith, @christophfriedrich and @pjonsson.

1.9.0-rc1 (2024-08-01)
----------------------

* Compatibility with datacube-1.9 and postgres index driver (#1009)
* Cleanup (#1012)
* ODC environment configuration (#1015)
* Postgres ranges rebuild (#1017)
* Cherry picks of bug fixes and new features from 1.8 branch (#1018, #1028, #1040)
* Test database build (#1021)
* Index driver abstraction (#1020)
* Postgis driver support (#1032)
* Prepare for 1.9.0-rc1 release (#1044)

This release includes contributions from @SpacemanPaul

1.8.x Releases
==============

Datacube-ows version 1.8.x indicates that it is designed work with datacube-core versions 1.8.x.

1.8.43 (2024-11-15)
-------------------

* Suppress various upstream warning messages (#1045)
* Various docker image cleanups and updates (#1046, #1047, #1048, #1057, #1059, #1061, #1080)
* Various CI cleanups/improvements (#1050, #1052, #1053, #1055)
* Fix TIFF statistics in case WCS output has NaNs (#1054)
* Documentation improvements (#1064)
* Various auto-updates (#1066. #1071, #1075, #1078, #1082, #1088)
* Fix bug in resource limiting defaults (#1077)
* Prepare for release (#1089)

This release includes contributions from @SpacemanPaul, @alexgleith, @christophfriedrich and @pjonsson.

1.8.42 (2024-08-01)
-------------------

Bug fixes and major extensions for defining custom feature info includes - refer to the documentation
for details.

* Fix dockerfile casing warning (#1035)
* Add --version argument to datacube-ows CLI entry point (#1036)
* Auto-add implicit single top-level folder to ensure strict WMS standard compliance (#1036)
* Changes to materialised view definition to prevent errors on databases with WKT CRS (#1037)
* Custom Feature Info enhancements (#1039)
* Miscellaneous cleanup and backported fixes from 1.9 branch (#1042)
* Update default version number and HISTORY.rst for release (#1043)

This release includes contributions from @SpacemanPaul and @pjonsson.

1.8.41 (2024-07-16)
-------------------

New Feature!  Multi-date handler aggregator functions for colour-ramp type styles can now receive
either the results of the index function, or the raw band data by setting a config option.  (Previously
they always received the results of the index function.)

* Improved error messages when creating extents without materialised views (#1016)
* Several minor bug-fixes and improved error handling in WCS code (#1027)
* Automated updates (#1022)
* Allow multi-date handler aggregator functions to receive raw data (#1033)
* Update HISTORY.rst and increment default version for release (#1034)

This release includes contributions from @SpacemanPaul and @whatnick

1.8.40 (2024-04-29)
-------------------

Bug fix release

* Loading now uses `skip_broken_datasets=True` by default. (#1001)
* Bump base osgeo/gdal docker image version. (#1003)
* Update versions of several upstream packages to avoid known security issues (#1004, #1005, #1008)
* pre-commit autoupdate (#1006)
* Make S3 URL rewriting work with metadata indexed from STAC (#1011)
* Update HISTORY.rst and increment default version for release and some tests. (#1013)

This release includes contributions from @whatnick, @pjonsson, @SpacemanPaul, and various automatic updater bots.

1.8.39 (2024-03-13)
-------------------

Emergency release to complete half-implemented new feature.

The changes to the spatial materialised view introduced in the previous release are now also implemented
in the time materialised view.

Please run `datacube-ows-update --schema --role <ows_db_username>` again with this new release
to access the new behaviour.

* Automatic CI action update (#998)
* Fix materialised view definition to handle all eo3 compatible metadata types (#999)
* Update HISTORY.rst and increment default version for release (#999)

1.8.38 (2024-03-12)
-------------------

Previously the spatial materialised view recognised metadata types by individual name and required manual tweaking
for every new metadata type.  From 1.8.38, all metadata types with a name starting with `eo3_` will be treated as
eo3 compatible.

Run `datacube-ows-update --schema --role <ows_db_username>` to activate the new definitions.

Also includes miscellaneous bug fixes and maintenance.

* Upgrade pypi publish github action from unsupported version (#994)
* Tweak FeatureInfo JSON documents to be compliant geojson (#995)
* Tweak materialised view definition to handle all eo3 compatible metadata types (#996)
* Fix Dimension sections of WMTS Capabilities documents to comply with standard (#996)
* Update HISTORY.rst and increment default version for release (#997)

1.8.37 (2024-02-28)
-------------------

Maintenance release.  Security updates and bug fixes around timezone handling.

* Fixes to timezone handling (#958, #982)
* Various Github CI improvements (#959, #972, #974)
* Automatic dependency updates (#966, #970, #971, #975, #976, #977, #980, #981, #984, #986, #988, #991, #992)
* Update dependencies to block upstream security issues (#973)
* Label Prometheus metrics by endpoint, not path (#978)
* Update base docker image and remove docker efficiency analysis GHA (#990)
* Update HISTORY.rst and increment default version for release (#993)

Contributions from @benjimin, @pjonsson, @SpacemanPaul and @dependabot.

1.8.36 (2023-10-24)
-------------------

* Fix Docker image and CI pipeline (#954)
* Make PYDEV_DEBUG behaviour less counter-intuitive (#955)
* Update HISTORY.rst and increment default version for release (#956)

1.8.35 (2023-09-01)
-------------------

Maintenance release.

* Changes to dependency version pins (#983, #942, #948, #949)

Includes contributions from @pindge, @emmaai and @SpacemanPaul.

1.8.34 (2023-03-21)
-------------------

This OWS release includes two significant new features:

1. Timeless mosaic layers.

   The new `mosaic_date_func` configuration option allows the creation of timeless (i.e. single time-slice)
   layers.  The user-provided function returns the start/end date to use for dataset date searches, and a
   mosaic layer is generated, with the most recent available date for any given pixel returned.

2. Enhanced time resolution handling (subday and overlapping summary periods).

   Major refactor of time resolution handling.

   There are now only 3 time resolution options:

   *solar:* Replaces the old "raw" option. Local-solar-day time model, used for imagery captured in daily swathes
   by satellites in heliosynchronous orbits.

   *summary:* Replaces the old "day", "month", and "year" options. Only looks at the "start" datetime, and
   so neatly supports products with overlapping or non-exclusive dataset date-ranges. Expects the time portion
   of the start date to always be "midnight UTC". Used for summary/calculated products.

   *subday:* New option. Used for for products with multiple time values per day (e.g. hourly/minutely data). Uses
   the "start" datetime of the dataset.

   Note that the *solar* and *summary* options explicitly ignore the **time** component of the *time* query parameter
   passed by the user. If you need the time component to be significant, you must use subday.

   The old "raw", "day", "month", "year" time_resolution options are still supported as aliases for the new
   values above.  A deprecation warning will be issued advising you to update your configuration to the new
   values, but the old values will continue to work.  You should not actually move your configuration to
   the new values until after all of your deployment environments have been upgraded v1.8.34.

Full list of changes:

* Increment default version number and update version history (#937)
* Enhanced time resolution handling (subday and overlapping summary periods) (#933, #936)
* Add spellcheck to RST documentation (#929, #930)
* Implement timeless mosaic layers (#928)
* Refactor integration tests to use new collection DEA data (#927)
* Bump datacube-core version (#923, #927, #933)
* Miscellaneous cleanup and code-maintenance (#922)
* Pre-commit auto-updates (#920, #926, #932, #934)

1.8.33 (2022-12-20)
-------------------

Full list of changes:

* Update to examples in documentation (#912)
* Bug-fixes to WCS2 (#913, #915)
* Pre-commit auto-updates (#914, #917)
* Make compatible with numpy 1.24.0+ (#918)
* Update default version number and HISTORY.rst (#919)


1.8.32 (2022-11-30)
-------------------

Full list of changes:

* Add datacube pypi badge (#891)
* Pre-commit auto-updates (#894, #899, #906)
* Github action update (#896)
* Documentation updates (#898, #903, #904)
* WCS grid counts and add checks for sign errors in native resolution (#902)
* Match docker image version numbers to github SCM version numbers (#907, #908, #909)
* Update default version number and HISTORY.rst (#910)

Contributions from @pindge and @SpacemanPaul (and of course, the pre-commit-ci bot).


1.8.31 (2022-10-24)
-------------------

Full list of changes:

* Added pre_scaled_norm_diff to band_utils.py, allowing calculation of normalised difference calculations on
  data that is scaled with an offset. (#881)
* Add support for url patching - allowing OWS to serve data from commercial data repositories that use
  uri signing for authentication (e.g. Microsoft Planetary Computer) (#883)
* Further refinements to Sentry logging. (#884)
* Improve interoperability with Jupyter Notebooks. (#886)
* Allow band alises for Flag Bands taken from main product(s). (#887)
* Add new metadata type to MV definitions, to support DEA Sentinel-2 Collection 3. (#888)
* Add support for html info_format for GetFeatureInfo queries in WMS and WMTS - may improve ArcGIS
  compatibility. (#889)
* Updates to HISTORY.rst, README.rst and default version string for release (#890)

Contributions from @pindge, @rtaib and @SpacemanPaul.

1.8.30 (2022-10-11)
-------------------

Minor release, consisting of better Sentry reporting for production deployments, and routine repository
maintenance.

Full list of changes:

* Update code-of-conduct.md to refer to current ODC Steering Council chair (#862)
* Fixes to docker-compose files and github workflows (#864, #866, )
* Simplify and cleanup scripts and config to create database for integration tests (#865, #871)
* Change interpretation of Sentry environment variables to allow Sentry reporting to any hosted Sentry service (#868, #877)
* Prevent mysterious Shapely warning message from clogging up Sentry logs (#873)
* Minor tweaks to aid trouble-shooting and better support local deployments (#878)
* Updates to HISTORY.rst, README.rst and default version string for release (#879)

Contributions from @pindge and @SpacemanPaul.

1.8.29 (2022-08-30)
-------------------

This release includes support for heterogenous multi-product layers (single layers that combine data
from satellite platforms with different bands and native resolutions - e.g. Sentinel-2 plus Landsat),
an upgrade to the docker container (now based on Ubuntu 22.04, with Python 3.10), plus documentation updates
and bug fixes.

Full list of changes:

* Enhancements to support heterogenous multi-product layers (#837, #841, #844)
* Refactor data for integration test fixtures (#835)
* Docker image migrated to Python3.10/Ubuntu-22.040-based osgeo/gdal base image, and updates to
  dependencies (#838, #843, #852, #854, #856, #859)
* Isolate ops imports to minimise dependencies for applications only using the styling API (#855)
* Documentation updates and improvements (#846, #847, #848, #849)
* Bug Fix: Skip cached bounding boxes when layer extent is entirely outside the valid region for the CRS (#832)
* Bug Fix: Invalid version parameters in otherwise valid requests were failing with unhandled 500 errors. OWS now
  makes a best-effort guess in this case, tending towards the lowest supported version (#850)
* Bug Fix: response_crs parameter was not being handled correctly by WCS1 (#858)
* Updates to HISTORY.rst and default version string for release (#860)

This release includes contributions from @SpacemanPaul, and @pindge.

1.8.28 (2022-04-12)
-------------------

This release introduces changes to both the materialised view definitions and the ``datacube-ows-update``
utility to improve the accuracy and reliability of these extents, as well as bug fixes for
externally-hosted legend images.

This release includes:

* A bug fix to the OWS code which reads from the materialised views, preventing runtime errors
  from occurring in scenarios where accurate extent information is not available (#825)
* Enhancements to the materialised view definitions to support extracting extent polygons
  from various optional metadata locations in both EO and EO3 based products. (#826)
* Sanity-check and sanitise bounding box ranges for global datasets.  It should now be
  possible to use datasets with bounding box ``(-180, -90, 180, 90, crs=EPSG:4326)`` in
  OWS.  Previously this required hacking the metadata to result in e.g.
  ``(-179.9999, -89.9999, 179.999, 89.999, crs=EPSG:4326)`` (#828)
* Usability improvements for external legends. Clearer reporting of read errors on external
  urls, and raise warning instead of failing if external image format is not PNG. (#829)
* Update HISTORY.rst and default version number (#830)

Upgrade notes:
++++++++++++++

To enjoy all the advantages of these extent handling enhancements you will need to
run the following command, using a database role capable of altering the schema::

     datacube-ows-update --schema --role role_to_grant_access_to

After regenerating the schema, the range tables should also be updated::

     datacube-ows-update

(Note that there is no need to run ``datacube-ows-update`` with the ``--views`` option in between these
two steps.)

1.8.27 (2022-04-04)
-------------------

Several bugfixes, and documentation updates and we had to change our CI test data because the old USGS Landsat PDS went user-pays.

Cache-control hints can now be configured for the XML requests (GetCapabilities, DescribeCoverage).  WMS and WCS GetCapabilities can be configured separately.  WCS DescribeCoverage can be configured globally and optionally over-ridden per layer/coverage.   Refer to the documentation for details.

Full list of changes since 1.8.26:
++++++++++++++++++++++++++++++++++

* Bug fix: Multidate NetCDF requests were broken in both WCS1 and WCS2- now fixed (#799)
* int8 added as a supported dtype (#801, #802)
* Logging updated to include remote IP (#808,#811,#818)
* Documentation updates (#810, #819, #820)
* Replace USGS Landsat data with Sentinel-2 data for CI integration testing. (#812, #817)
* Bug fix: Manual merge where no extent mask function was broken (#817)
* Cache-control hints for XML requests (GetCapabilities/DescribeCoverage) (#821, #822)
* Update HISTORY.rst and default version number (#823)

1.8.26 (2022-01-31)
-------------------

Optimisation release.  Performance improvements to colour-map style rendering algorithm.
For large, complex value_map rule sets the improvement is dramatic (e.g. DEA LCCS level4 style,
which contains over 100 rules, rendering speed is increased by 70-80%).

* Minor improvements to unit and docker testing (#792, #793)
* Optimisation of colour-map style rendering algorithm (#795)
* Increment default version number and update HISTORY.rst (#797)

1.8.25 (2022-01-19)
-------------------
Bug fix release.

The legend internationalisation code in 1.8.24 caused errors in manual legends for deployments that do not have internationalisation enabled.  This release fixes that issue.

* Legend internationalisation bug fix (#789, #790)
* Update default version number and HISTORY.rst (#791)

1.8.24 (2022-01-18)
-------------------

Introduces support for internationalisation (translation) of style legends - see the documentation for details:

https://datacube-ows.readthedocs.io/en/latest/configuration.html#metadata-separation-and-internationalisation
https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#url

This is the first formal release since the 9th December, although there were several interim releases in
mid-December when we were testing the Prometheus metric changes (see below).

Due to an oversight in deprecation warnings several releases ago, some configurations that worked in 1.8.23
will now raise errors.  Affected configurations have legacy "legend" hints embedded inside the colour ramp
definitions.  Such hints have not been read by OWS for quite some time, having been replaced by the "tick_labels" entry in the "legend" section.  Digital Earth Australia and Digital Earth Africa configurations have already been updated.

Changes since 1.8.23:

* Prometheus metric enhancements and release notes for interim releases (#777, #778, #779, #780, #781, #782)
* Github integration tests against a large real world OWS configuration (DEA) (#784)
* Internationalisation of style legends. (#783, #786)
* Fix WCS1 DescribeCoverage regression (missing SRS/CRS) (#787)
* Update History.RST and increment default version number (#788)

1.8.23.3 (2021-12-16)
---------------------

Interim administrative release.

* Upgraded Prometheus metrics to histogram type, and updated HISTORY.rst (#781)

1.8.23.2 (2021-12-15)
---------------------

Interim administrative release.

* Improved Prometheus metrics for monitoring (#779)
* Update HISTORY.rst (#780)

1.8.23.1 (2021-12-10)
---------------------

Interim administrative release.

* Improved Prometheus metrics for monitoring (#777)
* Update HISTORY.rst (#778)

1.8.23 (2021-11-16)
-------------------

In addition to the standard animated handlers previously supported by all style types, this release
introduces two additional approaches to produce an non-animated image from a multi-date request for
colour-map (aka value_map) type styles:

* Using a variant of the value_map_ entry used for the single-date case. This is a much simpler way of achieving most use cases.
* Using an aggregator function, which allows for fully customisable behaviour but requires writing Python code.

The new behaviour is fully documented here: https://datacube-ows.readthedocs.io/en/latest/cfg_colourmap_styles.html#multi-date-requests

This means that OWS now supports rich comparison visualisation techniques for both contiguous and discrete data products.

Also, the masking rule parser for pq_masks sections now uses the same code as the parser for value_map rules in colour map styles.

This means that:

* pq_mask rules now supports and/or operators, consistent with value_map rules.
* value_map rules now support the invert operator, consistent with pq_mask rules.
* The old "enum" keyword in pq_masks is now deprecated - please now use the values keyword, as in value_maps.

Full details are in the documentation. Old style syntax will continue to work as before - except the
enum keyword in pq_masks now produces a deprecated warning message.

Changes in this release:
++++++++++++++++++++++++

New Feature:

*  Support for non-animated multi-date handlers for "colour-map" type styles. (#770)
*  Consistent syntax for masking rules in pq_masks and value_map rules (#774)

Bug fixes

* Fix to bug affecting resource-limiting for WCS (#769)
* Fix bug in handling of missing data when applying cross-product masking (#772)

Dependency management and release process

* Remove constraint requiring very recent versions of numpy (#766)
* Upgrade to Postgis 3.1 (#767)
* Add automated spell check of documentation to github actions (#775)
* Increment default version number. (#776)

This release includes contributions from @Kirill888, @NikitaGandhi, @pindge and @SpacemanPaul

1.8.22 (2021-11-11)
-------------------

* Raise error on duplicate layer names. (#759)
* Add layer name to config manifest file format (#759)
* Apply configured http headers to WCS2 GetCoverage responses (#761)
* Remove and replace tests based on S3FS, removing test dependency on aiobotocore (#762)
* Documentation updates (#758)
* Increment default version number (#763)

1.8.21 (2021-10-21)
-------------------

* Allow layers with no ``extent_mask_function`` (#739)
* Eliminate redundant connection pool - use datacube-core connection pool directly (#740)
* Remove requirements.txt Use setup.py exclusively for dependency management. (#741, #744)
* Improve docker image efficiency (#743, #745, #746)
* Fix WCS1 bug affecting requests with no explicit measurements or style (#749)
* Add ``$AWS_S3_ENDPOINT`` to environment variable documentation (#751)
* Improve Prometheus metrics (#752)
* Fix function config internal over-writing issue - was causing issues for odc-stats (#754)
* Increment default version number and switch setuptools_scm to post-release version numbering (#753)

1.8.20 (2021-10-06)
-------------------

WCS enhancements, new docker image, bug fixes, and doc updates.

Please read the release notes before upgrading.

WCS changes
+++++++++++

As more in the community are starting to actively use WCS, we are slowly polishing away the rough edges. This
release has two changes of interest to OWS administrators who use WCS:

1. Firstly, the wcs ``default_bands`` has been removed. The default behaviour for WCS requests that do not specify
   bands is now to return all available bands, as specified in the WCS2 standards.

This means that layer-level ``wcs`` sections is no longer required. If you have any, you will get warning
messages. You can ignore these until you are sure that all your server instances have been upgraded to 1.8.20,
when it is safe to remove the layer ``wcs`` sections from your config to suppress the warning.

2. Secondly, more options are available for resource limiting in WCS. Refer to the documentation for details:

https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#resource-limits-wcs

Docker image base change
++++++++++++++++++++++++

The Docker images are now based on ``osgeo/gdal`` instead of ``opendatacube/geobase``. You may need to tweak
your build environment slightly - check your env files against the latest examples.

New in this release
+++++++++++++++++++

* Switch docker base image from geobase to osgeo/gdal. (#727)
* Remove support for wcs ``default_bands`` entry (# 725)
* Extend resource management capabilities for WCS (#730)
* Fixed several corner-case bugs in the color ramp legend generator (#732)
* Add chapter on legend generation to HOWTO (#733, #735)
* Added Security.md file (#734)
* Other improved documentation (#711)
* Fix bug affecting layers with no extent mask function. (#737, #739)
* Increment default version number to 1.8.20 (#738)

1.8.19 (2021-09-20)
-------------------

Improved test coverage and documentation; bug fixes; repo cleanup.

* Improved test coverage (#708, #709, #710)
* Fixed zero-day bug in WMTS GetFeatureInfo (#708)
* Improved pylint github action (thanks @pindge). (#713)
* Cleanup of requirements lists, and removal of old unused files. (#714)
* Fix platform-dependent numpy.typing import issue (thanks @alexgleith) (#718)
* Fix two WCS query interpretation bugs (#719)
* Documentation updates, including a cleanup of the README. (#720)
* Add support for ows_stats performance diagnostic tool to WMTS and WCS. (#721)
* Pin s3fs version in requirements.txt for compatibility with odc_tools (#722, #724)
* Increment version number (#723)


1.8.18 (2021-09-02)
-------------------

Adds support for dynamic credentials for S3 access.

Thanks to @woodcockr, @valpesendorfer and @pindge.

* Docker-compose fix for v1.29 (#702)
* Add smart resource management data to ows_stats output (#703)
* Renewable S3 credentials (#704, #706)
* Fix bug in direct config inheritance for objects supporting named inheritance (#705)
* Increment default version number (#707)


1.8.17 (2021-08-25)
-------------------

Urgent bug-fix release to address a WCS bug.

This release also contains a couple of minor backwards compatibility issues, see below for details.

Version 1.8.18 will probably follow fairly rapidly as there are a couple of other known issues that
are actively being worked on, see below for details.

Changes:
++++++++

* Cleanup/refactor of styles package: docstrings, type-hints, cleanup and improved test coverage (#695)
* Change default behaviour of ``$AWS_NO_SIGN_REQUEST`` to match the standard default behaviour for boto3-based applications (#696)
* Fix WCS queries against layers with a flag-band in the main product (#699)
* Increment version number (#700)

Backward Incompatibilities
++++++++++++++++++++++++++

1. #695 removed support for some legacy legend config formats that have been deprecated (and undocumented)
   for over a year.
2. #696 changes the default behaviour if ``$AWS_NO_SIGN_REQUEST`` is not set. Previously the default behaviour
   was unsigned requests, it is now signed requests. This was a necessary first-step to supporting dynamic
   credentials for S3 access, and brings OWS into line with other software using boto3 for S3 access.

Known Issues
++++++++++++

1. There are still issues with WCS queries against layers with a flag-band in the main product. These will be
   addressed in the next release and should not effect queries generated by the Terria Export function.
2. Dynamic credentialling for S3 access is still problematic. We have a PR almost ready to merge (#697) but
   it needs further testing.

1.8.16 (2021-08-16)
-------------------

Mostly about implementing smarter resource limiting to make time-series animation production ready.

* Smarter resource limiting (#686, #689, #690)
* docker-compose.yml fixes. (#685)
* Fix typo in ``.env_ows_root`` (#683)
* Remove "experimental" warning on time-series animations (#691)
* Better error reporting of config error cases potentially caused by easy-to-make typos (#692)
* Increment version number (#693)

Note the following changes to configuration introduced in this release. Old configurations should continue to work,
with the backwards-incompatible exceptions noted below, however you may see warning messages on startup advising
which parts of your config are now deprecated and should be updated.

1. ``native_crs`` and ``native_resolution`` were previously part of the ``wcs`` configuration section of layers,
   as they were previously only used for generating WCS metadata. They are now also used by the new
   ``min_zoom_level`` resource limit for WMS/WMTS, and have therefore moved out of the ``wcs`` section and into
   the main layer config section. These entries will continue to be read from the old location with a
   deprecation warning. If present in both locations, the values in the new locations take precedence, and
   the deprecation warning will still be raised.
2. There is a new ``min_zoom_level`` configuration option, which should be considerably easier to set and
   use than ``min_zoom_factor``, as well as being much smarter about how resource requirements for request
   are estimated. ``min_zoom_factor`` is still supported, but will be deprecated in a future release.

Backwards Incompatibility Notes

I try to avoid backwards incompatible changes to config format, but some minor ones were unavoidable in this release:

1. Layers with no CRS and/or resolution defined in the ODC product metadata now ALWAYS require a native CRS and resolution to be defined in configuration. This was previously only the case if WCS was enabled for the layer.
2. The default resource_limiting behaviour for WMS/WMTS has changed from "min_zoom_factor = 300.0" to "no resource limits". Maintaining backwards compatibility would have resulted in confusing and inconsistent behaviour.


1.8.15 (2021-07-30)
-------------------

1.8.15 introduces experimental* support for time-series animations from WMS/WMTS, in APNG format,
and has increased CI test coverage to over 90%.

If you use docker-compose to orchestrate your configuration, you may need to make some changes to
your ``.env`` file after upgrading to this release. See the updated examples and the documentation for details.

Thanks to all contributors, especially @whatnick for the prototype implementation of time-series animation,
and @alexgleith for supplying much needed user-feedback on the CLI interfaces.

(* experimental) = produces a warning message when activated. The existing resource limit implementation is
not suitable for production deployment with time-series animations. I hope to address this in the next release.

* Support for time-series animation APNG output for WMS and WMTS. (#656, #670, #678)
* User configurable WMS default time (#676)
* Code cleanup, starting to systematically add type hints and docstrings. (#660, #663, #664, #665, #671)
* CI enhancements (#662, #672, #674)
* datacube-ows-update changes to error handling to improve UX for maintainers. (#666, #679)
* Enhancements to config management in docker-compose. Note that if you use docker-compose, you may need to make some changes to your ``.env`` file. See the updated examples and the documentation for details. (#681)
* Release housekeeping, including incrementing default version number (#682)

1.8.14 (2021-07-09)
-------------------

* Default band names (as exposed by WCS) are now internationalisable (#651)
* Extent polygon rendering now uses rasterio rasterize, removing the dependency on scikit-image (#655)
* Calculating GeoTIFF statistics in WCS is now (globally) configurable (#654)
* Return an empty response if data for any requested dates is not available (#652)
* Bug fix - summary products (time_resolution not raw) were broken in areas close to 0 longitude. (e.g. Africa) (#657)
* Increment default version number (#658)

1.8.13 (2021-06-29)
-------------------

* Support for Regular Time Dimensions: Two independent requests for this behaviour have come from the user community. (#642)
* Fix for WCS2 band-aliasing bug (#645)
* Increment default version number (#647)

1.8.12 (2021-06-22)
-------------------

Documentation and API tweaks for the styling workshops at the 2021 ODC conference.

* Fix output aspect ratio when plotting from notebooks. (#369)
* Fixes to Styling HOWTO and JupyterHub Quick Start. (#641)
* Increment default version number to 1.8.12 (#640)


1.8.11 (2021-06-18)
-------------------

Bug Fix release.

* Multiproduct masking bugfix (#633)
* Better error reporting (#637)
* Documentation tweaks. (#632, #634, #645)
* Increment default version number (#636)

1.8.10 (2021-06-16)
-------------------

Mostly a bugfix release.

* plot_image functions added to styling API (e.g. for use in notebooks). (#619)
* Pass $AWS_S3_ENDPOINT through from calling environment to docker. (#622)
* Add dive for monitoring container size and contents (#626)
* Suppress confusing error messages when update_ranges is first run (#629)
* Bug fix (#620, #621,#623)
* Documentation corrections and enhancements. (#624,#625,#627,#630)
* Increment default version number to 1.8.10 (#631)

1.8.9 (2021-06-03)
------------------

New features:
+++++++++++++

* Optional separation of metadata from configuration and internationalisation (#587, #608, #609).
* Docker containers now run on Python 3.8 (#592, #598, #599, #602, #603, #604, #605, #606, #610, #612, #614).
* Bulk processing capabilities in Styling API (#595).
* Ability to load json config from S3 (disabled by default - enable with environment variable). (#591, #601)
* Misc bug-fixes and documentation updates (#611, #616, #617)

Repository Maintenance and Administrivia:
+++++++++++++++++++++++++++++++++++++++++

* Reduce redundant processing in Github Actions (#594).
* Add license headers and code-of-conduct. Improve documentation to meet OSGeo project requirements (#593)
* Make ows_cfg_example.py (more) valid. (#600)
* Increment version number (#618)

WARNING: Backwards incompatible change:
+++++++++++++++++++++++++++++++++++++++

* The old datacube-ows-cfg-parse CLI tool has been replaced by the check sub-command of the new, more general purpose datacube-ows-cfg CLI tool.


1.8.8 (2021-05-04)
------------------

New Features:
+++++++++++++

* Multidate ordering (#580)
* New "day_summary" time_resolution type, for data with summary-style time coordinates (as opposed to local solar-date style time coordinates). (#584)

Bug Fixes and Administrivia:
++++++++++++++++++++++++++++

* More thorough testing of styling engine (#578)
* Bug fixes (#579, #583)
* Upgrade pydevd version for debugging against Pycharm 2021.1.1 (#581)
* Repository security issue mediation (Codecov security breach) (#585)
* Increment version number (#586)

1.8.7 (2021-04-20)
------------------

* Includes support for user-defined band math (for colour ramp styles with matplotlib colour ramps). This is
  an experimental non-standard WMS extension that extends the WMS GetCapabilities document in the standard
  manner. The output validates against an XSD which is a valid extension of the WMS GetCapabilities schema.
  Backwards compatible extensions to GetMap allow the feature to be called by client software (#562, #563).
* If all goes to plan this will be the first OWS release automatically pushed to PyPI
  (#560, #568, #369, #570, #571, #572, #573, #574, #575, #576).
* Multi-product masking bug fix (#567). This was a serious bug affecting most multi-product masking use cases.
* Documentation updates (#561, #564)
* Version number increment to 1.8.7 (#577)

1.8.6 (2021-04-08)
------------------

* Enhanced documentation (including HOWTO Styling Guide). (#545, #551, #554, #555, #558)
* Stricter linting (#549, #550, #552, #557)
* Minor improvements to extent masking (#546)
* Miscellaneous bug fixes (#553, #556)

1.8.5 (2021-03-25)
------------------

First release to
PyPI: `https://pypi.org/project/datacube-ows/1.8.5/ <https://pypi.org/project/datacube-ows/1.8.5/>`_

* Date delta can now control subtraction direction from config (#535)
* New helper functions in standalone API (#538)
* Bug fixes in standalone API. (#542, #543)
* First draft of new "HOWTO" Styling guide. (#540, #543)
* Miscellaneous cleanup. (#533, #534, #537, #541)
* Prep for PyPI (#544)

1.8.4 (2021-03-19)
------------------

*    Standalone API for OWS styling. (#523)
*    Support for enumeration type bands in colour-map styles. (#529)
*    Numerous bugfixes.
*    Updated documentation.

1.8.3 (2021-03-12)
------------------

*    Generalised handling of WMTS tile matrix sets (#452)
*    Progressive cache control headers (#476)
*    Support for multi-product masking flags. (#499)
*    Greatly improved test coverage (various)
*    Many bug-fixes, documentation updates and minor enhancements (various)

1.8.2 (2020-10-26)
------------------

*    Config inheritance for layers and styles.
*    CRS aliases
*    Enhanced band util functions.
*    Query stats parameter.
*    Stand-alone config parsing/validating tool.
*    Cleaner internal APIs, improved test coverage, and bug fixes.

1.8.1 (2020-08-18)
------------------

* Bug fixes
* Performance enhancements - most notable using materialised views for spatio-temporal DB searches.
* Improved testing and documentation.

1.8.0 (2020-06-10)
------------------

* Synchronise minor version number with datacube-core.
* Materialised spatio-temporal views for ranges.
* WCS2 support.

Incomplete list of pre-1.8 releases.
====================================

Prior to 1.8.0 the release process was informal and ad hoc.

0.8.1 (2019-01-10)
------------------

* Reconcile package version number with git managed version number

0.2.0 (2019-01-09)
------------------

* Establishing proper versioning
* WMS, WMTS, WCS support

0.1.0 (2017-02-24)
------------------

* First release on (DEA internal) PyPI.
