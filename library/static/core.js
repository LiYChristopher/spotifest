$("#login").click(function() {
    if ($('#login-form').is(":visible()") && !($('#festi-text').is(":focus"))) {
        $("#login-form").hide()
    }
    else {
        $("#login-form").show();
    }
});

