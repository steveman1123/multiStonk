<?php
/* this should act identically to the python file
 * to read and write into the same json file
 * but provides a web interface for easier accessiblity
 */

 /*
https://beamtic.com/http-requests-in-php
https://raybb.github.io/random-stock-picker/stocks.json
https://api.nasdaq.com/api/news/topic/articlebysymbol?q={symb}%7Cstocks&offset=0&limit={numHeads}
*/
?>
 
<!DOCTYPE html>

<html lang=en>
  <head>
    <title>Sentiment Analysis Game</title>
    <style>
      html, body {
        width: 100%;
        height: 100%;
        font-family: sans-serif;
      }
      button {
        border-radius: 10px;
      }
    </style>
  </head>
  <body>
    <div id="headline"><?php echo $head; ?></div>
    <p><button>-</button><button>x</button><button>+</button></p>
  </body>
</html>