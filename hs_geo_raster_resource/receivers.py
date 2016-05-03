__author__ = 'Hong Yi'
## Note: this module has been imported in the models.py in order to receive signals
## at the end of the models.py for the import of this module
import tempfile
import os
import subprocess
import shutil
import zipfile
from collections import OrderedDict
import xml.etree.ElementTree as ET

import gdal
from gdalconst import GA_ReadOnly

from django.core.files.uploadedfile import UploadedFile
from django.dispatch import receiver

from hs_core.hydroshare import utils
from hs_core.hydroshare.resource import ResourceFile
from hs_core.signals import pre_create_resource, pre_add_files_to_resource, pre_delete_file_from_resource, \
    pre_metadata_element_create, pre_metadata_element_update
from forms import CellInfoValidationForm, BandInfoValidationForm, OriginalCoverageSpatialForm
from models import RasterResource
import raster_meta_extract

# signal handler to extract metadata from uploaded geotiff file and return template contexts
# to populate create-resource.html template page


def raster_file_validation(files):
    error_info = []
    vrt_file_path = ''

    # process uploaded .tif or .zip file
    if len(files) == 1:
        ext = os.path.splitext(files[0].name)[1]
        if ext == '.tif':
            temp_vrt_file_path, temp_dir = create_vrt_file(files[0])
            if os.path.isfile(temp_vrt_file_path):
                files.append(UploadedFile(file=open(temp_vrt_file_path, 'r'), name=os.path.basename(temp_vrt_file_path)))

        elif ext == '.zip':
            extract_file_paths, temp_dir = explode_zip_file(files[0])
            if extract_file_paths:
                del files[0]
                for file_path in extract_file_paths:
                    files.append(UploadedFile(file=open(file_path, 'r'), name=os.path.basename(file_path)))

    # check if raster is valid in format and data
    files_names = [f.name for f in files]
    files_ext = [os.path.splitext(path)[1] for path in files_names]
    files_path = [f.file.name for f in files]

    if set(files_ext) == {'.vrt', '.tif'} and files_ext.count('.vrt') == 1:
        vrt_file_path = files_path[files_ext.index('.vrt')]
        raster_dataset = gdal.Open(vrt_file_path, GA_ReadOnly)

        # check if the vrt file is valid
        try:
            raster_dataset.RasterXSize
            raster_dataset.RasterYSize
            raster_dataset.RasterCount
        except AttributeError:
            error_info.append('Please define the raster with raster size and band information.')

        # check if the raster file numbers and names are valid in vrt file
        with open(vrt_file_path, 'r') as vrt_file:
            vrt_string = vrt_file.read()
            root = ET.fromstring(vrt_string)
            raster_file_names = {file_name.text for file_name in root.iter('SourceFilename')}
        files_names.pop(files_ext.index('.vrt'))
        if raster_file_names != set(files_names):
            error_info.append('The .tif files provided are inconsistent (e.g. missing or extra)'\
                             ' with the references in the .vrt file.')
    elif files_ext.count('.tif') == 1 and files_ext.count('.vrt') == 0:
        error_info.append('Please define the .tif file with raster size, band, and georeference information.')
    else:
        error_info.append('The uploaded files should contain only one .vrt file and .tif files referenced by the .vrt file.')

    return error_info, vrt_file_path, temp_dir


def create_vrt_file(tif_file):
    # create vrt file
    temp_dir = tempfile.mkdtemp()
    tif_base_name = os.path.basename(tif_file.name)
    vrt_file_path = os.path.join(temp_dir, os.path.splitext(tif_base_name)[0]+'.vrt')

    with open(os.devnull, 'w') as fp:
        subprocess.Popen(['gdalbuildvrt', vrt_file_path, tif_file.file.name], stdout=fp, stderr=fp).wait()   # remember to add .wait()

    # modify vrt file SourceFileName
    try:
        tree = ET.parse(vrt_file_path)
        root = tree.getroot()
        for element in root.iter('SourceFilename'):
            element.text = tif_base_name
        tree.write(vrt_file_path)
    except Exception:
        shutil.rmtree(temp_dir)

    return vrt_file_path, temp_dir


def explode_zip_file(zip_file):
    temp_dir = tempfile.mkdtemp()
    try:
        zf = zipfile.ZipFile(zip_file.file.name, 'r')
        zf.extractall(temp_dir)
        zf.close()
        # get all the file abs names in temp_dir
        raw_file_paths = []
        for dirpath,_,filenames in os.walk(temp_dir):
            for name in filenames:
                raw_file_paths.append(os.path.abspath(os.path.join(dirpath, name)))
        # get all the valid files with .tif and .vrt extension
        extract_file_paths = [os.path.join(temp_dir, file_name) for file_name in raw_file_paths if os.path.splitext(file_name)[1] in ['.vrt', '.tif']]

    except Exception:
        extract_file_paths = []
        shutil.rmtree(temp_dir)

    return extract_file_paths, temp_dir


@receiver(pre_create_resource, sender=RasterResource)
def raster_pre_create_resource_trigger(sender, **kwargs):
    files = kwargs['files']
    title = kwargs['title']
    validate_files_dict = kwargs['validate_files']
    metadata = kwargs['metadata']

    if files:
        # raster file validation
        error_info, vrt_file_path, temp_dir = raster_file_validation(files)

        # metadata extraction
        if not error_info:
            res_md_dict = raster_meta_extract.get_raster_meta_dict(vrt_file_path)
            wgs_cov_info = res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
            # add core metadata coverage - box
            if wgs_cov_info:
                box = {'coverage': {'type': 'box', 'value': wgs_cov_info}}
                metadata.append(box)

            # Save extended meta to metadata variable
            ori_cov = {'OriginalCoverage': {'value': res_md_dict['spatial_coverage_info']['original_coverage_info'] }}
            metadata.append(ori_cov)

            # Save extended meta to metadata variable
            cellInfo = OrderedDict([
                ('name', os.path.basename(vrt_file_path)),
                ('rows', res_md_dict['cell_and_band_info']['rows']),
                ('columns', res_md_dict['cell_and_band_info']['columns']),
                ('cellSizeXValue', res_md_dict['cell_and_band_info']['cellSizeXValue']),
                ('cellSizeYValue', res_md_dict['cell_and_band_info']['cellSizeYValue']),
                ('cellDataType', res_md_dict['cell_and_band_info']['cellDataType']),
                ('noDataValue', res_md_dict['cell_and_band_info']['noDataValue'])
                ])
            metadata.append({'CellInformation': cellInfo})
            bcount = res_md_dict['cell_and_band_info']['bandCount']
        else:
            bcount = 0
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Raster validation error. {0}'.format(' '.join(error_info))

        # remove temp vrt file
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)

    else:
        # initialize required raster metadata to be place holders to be edited later by users
        cell_info = OrderedDict([
            ('name', title),
            ('rows', 0),
            ('columns', 0),
            ('cellSizeXValue', 0),
            ('cellSizeYValue', 0),
            ('cellDataType', "NA"),
            ('noDataValue', 0)
        ])
        metadata.append({'CellInformation': cell_info})
        bcount = 1
        spatial_coverage_info = OrderedDict([
             ('units', "NA"),
             ('projection', 'NA'),
             ('northlimit', 'NA'),
             ('southlimit', 'NA'),
             ('eastlimit', 'NA'),
             ('westlimit', 'NA')
        ])

        # Save extended meta to metadata variable
        ori_cov = {'OriginalCoverage': {'value': spatial_coverage_info }}
        metadata.append(ori_cov)

    for i in range(bcount):
        band_dict = OrderedDict()
        band_dict['name'] = 'Band_' + str(i+1)
        band_dict['variableName'] = 'Unknown'
        band_dict['variableUnit'] = 'Unknown'
        band_dict['method'] = ''
        band_dict['comment'] = ''
        metadata.append({'BandInformation': band_dict})


@receiver(pre_add_files_to_resource, sender=RasterResource)
def raster_pre_add_files_to_resource_trigger(sender, **kwargs):
    files = kwargs['files']
    res = kwargs['resource']
    validate_files_dict = kwargs['validate_files']

    if files:
        # raster file validation
        error_info, vrt_file_path, temp_dir = raster_file_validation(files)

        # metadata extraction
        if not error_info:
            res_md_dict = raster_meta_extract.get_raster_meta_dict(vrt_file_path)

            # update core metadata coverage - box
            wgs_cov_info = res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
            if wgs_cov_info:
                res.metadata.create_element('Coverage', type='box', value=res_md_dict['spatial_coverage_info']['wgs84_coverage_info'])

            # update extended original box coverage
            if res.metadata.originalCoverage:
                res.metadata.originalCoverage.delete()
            v = {'value': res_md_dict['spatial_coverage_info']['original_coverage_info'] }
            res.metadata.create_element('OriginalCoverage', **v)

            # update extended metadata CellInformation
            res.metadata.cellInformation.delete()
            res.metadata.create_element('CellInformation', name=os.path.basename(vrt_file_path), rows=res_md_dict['cell_and_band_info']['rows'],
                                        columns = res_md_dict['cell_and_band_info']['columns'],
                                        cellSizeXValue = res_md_dict['cell_and_band_info']['cellSizeXValue'],
                                        cellSizeYValue = res_md_dict['cell_and_band_info']['cellSizeYValue'],
                                        cellDataType = res_md_dict['cell_and_band_info']['cellDataType'],
                                        noDataValue = res_md_dict['cell_and_band_info']['noDataValue'])

            bcount = res_md_dict['cell_and_band_info']['bandCount']
            # update extended metadata BandInformation
            for band in res.metadata.bandInformation:
                band.delete()
            for i in range(bcount):
                res.metadata.create_element('BandInformation', name='Band_' + str(i+1), variableName='Unnamed', variableUnit='Unnamed', method='', comment='')

        else:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Raster validation error. {0}' \
                                             'See http://www.gdal.org/gdal_vrttut.html ' \
                                             'for information on the .vrt format.'.format(' '.join(error_info))

        # remove temp dir
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)


@receiver(pre_delete_file_from_resource, sender=RasterResource)
def raster_pre_delete_file_from_resource_trigger(sender, **kwargs):
    res = kwargs['resource']
    del_file = kwargs['file']

    # delete core metadata coverage now that the only file is deleted
    res.metadata.coverages.all().delete()

    # delete extended OriginalCoverage now that the only file is deleted
    res.metadata.originalCoverage.delete()

    # reset extended metadata CellInformation now that the only file is deleted
    res.metadata.cellInformation.delete()
    res.metadata.create_element('CellInformation', name=res.metadata.title.value, rows=0, columns=0,
                                cellSizeXValue=0, cellSizeYValue=0,
                                cellDataType="NA",
                                noDataValue=0)

    # reset extended metadata BandInformation now that the only file is deleted
    for band in res.metadata.bandInformation:
        band.delete()
    res.metadata.create_element('BandInformation', name='Band_1', variableName='Unnamed', variableUnit='Unnamed',
                                method='', comment='')

    # delete all the files that is not the user selected file
    for f in ResourceFile.objects.filter(object_id=res.id):
        if f.resource_file.name != del_file.resource_file.name:
            f.resource_file.delete()
            f.delete()

    # delete the format of the files that is not the user selected delete file
    del_file_format = utils.get_file_mime_type(del_file.resource_file.name)
    for format_element in res.metadata.formats.all():
        if format_element.value != del_file_format:
            res.metadata.delete_element(format_element.term, format_element.id)

@receiver(pre_metadata_element_create, sender=RasterResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    if element_name == "cellinformation":
        element_form = CellInfoValidationForm(request.POST)
    elif element_name == 'bandinformation':
        element_form = BandInfoValidationForm(request.POST)
    elif element_name == 'originalcoverage':
        element_form = OriginalCoverageSpatialForm(data=request.POST)
    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}


@receiver(pre_metadata_element_update, sender=RasterResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    element_id = kwargs['element_id']
    request = kwargs['request']
    if element_name == "cellinformation":
        element_form = CellInfoValidationForm(request.POST)
    elif element_name == 'bandinformation':
        form_data = {}
        for field_name in BandInfoValidationForm().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]
        element_form = BandInfoValidationForm(form_data)
    elif element_name == 'originalcoverage':
        element_form = OriginalCoverageSpatialForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}
"""
Since each of the Raster metadata element is required no need to listen to any delete signal
The Raster landing page should not have delete UI functionality for the resource specific metadata elements
"""
