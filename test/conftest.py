import json

import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from hs_core import hydroshare
from hs_core.hydroshare import users


@pytest.mark.django_db
@pytest.fixture(scope="function")
def resource_with_metadata():
    """
    The followings are the core metadata elements that can be passed as part of the
    'metadata' parameter when creating a resource:

    coverage
    creator
    contributor
    source,
    relation,
    identifier,
    fundingagency

    The statements after the yield statement will execute when the last test in the module has finished execution,
    regardless of the exception status of the tests. https://docs.pytest.org/en/latest/fixture.html

    """
    client = APIClient()
    group, _ = Group.objects.get_or_create(name='Hydroshare Author')
    user = users.create_account(
        'test_user@email.com',
        username='testuser',
        password='foobar',
        first_name='some_first_name',
        last_name='some_last_name',
        superuser=False)
    client.force_authenticate(user=user)
    client.login(username='testuser', password='foobar')

    rtype = 'GenericResource'
    title = 'Resource d49aebb3-4e64-4732-8ff2-5c43617effee'
    metadata = []
    metadata.append({'coverage': {'type': 'period', 'value': {'start': '01/01/2000',
                                                              'end': '12/12/2010'}}})
    statement = 'This resource is shared under the Creative Commons Attribution CC BY.'
    url = 'http://creativecommons.org/licenses/by/4.0/'
    metadata.append({'rights': {'statement': statement, 'url': url}})
    metadata.append({'language': {'code': 'fre'}})

    # contributor
    con_name = 'Mike Sundar'
    con_org = "USU"
    con_email = 'mike.sundar@usu.edu'
    con_address = "11 River Drive, Logan UT-84321, USA"
    con_phone = '435-567-0989'
    con_homepage = 'http://usu.edu/homepage/001'
    con_identifiers = {'ORCID': 'https://orcid.org/mike_s',
                       'ResearchGateID': 'https://www.researchgate.net/mike_s'}
    metadata.append({'contributor': {'name': con_name,
                                     'organization': con_org, 'email': con_email,
                                     'address': con_address, 'phone': con_phone,
                                     'homepage': con_homepage,
                                     'identifiers': con_identifiers}})

    # creator
    cr_name = 'John Smith'
    cr_org = "USU"
    cr_email = 'jsmith@gmail.com'
    cr_address = "101 Clarson Ave, Provo UT-84321, USA"
    cr_phone = '801-567=9090'
    cr_homepage = 'http://byu.edu/homepage/002'
    cr_identifiers = {'ORCID': 'https://orcid.org/john_smith',
                      'ResearchGateID': 'https://www.researchgate.net/john_smith'}
    metadata.append({'creator': {'name': cr_name, 'organization': cr_org,
                                 'email': cr_email, 'address': cr_address,
                                 'phone': cr_phone, 'homepage': cr_homepage,
                                 'identifiers': cr_identifiers}})

    # relation
    metadata.append({'relation': {'type': 'isPartOf',
                                  'value': 'http://hydroshare.org/resource/001'}})
    # source
    metadata.append({'source': {'derived_from': 'http://hydroshare.org/resource/0001'}})

    # identifier
    metadata.append({'identifier': {'name': 'someIdentifier', 'url': 'http://some.org/001'}})

    # fundingagency
    agency_name = 'NSF'
    award_title = "Cyber Infrastructure"
    award_number = "NSF-101-20-6789"
    agency_url = "http://www.nsf.gov"
    metadata.append({'fundingagency': {'agency_name': agency_name, 'award_title': award_title,
                                       'award_number': award_number, 'agency_url': agency_url}})

    params = {'resource_type': rtype,
              'title': title,
              'metadata': json.dumps(metadata),
              'file': ('cea.tif',
                       open('assets/cea.tif'),
                       'image/tiff')}
    rest_url = '/hsapi/resource/'
    response = client.post(rest_url, params)
    content = json.loads(response.content)
    res_id = content['resource_id']
    yield res_id
    hydroshare.delete_resource(res_id)  # can resource = get_resource_by_shortkey(res_id) be used instead?
