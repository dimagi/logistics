$(function() {
    $('.monthPicker').datepicker( {
		showOn: "button",
		buttonImage: "/static/logistics/images/calendar.gif",
		buttonImageOnly: true,
        changeMonth: true,
        changeYear: true,
        showButtonPanel: true,
        dateFormat: 'MM yy',
        onClose: function(dateText, inst) {
            var month = $("#ui-datepicker-div .ui-datepicker-month :selected").val();
            var year = $("#ui-datepicker-div .ui-datepicker-year :selected").val();
            var locWithoutGetParams = location.href.split("?")[0]
            var newurl = $.query.set("year", year).set("month", parseInt(month)+1)
            window.location.replace(locWithoutGetParams + newurl)
        }
    });
});