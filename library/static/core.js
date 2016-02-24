var $input = $('input:text'),
    $register = $('#festivalSubmit');

$register.attr('disabled', true);
$input.keyup(function() {
    var trigger = false;
    $input.each(function() {
        if (!$(this).val()) {
            trigger = true;
        }
    });
    trigger ? $register.attr('disabled', true) : $register.removeAttr('disabled');
});

$("#login").click(function() {
    if ($('#login-form').is(":visible()") && !($('#festi-text').is(":focus"))) {
        $("#login-form").hide()
    }
    else {
        $("#login-form").show();
        $("#festi-text").focus();
    }
});
