function test_edit() {
    $('form#save_form').get(0).setAttribute('action', '../app/edit/test');
}

$(function() {
    "use strict";

    $('#wikipedia-info').click(function (e) {
        e.preventDefault();
        $("#wikipedia-edit-info").slideToggle('slow');
        return false;
    });

    $("#wikipedia-edit-info").hide();

    $("#saveform").submit(function(e) {
        e.preventDefault();
        
        $.ajax({
            data: $(this).serialize(),
            type: $(this).attr('method'),
            url: $(this).attr('action'),
            dataType: "html",
            success: function (result) {
                $('.app-popup').show();
                $('.app-popup-container').html(result);
            },
            error: function (){
                  alert('Error!');
            }
        });
        return false;
    }); 
});

