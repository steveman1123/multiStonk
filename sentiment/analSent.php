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
$url = "https://api.nasdaq.com/api/news/topic/articlebysymbol?q=$symb%7Cstocks%26offset=0%26limit=$numHeads";

//exec("powershell \$r = curl \"".$url."\" -UseBasicParsing ; \$r.content", $headlines);
$headlines = Array("{\"data\":[{\"title\":\"How To Read An Earnings Report\",\"image\":\"/image/087f888dbccf78a2d019ad25c86e8678d53f9688_finance56.jpg\",\"created\":\"Apr 23, 2021 09:28 AM\",\"ago\":\"4 days ago\",\"primarysymbol\":\"\",\"publisher\":\"\",\"url\":\"/articles/how-to-read-an-earnings-report-2021-04-23\"},{\"title\":\"Mining giant Chile flush with cash as copper price soars\",\"image\":\"/2021-04-27T152544Z_1_SS6_RTRLXPP_2_LYNXPACKAGER.JPG\",\"created\":\"Apr 27, 2021 01:39 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"\",\"publisher\":\"Reuters\",\"url\":\"/articles/mining-giant-chile-flush-with-cash-as-copper-price-soars-2021-04-27\"},{\"title\":\"Russia's Sputnik V developers reject Brazil's criticisms\",\"image\":\"/2021-04-27T091935Z_1_IQ2_RTRLXPP_2_LYNXPACKAGER.JPG\",\"created\":\"Apr 27, 2021 01:39 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"azn\",\"publisher\":\"Reuters\",\"url\":\"/articles/russias-sputnik-v-developers-reject-brazils-criticisms-2021-04-27\"},{\"title\":\"POLL-U.S. crude and gasoline stocks seen rising last week, distillates likely down\",\"image\":\"/2021-04-26T215754Z_1_VE7_RTRLXPP_2_LYNXPACKAGER.JPG\",\"created\":\"Apr 27, 2021 01:38 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"\",\"publisher\":\"Reuters\",\"url\":\"/articles/poll-u.s.-crude-and-gasoline-stocks-seen-rising-last-week-distillates-likely-down-2021-04\"},{\"title\":\"Beyond Meat Launches New Meat-free Burgers \",\"image\":\"\",\"created\":\"Apr 27, 2021 01:34 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"bynd\",\"publisher\":\"RTTNews\",\"url\":\"/articles/beyond-meat-launches-new-meat-free-burgers-2021-04-27\"},{\"title\":\"How a Fast, Interactive Investor Experience Can Help Advisors Grow Their Practice\",\"image\":\"\",\"created\":\"Apr 27, 2021 01:32 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"\",\"publisher\":\"\",\"url\":\"/articles/how-a-fast-interactive-investor-experience-can-help-advisors-grow-their-practice-2021-04\"},{\"title\":\"Canada unveils back-to-work legislation to end Montreal port strike\",\"image\":\"/2021-04-27T173319Z_1_XT8_RTRLXPP_2_LYNXPACKAGER.JPG\",\"created\":\"Apr 27, 2021 01:31 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"\",\"publisher\":\"Reuters\",\"url\":\"/articles/canada-unveils-back-to-work-legislation-to-end-montreal-port-strike-2021-04-27\"},{\"title\":\"Novartis (NVS) Q1 2021 Earnings Call Transcript\",\"image\":\"\",\"created\":\"Apr 27, 2021 01:30 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"nvs\",\"publisher\":\"The Motley Fool\",\"url\":\"/articles/novartis-nvs-q1-2021-earnings-call-transcript-2021-04-27\"},{\"title\":\"FLEXSTEEL INDUSTRIES, INC. (FLXS) Q3 2021 Earnings Call Transcript\",\"image\":\"\",\"created\":\"Apr 27, 2021 01:30 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"flxs\",\"publisher\":\"The Motley Fool\",\"url\":\"/articles/flexsteel-industries-inc.-flxs-q3-2021-earnings-call-transcript-2021-04-27\"},{\"title\":\"Encore Wire Corp (WIRE) Q1 2021 Earnings Call Transcript\",\"image\":\"\",\"created\":\"Apr 27, 2021 01:30 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"wire\",\"publisher\":\"The Motley Fool\",\"url\":\"/articles/encore-wire-corp-wire-q1-2021-earnings-call-transcript-2021-04-27\"}],\"message\":null,\"status\":{\"rCode\":200,\"bCodeMessage\":null,\"developerMessage\":null}}"); //use this for testing instead of the other getting it from the api all the time
$headlines = json_decode($headlines[0])->data;
/* save headlines to a file
 * loop through all the saved ones, vote on each
 * take the vote and add to each word
 * save words in a file
 */

/* alternatively:
 * get a buttload of headlines saved in one big file
 * loop through each of those until empty, then regen headline list
 * vote on each headline
 *
 */
$head = $headlines[random_int(0,$numHeads)]->title;
?>
 
<!DOCTYPE html>

<html lang=en>
  <head>
    <title>Sentiment Analysis Game</title>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <style>
      /** { border: solid red 1px; }*/
      html, body {
        width: 100%;
        height: 100%;
        font-family: sans-serif;
        margin: auto;
        text-align: center;
        font-size: 14pt;
      }
      
      button {
        border-radius: 10px;
        font-size: 24pt;
        background-color: #fff;
      }
      
      #headline {
        width: 33%;
        margin: 0 auto;
      }
      
      #wrap {
        margin-top: 20%;
      }
      
      @media screen and (max-width: 640px){
        #headline {
          width: 90%;
        }
        #wrap {
          margin-top: 50%;
        }
      }
      
    </style>
  </head>
  <body>
    <div id="wrap">
      <p id="headline"><?php echo $head; ?></p>
      <form method="post">
        <p>
          <button type="submit" name="sent" value="-1">-</button>&emsp;
          <button type="submit" name="sent" value="0" autofocus>&#215;</button>&emsp;
          <button type="submit" name="sent" value="1">+</button>
        </p>
      </form>
    </div>
  </body>
</html>
