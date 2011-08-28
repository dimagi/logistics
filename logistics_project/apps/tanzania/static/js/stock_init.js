function clear_custom_classes(elem) {
    $(elem).removeClass("insufficient_data zero_count");
}
function update_class_by_stock(elem) {
    clear_custom_classes(elem);
    var stock = $(elem).data("stock");
    if (stock == "No data") { 
        $(elem).addClass("insufficient_data");
    } else if (stock == "0") {
        $(elem).addClass("zero_count");
    }
}
function update_class_by_months(elem) {
    clear_custom_classes(elem);
    var stock = $(elem).data("months");
    if (stock == "N/A") { 
        $(elem).addClass("insufficient_data");
    } else if (stock == "0") {
        $(elem).addClass("zero_count");
    }
}
$(function() {
    $("#show_stock").hide();
    $("#show_months").click(function() {
        $("td.stock").each(function () {
            $(this).text($(this).data("months"));
            update_class_by_months(this);
        });
        $("#show_stock").show();
        $("#show_months").hide();
        
    });
    $("#show_stock").click(function() {
        $("td.stock").each(function () {
            $(this).text($(this).data("stock"));
            update_class_by_stock(this);
        });
        $("#show_months").show();
        $("#show_stock").hide();
    });
    $("td.stock").each(function () {
        $(this).text($(this).data("stock"));
        update_class_by_stock(this);
    });
        
});                 
