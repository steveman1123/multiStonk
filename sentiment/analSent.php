<?php
//the purpose of this is to generate word sentiment based on financial headlines
//there will be a second file/game that will attempt to profile and learn whether a headline means good news or bad news (and the confidence it has on it)
//TODO: try using the following to compress the page even more (and expand out to main website)
//if (substr_count($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip'))
//  ob_start("ob_gzhandler"); else ob_start();


//TODO: add scoring
//TODO: add multiple users
//TODO: add "accounts" (basically just usernames with associated scores) and display them

/*
* get a buttload of headlines saved in one big file
* pop through each of those until empty, then regen headline list
* vote on each headline
* explode headline text into individual words (removing punctuation)
* add scores to the output dict (of format {word:score} -> 0=neutral +=positive, -=negative connotation)
*/

global $fileLocation;
global $symbFile;
global $headlinesFile;

//set the working directory (this is where this file is assuming that there's a simple include '/path/to/this/file' file in the server document root)
$fileLocation = join("\\",array_slice(explode("\\",get_included_files()[1]),0,-1));
$symbFile = $fileLocation."/allSymbs.json";
$headlinesFile = $fileLocation."/headlines.json";
$wordFile = $fileLocation."/wordScores.json";

if(!file_exists($symbFile)) { //create the file if it doesn't exist
  if(exec("python3 $fileLocation/allNdaq.py")) { //try running python3 (as linux standard)
    if(exec("py $fileLocation/allNdaq.py")) { //try running py (as windows standard)
      throw new Exception("No python installation or file found");
    }
  }
}


//get $numHeads number of headlines for $symb from the internet
function getInternetHeadlines($symb, $numHeads) {
  $url = "https://api.nasdaq.com/api/news/topic/articlebysymbol?q=$symb%7Cstocks%26offset=0%26limit=$numHeads";
  
  //exec("powershell \$r = curl \"".$url."\" -UseBasicParsing ; \$r.content", $headlines);
  //use this for testing instead of the other getting it from the api all the time
  $headlines = Array("{\"data\":[{\"title\":\"How To Read An Earnings Report\",\"image\":\"/image/087f888dbccf78a2d019ad25c86e8678d53f9688_finance56.jpg\",\"created\":\"Apr 23, 2021 09:28 AM\",\"ago\":\"4 days ago\",\"primarysymbol\":\"\",\"publisher\":\"\",\"url\":\"/articles/how-to-read-an-earnings-report-2021-04-23\"},{\"title\":\"Mining giant Chile flush with cash as copper price soars\",\"image\":\"/2021-04-27T152544Z_1_SS6_RTRLXPP_2_LYNXPACKAGER.JPG\",\"created\":\"Apr 27, 2021 01:39 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"\",\"publisher\":\"Reuters\",\"url\":\"/articles/mining-giant-chile-flush-with-cash-as-copper-price-soars-2021-04-27\"},{\"title\":\"Russia's Sputnik V developers reject Brazil's criticisms\",\"image\":\"/2021-04-27T091935Z_1_IQ2_RTRLXPP_2_LYNXPACKAGER.JPG\",\"created\":\"Apr 27, 2021 01:39 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"azn\",\"publisher\":\"Reuters\",\"url\":\"/articles/russias-sputnik-v-developers-reject-brazils-criticisms-2021-04-27\"},{\"title\":\"POLL-U.S. crude and gasoline stocks seen rising last week, distillates likely down\",\"image\":\"/2021-04-26T215754Z_1_VE7_RTRLXPP_2_LYNXPACKAGER.JPG\",\"created\":\"Apr 27, 2021 01:38 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"\",\"publisher\":\"Reuters\",\"url\":\"/articles/poll-u.s.-crude-and-gasoline-stocks-seen-rising-last-week-distillates-likely-down-2021-04\"},{\"title\":\"Beyond Meat Launches New Meat-free Burgers \",\"image\":\"\",\"created\":\"Apr 27, 2021 01:34 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"bynd\",\"publisher\":\"RTTNews\",\"url\":\"/articles/beyond-meat-launches-new-meat-free-burgers-2021-04-27\"},{\"title\":\"How a Fast, Interactive Investor Experience Can Help Advisors Grow Their Practice\",\"image\":\"\",\"created\":\"Apr 27, 2021 01:32 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"\",\"publisher\":\"\",\"url\":\"/articles/how-a-fast-interactive-investor-experience-can-help-advisors-grow-their-practice-2021-04\"},{\"title\":\"Canada unveils back-to-work legislation to end Montreal port strike\",\"image\":\"/2021-04-27T173319Z_1_XT8_RTRLXPP_2_LYNXPACKAGER.JPG\",\"created\":\"Apr 27, 2021 01:31 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"\",\"publisher\":\"Reuters\",\"url\":\"/articles/canada-unveils-back-to-work-legislation-to-end-montreal-port-strike-2021-04-27\"},{\"title\":\"Novartis (NVS) Q1 2021 Earnings Call Transcript\",\"image\":\"\",\"created\":\"Apr 27, 2021 01:30 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"nvs\",\"publisher\":\"The Motley Fool\",\"url\":\"/articles/novartis-nvs-q1-2021-earnings-call-transcript-2021-04-27\"},{\"title\":\"FLEXSTEEL INDUSTRIES, INC. (FLXS) Q3 2021 Earnings Call Transcript\",\"image\":\"\",\"created\":\"Apr 27, 2021 01:30 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"flxs\",\"publisher\":\"The Motley Fool\",\"url\":\"/articles/flexsteel-industries-inc.-flxs-q3-2021-earnings-call-transcript-2021-04-27\"},{\"title\":\"Encore Wire Corp (WIRE) Q1 2021 Earnings Call Transcript\",\"image\":\"\",\"created\":\"Apr 27, 2021 01:30 PM\",\"ago\":\"4 hours ago\",\"primarysymbol\":\"wire\",\"publisher\":\"The Motley Fool\",\"url\":\"/articles/encore-wire-corp-wire-q1-2021-earnings-call-transcript-2021-04-27\"}],\"message\":null,\"status\":{\"rCode\":200,\"bCodeMessage\":null,\"developerMessage\":null}}");
  $headlines = json_decode($headlines[0])->data; //isolate just the headline list after converting to json object
  return $headlines;
}


//get $n headlines for the specified $symb from the file or from the internet
function getHeadline($symb) {
  global $headlinesFile;
  global $fileLocation;
  //check that the headlines file exists
  if(file_exists($headlinesFile)) {
    //file exists, read it and get the headlines
    $headlines = (array)json_decode(file_get_contents($headlinesFile), true);
    if(count($headlines)==0) { //if none are remaining, get headlines from internet and write to file
      $numHeads = 15; #get this many headlines per request
      $headlines = getInternetHeadlines($symb, $numHeads); //get headlines rom the internet
      file_put_contents($fileLocation.'/headlines.json',json_encode($headlines)); //write the headlines to the file
    }
  } else { //file doesn't exist, get headlines from internet and write to file
    $headlines = getInternetHeadlines($symb, $numHeads);
    file_put_contents($fileLocation.'/headlines.json',$headlines);  
  }
   
  //$head = $headlines[random_int(0,$numHeads)]->title;
  return $headlines[0]['title']; #return the first term in the array always
}

/*
we're going to ignore concurrent clients for now (may restructure later if we feel like it)
if isset post:
  ensure it has reaction and headline
    ensure headline is present in headlines (get the index of it)
      explode sentance, remove punct, add scores to score dict
      remove index of it
    else
      explode sentence and remove punct (clean text too) (may want to remove this functionality in concurrency update)
  else
    do nothing
else
  do what's currently being done (check for symbs, get new headlines, serve headline, etc)
*/

//TODO: restructure so that idx is only set if needed and all the other stuff happens regardless (then only unset if idx isset)
/*
if(isset($_POST)) { //make sure post has data
  if(array_key_exists("head",$_POST) and array_key_exists("sent",$_POST)) { //make sure it has the right data
    $headList = (array)json_decode(file_get_contents($headlinesFile),true); //get the list of recorded headlines
    if(in_array($_POST['head'], $headList) { //make sure that the headline is in the headline list
      $idx = array_search($_POST['head'],$headList); //find where it is
      $head = preg_replace("/[^A-Za-z0-9\-]/","",$_POST['head']); //strip out special chars (other than alphanumerics)
      $wordList = explode(" ",$head); //split by spaces
      $wordScores = file_get_contents($wordFile); //load in the words with scores TODO
      foreach($wordList as $w) { //loop thru every word in the headline
        if($w in_array($wordScores)) { #if it's already present in the scores, then append to it TODO
          $wordScores[$w] = {"sent":$wordScores[$w]['sent']+$_POST['sent'], "votes":$wordScores[$w]['votes']++};
        } else { //if it's not already present in the scores, then init it TODO
          $wordScores[$w] = {"sent":$_POST['sent'], "votes":1};
        }
      }
      //TODO: write to scores file
      
      unset($headList[$idx]); //remove the headline from the headline list
      //TODO: write headList back to the headlines file
      
    } else { //else the headline is not in the headline list
      
    }
  }
}
*/



$symbs = (array)json_decode(file_get_contents($symbFile, true)); //get all the symbols & company names from the file stored into a keyed array
$symb = array_rand($symbs);
$head = getHeadline($symb);
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
        margin: auto;
        text-align: center;
        font-size: 14pt;
      }
      
      button {
        border-radius: 10px;
        font-size: 24pt;
        background-color: #fff;
      }
      
      button:focus { background-color: #aaa; }
      
      #headline {
        width: 33%;
        margin: 0 auto;
      }

      #wrap { margin-top: 20%; }
      
      @media screen and (max-width: 640px){
        #headline { width: 90%; }
        #wrap { margin-top: 50%; }
      }
    </style>
  </head>
  <body>
    <div id="wrap">
      <form method="post">
        <p id="headline"><?php echo $head; ?></p>
        <input type="hidden" name="head" value="<?php echo $head; ?>"/>
        <p>
          <button type="submit" name="sent" value="-1">-</button>&emsp;
          <button type="submit" name="sent" value="0" autofocus>&#215;</button>&emsp;
          <button type="submit" name="sent" value="1">+</button>
        </p>
      </form>
    </div>
  </body>
</html>
