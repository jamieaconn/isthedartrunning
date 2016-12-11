
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <link rel='shortcut icon' href='favicon.ico' type='image/x-icon'/ >
    <title>River Dart Levels</title>
    <meta property="og:url"                content="http://www.isthedartrunning.co.uk" />
    <meta property="og:type"               content="website" />
    <meta property="fb:app_id"               content="246515359021141" />
    <meta property="og:title"              content="is the dart running?" />
    <?php
        $contents = file_get_contents("dart.json"); 
        $contents1 = json_decode($contents);
        $text = $contents1->text;
        if (strlen($text) < 4){
            $img = "http://www.isthedartrunning.co.uk/" . $text . ".jpg";
        } else {
            $img = "http://www.isthedartrunning.co.uk/YES.jpg";
        }
    ?>
    <meta property="og:description"        content="<?= $text ?>" />
    <meta property="og:image"        content="<?= $img ?>" />
  </head>

  <body>
    <div id="fb-root"></div>
    
    <script>(function(d, s, id) {
      var js, fjs = d.getElementsByTagName(s)[0];
      if (d.getElementById(id)) return;
      js = d.createElement(s); js.id = id;
      js.src = "//connect.facebook.net/en_GB/sdk.js#xfbml=1&version=v2.8&appId=246515359021141";
      fjs.parentNode.insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));</script>
       <div style="text-align: center; font-size: 250px; font-weight: bold; line-height: 600px; font-family: Arial, Helvetica, sans-serif;">
 
       <div class='yesno'></div>
        
       </div>
      
       <div style="text-align: center; font-size: 100px; font-weight: bold; line-height: 200px; font-family: Arial, Helvetica, sans-serif;">
 
       <div class='message'></div>

       </div>

        
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>



<div class="fb-like" data-href="http://isthedartrunning.co.uk" data-layout="button_count" data-action="like" data-size="small" data-show-faces="true" data-share="true"></div>
<p> <a href="/graph.html">graph</a> </p>
</body>
<script>

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

    // Grpah of data at isthedartrunning.co.uk/testing.html

    $.getJSON('dart.json', function(data) { 
        current_level = data.current_level;
        next_up = data.next_up;
        current_time = data.current_time;
        text = data.text;   
        console.log(next_up - current_time);
        if (text.length < 5){
            document.querySelector('.yesno').innerHTML = text; 
        } else {

            document.querySelector('.message').innerHTML = text; 
        }
    }); 

</script>
</html>
