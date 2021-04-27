<?php
/* this should act identically to the python file
 * to read and write into the same json file
 * but provides a web interface for easier accessiblity
 */

 /*
https://beamtic.com/http-requests-in-php
https://api.nasdaq.com/api/news/topic/articlebysymbol?q={symb}%7Cstocks&offset=0&limit={numHeads}

https://thisinterestsme.com/php-curl-custom-headers/

TODO: add comments
*/
 

$symbFile = file_get_contents(join("\\",array_slice(explode("\\",get_included_files()[1]),0,-1))."/allSymbs.json");
$symbs = json_decode($symbFile, true);

$symb = array_rand($symbs);
$numHeads = 5;
//$url = "https://api.nasdaq.com/api/news/topic/articlebysymbol?q=".$symb."%7Cstocks&offset=0&limit=".$numHeads;
//$url = "http://stevenw.duckdns.org/stevenw/";
$url = "https://er.jsc.nasa.gov/seh/";

$surl = "https://beamtic.com/api/request-headers"; // The POST URL



$js = file_get_contents($url);
var_dump($js);

/*
$aHTTP['http']['method'] = 'GET';
$aHTTP['http']['header'] = "User-Agent: testing\r\n";
//$aHTTP['http']['header'] .= "GET /api/news/topic/articlebysymbol?q=usdeur|currencies&offset=0&limit=7 HTTP/2\r\n";
//$aHTTP['http']['header'] .= "Host: api.nasdaq.com\r\n";
//$aHTTP['http']['header'] .= "Accept-Encoding: gzip, deflate, br\r\n";
$aHTTP['http']['header'] .= "Connection: keep-alive\r\n";
//$aHTTP['http']['header'] .= "TE: Trailers";
//$aHTTP['http']['content'] = "body";

var_dump($aHTTP);

$context = stream_context_create($aHTTP);
//var_dump($context);

$contents = file_get_contents($url, false, $context);
var_dump($contents);
*/

/*

$handle = fopen($url, "rb");
$contents = stream_get_contents($handle);
fclose($handle);

var_dump($contents);

/*
$heads = json_decode($contents,true)['data'];

var_dump($heads);

#file_put_contents("./heads.json",$contents);

$head = array_rand($heads)['title'];
var_dump($head);
*/
$head = "";
?>
 
<!DOCTYPE html>

<html lang=en>
  <head>
    <title>Sentiment Analysis Game</title>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <style>
      html, body {
        width: 100%;
        height: 100%;
        font-family: sans-serif;
        margin: 0;
        text-align: center;
        padding-top: 20px;
      }
      
      button {
        border-radius: 10px;
      }
      
      #headline {
        width: 33%;
      }
      
      @media screen and (max-width: 640px){
        #headline {
          width: 90%;
        }
      }
    </style>
  </head>
  <body>
    <div id="headline"><?php echo $head; ?></div>
    <form method="post">
      <p>
        <button type="submit" name="sent" value="-1">-</button>
        <button type="submit" name="sent" value="0">x</button>
        <button type="submit" name="sent" value="1">+</button>
      </p>
    </form>
  </body>
</html>
