function test_edit() {
    $('form#saveform').get(0).setAttribute('action', '../../app/test/edit');
}

function toggle_info() {
    $('#wikipedia-info').click(function (e) {
        e.preventDefault();
        $("#wikipedia-edit-info").slideToggle('slow');
        return false;
    });
}

$(function() {
    function load_preview() {
        "use strict";

        $("#wikipedia-edit-info").hide();

        $('.app-popup a.close').click(function () {
            $('.app-popup').hide();
        });

        $("#saveform").submit(function(e) {
            e.preventDefault();
            
            $.ajax({
                data: $(this).serialize(),
                type: $(this).attr('method'),
                url: $(this).attr('action'),
                dataType: "html",
                success: function (result) {
                    $('#app-popup-main').show();
                    $('#app-popup-main-container').html(result);
                },
                error: function (){
                      alert('Error!');
                }
            });
            return false;
        }); 
    };
});
