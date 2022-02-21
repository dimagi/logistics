

function clear_custom_classes(elem) {
    $(elem).removeClass("insufficient_data zero_count");
}
function update_class(elem, min, max) {
    var stock = parseFloat($(elem).data("months"));
    if (isNaN(stock)) { 
        $(elem).addClass("insufficient_data");
    } else if (stock == 0) {
        $(elem).addClass("zero_count stock_iconified");
    } else if (stock < min){
        $(elem).addClass("low_stock stock_iconified");
    } else if (stock <= max) {
        $(elem).addClass("adequate_stock stock_iconified");
    } else {
        console.log("stock: " + stock + " min: " + min + " max: " + max);
        $(elem).addClass("overstock stock_iconified");
    }
}

function stock_init (min, max) {
    $(function() {
	    $("#show_stock").hide();
	    $("#show_months").click(function() {
	        $("td.stock").each(function () {
	            $(this).text($(this).data("months"));
	        });
	        $("#show_stock").show();
	        $("#show_months").hide();
	    });
	    $("#show_stock").click(function() {
	        $("td.stock").each(function () {
	            $(this).text($(this).data("stock"));
	        });
	        $("#show_months").show();
	        $("#show_stock").hide();
	    });
	    $("td.stock").each(function () {
	        $(this).text($(this).data("stock"));
	        update_class(this, min, max);
	    });
    });
}                 
