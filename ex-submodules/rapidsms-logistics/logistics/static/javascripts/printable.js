(function($) {
 $.fn.printableview = function() {
    document.getElementById("wrapper").removeAttribute('id');
    $(".noprint").hide();
    window.location.hash = "print";
    window.print();
 };
})(jQuery)