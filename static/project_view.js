$(document).ready(function () {
    console.log("----------over here")
    $('#loading').hide();
    $("#train").click(function (e) {
        console.log("here--------------------")
        e.preventDefault();
        $('#loading').show();
        // var path = $("#csvfile").val();
        $.ajax({
            
            //change url below
            url: $("#train").data('path'),
            type: "POST",
            // data: { filepath: path },
            success: function (response) {
                console.log("finally done!")
                $(".json-result").html('<p>"Prediction File created at !!!Prediction_Output_File/Predictions.csvand few of the predictions are"</p><pre>' + response + '</pre>');
                $('#loading').hide();
            },
            
        });
    });
    $("#test").click(function (e) {
        console.log("here--------------------")
        e.preventDefault();
        $('#loading').show();
        // var path = $("#csvfile").val();
        $.ajax({
            
            //change url below
            url: $("#test").data('path'),
            type: "POST",
            // data: { filepath: path },
            success: function (response) {
                console.log("finally done!")
                $(".json-result").html('<p>"Prediction File created at !!!Prediction_Output_File/Predictions.csvand few of the predictions are"</p><pre>' + response + '</pre>');
                $('#loading').hide();
            },
            
        });
    });
    $(".get-link").click(function (e) {
        console.log("----------over here--------------------")
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        $('#loading').show();
        // var path = $("#csvfile").val();
        $.ajax({
            
            //change url below
            url: $(".get-link").data('path'),
            data:{
                'project_name':$(".get-link").data('project_name'),
                'directory_path':$(".get-link").data('directory_path'),
                'blob_name':$(".get-link").data('file_name'),

            },
            type: "POST",
            // data: { filepath: path },
            success: function (response) {
                console.log("done!")
                console.log(response);
                $('#loading').hide();
                window.open(response);
            },
            
        });
    });
    
});