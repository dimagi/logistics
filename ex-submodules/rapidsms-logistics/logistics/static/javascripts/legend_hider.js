$(function() {
    $("#legendhider").click(function() {
        $("#main_legend").hide("fast");
        $("#legendhider").hide();
        $("#legendshower").show();
    });
    $("#legendshower").click(function() {
        $("#main_legend").show("fast");
        $("#legendhider").show();
        $("#legendshower").hide();
    });    
    $("#legendshower").hide();
});