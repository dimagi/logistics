$(function() {
    var dates = $( "#from, #to" ).datepicker({
        defaultDate: "-1m",
        changeMonth: true,
        maxDate: "+0d",
        numberOfMonths: 2,
        dateFormat: "yy-mm-dd",
        onSelect: function( selectedDate ) {
            var option = this.id == "from" ? "minDate" : "maxDate",
                instance = $( this ).data( "datepicker" ),
                date = $.datepicker.parseDate("yy-mm-dd",
                    selectedDate, instance.settings );
            dates.not( this ).datepicker( "option", option, date );
        }
    });
});