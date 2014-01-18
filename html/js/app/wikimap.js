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

var infocontent = "<em>" + dec_title.replace(/_/g, ' ') + "</em>";

L.marker([lat, lon]).addTo(map).bindPopup(infocontent).openPopup();

var redIcon = new L.icon({
    iconUrl: 'img/marker-icon-red.png',
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
    'dim': dim
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
        .setContent(msg)
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
        'dim': dim
    };

    $("a#wiki-user-edit").attr("href", "../app/preview?"+$.param(data));

});

// $( document ).ready(function() {
//     $( "a#wiki-user-edit" ).click(function(e) {
//         e.preventDefault();

//         $.ajax({
//             url: "../app/login",
//             data: data,
//             success: function(result){
//                 $("#div1").html(result);
//             }
//         });

//         alert("pippo");
//     });
// });
