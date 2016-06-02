from __future__ import unicode_literals

import os
import shutil
import logging
import tempfile
import subprocess
import xml.etree.ElementTree as ET
import urllib2

from django.db import migrations
from django.core.files.uploadedfile import UploadedFile

from django_irods.storage import IrodsStorage
from hs_core import hydroshare
from hs_core.hydroshare.utils import resource_modified
from hs_geo_raster_resource.models import RasterResource
from hs_geo_raster_resource import raster_meta_extract


def migrate_tif_file(apps, schema_editor):
    log = logging.getLogger()
    istorage = IrodsStorage()

    start_migrate = True
    check_success = False

    copy_res_fail = []
    vrt_update_fail = []
    vrt_update_success = []
    meta_update_fail = []
    meta_update_success = []

    # check whether the migration has been executed or not
    print RasterResource.objects.all()
    for res in RasterResource.objects.all():
        try:

            scimeta_path = "{}/data/resourcemetadata.xml".format(res.short_id)
            scimeta_url = istorage.url(scimeta_path)
            print scimeta_url
            scimeta_str = urllib2.urlopen(scimeta_url).read()

            check_success = True

            if scimeta_str.find('hsterms:maximumValue') != -1 or scimeta_str.find('hsterms:minimumValue') != -1:
                start_migrate = False
                break

        except Exception as e:
            check_success = False
            log.exception(e.message)
            print e.message

    # start migration for each raster resource that has raster files
    if check_success and start_migrate:

        for res in RasterResource.objects.all():
            if res.files.all():

                # copy all the resource files to temp dir
                try:
                    temp_dir = tempfile.mkdtemp()
                    for res_file in res.files.all():
                        shutil.copy(res_file.resource_file.file.name,
                                    os.path.join(temp_dir, os.path.basename(res_file.resource_file.name)))

                    vrt_file_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if '.vrt' == f[-4:]].pop()

                except Exception as e:
                    log.exception(e.message)
                    copy_res_fail.append('{}:{}'.format(res.short_id, res.metadata.title.value))
                    continue

                # update vrt file if the raster resource that has a single tif file
                try:
                    if len(os.listdir(temp_dir)) == 2:
                        # create new vrt file
                        tif_file_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if '.tif' == f[-4:]].pop()
                        with open(os.devnull, 'w') as fp:
                            subprocess.Popen(['gdal_translate', '-of', 'VRT', tif_file_path, vrt_file_path], stdout=fp, stderr=fp).wait()   # remember to add .wait()

                        # modify the vrt file contents
                        tree = ET.parse(vrt_file_path)
                        root = tree.getroot()
                        for element in root.iter('SourceFilename'):
                            element.attrib['relativeToVRT'] = '1'
                        tree.write(vrt_file_path)

                        # delete vrt res file
                        for f in res.files.all():
                            if 'vrt' == f.resource_file.name[-3:]:
                                f.resource_file.delete()
                                f.delete()

                        # add new vrt file to resource
                        new_file = UploadedFile(file=open(vrt_file_path, 'r'), name=os.path.basename(vrt_file_path))
                        hydroshare.add_resource_files(res.short_id, new_file)

                        # update the bag
                        # bag_name = 'bags/{res_id}.zip'.format(res_id=res.short_id)
                        # if istorage.exists(bag_name):
                        #     # delete the resource bag as the old bag is not valid
                        #     istorage.delete(bag_name)
                        resource_modified(res, res.creator)

                        vrt_update_success.append('{}:{}'.format(res.short_id,res.metadata.title.value))

                except Exception as e:
                    log.exception(e.message)
                    vrt_update_fail.append('{}:{}'.format(res.short_id,res.metadata.title.value))

                # update the metadata for the band information of all the raster resources
                try:
                    meta_updated = False

                    # extract meta
                    ori_dir = os.getcwd()
                    os.chdir(temp_dir)
                    res_md_dict = raster_meta_extract.get_raster_meta_dict(vrt_file_path)
                    os.chdir(ori_dir)
                    shutil.rmtree(temp_dir)

                    # update band information metadata in django
                    if res_md_dict['band_info']:
                        for i, band_meta in res_md_dict['band_info'].items():
                            band_obj = res.metadata.bandInformation.filter(name='Band_{}'.format(i)).first()
                            if band_obj:
                                res.metadata.update_element('bandInformation',
                                                            band_obj.id,
                                                            maximumValue=band_meta['maximumValue'],
                                                            minimumValue=band_meta['minimumValue'],
                                                            noDataValue=band_meta['noDataValue'],
                                                            )
                                meta_updated = True

                    # update the bag if meta is updated
                    if meta_updated:
                        # bag_name = 'bags/{res_id}.zip'.format(res_id=res.short_id)
                        # if istorage.exists(bag_name):
                        #     # delete the resource bag as the old bag is not valid
                        #     istorage.delete(bag_name)
                        resource_modified(res, res.creator)
                        meta_update_success.append('{}:{}'.format(res.short_id, res.metadata.title.value))

                except Exception as e:
                    log.exception(e.message)
                    meta_update_fail.append('{}:{}'.format(res.short_id, res.metadata.title.value))

        # Print migration information
        print 'Copy resource to temp folder failure: Number: {} List: {}'.format(len(copy_res_fail), copy_res_fail)
        print 'VRT file update success: Number: {} List{}'.format(len(vrt_update_success), vrt_update_success)
        print 'VRT file update fail: Number: {} List{}'.format(len(vrt_update_fail), vrt_update_fail)
        print 'Meta update success: Number: {} List {}'.format(len(meta_update_success), meta_update_success)
        print 'Meta update fail: Number: {} List {}'.format(len(meta_update_fail), meta_update_fail)

    else:
        print 'Migration is not executed. Migration status check successful ?: {}. First time migration ? : {}'.format(check_success, start_migrate)


def undo_migrate_tif_file(apps, schema_editor):
    log = logging.getLogger()
    meta_reverse_fail = []

    # loop through each raster resource and change the no data value, min, max values of each band
    for res in RasterResource.objects.all():
        for band_obj in res.metadata.bandInformation:
            try:
                res.metadata.update_element('bandInformation',
                                            band_obj.id,
                                            maximumValue=None,
                                            minimumValue=None,
                                            noDataValue=None,
                                            )
            except Exception as e:
                log.exception(e.message)
                meta_reverse_fail.append('{}:{}, band:{}'.format(res.short_id, res.metadata.title.value, band_obj.id))

    print 'Meta recover to initial state fail: List {}'.format(meta_reverse_fail)


class Migration(migrations.Migration):

    dependencies = [
        ('hs_geo_raster_resource', '0005_auto_20160509_2116'),
    ]

    operations = [
        migrations.RunPython(code=migrate_tif_file, reverse_code=undo_migrate_tif_file),
    ]
