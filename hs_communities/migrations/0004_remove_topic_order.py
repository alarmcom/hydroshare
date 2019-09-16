# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-09-04 13:16


from django.db import migrations

from hs_communities.models import Topic


def populate_topics(apps, schema_editor):
    topics = ["Air Temperature", "Barometric Pressure", "Chlorophyll", "Climate", "Diatoms",
              "Digital Elevation Model (DEM)",
              "Dissolved Organic Matter (DOM)", "Ecosystem model", "Electrical Conductivity",
              "Flux Tower", "Geology",
              "Geomorphology", "Geophysics", "GIS / Map Data",
              "Ground Penetrating Radar (GPR)", "Groundwater Chemistry",
              "Groundwater Depth", "Groundwater Temperatures", "Hydropedologic Properties",
              "Land Cover", "Land Use History",
              "LiDAR", "Lysimeter Water Samples Chemistry", "Matric Potential",
              "Meteorology", "Nutrient Fluxes",
              "Overland Water Chemistry", "Ozone", "Photographic Imagery", "Piezometer",
              "Precipitation",
              "Precipitation Chemistry", "Rainfall Chemistry", "Regolith Survey",
              "Reservoir Height", "Rock Moisture",
              "Sap Flow", "Sediment Transport", "Seismic Refraction", "Snow Depth",
              "Snow Pits", "Snow Survey",
              "Soil Biogeochemistry", "Soil Electrical Resistivity",
              "Soil Evapotranspiration", "Soil Gas",
              "Soil Geochemistry", "Soil Invertebrates", "Soil Microbes",
              "Soil Mineralogy", "Soil Moisture",
              "Soil Porewater Chemistry", "Soil Porosity", "Soil Redox Potential",
              "Soil Respiration",
              "Soil Survey",
              "Soil Temperature", "Soil Texture", "Soil Water", "Soil Water Chemistry",
              "Solar Radiation", "Stable Isotopes",
              "Stage", "Stream Ecology", "Stream Suspended Sediment",
              "Stream Water Chemistry", "Stream Water Temperatures",
              "Streamflow / Discharge", "Surface Water Chemistry",
              "Throughfall Chemistry", "Topographic Carbon Storage",
              "Tree Growth & Physiology", "Vegetation", "Water Potential",
              "Well Water Levels"]

    for t in topics:
        n = Topic()
        n.name = t
        n.save()


class Migration(migrations.Migration):

    dependencies = [
        ('hs_communities', '0003_auto_20190903_1548'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topic',
            name='order',
        ),
        migrations.RunPython(populate_topics),
    ]
