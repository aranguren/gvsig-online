# -*- coding: utf-8 -*-

'''
    gvSIG Online.
    Copyright (C) 2007-2015 gvSIG Association.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
'''
@author: Javier Rodrigo <jrodrigo@scolab.es>
'''

from django.shortcuts import render_to_response, RequestContext, HttpResponse, redirect
from models import Project, ProjectUserGroup, ProjectLayerGroup
from gvsigol_services.models import LayerGroup
from gvsigol_auth.models import UserGroup, UserGroupUser
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from gvsigol_auth.utils import is_admin_user
from gvsigol_services.backend_geocoding import geocoder
from gvsigol import settings
import utils as core_utils
import urllib
import json

def not_found_view(request):
    response = render_to_response('404.html', {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response

@login_required(login_url='/gvsigonline/auth/login_user/')
def home(request):
    user = User.objects.get(username=request.user.username)
    groups_by_user = UserGroupUser.objects.filter(user_id=user.id)
    
    projects_by_user = []
    for usergroup_user in groups_by_user:
        user_group = UserGroup.objects.get(id=usergroup_user.user_group_id)
        projects_by_group = ProjectUserGroup.objects.filter(user_group_id=user_group.id)
        for project_group in projects_by_group:
            exists = False
            for aux in projects_by_user:
                if aux.project_id == project_group.project_id:
                    exists = True
            if not exists:
                projects_by_user.append(project_group)
    
    projects = []
    if len (projects_by_user) > 0:
        for ua in projects_by_user:
            a = Project.objects.get(id=ua.project_id)
            image = ''
            if "no_project.png" in a.image.url:
                image = a.image.url.replace(settings.MEDIA_URL, '')
            else:
                image = a.image.url
                
            project = {}
            project['id'] = a.id
            project['name'] = a.name
            project['description'] = a.description
            project['image'] = urllib.unquote(image)
            projects.append(project)
   
    return render_to_response('home.html', {'projects': projects}, RequestContext(request))

@login_required(login_url='/gvsigonline/auth/login_user/')
@is_admin_user
def project_list(request):
    
    project_list = Project.objects.all()
    
    projects = []
    for p in project_list:
        project = {}
        project['id'] = p.id
        project['name'] = p.name
        project['description'] = p.description
        projects.append(project)
                      
    response = {
        'projects': projects
    }     
    return render_to_response('project_list.html', response, context_instance=RequestContext(request))

@login_required(login_url='/gvsigonline/auth/login_user/')
@is_admin_user
def project_add(request):
    if request.method == 'POST':
        name = request.POST.get('project-name')
        description = request.POST.get('project-description')
        latitude = request.POST.get('center-lat')
        longitude = request.POST.get('center-lon')
        extent = request.POST.get('extent')
        zoom = request.POST.get('zoom')
            
        has_image = False
        if 'project-image' in request.FILES:
            has_image = True
                
        assigned_layergroups = []
        for key in request.POST:
            if 'layergroup-' in key:
                assigned_layergroups.append(int(key.split('-')[1]))
                
        assigned_usergroups = []
        for key in request.POST:
            if 'group-' in key:
                assigned_usergroups.append(int(key.split('-')[1]))
                
        exists = False
        projects = Project.objects.all()
        for p in projects:
            if name == p.name:
                exists = True
                
        layergroups = LayerGroup.objects.exclude(name='__default__')
        groups = core_utils.get_all_groups()
        if name == '':
            message = _(u'You must enter an project name')
            return render_to_response('project_add.html', {'message': message, 'layergroups': layergroups, 'groups': groups}, context_instance=RequestContext(request))
                
        if not exists:
            project = None
            if has_image:
                project = Project(
                    name = name,
                    description = description,
                    image = request.FILES['project-image'],
                    center_lat = latitude,
                    center_lon = longitude,
                    zoom = int(zoom),
                    extent = extent
                )
            else:
                project = Project(
                    name = name,
                    description = description,
                    center_lat = latitude,
                    center_lon = longitude,
                    zoom = int(zoom),
                    extent = extent
                )
            project.save()
            
            for alg in assigned_layergroups:
                layergroup = LayerGroup.objects.get(id=alg)
                project_layergroup = ProjectLayerGroup(
                    project = project,
                    layer_group = layergroup
                )
                project_layergroup.save()
                
            for aug in assigned_usergroups:
                usergroup = UserGroup.objects.get(id=aug)
                project_usergroup = ProjectUserGroup(
                    project = project,
                    user_group = usergroup
                )
                project_usergroup.save()
                
            admin_group = UserGroup.objects.get(name__exact='admin')
            project_usergroup = ProjectUserGroup(
                project = project,
                user_group = admin_group
            )
            project_usergroup.save()
            
        else:
            message = _(u'Project name already exists')
            return render_to_response('project_add.html', {'message': message, 'layergroups': layergroups, 'groups': groups}, context_instance=RequestContext(request))
        
        return redirect('project_list')
    
    else:
        layergroups = LayerGroup.objects.exclude(name='__default__')
        groups = core_utils.get_all_groups()
        return render_to_response('project_add.html', {'layergroups': layergroups, 'groups': groups}, context_instance=RequestContext(request))
    
    
@login_required(login_url='/gvsigonline/auth/login_user/')
@is_admin_user
def project_update(request, pid):
    if request.method == 'POST':
        name = request.POST.get('project-name')
        description = request.POST.get('project-description')
        latitude = request.POST.get('center-lat')
        longitude = request.POST.get('center-lon')
        extent = request.POST.get('extent')
        zoom = request.POST.get('zoom')
                
        assigned_layergroups = []
        for key in request.POST:
            if 'layergroup-' in key:
                assigned_layergroups.append(int(key.split('-')[1]))
                
        assigned_usergroups = []
        for key in request.POST:
            if 'group-' in key:
                assigned_usergroups.append(int(key.split('-')[1]))
                
        project = Project.objects.get(id=int(pid))
               
        exists = False
        projects = Project.objects.all()
        for p in projects:
            if name == p.name:
                exists = True
                
        sameName = False
        if project.name == name:
            sameName = True
            
            
        if sameName:
            project.description = description
            project.center_lat = latitude
            project.center_lon = longitude
            project.zoom = int(zoom)
            project.extent = extent
            project.save()
            
            for lg in ProjectLayerGroup.objects.filter(project_id=project.id):
                lg.delete()
                    
            for ug in ProjectUserGroup.objects.filter(project_id=project.id):
                ug.delete()
                
            for alg in assigned_layergroups:
                layergroup = LayerGroup.objects.get(id=alg)
                project_layergroup = ProjectLayerGroup(
                    project = project,
                    layer_group = layergroup
                )
                project_layergroup.save()
                    
            for aug in assigned_usergroups:
                usergroup = UserGroup.objects.get(id=aug)
                project_usergroup = ProjectUserGroup(
                    project = project,
                    user_group = usergroup
                )
                project_usergroup.save()
                
            admin_group = UserGroup.objects.get(name__exact='admin')
            project_usergroup = ProjectUserGroup(
                project = project,
                user_group = admin_group
            )
            project_usergroup.save()
                
            return redirect('project_list')
            
        else:
            if not exists:
                project.name = name
                project.description = description
                project.center_lat = latitude
                project.center_lon = longitude
                project.zoom = int(zoom)
                project.extent = extent
                project.save()
                
                for lg in ProjectLayerGroup.objects.filter(project_id=project.id):
                    lg.delete()
                    
                for ug in ProjectUserGroup.objects.filter(project_id=project.id):
                    ug.delete()
                
                for alg in assigned_layergroups:
                    layergroup = LayerGroup.objects.get(id=alg)
                    project_layergroup = ProjectLayerGroup(
                        project = project,
                        layer_group = layergroup
                    )
                    project_layergroup.save()
                    
                for aug in assigned_usergroups:
                    usergroup = UserGroup.objects.get(id=aug)
                    project_usergroup = ProjectUserGroup(
                        project = project,
                        user_group = usergroup
                    )
                    project_usergroup.save()
                    
                admin_group = UserGroup.objects.get(name__exact='admin')
                project_usergroup = ProjectUserGroup(
                    project = project,
                    user_group = admin_group
                )
                project_usergroup.save()
                    
                return redirect('project_list')
                    
            else:
                message = _(u'Project name already exists')
                project = Project.objects.get(id=int(pid))    
                groups = core_utils.get_all_groups_checked_by_project(project)
                layer_groups = core_utils.get_all_layer_groups_checked_by_project(project)  
                return render_to_response('project_update.html', {'message': message, 'pid': pid, 'project': project, 'groups': groups, 'layergroups': layer_groups}, context_instance=RequestContext(request))
                
        
        
    else:
        project = Project.objects.get(id=int(pid))    
        groups = core_utils.get_all_groups_checked_by_project(project)
        layer_groups = core_utils.get_all_layer_groups_checked_by_project(project) 
        return render_to_response('project_update.html', {'pid': pid, 'project': project, 'groups': groups, 'layergroups': layer_groups}, context_instance=RequestContext(request))
    
    
@login_required(login_url='/gvsigonline/auth/login_user/')
@is_admin_user
def project_delete(request, pid):        
    if request.method == 'POST':
        project = Project.objects.get(id=int(pid))
        project.delete()
            
        response = {
            'deleted': True
        }     
        return HttpResponse(json.dumps(response, indent=4), content_type='project/json')
    
@login_required(login_url='/gvsigonline/auth/login_user/')
@is_admin_user
def project_load(request, pid):
    return render_to_response('viewer.html', {'pid': pid}, context_instance=RequestContext(request))

@login_required(login_url='/gvsigonline/auth/login_user/')
@is_admin_user
def project_get_conf(request):
    if request.method == 'POST':
        '''
        pid = request.POST.get('pid')
        
        project = Project.objects.get(id=int(pid))
        map = Map.objects.get(id=project.map_id)
            
        project_layers_groups = ProjectLayerGroup.objects.filter(project_id=project.id)
        layer_groups = []
        workspaces = []
        capabilities = mapservice_backend.getCapabilities(request.session)
        for project_group in project_layers_groups:            
            group = LayerGroup.objects.get(id=project_group.layer_group_id)
            
            conf_group = {}
            conf_group['groupTitle'] = group.description
            conf_group['groupId'] = ''.join(random.choice(string.ascii_uppercase) for i in range(6))
            conf_group['groupOrder'] = group.order
            conf_group['groupName'] = group.name
            conf_group['cached'] = group.cached
            layers_in_group = Layer.objects.filter(layer_group_id=group.id).order_by('order')
            layers = []
            for l in layers_in_group:
                read_roles = core_utils.get_read_roles(l)
                write_roles = core_utils.get_write_roles(l)
                
                layer = {}                
                layer['name'] = l.name
                layer['title'] = l.title
                layer['visible'] = l.visible 
                layer['queryable'] = l.queryable 
                layer['cached'] = l.cached
                layer['single_image'] = l.single_image
                layer['read_roles'] = read_roles
                layer['write_roles'] = write_roles
                
                datastore = Datastore.objects.get(id=l.datastore_id)
                workspace = Workspace.objects.get(id=datastore.workspace_id)
                
                if datastore.type == 'v_SHP' or datastore.type == 'v_PostGIS': 
                    layer['is_vector'] = True
                else:
                    layer['is_vector'] = False
                
                properties = capabilities.contents[workspace.name + ':' + l.name]
                defaultCrs = properties.boundingBox[4]
                epsg = gvsigonline.settings.SUPPORTED_CRS[defaultCrs.split(':')[1]]
                layer['crs'] = {
                    'crs': defaultCrs,
                    'units': epsg['units']
                }
                
                if properties.timepositions is not None:
                    layer['is_time_layer'] = True
                    layer['time_params'] = {
                        'default': properties.timepositions[0],
                        'values': ','.join(properties.timepositions)
                    }
                
                else:
                    layer['is_time_layer'] = False
                    
                split_wms_url = workspace.wms_endpoint.split('//')
                authenticated_wms_url = split_wms_url[0] + '//' + request.session['username'] + ':' + request.session['password'] + '@' + split_wms_url[1]
                layer['wms_url'] = authenticated_wms_url
                    
                split_wfs_url = workspace.wfs_endpoint.split('//')
                authenticated_wfs_url = split_wfs_url[0] + '//' + request.session['username'] + ':' + request.session['password'] + '@' + split_wfs_url[1]
                layer['wfs_url'] = authenticated_wfs_url
                layer['namespace'] = workspace.uri
                layer['workspace'] = workspace.name                
                #layer['wfs_url'] = workspace.wfs_endpoint
                
                if l.cached:  
                    split_cache_url = workspace.cache_endpoint.split('//')
                    authenticated_cache_url = split_cache_url[0] + '//' + request.session['username'] + ':' + request.session['password'] + '@' + split_cache_url[1]
                    layer['cache_url'] = authenticated_cache_url
                else:
                    layer['cache_url'] = authenticated_wms_url
                    
                layer['legend'] = authenticated_wms_url + '?SERVICE=WMS&VERSION=1.1.1&layer=' + l.name + '&REQUEST=getlegendgraphic&FORMAT=image/png'
                if 'http' in gvsigonline.settings.GVSIGONLINE_CATALOG['URL']:
                    if l.metadata_uuid is not None and l.metadata_uuid != '':
                        split_catalog_url = gvsigonline.settings.GVSIGONLINE_CATALOG['URL'].split('//')
                        authenticated_catalog_url = split_catalog_url[0] + '//' + request.session['username'] + ':' + request.session['password'] + '@' + split_catalog_url[1]  + 'catalog.search#/metadata/' + l.metadata_uuid
                        layer['metadata'] = authenticated_catalog_url
                        
                    else:
                        layer['metadata'] = ''
                    
                else:
                    layer['metadata'] = ''
                                                
                layers.append(layer)
                
                w = {}
                w['name'] = workspace.name
                w['wms_url'] = workspace.wms_endpoint
                workspaces.append(w)
            
            if len(layers) > 0:   
                conf_group['layers'] = layers
                layer_groups.append(conf_group)
            
        ordered_layer_groups = sorted(layer_groups, key=itemgetter('groupOrder'))
        
        geoserver_url = gvsigonline.settings.GVSIGONLINE_SERVICES['URL']
        split_geoserver_url = geoserver_url.split('//')
        authenticated_geoserver_url = split_geoserver_url[0] + '//' + request.session['username'] + ':' + request.session['password'] + '@' + split_geoserver_url[1]
            
        conf = {
            'pid': pid,
            'user': {
                'id': request.user.id,
                'username': request.user.first_name + ' ' + request.user.last_name,
                'login': request.user.username,
                'email': request.user.email,
                'permissions': {
                    'is_admin': core_utils.check_admin_user(request.user),
                    'roles': core_utils.get_groups_by_user(request.user)
                }
            },
            'map': {
                'center_lat': map.center_lat,
                'center_lon': map.center_lon,
                'zoom': map.zoom
            },
            'supported_crs': gvsigonline.settings.SUPPORTED_CRS,
            'workspaces': workspaces,
            'layerGroups': ordered_layer_groups,
            'tools': gvsigonline.settings.GVSIGONLINE_TOOLS,
            'base_layers': gvsigonline.settings.GVSIGONLINE_BASE_LAYERS,
            'is_public_project': False,
            'geoserver_base_url': authenticated_geoserver_url
        } 
        '''
        
        conf = {
            "pid": "2",
            "view": {
                "center_lon": "-3.7078857421875", 
                "zoom": 7, 
                "center_lat": "40.04443758460857"
            }, 
            "workspaces": [
                {
                    "name": "test", 
                    "wms_url": "https://test.scolab.eu/geoserver/test/wms"
                }, 
                {
                    "name": "test", 
                    "wms_url": "https://test.scolab.eu/geoserver/test/wms"
                }, 
                {
                    "name": "test", 
                    "wms_url": "https://test.scolab.eu/geoserver/test/wms"
                }
            ], 
            "base_layers": {
                "bing": {
                    "active": False, 
                    "key": "Ak-dzM4wZjSqTlzveKz5u0d4IQ4bRzVI309GxmkgSVr1ewS6iPSrOvOKhA-CJlm3"
                }
            }, 
            "layerGroups": [
                {
                    "layers": [
                        {
                            "crs": {
                                "units": "degrees", 
                                "crs": "EPSG:4258"
                            }, 
                            "cache_url": "https://admin:admin52@test.scolab.eu/geoserver/test/wms", 
                            "read_roles": [], 
                            "name": "aeropuertos", 
                            "title": "Aeropuertos y aerodromos", 
                            "abstract": "Aeropuertos y aerodromos",
                            "cached": False, 
                            "wfs_url": "https://admin:admin52@localhost/gs-test/wfs", 
                            "namespace": "https://test.scolab.eu/geoserver/test", 
                            "wms_url": "https://admin:admin52@localhost/gs-test/wms", 
                            "legend": "https://admin:admin52@localhost/gs-test/wms?SERVICE=WMS&VERSION=1.1.1&layer=aeropuertos&REQUEST=getlegendgraphic&FORMAT=image/png", 
                            "visible": False, 
                            "is_time_layer": False, 
                            "workspace": "test", 
                            "single_image": False, 
                            "write_roles": [], 
                            "metadata": "http://admin:admin52@test.scolab.eu/geonetwork/srv/spa/catalog.search#/metadata/ae937e72-a2bd-4deb-bcf0-25e6afaeb5ea", 
                            "queryable": True, 
                            "is_vector": True
                        },{
                            "crs": {
                                "units": "degrees", 
                                "crs": "EPSG:4258"
                            }, 
                            "cache_url": "https://admin:admin52@test.scolab.eu/geoserver/test/wms", 
                            "read_roles": [], 
                            "name": "espacios_naturales", 
                            "title": "Espacios naturales", 
                            "abstract": "Espacios naturales",
                            "cached": False, 
                            "wfs_url": "https://admin:admin52@localhost/gs-test/wfs", 
                            "namespace": "https://test.scolab.eu/geoserver/test", 
                            "wms_url": "https://admin:admin52@localhost/gs-test/wms", 
                            "legend": "https://admin:admin52@localhost/gs-test/wms?SERVICE=WMS&VERSION=1.1.1&layer=espacios_naturales&REQUEST=getlegendgraphic&FORMAT=image/png", 
                            "visible": False, 
                            "is_time_layer": False, 
                            "workspace": "test", 
                            "single_image": False, 
                            "write_roles": [], 
                            "metadata": "http://admin:admin52@test.scolab.eu/geonetwork/srv/spa/catalog.search#/metadata/ae937e72-a2bd-4deb-bcf0-25e6afaeb5ea", 
                            "queryable": True, 
                            "is_vector": True
                        },{
                            "crs": {
                                "units": "degrees", 
                                "crs": "EPSG:4258"
                            }, 
                            "cache_url": "https://admin:admin52@test.scolab.eu/geoserver/test/wms", 
                            "read_roles": [], 
                            "name": "lugares_interes", 
                            "title": "Lugares de interes", 
                            "abstract": "Lugares de interes",
                            "cached": False, 
                            "wfs_url": "https://admin:admin52@localhost/gs-test/wfs", 
                            "namespace": "https://test.scolab.eu/geoserver/test", 
                            "wms_url": "https://admin:admin52@localhost/gs-test/wms", 
                            "legend": "https://admin:admin52@localhost/gs-test/wms?SERVICE=WMS&VERSION=1.1.1&layer=lugares_interes&REQUEST=getlegendgraphic&FORMAT=image/png", 
                            "visible": False, 
                            "is_time_layer": False, 
                            "workspace": "test", 
                            "single_image": False, 
                            "write_roles": [], 
                            "metadata": "http://admin:admin52@test.scolab.eu/geonetwork/srv/spa/catalog.search#/metadata/ae937e72-a2bd-4deb-bcf0-25e6afaeb5ea", 
                            "queryable": True, 
                            "is_vector": True
                        }
                    ], 
                    "cached": False, 
                    "groupOrder": 0, 
                    "groupName": "vectorial", 
                    "groupTitle": "vectorial", 
                    "groupId": "MTRKYE"
                }
            ], 
            "user": {
                "username": " ", 
                "login": "admin", 
                "permissions": {
                    "is_admin": True, 
                    "roles": [
                        "admin"
                    ]
                }, 
                "id": 1, 
                "email": "jrodrigo@scolab.es"
            }, 
            "tools": {
                "get_feature_info_control": {
                    "private_fields_prefix": "_"
                }, 
                "attribute_table": {
                    "private_fields_prefix": "_"
                }
            }, 
            "supported_crs": {
                "4258": {
                    "units": "degrees", 
                    "definition": "+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs", 
                    "code": "EPSG:4258", 
                    "title": "ETRS89"
                }, 
                "900913": {
                    "units": "meters", 
                    "definition": "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs", 
                    "code": "EPSG:900913", 
                    "title": "Google Maps Global Mercator -- Spherical Mercator"
                }, 
                "4326": {
                    "units": "degrees", 
                    "definition": "+proj=longlat +datum=WGS84 +no_defs", 
                    "code": "EPSG:4326", 
                    "title": "WGS84"
                }, 
                "3857": {
                    "units": "meters", 
                    "definition": "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs", 
                    "code": "EPSG:3857", 
                    "title": "WGS 84 / Pseudo-Mercator"
                }
            }, 
            "geoserver_base_url": "https://admin:admin52@test.scolab.eu/geoserver"          
        }
    
        return HttpResponse(json.dumps(conf, indent=4), content_type='application/json')
    
@login_required(login_url='/gvsigonline/auth/login_user/')
@is_admin_user 
def search_candidates(request):
    if request.method == 'GET':
        query = request.GET.get('query')           
        suggestions = geocoder.search_candidates(query)
            
        return HttpResponse(json.dumps(suggestions, indent=4), content_type='application/json')


@login_required(login_url='/gvsigonline/auth/login_user/')
@is_admin_user 
def get_location_address(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        location = geocoder.get_location_address(query)
        
        return HttpResponse(json.dumps(location, indent=4), content_type='application/json')
    
def export(request):   
    return render_to_response('export_a4h.html', {}, context_instance=RequestContext(request))