if (!$) {
    $ = django.jQuery;
}

$(document).ready(function() {
    if(!$('#id_is_pilot').attr('checked')) {
        $('.field-closest_supply_points').css('display', 'none');
    }

    $('#id_is_pilot').click(function(){
        if($(this).attr('checked')) {
            $('.field-closest_supply_points').css('display', 'block');
        } else {
            $('.field-closest_supply_points').css('display', 'none');
        }
    });
});
