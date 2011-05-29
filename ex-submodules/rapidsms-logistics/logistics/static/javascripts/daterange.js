$(function() {
    var dates = $( "#from, #to" ).datepicker({
        defaultDate: "-1m",
        changeMonth: true,
        maxDate: "+0d",
        numberOfMonths: 2,
        onSelect: function( selectedDate ) {
            var option = this.id == "from" ? "minDate" : "maxDate",
                instance = $( this ).data( "datepicker" ),
                date = $.datepicker.parseDate(
                    instance.settings.dateFormat ||
                    $.datepicker._defaults.dateFormat,
                    selectedDate, instance.settings );
            dates.not( this ).datepicker( "option", option, date );
        }
    });
});