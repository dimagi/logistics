(function($) {
 $.fn.printableview = function() {
    document.getElementById("wrapper").removeAttribute('id');
    $(".noprint").hide();
    window.print();
 };
})(jQuery)