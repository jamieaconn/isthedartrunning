
function getQueryVariable(variable)
{
       var query = window.location.search.substring(1);
       var vars = query.split("&");
       for (var i=0;i<vars.length;i++) {
               var pair = vars[i].split("=");
               if(pair[0] == variable){return pair[1];}
       }
       return(false);
}

 (function(d, s, id) {

      var js, fjs = d.getElementsByTagName(s)[0];
      if (d.getElementById(id)) return;
      js = d.createElement(s); js.id = id;
      js.src = "//connect.facebook.net/en_GB/sdk.js#xfbml=1&version=v2.8&appId=246515359021141";
      fjs.parentNode.insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));


$.getJSON('dart.json', function(data) { 
    current_level = data.current_level;
    next_up = data.next_up;
    current_time = data.current_time;
    text = data.text;   
    console.log(next_up - current_time);
    if (text.length < 5){
        document.querySelector('#yesno').innerHTML = text;
    } else {

        document.querySelector('#message').innerHTML = text; 
    }
});

setInterval(function() {
        window.location.reload();
}, 900000); 





/*
 * Make Facebook Page-Plugin responsive
 */
var loop;
$( window ).bind( "resize", function() {

    // run only once, after the resizing finished
    clearInterval( loop );
    loop = setTimeout(function() {

        var container = $( '#fb-container' );
        var containerWidth = container.width();
        var fbPage = container.find( '.fb-like' );

        // `fb_iframe_widget` class is added after first FB.FXBML.parse()
        // `fb_iframe_widget_fluid is added in same situation, but only for mobile devices (tablets, phones)
        // By removing those classes FB.XFBML.parse() will reset the plugin widths.
        fbPage.removeClass('fb_iframe_widget fb_iframe_widget_fluid');

        // update width and re-render
        fbPage.data("width", containerWidth);
        FB.XFBML.parse();

    }, 100 );

});
