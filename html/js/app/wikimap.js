var cloudmadeUrl = 'http://{s}.tile.cloudmade.com/'+
                   '{key}/{styleId}/256/{z}/{x}/{y}.png',
    cloudmadeAttribution = 'Map data &copy; 2013 OpenStreetMap contributors, ' +
                           'Imagery &copy; 2012 CloudMade',
    cloudmadeKey = '2d72720041c94acf89b2e51c3d1792de';

var standard = L.tileLayer(cloudmadeUrl, {
    styleId: 997,
    attribution: cloudmadeAttribution,
    key: cloudmadeKey});

var map = L.map('map_canvas', {
    center: new L.LatLng(lat, lon),
    zoom: 17,
    layers: [standard]
});

var dec_title = decodeURIComponent(title);

var blueIcon = new L.icon({
    iconUrl: '../app/img/marker-icon-blue.png',
    iconSize:     [25, 41],
    shadowSize:   [50, 64],
    iconAnchor:   [12, 41],
    shadowAnchor: [4, 62],
    popupAnchor:  [-50, -33]
});

var infocontent = "<em>" + dec_title.replace(/_/g, ' ') + "</em>";

var fixed_marker = new L.marker([lat, lon], {icon: blueIcon});

var infopopup = L.popup();

infopopup
    .setLatLng(fixed_marker.getLatLng())
    .setContent(infocontent);

map.addLayer(fixed_marker);

fixed_marker
        .bindPopup(infopopup)
        .update();

var redIcon = new L.icon({
    iconUrl: '../app/img/marker-icon-red.png',
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
map.addLayer(draggable_marker);

var data = {
    'title': dec_title,
    'lat': lat,
    'lon': lon,
    'dim': dim,
    'ref': referrer,
    'id': id
};

draggable_marker.on('dragend', function(e){
    var draggable_marker = e.target;
    var position = draggable_marker.getLatLng();

    var precision = 1000000;

    var drag_lat = Math.round(position.lat * precision) / precision;
    var drag_lng = Math.round(position.lng * precision) / precision;

    var msg = "Il marker si trova a:<br />";
        msg += "(" + drag_lat + "; " + drag_lng + ")";

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

    $("a#wiki-user-edit").attr("href", "../app/preview?"+$.param(data));

});

function login() {
    var r = $.Deferred();
    var popup_baseurl =  '../app/login?';
    
    var params = {'next': '../app/login/success'}
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
                    '/app/login/success') {
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

$(function () {
    $('#app-popup-map').hide();

    $('#app-popup-map a.close').click(function () {
        $('#app-popup-map').hide();
    });

    $('.wiki_user_edit').click(function (e) {
        e.preventDefault();

        var data = {
            lat: lat,
            lon: lon,
            dim: dim,
            title: title,
            referrer: referrer,
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

        ajaxCall();

        if ( needs_login ) {
            login().done(callPreview);
        }
        return false;

    });
});