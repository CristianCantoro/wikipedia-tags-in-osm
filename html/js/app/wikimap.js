// Attribution to OSM contributors
var common_attr = 'Map data &copy; <a href="http://osm.org/copyright">' +
                  'OpenStreetMap</a> contributors, Imagery &copy; '
// Cloudmade
var map_url_cm = 'http://{s}.tile.cloudmade.com/'+
                 '{key}/{styleId}/256/{z}/{x}/{y}.png',
    map_attribution_cm = common_attr + 'CloudMade',
    map_key_cm = '2d72720041c94acf89b2e51c3d1792de';

map_url_cm = map_url_cm.replace("{key}", map_key_cm)



// OpenCycleMap
var map_url_oc = 'http://{s}.tile2.opencyclemap.org/' +
                 'transport/{z}/{x}/{y}.png',
    map_attribution_oc = common_attr + 'OpenCycleMap'

// Toolserver
var map_url_ts = 'http://{s}.www.toolserver.org/' +
                 'tiles/bw-mapnik/{z}/{x}/{y}.png',
    map_attribution_ts = common_attr + 'Toolserver'

// Mapquest
var map_url_mq = 'http://otile1.mqcdn.com/' +
                 '/tiles/1.0.0/osm/{z}/{x}/{y}.jpg',
    map_attribution_mq = common_attr + 'MapQuest'

// OpenStreetMap classic tiles
var map_url_osm_classic = 'http://{s}.tile.osm.org/' +
                 '{z}/{x}/{y}.png',
    map_attribution_osm_classic = common_attr + 'OpenStreetMap'

var cloudmade_base = L.tileLayer(map_url_cm, {
        styleId: 997,
        attribution: map_attribution_cm
    }),
    cloudmade_classic = L.tileLayer(map_url_cm, {
        styleId: 1,
        attribution: map_attribution_cm
    }),
    opencyclemap = L.tileLayer(map_url_oc, {
        attribution: map_attribution_oc
    }),
    toolserver = L.tileLayer(map_url_ts, {
        attribution: map_attribution_ts
    }),
    mapquest = L.tileLayer(map_url_mq, {
        attribution: map_attribution_mq
    });
    osm_classic = L.tileLayer(map_url_osm_classic, {
        attribution: map_attribution_osm_classic
    });

var map = L.map('map_canvas', {
        center: new L.LatLng(lat, lon),
        zoom: 17,
        layers: [toolserver]
});

var dec_title = decodeURIComponent(title);

var blueIcon = new L.icon({
        iconUrl: '../app/img/marker-icon-blue.png',
        iconSize:     [25, 41],
        shadowSize:   [50, 64],
        iconAnchor:   [12, 41],
        shadowAnchor: [4, 62],
        popupAnchor:  [3, -33]
});

var infocontent = "Questa è la posizione del centroide " +
                  "ricavato da OpenStreetMap per l'oggetto collegato " +
                  "alla voce di Wikipedia: <em>" +
                  dec_title.replace(/_/g, ' ') + "</em>";

var fixed_marker = new L.marker([lat, lon], {icon: blueIcon});

var infopopup = L.popup();

infopopup
    .setLatLng(fixed_marker.getLatLng())
    .setContent(infocontent);

fixed_marker
        .bindPopup(infopopup)
        .update();

var redIcon = new L.icon({
    iconUrl: '../app/img/marker-icon-green.png',
    iconSize:     [25, 41],
    shadowSize:   [50, 64],
    iconAnchor:   [12, 41],
    shadowAnchor: [4, 62],
    popupAnchor:  [3, -33]
});

var popup = L.popup();

var draggable_marker = new L.marker([lat-0.00005, lon-0.00005], {
    icon: redIcon,
    draggable:'true'
});


var data = {
    'title': dec_title,
    'lat': lat,
    'lon': lon,
    'dim': dim,
    'ref': referrer,
    'id': id
};

var base_maps = {
    "OpenStreetMap Classic (Mapnik)": osm_classic,
    "OpenCycleMap": opencyclemap,
    "CloudMade Base": cloudmade_base,
    "CloudMade Classic": cloudmade_classic,
    "MapQuest": mapquest,
    "Toolserver": toolserver
};

var overlay_maps = {
    "Centroide in OSM": fixed_marker,
};

fixed_marker.addTo(map);

draggable_marker.addTo(map);

L.control.layers(base_maps, overlay_maps).addTo(map);

draggable_marker.on('dragend', function(e){
    var draggable_marker = e.target;
    var position = draggable_marker.getLatLng();

    var precision = 1000000;

    var drag_lat = Math.round(position.lat * precision) / precision;
    var drag_lng = Math.round(position.lng * precision) / precision;

    var msg = "La coordinate inserite su Wikipedia saranno:<br />" +
              "(" + drag_lat + "; " + drag_lng + ")";

    popup
        .setLatLng(position)
        .setContent(msg);
    draggable_marker
        .setLatLng(position,{draggable:'true'})
        .bindPopup(popup)
        .update()
        .openPopup();

    $("#final-lat").text(drag_lat);
    $("#final-lon").text(drag_lng);

    data = {
        'title': dec_title,
        'lat': drag_lat,
        'lon': drag_lng,
        'dim': dim,
        'ref': referrer,
        'id': id
    };

    lat = drag_lat;
    lon = drag_lng;

    $("a.wiki-edit").attr("href", "../app/preview?"+$.param(data));

});



$(function () {

    function login() {
        var r = $.Deferred();
        var popup_baseurl =  '../app/login?';
        
        var params = {'next': '/wtosm/app/login/success'}
        var popup_params = $.param(params)

        var popup_title = "Login";
        var popup_window = window.open(popup_baseurl + popup_params, 
                                       popup_title,
                                       'width=800, height=600');
        if (window.focus) {
            popup_window.focus();
        }

        var pollTimer = window.setInterval(function() {
            try {
                console.log(popup_window.document.URL) 
                if ( popup_window.location.pathname === 
                        '/wtosm/app/login/success') {
                    window.clearInterval(pollTimer);
                    popup_window.close();
                    r.resolve()
                    return r;
                }
            }
            catch(e) {
                if (e instanceof TypeError) {
                    console.log('Waiting for the user to log in');
                }
            }
        }, 1500);
    }

    $('#app-popup-map').hide();

    $('.app-popup a.close').click(function () {
        $('.app-popup').hide();
    });

    $('.wiki_user_edit').click(function (e) {
        e.preventDefault();

        var dec_title = decodeURIComponent(title);
        var dec_referrer = decodeURIComponent(referrer);

        var data = {
            lat: lat,
            lon: lon,
            dim: dim,
            title: dec_title,
            ref: dec_referrer,
            id: id
        };

        var needs_login = false;

        var callPreview = function ajaxCall() {
            $.ajax({
                url: "../app/preview",
                data: data,
                dataType: "html",
                type: 'GET',
                async: false,
                success: function (result) {
                    $('.app-popup').show();
                    $('.app-popup-container').html(result);
                },
                error: function (jqXHR, textStatus, errorThrown ) {
                    needs_login = true;
                }
            });
        }

        callPreview();

        if ( needs_login ) {
            login().done(callPreview);
        }
        return false;

    });

    $('.wiki_anon_edit').click(function (e) {
        e.preventDefault();

        var dec_title = decodeURIComponent(title);
        var dec_referrer = decodeURIComponent(referrer);

        var data = {
            lat: lat,
            lon: lon,
            dim: dim,
            title: dec_title,
            ref: dec_referrer,
            id: id
        };

        var needs_login = false;

        var callAnonEdit = function ajaxCall() {
            $.ajax({
                url: "../app/anon-edit",
                data: data,
                dataType: "html",
                type: 'GET',
                success: function (result) {
                    $('.app-popup').show();
                    $('.app-popup-container').html(result);
                },
            });
        }

        callAnonEdit();
       return false;

    });

});
