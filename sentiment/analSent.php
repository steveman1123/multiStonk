<?php
//the purpose of this is to generate word sentiment based on financial headlines
//there will be a second file/game that will attempt to profile and learn whether a headline means good news or bad news (and the confidence it has on it)
//TODO: try using the following to compress the page even more (and expand out to main website)
//if (substr_count($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip'))
//  ob_start("ob_gzhandler"); else ob_start();


//TODO: add multiple users
//TODO: add "accounts" (basically just usernames with associated scores) and display them

/*
* get a buttload of headlines saved in one big file
* pop through each of those until empty, then regen headline list
* vote on each headline
* explode headline text into individual words (removing punctuation)
* add scores to the output dict (of format {word:score} -> 0=neutral +=positive, -=negative connotation)
*/

/*
TODO:
add scoring
add comments
make things into their own functions
add file locking (another step needed for concurrent users)
make more adjustments for multiple users
remove words that are just numbers or are less than 2 letters long (also might want to remove words not in a real dict (like stock symbols))



for scores:
might be easiest to just have a scores file, have the user have a cookie with their username, then return back their score (that'd solve concurrency right away, and high scores)
*/

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
set_time_limit(300);
error_reporting(E_ALL);


global $symbFile;
global $headlinesFile;

//set the working directory (this is where this file is assuming that there's a simple include '/path/to/this/file' file in the server document root)
if(substr_count(PHP_OS,"WIN")) { //split via \ on windows, and / on non-windows
  $fileLocation = join("/",array_slice(explode("\\",get_included_files()[1]),0,-1));
} else {
  $fileLocation = join("/",array_slice(explode("/",get_included_files()[1]),0,-1));
}
$unlistedLocation = join("/",array_slice(explode("/",$fileLocation),0,-2))."/stockStuff"; //location outside of the git repo
$symbFile = $unlistedLocation."/allSymbs.json"; //where all the nasdaq symbols are stored - TODO: may want to expand beyond just nasdaq
$headlinesFile = $unlistedLocation."/headlines.json"; //where the headlines are stored
$wordFile = $unlistedLocation."/wordScores.json"; //where the word sentiment is stored


if(!file_exists($symbFile)) { //create the file if it doesn't exist - TODO: this really doesn't work since the python script takes so long to execute. A solution could be to have a loading screen, or just to quit if it doesn't exist
  if(substr_count(PHP_OS,"WIN")) { //is windows
    exec("python $fileLocation/allNdaq.py",$o,$r);
  } else { //is not windows
    exec("py $fileLocation/allNdaq.py",$o,$r);
  }
}
$symbs = (array)json_decode(file_get_contents($symbFile, true)); //get all the symbols & company names from the file stored into a keyed array


//get $numHeads number of headlines for $symb from the internet
function getInternetHeadlines($symb, $numHeads) {
  //TODO: use multiple sources (cnbc, yahoo finance, market watch)
  // ^ it should randomly select one of the sources and save them in the same format
  $url = "https://api.nasdaq.com/api/news/topic/articlebysymbol?q=$symb%7Cstocks%26offset=0%26limit=$numHeads";
  
  if(substr_count(PHP_OS,"WIN")>0) { //is a windows system
    exec("powershell \$r = curl \"".$url."\" -UseBasicParsing ; \$r.content", $headlines); //use the windows PS curl
  } else {
    exec("curl -A 'test/1.0 (Linux)' $url",$headlines); //use the linux curl (TODO: may want to change the user agent?)
  }
  //use this for testing instead of the other getting it from the api all the time
  $headlines = json_decode($headlines[0],true)['data']; //isolate just the headline list after converting to json object
  return $headlines;
}


//get $n headlines for the specified $symb from the file or from the internet
function getHeadline($symb) {
  global $headlinesFile;
  $numHeads = 5; #get this many headlines per request
  //check that the headlines file exists
  if(file_exists($headlinesFile)) {
    //file exists, read it and get the headlines
    $headlines = (array)json_decode(file_get_contents($headlinesFile), true);
    //echo count(" $headlines ");
    if(count($headlines)<1) { //if none are remaining, get headlines from internet and write to file
      $headlines = getInternetHeadlines($symb, $numHeads); //get headlines rom the internet
      file_put_contents($headlinesFile,json_encode($headlines)); //write the headlines to the file
      //var_dump($headlines);
    }
  } else { //file doesn't exist, get headlines from internet and write to file
    $headlines = getInternetHeadlines($symb, $numHeads);
    file_put_contents($headlinesFile,json_encode($headlines));  
  }
   
  return $headlines[0]['title']; #return the first term in the array always
}

//get the supposed sentiment value of a str (based on what we've calculated)
function getSent($str) {
  global $wordFile;
  //sentiment calc is something like sum(averages sents of each word)/number of words
  //TODO: there should also be a confidence number as well (calculated based on number of votes)
  //confidence should be calculated according to the number of votes (more votes=more confidence (and similar number of votes per word))
  //confidence could be min^2/max number of votes? That way we get relative spread of votes  with basis on the minimum?
  //or could be avgVotes*min/max
  
  //get the word sentiments
  $wordScores = (array) json_decode(file_get_contents($wordFile),true);
  
  //clean string to only have lowercase letters and spaces
  $str = strtolower(preg_replace("/[^A-Za-z ]/","",$str));
  //turn into array
  $txt = explode(" ",$str);
  
  $sent = 0;
  $conf = 0;
  foreach($txt as $w) {
    if(array_key_exists($w,$wordScores)) {
      $sent += $wordScores[$w]['sent']/$wordScores[$w]['votes'];
      $conf += $wordScores[$w]['votes'];
    }
  }
  $sent /= count($txt); //average sentiment over number of words
  $conf /= count($txt); //average votes over number of words
  return ["sent"=>$sent,"conf"=>$conf];
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

if(count($_POST)>0) { //make sure post has data
  //var_dump($_POST);
  if(array_key_exists("head",$_POST) and array_key_exists("sent",$_POST)) { //make sure it has the right data
    if(file_exists($headlinesFile)) { //ensure we have saveed headlines
      $headList = (array)json_decode(file_get_contents($headlinesFile),true); //get the list of recorded headlines      
    } else { //we don't have saved headlines
      $headlines = [];
    }
    
    //isolate just the headline from the data
    $heads = [];
    foreach($headList as $h) { $heads[] = $h['title']; }
    
    
    if(in_array($_POST['head'], $heads)) { //make sure that the headline is in the headline list
      $head = strtolower(preg_replace("/[^A-Za-z ]/"," ",$_POST['head'])); //strip out special chars (other than letters) (turn them into spaces)
      $wordList = explode(" ",$head); //split by spaces (will create a bunch of blank elements)

      //remove all words <=1 letter long (including blank elements)
      foreach($wordList as $i=>$w) {
        if(strlen($w)<=1) {
          unset($wordList[$i]); //TODO: is unset the right fxn to use? Might not matter, but it preserves the indicies
        }
      }
      
      //populate the word scores
      if(file_exists($wordFile)) {
        $wordScores = (array) json_decode(file_get_contents($wordFile),true); //load in the words with scores
      } else {
        $wordScores = [];
      }
      
      foreach($wordList as $w) { //loop thru every word in the headline
        if(array_key_exists($w, $wordScores)) { #if it's already present in the scores, then append to it
          $wordScores[$w] = array("sent" => (int) $wordScores[$w]['sent'] + (int) $_POST['sent'],
                              "votes" => (int) $wordScores[$w]['votes'] + 1
                            );
        } else { //if it's not already present in the scores, then init it
          $wordScores[$w] = array("sent" => (int)$_POST['sent'], "votes" => 1);
        }
      }

      file_put_contents($wordFile, json_encode($wordScores));
      
      $idx = array_search($_POST['head'],$headList); //find where the processed headline is
      array_splice($headList,$idx,1); //remove the headline from the headline list
      
      file_put_contents($headlinesFile,json_encode($headList));
      //echo "blah";
    } else { //else the headline is not in the headline list
      var_dump($_POST); //TODO: this shows up periodically, could address by simply skipping (not doing anything), or by using both and getting both votes in
    }
  }
}




$symb = array_rand($symbs);
$head = getHeadline($symb);
$headSent = getSent($head);
?>
 <!DOCTYPE html>

<html lang=en>
  <head>
    <title>Sentiment Analysis Game</title>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <style>
      html, body {
        width: 100%;
        font-family: sans-serif;
        margin: auto;
        text-align: center;
        font-size: 14pt;
      }
      
      #headline {
        height: 4em;
      }
      
      #voting p,#score,#headline {
        font-family: sans-serif;
        font-size: 14pt;
        text-align: center;
        border: none;
        color: #000;
        background-color: #fff;
      }
      
      #score {
        width: 3em;
        border-bottom: solid black 1px;
      }
      
      button {
        border-radius: 10px;
        font-size: 24pt;
        background-color: #fff;
      }
      
      button:focus { background-color: #aaa; }
      
      #headline {
        margin: 0 auto;
        width: 33%;
        overflow: hidden;
        display: block;
        resize: none;
      }

      #voting { margin-top: 20%; }
      
      #computed {
        width: 50%;
        border: solid grey 3px;
        border-radius: 10px;
        margin: 0 auto;
      }
      
      #computed * { text-align: left; }
      
      #computed h1 {
        font-size: 14pt;
        font-style: italic;
        font-weight: bold;
      }
      
      #computed p {
        font-size: 12pt;
      }
      
      @media screen and (max-width: 640px){
        #headline, #computed { width: 90%; }
        #voting { margin-top: 50%; }
      }
    </style>
  </head>
  <body>
    <div id="voting">
      <form method="post">
        <p>Your score: <input id='score' type="text" readonly name="score" tabindex=-1 value="<?php if(array_key_exists("score",$_POST)) { echo ((int) $_POST['score'])+1; } else { echo 0; }?>"/></p>
        <textarea readonly name="head" tabindex=-1 id="headline"><?php echo $head; ?></textarea>
        <p>
          <button type="submit" name="sent" value="-1">-</button>&emsp;
          <button type="submit" name="sent" value="0" autofocus>&#215;</button>&emsp;
          <button type="submit" name="sent" value="1">+</button>
        </p>
      </form>
    </div>
        
    <div id="computed">
      <h1>What I think (my opinion, and how strongly I feel about it):</h1>
      <p><?php echo round($headSent['sent'],2)." - ";
      if($headSent['sent']>=0.6) { echo "very positive"; }
      elseif($headSent['sent']>=0.2) { echo "somewhat positive"; }
      elseif($headSent['sent']>=-0.2) { echo "neutral"; }
      elseif($headSent['sent']>=-0.6) { echo "somewhat negative"; }
      elseif($headSent['sent']>=-1) { echo "very negative"; }
      ?></p>
      <p><?php echo (int) $headSent['conf']." - ";
      if($headSent['conf']>=10000) { echo "very confident"; }
      elseif($headSent['conf']>=1000) { echo "somewhat confident"; }
      elseif($headSent['conf']>=100) { echo "somewhat unconfident"; }
      else { echo "very unconfident"; }
      ?></p>
    </div>
  </body>
</html>

