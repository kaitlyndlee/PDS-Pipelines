import os
# Database credentials
credentials = {'pdsdi': {'user': 'pdsdi',
                         'pass': 'dataInt',
                         'host': 'dino.wr.usgs.gov',
                         'port': '3309',
                         'db': 'pds_di_prd'},

               'pdsdi_dev': {'user': 'pdsdi',
                             'pass': 'dataInt',
                             'host': 'dino.wr.usgs.gov',
                             'port': '3309',
                             'db': 'pds_di_dev'},

               'clusterjob_prd': {'user': 'jobmgr',
                                  'pass': 'jbMg!r',
                                  'host': 'spacely.wr.usgs.gov',
                                  'port': '3309',
                                  'db': 'clusterjobs_prd'},

               'upcdev': {'user': 'upcmgr',
                          'pass': '1234',
                          'host': 'namikaze',
                          'port': '9010',
                          'db': 'upc'},

               'upcprd': {'user': 'upcmgr',
                          'pass': '1234',
                          'host': 'namikaze',
                          'port': '9010',
                          'db': 'upc'}
               }

# Redis path(?) info
redis_info = {'host': 'redis.wr.usgs.gov', 'port': '6379', 'db': '0'}

# POW / MAP2 base path
pow_map2_base = '/pds_san/PDS_Services/'

web_base = 'https://pdsimage.wr.usgs.gov/Missions/'
archive_base = '/pds_san/PDS_Archive/'
link_dest = '/pds_san/PDS_Archive_Links/'

# Recipe base path
recipe_base = '/home/kdlee/builds/PDS-Pipelines/recipe/new/'

pds_info = '/home/kdlee/builds/PDS-Pipelines/pds_pipelines/PDSinfo.json'

pds_log = '/home/kdlee/builds/PDS-Pipelines/logs/'

slurm_log = '/home/kdlee/builds/PDS-Pipelines/output/'

cmd_dir = '/home/kdlee/builds/PDS-Pipelines/pds_pipelines/'

keyword_def = '/home/kdlee/builds/PDS-Pipelines/recipe/Keyword_Definition.json'

# workarea = '/scratch/pds_services/dpmayer_upc_testing/PDS-Pipelines/products/'
workarea = '/home/kdlee/builds/PDS-Pipelines/work'
default_namespace = 'kdlee_queue'

pds_db = 'pdsdi'
upc_db = 'upcprd'

scratch = '/scratch/pds_services/'

lock_obj = 'processes'

upc_error_queue = 'UPC_ErrorQueue'

disk_usage_ratio = 0.4
