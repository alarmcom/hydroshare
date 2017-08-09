from django.conf.urls import patterns, url
from hs_core import views
from hs_file_types import views as file_type_views

from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='Hydroshare API')

urlpatterns = patterns(
    '',

    # Swagger Docs View
    url(r'^$', schema_view),

    # resource API
    url(r'^resource/types/$', views.resource_rest_api.ResourceTypes.as_view(),
        name='list_resource_types'),

    # DEPRECATED: use from above instead
    url(r'^resourceTypes/$', views.resource_rest_api.ResourceTypes.as_view(),
        name='DEPRECATED_list_resource_types'),

    # DEPRECATED: use GET /resource/ instead
    url(r'^resourceList/$', views.resource_rest_api.ResourceList.as_view(),
        name='DEPRECATED_list_resources'),

    url(r'^resource/$', views.resource_rest_api.ResourceListCreate.as_view(),
        name='list_create_resource'),

    # Public endpoint for resource flags
    url(r'^resource/(?P<pk>[0-9a-f-]+)/flag/$', views.set_resource_flag_public,
        name='public_set_resource_flag'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/$',
        views.resource_rest_api.ResourceReadUpdateDelete.as_view(),
        name='get_update_delete_resource'),

    # Create new version of a resource
    url(r'^resource/(?P<pk>[0-9a-f-]+)/version/$', views.create_new_version_resource_public,
        name='new_version_resource_public'),

    # public copy resource endpoint
    url(r'^resource/(?P<pk>[0-9a-f-]+)/copy/$',
        views.copy_resource_public, name='copy_resource_public'),

    # DEPRECATED: use form above instead
    url(r'^resource/accessRules/(?P<pk>[0-9a-f-]+)/$',
        views.resource_rest_api.AccessRulesUpdate.as_view(),
        name='DEPRECATED_update_access_rules'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/sysmeta/$',
        views.resource_rest_api.SystemMetadataRetrieve.as_view(),
        name='get_system_metadata'),

    # DEPRECATED: use from above instead
    url(r'^sysmeta/(?P<pk>[0-9a-f-]+)/$',
        views.resource_rest_api.SystemMetadataRetrieve.as_view(),
        name='DEPRECATED_get_system_metadata'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/$',
        views.resource_rest_api.ScienceMetadataRetrieveUpdate.as_view(),
        name='get_update_science_metadata'),

    # Resource metadata editing
    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/elements/$',
        views.resource_metadata_rest_api.MetadataElementsRetrieveUpdate.as_view(),
        name='get_update_science_metadata_elements'),

    # Update key-value metadata
    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/custom/$',
        views.update_key_value_metadata_public,
        name='update_custom_metadata'),

    # DEPRECATED: use from above instead
    url(r'^scimeta/(?P<pk>[0-9a-f-]+)/$',
        views.resource_rest_api.ScienceMetadataRetrieveUpdate.as_view(),
        name='DEPRECATED_get_update_science_metadata'),

    url(r'^resource/(?P<pk>[A-z0-9]+)/map/$',
        views.resource_rest_api.ResourceMapRetrieve.as_view(),
        name='get_resource_map'),

    # Patterns are now checked in the view class.
    url(r'^resource/(?P<pk>[0-9a-f-]+)/files/(?P<pathname>.+)/$',
        views.resource_rest_api.ResourceFileCRUD.as_view(),
        name='get_update_delete_resource_file'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/files/$',
        views.resource_rest_api.ResourceFileListCreate.as_view(),
        name='list_create_resource_file'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/folders/(?P<pathname>.*)/$',
        views.resource_folder_rest_api.ResourceFolders.as_view(),
        name='list_manipulate_folders'),

    # public unzip endpoint
    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/unzip/(?P<pathname>.*)/$',
        views.resource_folder_hierarchy.data_store_folder_unzip_public),

    # public zip folder endpoint
    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/zip/$',
        views.resource_folder_hierarchy.data_store_folder_zip_public),

    # public move or rename
    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/move-or-rename/$',
        views.resource_folder_hierarchy.data_store_file_or_folder_move_or_rename_public),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/set-file-type/(?P<file_path>.*)/'
        r'(?P<hs_file_type>[A-z]+)/$',
        file_type_views.set_file_type_public,
        name="set_file_type_public"),

    # DEPRECATED: use form above instead. Added unused POST for simplicity
    url(r'^resource/(?P<pk>[0-9a-f-]+)/file_list/$',
        views.resource_rest_api.ResourceFileListCreate.as_view(),
        name='DEPRECATED_get_resource_file_list'),

    url(r'^taskstatus/(?P<task_id>[A-z0-9\-]+)/$',
        views.resource_rest_api.CheckTaskStatus.as_view(),
        name='get_task_status'),

    url(r'^user/$',
        views.user_rest_api.UserInfo.as_view(), name='get_logged_in_user_info'),

    url(r'^userInfo/$',
        views.user_rest_api.UserInfo.as_view(), name='get_logged_in_user_info'),

    # Resource Access
    url(r'^resource/(?P<pk>[0-9a-f-]+)/access/$',
        views.resource_access_api.ResourceAccessUpdateDelete.as_view(),
        name='get_update_delete_resource_access'),
)