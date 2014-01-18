function test_edit() {
    $('form#save_form').get(0).setAttribute('action', '../app/edit/test');
}

$(document).ready(function() {
    $('#app-popup-preview').hide();

    $('#app-popup-preview a.close').click(function () {
        $('#app-popup-preview').hide();
    });

    $("#submit").click(function (event) {
        event.preventDefault();

        var serialized_data = $("#save_form").serialize();
        
        $.ajax({
            type: "POST",
            url: "../app/edit",
            data: serialized_data,
            success: function (result) {
                $('#app-popup-preview').show();
                $('#app-popup-preview-container').html(result);
            },
            error: function (){
                  alert('Error!');
            }
        });
    }); 
});


// function test_edit2() {
//     alert("Chiamata test_edit2()");
// }

// $(document).ready(function() {
//     $("#test2").click(function (event) {
//         event.preventDefault();
//         alert("Test test!");

//     });
//     $("#submit2").click(function (event) {
//         event.preventDefault();
//         alert("Test subnit!");

//     });
// });