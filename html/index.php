
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
            $img = "http://www.isthedartrunning.co.uk/EXCITED.jpg";
        }
    ?>
    <meta property="og:description"        content="<?= $text ?>" />
    <meta property="og:image"        content="<?= $img ?>" />
    <link href="mycss.css" rel="stylesheet">

  </head>

  <body>
    <div id="fb-root"></div>

        <div id="yesno" ></div>
        <div id='message'></div>

    <div id="link-container">
        <p> <a class= "button-link" href="/graph.html">graph</a> </p>
    </div>
    <div id="fb-container" style="width:100%;">
        <div class="fb-like" data-href="http://isthedartrunning.co.uk" data-layout="button_count" data-action="like" data-size="large" data-show-faces="true" data-share="true"></div>
    </div>



    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
    <script type="text/javascript" src="myscript.js"></script>
  </body>

</html>
